use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct Account {
    pub account_id: i64,
    pub account_name: String,

    pub x: i64,
    pub y: i64,
}