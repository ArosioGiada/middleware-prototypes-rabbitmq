use uuid::Uuid;
use common::account::Account;
use common::database::Database;


pub trait DatabaseBackendExt {
    async fn add_account(&self, account_name: &str, x: i64, y: i64) -> i64;
    async fn get_account_by_session_id(&self, session_id: Uuid) -> Option<Account>;
    async fn set_account_position(&self, account_id: i64, x: i64, y: i64);
    async fn add_account_session_id(&self, account_id: i64) -> Uuid;
    async fn get_accounts(&self) -> Vec<Account>;
}

impl DatabaseBackendExt for Database {
    async fn add_account(&self, account_name: &str, x: i64, y: i64) -> i64 {
        let mut conn = self.pool.acquire().await.unwrap();

        sqlx::query_scalar!("INSERT INTO accounts (account_name, x, y) VALUES ($1, $2, $3) RETURNING account_id", account_name, x, y).fetch_one(&mut *conn).await.unwrap()
    }

    async fn get_account_by_session_id(&self, session_id: Uuid) -> Option<Account> {
        let mut conn = self.pool.acquire().await.unwrap();

        sqlx::query_as!(Account, "
            SELECT accounts.account_id, account_name, x, y
            FROM sessions
            JOIN accounts ON accounts.account_id = sessions.account_id
            WHERE sessions.session_id = $1
        ", &session_id).fetch_optional(&mut *conn).await.unwrap()
    }

    async fn set_account_position(&self, account_id: i64, x: i64, y: i64) {
        let mut conn = self.pool.acquire().await.unwrap();

        sqlx::query!("UPDATE accounts SET x = $1, y = $2 WHERE account_id = $3", x, y, account_id).execute(&mut *conn).await.unwrap();
    }

    async fn add_account_session_id(&self, account_id: i64) -> Uuid {
        let mut conn = self.pool.acquire().await.unwrap();

        sqlx::query_scalar!("INSERT INTO sessions (account_id) VALUES ($1) RETURNING session_id", account_id).fetch_one(&mut *conn).await.unwrap()
    }

    async fn get_accounts(&self) -> Vec<Account> {
        let mut conn = self.pool.acquire().await.unwrap();

        sqlx::query_as!(Account, "SELECT account_id, account_name, x, y FROM accounts").fetch_all(&mut *conn).await.unwrap()
    }
}