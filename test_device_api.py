import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        resp = await client.post('http://127.0.0.1:8001/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = resp.json().get('data', {}).get('token')
        print(f'Token: {token[:30]}...' if token else 'No token')
        
        if token:
            headers = {'Authorization': f'Bearer {token}'}
            resp2 = await client.get('http://127.0.0.1:8001/api/v1/devices?page=1&page_size=1', headers=headers)
            data = resp2.json()
            print(f'Device list code: {data.get("code")}')
            items = data.get('data', {}).get('items', [])
            if items:
                mac = items[0].get('mac')
                print(f'Testing MAC: {mac}')
                resp3 = await client.get(f'http://127.0.0.1:8001/api/v1/devices/mac/{mac}', headers=headers)
                print(f'Device by MAC status: {resp3.status_code}')
                print(f'Response: {resp3.text[:500]}')

asyncio.run(test())
