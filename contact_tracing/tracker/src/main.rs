mod database;

use std::collections::HashMap;
use std::sync::Arc;
use lapin::{BasicProperties, Channel, Connection, ConnectionProperties, Consumer};
use lapin::options::{BasicAckOptions, BasicConsumeOptions, BasicPublishOptions, QueueBindOptions, QueueDeclareOptions};
use lapin::types::FieldTable;
use sqlx::postgres::{PgConnectOptions, PgPoolOptions};
use tracing::{error, info};
use futures_util::StreamExt;
use tokio::select;
use tokio::sync::{mpsc, Mutex};
use tracing_subscriber::EnvFilter;
use common::account::Account;
use common::broker::{Broker, POSITION_EXCHANGE, QUERY_REQUEST_EXCHANGE, QUERY_RESPONSE_EXCHANGE};
use common::database::Database;
use common::query::{QueryRequest, QueryResponse};
use crate::database::DatabaseBackendExt as _;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .init();

    info!("Hello, World!");
    
    let database = Database::new().await;
    let accounts = database.get_accounts().await;
    let mut accounts: HashMap<i64, Account> = accounts.into_iter().map(|account|(account.account_id, account)).collect();

    let broker = Broker::new().await;
    let mut position_consumer = create_consumer(&broker.channel, POSITION_EXCHANGE).await;
    let mut query_request_consumer = create_consumer(&broker.channel, QUERY_REQUEST_EXCHANGE).await;

    let mut collisions = Vec::new();

    loop {
        select! {
            delivery = position_consumer.next() => {
                let Some(delivery) = delivery else {
                    error!("rabbitmq channel closed");
                    break;
                };
                let delivery = delivery.unwrap();
                delivery.ack(BasicAckOptions::default()).await.unwrap();
                let message: Account = postcard::from_bytes(&delivery.data).unwrap();

                info!("received an event from position exchange: {message:?}");

                for (account_id, account) in accounts.iter().filter(|(id, _)| **id != message.account_id) {
                    if (account.x == message.x) && (account.y == message.y) {
                        collisions.push((account_id.clone(), message.account_id));

                        info!("collision detected between {{account_id: {}}} and {{account_id: {}}}, location: x: {}, y: {}", message.account_id, account_id, message.x, message.y)
                    }
                }

                accounts.insert(message.account_id, message);
            }

            delivery = query_request_consumer.next() => {
                let Some(delivery) = delivery else {
                    error!("rabbitmq channel closed");
                    break;
                };
                let delivery = delivery.unwrap();
                delivery.ack(BasicAckOptions::default()).await.unwrap();
                let request: QueryRequest = postcard::from_bytes(&delivery.data).unwrap();

                let collided_accounts = collisions.iter().rev().filter_map(|&(a, b)|{
                    if a == request.account_id {
                        Some(b)
                    } else if b == request.account_id {
                        Some(a)
                    } else {
                        None
                    }
                }).collect();

                let response = QueryResponse {
                    collided_accounts,
                };

                const MESSAGE_BUFFER_SIZE: usize = 2usize.pow(16);
                let response = postcard::to_vec::<_, MESSAGE_BUFFER_SIZE>(&response).unwrap();

                broker.channel.basic_publish(
                    QUERY_RESPONSE_EXCHANGE.into(),
                    request.account_id.to_string().into(),
                    BasicPublishOptions::default(),
                    &response,
                    BasicProperties::default().with_delivery_mode(1),
                ).await.unwrap().await.unwrap();
            }
        }
    }
}

async fn create_consumer(channel: &Channel, exchange: &str) -> Consumer {
    let queue = channel.queue_declare(
        "".into(),
        QueueDeclareOptions {
            exclusive: true,
            auto_delete: true,
            durable: false,
            ..Default::default()
        },
        FieldTable::default()
    ).await.unwrap();

    channel.queue_bind(
        queue.name().clone(),
        exchange.into(),
        "#".into(),
        QueueBindOptions::default(),
        FieldTable::default(),
    ).await.unwrap();

    let consumer = channel.basic_consume(
        queue.name().clone(),
        "".into(),
        BasicConsumeOptions::default(),
        FieldTable::default()
    ).await.unwrap();

    consumer
}