use axum::Router;
use tower_http::services::{ServeDir, ServeFile};
use crate::api;
use crate::context::Context;

pub fn router(context: Context) -> Router<Context> {
    let spa = ServeDir::new("./frontend/dist").fallback(ServeFile::new("./frontend/dist/index.html"));

    Router::new()
        .nest("/api", api::router(context))
        .fallback_service(spa)
}