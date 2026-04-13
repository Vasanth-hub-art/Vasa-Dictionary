import sqlite3

# Connect to database (creates database.db if not exists)
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# ---------- DICTIONARY TABLE ----------
cursor.execute("""
CREATE TABLE IF NOT EXISTS dictionary (
    word TEXT PRIMARY KEY,
    meaning TEXT
)
""")

# ---------- USERS TABLE ----------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

# ---------- HISTORY TABLE ----------
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    word TEXT,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ---------- SAMPLE DATA ----------

# Dictionary sample words
cursor.execute("INSERT OR IGNORE INTO dictionary VALUES ('python', 'A programming language')")
cursor.execute("INSERT OR IGNORE INTO dictionary VALUES ('apple', 'A fruit')")
cursor.execute("INSERT OR IGNORE INTO dictionary VALUES ('flask', 'A Python web framework')")

# Admin user
cursor.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123')")

# Optional: sample user
cursor.execute("INSERT OR IGNORE INTO users VALUES ('user', '123')")

# Save changes
conn.commit()
conn.close()

print("✅ Database setup completed successfully!")
