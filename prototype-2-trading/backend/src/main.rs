use std::net::ToSocketAddrs;
use std::time::Duration;
use axum_server::tls_rustls::RustlsConfig;
use tokio::time::sleep;
use tower_http::trace::TraceLayer;
use tracing::info;
use tracing_subscriber::EnvFilter;
use crate::context::Context;

mod app;
mod context;
mod api;
mod authentication_extractor;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .init();

    info!("Hello, World!");

    let config = RustlsConfig::from_pem_file("assets/localhost.pem", "assets/localhost-key.pem").await.unwrap();
    let addr = "0.0.0.0:8080".to_socket_addrs().unwrap().next().unwrap();
    let context = Context::new().await;

    let app = app::router(context.clone())
        .with_state(context)
        .layer(TraceLayer::new_for_http());

    axum_server::bind_rustls(addr, config).serve(app.into_make_service()).await.unwrap()
}
