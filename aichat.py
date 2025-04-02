import sqlite3

conn = sqlite3.connect("users.db")
c = conn.cursor()

# DROP existing history table (will remove all old data)
c.execute("DROP TABLE IF EXISTS history")

# Recreate the table with full schema
c.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        user_image_url TEXT,
        ai_response TEXT,
        ai_generated_image_url TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
