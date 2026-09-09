use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct QueryRequest {
    pub account_id: i64
}

#[derive(Serialize, Deserialize, Debug)]
pub struct QueryResponse {
    pub collided_accounts: Vec<i64>,
}