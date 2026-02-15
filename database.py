import sqlite3

conn = sqlite3.connect("database.db")

# Existing tips table
conn.execute("""
CREATE TABLE IF NOT EXISTS tips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match TEXT,
    prediction TEXT,
    odds TEXT,
    category TEXT
)
""")

# New users table
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password TEXT,
    paid_status TEXT DEFAULT 'No',
    vip_expiry TEXT
)
""")

conn.close()
print("Database and users table ready")