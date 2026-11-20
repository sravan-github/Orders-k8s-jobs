"""Kubernetes CronJob: summarise the last 24h of orders into daily_reports."""
import db


def main():
    conn = db.connect()
    db.init_schema(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)                                        AS total_orders,
                   COALESCE(SUM(status='PENDING'), 0)              AS pending_orders,
                   COALESCE(SUM(status='PROCESSED'), 0)            AS processed_orders,
                   COALESCE(SUM(amount), 0)                        AS revenue
            FROM orders
            WHERE created_at >= NOW() - INTERVAL 1 DAY
            """
        )
        r = cur.fetchone()
        cur.execute(
            """
            REPLACE INTO daily_reports
                (report_date, total_orders, pending_orders, processed_orders, revenue)
            VALUES (CURDATE(), %s, %s, %s, %s)
            """,
            (r["total_orders"], r["pending_orders"], r["processed_orders"], r["revenue"]),
        )
    conn.commit()
    conn.close()
    print(
        f"Daily report: total={r['total_orders']} pending={r['pending_orders']} "
        f"processed={r['processed_orders']} revenue={r['revenue']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
