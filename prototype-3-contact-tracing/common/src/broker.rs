use std::time::Duration;
use lapin::{Channel, Connection, ConnectionProperties, ExchangeKind};
use lapin::options::ExchangeDeclareOptions;
use lapin::types::FieldTable;
use tokio::time::sleep;
use tracing::info;

pub const POSITION_EXCHANGE: &str = "position";
pub const QUERY_REQUEST_EXCHANGE: &str = "query_request";
pub const QUERY_RESPONSE_EXCHANGE: &str = "query_response";

pub struct Broker {
    pub conn: Connection,
    pub channel: Channel,
}

impl Broker {
    pub async fn new() -> Self {
        let conn = loop {
            match Connection::connect(
                "amqp://admin:secret@rabbitmq:5672",
                ConnectionProperties::default(),
            ).await {
                Ok(conn) => break conn,
                Err(_) => {
                    info!("Failed to connect to rabbitmq. Initialising retry");
                    sleep(Duration::from_secs(5)).await;
                }
            }
        };

        info!("Connected to RabbitMQ");

        let channel = conn.create_channel().await.unwrap();

        channel.exchange_declare(
            POSITION_EXCHANGE.into(),
            ExchangeKind::Topic,
            ExchangeDeclareOptions{
                durable: true,
                .. Default::default()
            },
            FieldTable::default(),
        ).await.unwrap();

        channel.exchange_declare(
            QUERY_REQUEST_EXCHANGE.into(),
            ExchangeKind::Topic,
            ExchangeDeclareOptions{
                durable: true,
                .. Default::default()
            },
            FieldTable::default(),
        ).await.unwrap();

        channel.exchange_declare(
            QUERY_RESPONSE_EXCHANGE.into(),
            ExchangeKind::Topic,
            ExchangeDeclareOptions{
                durable: true,
                .. Default::default()
            },
            FieldTable::default(),
        ).await.unwrap();

        Self {
            conn,
            channel,
        }
    }
}