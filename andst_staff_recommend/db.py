
import sqlite3
from datetime import datetime

DB_NAME = "recommend.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            week TEXT,
            name TEXT,
            type TEXT,
            new_app INTEGER,
            exist_app INTEGER,
            line INTEGER,
            survey INTEGER,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_or_update_record(record):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM records WHERE date=? AND name=? AND type=?", (record["date"], record["name"], record["type"]))
    row = c.fetchone()
    record["updated_at"] = datetime.now().isoformat()
    if row:
        c.execute("""
            UPDATE records
            SET week=?, new_app=?, exist_app=?, line=?, survey=?, updated_at=?
            WHERE id=?
        """, (
            record["week"],
            record.get("新規", 0),
            record.get("既存", 0),
            record.get("LINE", 0),
            record.get("アンケート", 0),
            record["updated_at"],
            row[0]
        ))
    else:
        c.execute("""
            INSERT INTO records (date, week, name, type, new_app, exist_app, line, survey, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["date"],
            record["week"],
            record["name"],
            record["type"],
            record.get("新規", 0),
            record.get("既存", 0),
            record.get("LINE", 0),
            record.get("アンケート", 0),
            record["updated_at"]
        ))
    conn.commit()
    conn.close()

def load_all_records():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT date, week, name, type, new_app, exist_app, line, survey FROM records")
    rows = c.fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "date": row[0],
            "week": row[1],
            "name": row[2],
            "type": row[3],
            "新規": row[4],
            "既存": row[5],
            "LINE": row[6],
            "アンケート": row[7]
        })
    return result


def init_target_table():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS targets (
            month TEXT,
            type TEXT,
            target INTEGER,
            PRIMARY KEY (month, type)
        )
    """)
    conn.commit()
    conn.close()

def set_target(month, category, value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO targets (month, type, target)
        VALUES (?, ?, ?)
        ON CONFLICT(month, type) DO UPDATE SET target=excluded.target
    """, (month, category, value))
    conn.commit()
    conn.close()

def get_target(month, category):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT target FROM targets WHERE month=? AND type=?", (month, category))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0
