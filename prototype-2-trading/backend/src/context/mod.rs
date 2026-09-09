pub mod database;

use std::sync::Arc;
use common::broker::Broker;
use common::database::Database;

#[derive(Clone)]
pub struct Context(pub Arc<InnerContext>);

impl Context {
    pub async fn new() -> Self {
        Self(Arc::new(InnerContext::new().await))
    }
}

pub struct InnerContext {
    pub broker: Broker,
    pub database: Database,
    pub dimensions: [i64; 2],
}

impl InnerContext {
    pub async fn new() -> Self {
        let broker = Broker::new().await;
        let database = Database::new().await;
        let dimensions = [
            std::env::var("WIDTH").unwrap().parse().unwrap(), 
            std::env::var("HEIGHT").unwrap().parse().unwrap()
        ];

        Self {
            broker,
            database,
            dimensions,
        }
    }
}