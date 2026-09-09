use sqlx::PgPool;
use sqlx::postgres::{PgConnectOptions, PgPoolOptions};
use std::time::Duration;
use tokio::time::sleep;
use tracing::info;

pub struct Database {
    pub pool: PgPool,
}

impl Database {
    pub async fn new() -> Self {
        let username = "admin";
        let password = "secret";

        let options = PgConnectOptions::new()
            .username(username)
            .password(password)
            .database("postgres")
            .host("postgres");

        let pool = loop {
            match PgPoolOptions::new()
                .max_connections(2)
                .connect_with(options.clone())
                .await
            {
                Ok(pool) => break pool,
                Err(_) => {
                    info!("failed to connect to postgres. initialising retry");
                    sleep(Duration::from_secs(5)).await;
                }
            }
        };

        info!("Connected to Postgres");
        Self { pool }
    }
}
