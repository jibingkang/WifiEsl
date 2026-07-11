import sqlite3
db = sqlite3.connect("backend/data/wifi_esl.db")
cursor = db.execute("PRAGMA table_info(templates)")
for row in cursor.fetchall():
    print(row[1], row[2])
db.close()
