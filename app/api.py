from decimal import Decimal

from flask import Flask, jsonify, request

import db

app = Flask(__name__)

_schema_ready = False


def get_conn():
    global _schema_ready
    conn = db.connect()
    if not _schema_ready:
        db.init_schema(conn)
        _schema_ready = True
    return conn


def _clean(row):
    """Make DB rows JSON friendly."""
    out = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            out[k] = float(v)
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/orders")
def place_order():
    """1. Customer places an order  ->  2. stored in MySQL as PENDING."""
    data = request.get_json(silent=True) or {}
    try:
        customer = str(data["customer_name"]).strip()
        product = str(data["product"]).strip()
        quantity = int(data["quantity"])
        amount = Decimal(str(data["amount"]))
    except (KeyError, ValueError, ArithmeticError):
        return jsonify(error="required: customer_name, product, quantity(int), amount(number)"), 400
    if not customer or not product or quantity <= 0 or amount < 0:
        return jsonify(error="invalid values"), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO orders (customer_name, product, quantity, amount) "
                "VALUES (%s, %s, %s, %s)",
                (customer, product, quantity, amount),
            )
            order_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    return jsonify(id=order_id, status="PENDING"), 201


@app.get("/orders")
def list_orders():
    status = request.args.get("status")
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if status:
                cur.execute(
                    "SELECT * FROM orders WHERE status=%s ORDER BY id DESC LIMIT 200",
                    (status.upper(),),
                )
            else:
                cur.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 200")
            rows = cur.fetchall()
    finally:
        conn.close()
    return jsonify([_clean(r) for r in rows])


@app.get("/orders/<int:order_id>")
def get_order(order_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
            row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(_clean(row))


@app.get("/reports")
def list_reports():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM daily_reports ORDER BY report_date DESC LIMIT 30")
            rows = cur.fetchall()
    finally:
        conn.close()
    return jsonify([_clean(r) for r in rows])
