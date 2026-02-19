"""SQLite storage for price snapshots and runs."""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "btdb.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            triggered_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            asin TEXT NOT NULL,
            is_yours INTEGER NOT NULL,
            price REAL,
            list_price REAL,
            deal_type TEXT,
            deal_details TEXT,
            coupon_amount TEXT,
            coupon_code TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        );
    """)
    conn.commit()
    conn.close()


def create_run():
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO runs (triggered_at) VALUES (?)",
        (datetime.utcnow().isoformat(),),
    )
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def save_snapshot(run_id, asin, is_yours, price=None, list_price=None,
                  deal_type=None, deal_details=None, coupon_amount=None, coupon_code=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO snapshots (run_id, asin, is_yours, price, list_price,
                              deal_type, deal_details, coupon_amount, coupon_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (run_id, asin, 1 if is_yours else 0, price, list_price,
          deal_type, deal_details, coupon_amount, coupon_code))
    conn.commit()
    conn.close()


def get_recent_runs(limit=10):
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, triggered_at FROM runs ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_snapshots_for_run(run_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT asin, is_yours, price, list_price, deal_type, deal_details,
                  coupon_amount, coupon_code
           FROM snapshots WHERE run_id = ? ORDER BY is_yours DESC, asin""",
        (run_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
