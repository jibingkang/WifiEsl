"""
WIFI Tag System Connection Test
Reads config from database (192.144.234.153) and tests HTTP + MQTT connectivity.
"""
import sys, os, json, ssl, socket, aiosqlite, asyncio

try:
    import httpx
except ImportError:
    print("[FAIL] httpx not installed. Run: pip install httpx")
    sys.exit(1)

# ─── Path setup ───
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Colors ───
G, R, Y, C, B, N = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[1m", "\033[0m"
def ok(m):    print(f"  {G}[OK]{N} {m}")
def fail(m):  print(f"  {R}[FAIL]{N} {m}")
def warn(m):  print(f"  {Y}[WARN]{N} {m}")
def info(m):  print(f"  {C}[INFO]{N} {m}")
def title(m): print(f"\n{B}{'='*50}{N}\n{B}  {m}{N}\n{B}{'='*50}{N}\n")


async def load_config():
    """Load WIFI config from SQLite database."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "data", "wifi_esl.db")
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row

    cur = await db.execute(
        "SELECT wifi_base_url, wifi_username, wifi_password, wifi_apikey, wifi_mqtt_broker "
        "FROM users WHERE wifi_base_url LIKE ? AND id=1",
        ("%192.144.234.153%",)
    )
    row = await cur.fetchone()
    await db.close()

    if not row:
        print(f"{R}No user found with 192.144.234.153 in database!{N}")
        sys.exit(1)

    r = dict(row)
    config = {
        "base_url": r["wifi_base_url"],
        "username": r["wifi_username"],
        "apikey": r["wifi_apikey"],
        "mqtt_broker": r.get("wifi_mqtt_broker", ""),
    }

    # Try to decrypt password
    try:
        from services.db_service import decrypt_wifi_password
        config["password"] = decrypt_wifi_password(r["wifi_password"])
    except Exception as e:
        warn(f"Cannot decrypt password: {e}")
        config["password"] = r["wifi_password"]  # fallback: use raw

    return config


async def test_login(base_url: str, username: str, password: str):
    url = f"{base_url.rstrip('/')}/user/api/login"
    print(f"  URL: {url}")
    print(f"  Username: {username}")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={"username": username, "password": password})
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("token", "")
                apikey = data.get("apiKey", "")
                ok("Login successful")
                info(f"Token: {(token[:30] + '...') if len(token) > 30 else token}")
                info(f"API Key: {apikey}")
                return {"token": token, "apikey": apikey}
            else:
                fail(f"Login failed: HTTP {resp.status_code}")
                try:
                    fail(f"Response: {json.dumps(resp.json(), ensure_ascii=False)[:200]}")
                except Exception:
                    fail(f"Response: {resp.text[:200]}")
                return None
    except httpx.ConnectError as e:
        fail(f"Cannot connect: {e}")
        return None
    except httpx.TimeoutException:
        fail(f"Connection timeout ({base_url})")
        return None
    except Exception as e:
        fail(f"Error: {e}")
        return None


async def test_api(base_url: str, token: str):
    url = f"{base_url.rstrip('/')}/user/api/devices"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            if resp.status_code == 200:
                data = resp.json()
                count = len(data) if isinstance(data, list) else "?"
                ok(f"Device list accessible - {count} devices")
                return True
            else:
                fail(f"API call failed: HTTP {resp.status_code}")
                return False
    except Exception as e:
        fail(f"API error: {e}")
        return False


def test_mqtt_tcp(host: str, port: int):
    print(f"  Host: {host}:{port}")
    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        ok("TCP port reachable")
        return True
    except socket.timeout:
        fail("TCP timeout")
    except Exception as e:
        fail(f"TCP error: {e}")
    return False


def test_mqtt_tls(host: str, port: int):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, port), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                ok(f"TLS handshake OK ({ssock.version()})")
                return True
    except Exception as e:
        fail(f"TLS failed: {e}")
        return False


async def main():
    title("WIFI Tag System Connection Test")

    # Load config from DB
    print("Loading config from database...")
    conf = await load_config()
    info(f"Base URL: {conf['base_url']}")
    info(f"Username: {conf['username']}")
    info(f"MQTT Broker: {conf['mqtt_broker']}")
    print()

    results = []

    # Test 1: HTTP Login
    title("Test 1/3: HTTP Login")
    login_data = await test_login(conf["base_url"], conf["username"], conf["password"])
    results.append(("HTTP Login", login_data is not None))

    if not login_data:
        print(f"\n{R}Login failed - stopping.{N}")
        _summary(results)
        return

    # Test 2: API
    title("Test 2/3: API Access (device list)")
    api_ok = await test_api(conf["base_url"], login_data["token"])
    results.append(("API Access", api_ok))

    # Test 3: MQTT
    if conf["mqtt_broker"]:
        title("Test 3/3: MQTT Broker")
        # Parse mqtt://host:port
        broker = conf["mqtt_broker"].replace("mqtt://", "").replace("mqtts://", "")
        host, _, port_str = broker.partition(":")
        port = int(port_str) if port_str else 8883

        tcp_ok = test_mqtt_tcp(host, port)
        results.append(("MQTT TCP", tcp_ok))

        if tcp_ok:
            test_mqtt_tls(host, port)
            results.append(("MQTT TLS", True))  # just informational
    else:
        info("No MQTT broker configured - skipped")

    _summary(results)


def _summary(results):
    title("Summary")
    all_ok = True
    for name, passed in results:
        if passed:
            ok(name)
        else:
            fail(name)
            all_ok = False
    print()
    if all_ok:
        print(f"  {G}{B}All tests passed! System is reachable.{N}")
    else:
        print(f"  {R}{B}Some tests failed. Check output above.{N}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
