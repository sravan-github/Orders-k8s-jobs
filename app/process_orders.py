"""Kubernetes Job: process all PENDING orders (PENDING -> PROCESSED).

Exit code 0 = Job succeeded, non-zero = Job failed (visible in Grafana).
Use --fail to simulate a failing Job for the dashboard demo.
"""
import argparse
import sys
import time

import db

BATCH_SIZE = 50


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail", action="store_true", help="simulate a failure")
    args = parser.parse_args()

    conn = db.connect()
    db.init_schema(conn)

    if args.fail:
        print("Simulated failure requested", flush=True)
        sys.exit(1)

    total = 0
    while True:
        with conn.cursor() as cur:
            # SKIP LOCKED lets several workers run safely in parallel.
            cur.execute(
                "SELECT id FROM orders WHERE status='PENDING' "
                "ORDER BY id LIMIT %s FOR UPDATE SKIP LOCKED",
                (BATCH_SIZE,),
            )
            ids = [r["id"] for r in cur.fetchall()]
            if not ids:
                conn.commit()
                break
            for order_id in ids:
                time.sleep(0.1)  # stand-in for real work (payment, stock, shipping...)
                print(f"Processed order {order_id}", flush=True)
            marks = ",".join(["%s"] * len(ids))
            cur.execute(
                f"UPDATE orders SET status='PROCESSED', processed_at=NOW() WHERE id IN ({marks})",
                ids,
            )
        conn.commit()
        total += len(ids)

    print(f"Done. Processed {total} order(s).", flush=True)
    conn.close()


if __name__ == "__main__":
    main()
