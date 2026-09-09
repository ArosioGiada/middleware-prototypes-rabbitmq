use axum::extract::State;
use axum::response::{IntoResponse, Response};
use axum::{Json, Router};
use axum::routing::get;
use serde::Serialize;
use crate::context::Context;

pub fn router() -> Router<Context> {
    Router::new()
        .route("/dimensions", get(get_dimensions))
}

#[derive(Serialize)]
struct GetDimensionsResponse {
    w: i64,
    h: i64,
}

async fn get_dimensions(
    State(state): State<Context>
) -> Response {
    let [w, h] = state.0.dimensions;

    Json(GetDimensionsResponse { w, h }).into_response()
}