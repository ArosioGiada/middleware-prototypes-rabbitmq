use common::account::Account;
use common::database::Database;

pub trait DatabaseBackendExt {
    async fn get_accounts(&self) -> Vec<Account>;
}

impl DatabaseBackendExt for Database {
    async fn get_accounts(&self) -> Vec<Account> {
        let mut conn = self.pool.acquire().await.unwrap();
        sqlx::query_as!(Account, "SELECT * FROM accounts").fetch_all(&mut *conn).await.unwrap()
    }
}