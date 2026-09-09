use crate::authentication_extractor::Authentication;
use crate::context::database::DatabaseBackendExt as _;
use crate::context::Context;
use axum::extract::State;
use axum::http::StatusCode;
use axum::response::sse::{Event, KeepAlive};
use axum::response::{IntoResponse, Response, Sse};
use axum::routing::{get, post};
use axum::{Json, Router};
use common::account::Account;
use common::broker::POSITION_EXCHANGE;
use futures_util::Stream;
use futures_util::StreamExt;
use lapin::options::{BasicAckOptions, BasicConsumeOptions, BasicPublishOptions, QueueBindOptions, QueueDeclareOptions};
use lapin::types::FieldTable;
use lapin::BasicProperties;
use serde::{Deserialize, Serialize};
use std::convert::Infallible;
use std::time::Duration;
use tracing::error;

pub fn router() -> Router<Context> {
    Router::new()
        .route("/", post(post_position))
        .route("/callback", get(get_position_callback))
}

#[derive(Deserialize)]
struct PostPositionRequest {
    x: i64,
    y: i64,
}

async fn post_position(
    State(state): State<Context>,
    authentication: Authentication,
    Json(request): Json<PostPositionRequest>,
) -> Response {
    if request.x < 0 || request.y < 0 || request.x >= state.0.dimensions[0] || request.y >= state.0.dimensions[1] {
        return StatusCode::BAD_REQUEST.into_response();
    }
    
    
    state.0.database.set_account_position(authentication.account.account_id, request.x, request.y).await;

    let message = Account {
        x: request.x,
        y: request.y,
        account_id: authentication.account.account_id,
        account_name: authentication.account.account_name,
    };

    const MESSAGE_BUFFER_SIZE: usize = 2usize.pow(8);
    let message = postcard::to_vec::<_, MESSAGE_BUFFER_SIZE>(&message).unwrap();

    state.0.broker.channel.basic_publish(
        POSITION_EXCHANGE.into(),
        authentication.account.account_id.to_string().into(),
        BasicPublishOptions::default(),
        &message,
        BasicProperties::default().with_delivery_mode(1),
    ).await.unwrap().await.unwrap();

    StatusCode::OK.into_response()
}


async fn get_position_callback(
    State(state): State<Context>,
) -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    let queue = state.0.broker.channel.queue_declare(
        "".into(),
        QueueDeclareOptions {
            exclusive: true,
            auto_delete: true,
            durable: false,
            ..Default::default()
        },
        FieldTable::default()
    ).await.unwrap();

    state.0.broker.channel.queue_bind(
        queue.name().clone(),
        POSITION_EXCHANGE.into(),
        "#".into(),
        QueueBindOptions::default(),
        FieldTable::default(),
    ).await.unwrap();

    let consumer = state.0.broker.channel.basic_consume(
        queue.name().clone(),
        "".into(),
        BasicConsumeOptions::default(),
        FieldTable::default()
    ).await.unwrap();

    let stream = consumer.filter_map(async |delivery| {
        match delivery {
            Ok(delivery) => {
                delivery.ack(BasicAckOptions::default()).await.unwrap();
                let message: Account = postcard::from_bytes(&delivery.data).unwrap();
                let json = serde_json::to_string(&message).unwrap();

                Some(Ok(Event::default().data(json)))
            }
            Err(err) => {
                error!("error: {err:?}");
                None
            }
        }
    });

    Sse::new(stream).keep_alive(KeepAlive::new().interval(Duration::from_secs(15)))
}