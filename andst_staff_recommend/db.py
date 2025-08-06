import sqlite3
from datetime import date

DB_NAME = "data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS records (
            date TEXT,
            week TEXT,
            name TEXT,
            type TEXT,
            新規 INTEGER DEFAULT 0,
            既存 INTEGER DEFAULT 0,
            LINE INTEGER DEFAULT 0,
            アンケート INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def init_target_table():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS targets (
            type TEXT PRIMARY KEY,
            value INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save_record(record):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM records WHERE date=? AND name=? AND type=?", (record["date"], record["name"], record["type"]))
    c.execute("""
        INSERT INTO records (date, week, name, type, 新規, 既存, LINE, アンケート)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["date"],
        record["week"],
        record["name"],
        record["type"],
        record.get("新規", 0),
        record.get("既存", 0),
        record.get("LINE", 0),
        record.get("アンケート", 0),
    ))
    conn.commit()
    conn.close()

def load_all_records():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM records")
    rows = c.fetchall()
    conn.close()
    records = []
    for row in rows:
        records.append({
            "date": row[0],
            "week": row[1],
            "name": row[2],
            "type": row[3],
            "新規": row[4],
            "既存": row[5],
            "LINE": row[6],
            "アンケート": row[7],
        })
    return records

def delete_record(target_date, name, category):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM records WHERE date=? AND name=? AND type=?", (target_date.isoformat(), name, category))
    conn.commit()
    conn.close()

def get_target(category):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM targets WHERE type=?", (category,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def set_target(category, value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("REPLACE INTO targets (type, value) VALUES (?, ?)", (category, value))
    conn.commit()
    conn.close()
