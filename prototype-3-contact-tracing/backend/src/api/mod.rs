mod position;
mod auth;
mod world;
mod accounts;

use axum::Router;
use crate::context::Context;

pub fn router(context: Context) -> Router<Context> {
    Router::new()
        .nest("/auth", auth::router())
        .nest("/world", world::router())
        .nest("/position", position::router())
        .nest("/accounts", accounts::router())
}