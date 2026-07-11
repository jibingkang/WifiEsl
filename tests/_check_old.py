import sys, json, sqlite3
sys.path.insert(0, 'backend')

# 直接解析 fabric.js 更新旧数据
db = sqlite3.connect("backend/data/wifi_esl.db")
db.row_factory = sqlite3.Row

cur = db.execute("SELECT id, tid, tname FROM templates WHERE screen_width=0 OR screen_height=0")
rows = cur.fetchall()

for row in rows:
    tid = row['tid']
    # 这里需要 fabric_data 才能解析分辨率，但旧数据没存 fabric_data
    # 只能重新同步才能获取
    print(f"{row['tname']}: 需要重新同步才能获取分辨率")

db.close()
print(f"\n共 {len(rows)} 个旧模板需要重新同步")
