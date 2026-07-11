import sqlite3
db = sqlite3.connect("backend/data/wifi_esl.db")
db.row_factory = sqlite3.Row
cursor = db.execute("SELECT tname, image, screen_width, screen_height, remote_updated_at FROM templates LIMIT 2")
for row in cursor.fetchall():
    print(f"{row['tname']}: image={bool(row['image'])}, w={row['screen_width']}, h={row['screen_height']}, updated={repr(row['remote_updated_at'])}")
db.close()
