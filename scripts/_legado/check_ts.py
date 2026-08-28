import sqlite3

DB = r"C:/Users/David Jr/.local/share/opencode/opencode.db"
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
rows = c.execute("SELECT time_created FROM part ORDER BY time_created DESC LIMIT 1").fetchone()
print("ultimo time_created:", rows[0] if rows else None)
c.close()