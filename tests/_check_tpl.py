import aiosqlite, asyncio

async def check():
    db = await aiosqlite.connect("backend/data/wifi_esl.db")
    db.row_factory = aiosqlite.Row
    cur = await db.execute("SELECT tid, tname, image FROM templates LIMIT 5")
    rows = await cur.fetchall()
    for r in rows:
        print(f"{r['tname']} | image={repr(r['image'])}")
    # 也检查列是否存在
    info = await db.execute("PRAGMA table_info(templates)")
    cols = [(row[1], row[2]) for row in await info.fetchall()]
    print(f"\nColumns: {cols}")
    await db.close()

asyncio.run(check())
