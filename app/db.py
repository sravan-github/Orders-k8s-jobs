import os
import time

import pymysql
import pymysql.cursors

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS orders (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        customer_name VARCHAR(100)  NOT NULL,
        product       VARCHAR(100)  NOT NULL,
        quantity      INT           NOT NULL,
        amount        DECIMAL(10,2) NOT NULL,
        status        VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
        created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
        processed_at  TIMESTAMP     NULL,
        INDEX idx_status (status),
        INDEX idx_created (created_at)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_reports (
        report_date      DATE PRIMARY KEY,
        total_orders     INT           NOT NULL,
        pending_orders   INT           NOT NULL,
        processed_orders INT           NOT NULL,
        revenue          DECIMAL(12,2) NOT NULL,
        generated_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
]


def connect(retries=30, delay=2):
    """Connect to MySQL, retrying while the database is still starting."""
    last = None
    for _ in range(retries):
        try:
            return pymysql.connect(
                host=os.environ.get("DB_HOST", "mysql"),
                port=int(os.environ.get("DB_PORT", "3306")),
                user=os.environ.get("DB_USER", "orders"),
                password=os.environ["DB_PASSWORD"],
                database=os.environ.get("DB_NAME", "ordersdb"),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
            )
        except pymysql.err.OperationalError as exc:
            last = exc
            print(f"MySQL not ready ({exc}); retrying in {delay}s", flush=True)
            time.sleep(delay)
    raise RuntimeError(f"Could not connect to MySQL: {last}")


def init_schema(conn):
    with conn.cursor() as cur:
        for stmt in SCHEMA:
            cur.execute(stmt)
    conn.commit()
