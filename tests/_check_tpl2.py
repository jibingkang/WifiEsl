import sys, asyncio
sys.path.insert(0, 'backend')
from services.db_service import get_all_templates

async def check():
    tpls = await get_all_templates()
    for t in tpls[:2]:
        print(f"{t['tname']}: w={t.get('screen_width')}, h={t.get('screen_height')}, updated={t.get('remote_updated_at')}")

asyncio.run(check())
