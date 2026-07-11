import asyncio, sys
sys.path.insert(0, 'backend')
from services.db_service import get_all_templates
async def check():
    tpls = await get_all_templates()
    for t in tpls[:2]:
        print(f"{t['tname']}: image={repr(t.get('image'))}")
asyncio.run(check())
