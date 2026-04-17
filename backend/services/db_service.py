"""
数据库服务层 - SQLite 持久化存储
使用 aiosqlite 提供异步访问能力

表结构:
  - users          系统用户 (登录账号密码)
  - system_config  系统配置项 (键值对: MQTT/WIFI凭证等)
  - templates      显示模板定义 (名称/描述/适用屏幕)
  - template_fields 模板字段 (动态可变，支持手动增删改)
  - operation_logs 操作审计日志
"""
import os
import logging
import hashlib
import json
import aiosqlite

from config import settings

logger = logging.getLogger(__name__)

# 数据库文件路径 (backend/data/ 目录下)
_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_DB_PATH = os.path.join(_DB_DIR, "wifi_esl.db")

# 全局数据库连接
_db: aiosqlite.Connection | None = None


def _get_db_path() -> str:
    """获取数据库路径，确保目录存在"""
    os.makedirs(_DB_DIR, exist_ok=True)
    return _DB_PATH


async def get_db() -> aiosqlite.Row:
    """获取全局数据库连接 (懒初始化)"""
    global _db
    if _db is None:
        db_path = _get_db_path()
        print(f"[DB] 正在连接数据库: {db_path}")
        print(f"[DB] 数据库文件是否存在: {os.path.exists(db_path)}")
        try:
            print(f"[DB] 调用 aiosqlite.connect...")
            _db = await aiosqlite.connect(db_path)
            print(f"[DB] aiosqlite.connect 成功")
            # 返回 dict-like Row
            print(f"[DB] 设置 row_factory...")
            _db.row_factory = aiosqlite.Row
            # 启用外键约束
            print(f"[DB] 启用外键约束...")
            await _db.execute("PRAGMA foreign_keys = ON")
            print(f"[DB] 外键约束已启用")
            logger.info(f"数据库已连接: {db_path}")
        except Exception as e:
            print(f"[DB] 连接失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    return _db


async def init_db():
    """创建表结构（如果不存在）并插入默认数据"""
    import time
    print("[DB] 开始初始化数据库...")
    start = time.time()
    
    print("[DB] 正在连接数据库...")
    try:
        db = await get_db()
        print(f"[DB] 数据库连接成功，耗时: {time.time() - start:.2f}s")
    except Exception as e:
        print(f"[DB] 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        raise

    # ── 用户表 ──
    print("[DB] 正在创建用户表...")
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'operator',
            avatar      TEXT    DEFAULT '',
            status      TEXT    NOT NULL DEFAULT 'active',
            
            -- WIFI系统独立配置（每个子账号有自己的WIFI配置）
            wifi_username    TEXT,      -- WIFI系统的用户名
            wifi_password    TEXT,      -- WIFI系统的密码（AES加密存储）
            wifi_apikey      TEXT,      -- 用于MQTT订阅的API Key
            wifi_token       TEXT,      -- WIFI系统登录后返回的token（新增，用于调用WIFI系统API）
            wifi_base_url    TEXT,      -- WIFI系统API地址
            wifi_mqtt_broker TEXT,      -- MQTT broker地址（新增）
            
            -- 用户关系（用于管理员管理子账号）
            parent_user_id   INTEGER DEFAULT 0,  -- 上级用户ID（0为根用户）
            created_by       INTEGER DEFAULT 0,   -- 创建者用户ID
            
            created_at  TEXT    DEFAULT (datetime('now', 'localtime')),
            updated_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        );
        
        -- 为增强的用户表创建索引
        CREATE INDEX IF NOT EXISTS idx_users_parent ON users(parent_user_id);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
        CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
    """)

    # 检查并添加缺失的列（数据库迁移）
    await db.executescript("""
        -- 检查并添加wifi_mqtt_broker列（如果不存在）
        PRAGMA table_info(users);
    """)
    
    # 获取当前列信息
    columns_info = await db.execute("PRAGMA table_info(users)")
    columns = await columns_info.fetchall()
    column_names = [col[1] for col in columns]
    
    # 添加缺失的列
    if 'wifi_mqtt_broker' not in column_names:
        print("[数据库迁移] 正在添加wifi_mqtt_broker列到users表...")
        await db.execute("ALTER TABLE users ADD COLUMN wifi_mqtt_broker TEXT")
        print("[数据库迁移] ✅ wifi_mqtt_broker列添加成功")
    
    if 'wifi_token' not in column_names:
        print("[数据库迁移] 正在添加wifi_token列到users表...")
        await db.execute("ALTER TABLE users ADD COLUMN wifi_token TEXT")
        print("[数据库迁移] ✅ wifi_token列添加成功")
    
    if 'mqtt_username' not in column_names:
        print("[数据库迁移] 正在添加mqtt_username列到users表...")
        await db.execute("ALTER TABLE users ADD COLUMN mqtt_username TEXT DEFAULT 'test'")
        print("[数据库迁移] ✅ mqtt_username列添加成功")
    
    if 'mqtt_password' not in column_names:
        print("[数据库迁移] 正在添加mqtt_password列到users表...")
        await db.execute("ALTER TABLE users ADD COLUMN mqtt_password TEXT DEFAULT '123456'")
        print("[数据库迁移] ✅ mqtt_password列添加成功")

    # ── 系统配置表 (key-value) ──
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS system_config (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT    NOT NULL DEFAULT 'general',
            key         TEXT    NOT NULL UNIQUE,
            value       TEXT,
            description TEXT    DEFAULT '',
            is_secret   INTEGER NOT NULL DEFAULT 0,
            updated_by  TEXT,
            updated_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        );
    """)

    # ── 操作日志表 ──
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS operation_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT,
            action      TEXT    NOT NULL,
            target_type TEXT,
            target_id   TEXT,
            detail      TEXT,
            result      TEXT    DEFAULT 'success',
            ip_address  TEXT,
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        );

        -- 索引优化查询
        CREATE INDEX IF NOT EXISTS idx_logs_action ON operation_logs(action);
        CREATE INDEX IF NOT EXISTS idx_logs_time ON operation_logs(created_at);
    """)

    # ── 模板表 ──
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS templates (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tid         TEXT    NOT NULL UNIQUE,
            tname       TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            screen_type TEXT    DEFAULT '',
            status      TEXT    NOT NULL DEFAULT 'active',
            created_at  TEXT    DEFAULT (datetime('now', 'localtime')),
            updated_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS template_fields (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
            field_key   TEXT    NOT NULL,
            field_label TEXT    NOT NULL,
            field_type  TEXT    NOT NULL DEFAULT 'text',
            required    INTEGER NOT NULL DEFAULT 0,
            default_value TEXT DEFAULT '',
            placeholder TEXT DEFAULT '',
            options     TEXT    DEFAULT '[]',
            sort_order  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now', 'localtime')),
            UNIQUE(template_id, field_key)
        );

        CREATE INDEX IF NOT EXISTS idx_template_fields_tid ON template_fields(template_id);
    """)

    # ── 设备状态表 (存储每个设备的最新实时状态) ──
    # 注意：多租户模式下，每个用户有自己的设备记录
    # 使用 (mac, user_id) 组合唯一约束，支持不同用户拥有相同设备
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS devices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            mac             TEXT    NOT NULL,
            user_id         INTEGER NOT NULL DEFAULT 0,
            name            TEXT    DEFAULT '',
            ip              TEXT    DEFAULT '',
            is_online       INTEGER NOT NULL DEFAULT 0,
            voltage         INTEGER,
            rssi            INTEGER,
            device_type     TEXT    DEFAULT '',
            screen_type     TEXT    DEFAULT '',
            firmware_ver    TEXT    DEFAULT '',
            last_seen_at    TEXT,
            first_seen_at   TEXT    DEFAULT (datetime('now', 'localtime')),
            created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
            updated_at      TEXT    DEFAULT (datetime('now', 'localtime')),
            UNIQUE(mac, user_id)
        );
    """)
    
    # 迁移：添加 user_id 列（如果不存在）
    try:
        existing = await (await db.execute("PRAGMA table_info(devices)")).fetchall()
        col_names = {row[1] for row in existing}
        if 'user_id' not in col_names:
            await db.execute("ALTER TABLE devices ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")
            logger.info("[DB] 已添加列 devices.user_id")
            await db.commit()
    except Exception as e:
        logger.warning(f"[DB] 添加 devices.user_id 列失败: {e}")
    
    # 迁移：修改mac唯一约束为(mac, user_id)组合唯一（支持多租户）
    try:
        # 检查现有索引
        existing_idx = await db.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='devices'")
        idx_rows = await existing_idx.fetchall()
        idx_info = {row[0]: row[1] for row in idx_rows}
        
        # 检查是否有sqlite_autoindex_devices_1（mac字段的自动唯一索引）
        if 'sqlite_autoindex_devices_1' in idx_info:
            logger.info("[DB] 检测到mac字段的唯一约束，需要迁移到(mac, user_id)组合唯一")
            
            # 1. 创建新表（使用正确的约束）
            await db.executescript("""
                CREATE TABLE devices_new (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac             TEXT    NOT NULL,
                    user_id         INTEGER NOT NULL DEFAULT 0,
                    name            TEXT    DEFAULT '',
                    ip              TEXT    DEFAULT '',
                    is_online       INTEGER NOT NULL DEFAULT 0,
                    voltage         INTEGER,
                    rssi            INTEGER,
                    device_type     TEXT    DEFAULT '',
                    screen_type     TEXT    DEFAULT '',
                    firmware_ver    TEXT    DEFAULT '',
                    last_seen_at    TEXT,
                    first_seen_at   TEXT    DEFAULT (datetime('now', 'localtime')),
                    created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
                    updated_at      TEXT    DEFAULT (datetime('now', 'localtime')),
                    UNIQUE(mac, user_id)
                );
            """)
            
            # 2. 迁移数据
            await db.execute("""
                INSERT INTO devices_new (
                    id, mac, user_id, name, ip, is_online, voltage, rssi,
                    device_type, screen_type, firmware_ver, last_seen_at, first_seen_at, created_at, updated_at
                )
                SELECT 
                    id, mac, COALESCE(user_id, 0), name, ip, is_online, voltage, rssi,
                    device_type, screen_type, firmware_ver, last_seen_at, first_seen_at, created_at, updated_at
                FROM devices
            """)
            
            # 3. 删除旧表
            await db.execute("DROP TABLE devices")
            
            # 4. 重命名新表
            await db.execute("ALTER TABLE devices_new RENAME TO devices")
            
            # 5. 重新创建索引
            await db.executescript("""
                CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id);
                CREATE INDEX IF NOT EXISTS idx_devices_online ON devices(is_online);
                CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac);
                CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen_at);
            """)
            
            await db.commit()
            logger.info("[DB] 已成功迁移devices表：mac唯一约束改为(mac, user_id)组合唯一")
    except Exception as e:
        logger.warning(f"[DB] 修改devices表唯一约束失败: {e}")
    
    # 创建索引（在确认 user_id 列存在后）
    await db.executescript("""
        CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id);
        CREATE INDEX IF NOT EXISTS idx_devices_online ON devices(is_online);
        CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac);
        CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen_at);
    """)

    # ── 设备事件记录表 (MQTT消息历史) ──
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS device_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            mac         TEXT    NOT NULL,
            event_type  TEXT    NOT NULL,           -- online/offline/button/battery_reply/led_reply/reboot_reply/display_reply
            payload     TEXT,                        -- JSON格式的原始数据
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        );

        -- 索引: 按MAC和时间查询最常见
        CREATE INDEX IF NOT EXISTS idx_events_mac ON device_events(mac);
        CREATE INDEX IF NOT EXISTS idx_events_type ON device_events(event_type);
        CREATE INDEX IF NOT EXISTS idx_events_time ON device_events(created_at);
        CREATE INDEX IF NOT EXISTS idx_events_mac_time ON device_events(mac, created_at DESC);
    """)

    # ── 模板-设备关联表 (数据更新页面的设备选择持久化) ──
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS template_device_bindings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tid         TEXT    NOT NULL,
            mac         TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now', 'localtime')),
            updated_at  TEXT    DEFAULT (datetime('now', 'localtime')),
            UNIQUE(tid, mac)
        );

        CREATE INDEX IF NOT EXISTS idx_bind_tid ON template_device_bindings(tid);
        CREATE INDEX IF NOT EXISTS idx_bind_mac ON template_device_bindings(mac);
    """)

    # ── 更新任务主表 ──
    # 先创建基础表（不包含 user_id，兼容旧表）
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS update_tasks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL DEFAULT '',
            tid             TEXT    NOT NULL,
            tname           TEXT    DEFAULT '',
            default_data    TEXT    DEFAULT '{}',
            status          TEXT    NOT NULL DEFAULT 'draft',
            total_devices   INTEGER NOT NULL DEFAULT 0,
            success_count   INTEGER NOT NULL DEFAULT 0,
            failed_count    INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
            updated_at      TEXT    DEFAULT (datetime('now', 'localtime')),
            sent_at         TEXT,
            completed_at    TEXT
        );
    """)
    
    # 迁移：添加 user_id 列（如果不存在）
    try:
        existing = await (await db.execute("PRAGMA table_info(update_tasks)")).fetchall()
        col_names = {row[1] for row in existing}
        if 'user_id' not in col_names:
            await db.execute("ALTER TABLE update_tasks ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")
            logger.info("[DB] 已添加列 update_tasks.user_id")
            await db.commit()
    except Exception as e:
        logger.warning(f"[DB] 添加 update_tasks.user_id 列失败: {e}")
    
    # 创建索引（在确认 user_id 列存在后）
    await db.executescript("""
        CREATE INDEX IF NOT EXISTS idx_utasks_user ON update_tasks(user_id);
        CREATE INDEX IF NOT EXISTS idx_utasks_tid ON update_tasks(tid);
        CREATE INDEX IF NOT EXISTS idx_utasks_status ON update_tasks(status);
    """)

    # ── 任务-设备明细表（每台设备的独立状态）═══
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS task_devices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id         INTEGER NOT NULL REFERENCES update_tasks(id) ON DELETE CASCADE,
            mac             TEXT    NOT NULL,
            custom_data     TEXT    DEFAULT '{}',
            update_status   TEXT    NOT NULL DEFAULT 'pending',
            error_msg       TEXT    DEFAULT '',
            retry_count     INTEGER NOT NULL DEFAULT 0,
            sent_at         TEXT,
            finished_at     TEXT,
            updated_at      TEXT    DEFAULT (datetime('now', 'localtime')),
            created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
            UNIQUE(task_id, mac)
        );
        CREATE INDEX IF NOT EXISTS idx_tdevices_task ON task_devices(task_id);
        CREATE INDEX IF NOT EXISTS idx_tdevices_mac ON task_devices(mac);
        CREATE INDEX IF NOT EXISTS idx_tdevices_status ON task_devices(update_status);
    """)

    # ── 设备多行数据子表（同一设备支持多条自定义数据记录）═══
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS task_device_rows (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task_device_id  INTEGER NOT NULL REFERENCES task_devices(id) ON DELETE CASCADE,
            sort_order      INTEGER NOT NULL DEFAULT 0,
            custom_data     TEXT    DEFAULT '{}',
            created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_rows_tdev_id ON task_device_rows(task_device_id);
        CREATE INDEX IF NOT EXISTS idx_rows_sort ON task_device_rows(task_device_id, sort_order);
    """)

    await db.commit()

    # ═══ 兼容旧数据库：确保 task_devices 有新列 ═══
    try:
        # SQLite 不支持 IF NOT EXISTS 加列，先查 PRAGMA
        existing = await (await db.execute("PRAGMA table_info(task_devices)")).fetchall()
        col_names = {row[1] for row in existing}
        if 'sent_at' not in col_names:
            await db.execute("ALTER TABLE task_devices ADD COLUMN sent_at TEXT")
            print("[DB] 已添加列 task_devices.sent_at")
        if 'finished_at' not in col_names:
            await db.execute("ALTER TABLE task_devices ADD COLUMN finished_at TEXT")
            print("[DB] 已添加列 task_devices.finished_at")
        await db.commit()
    except Exception as e:
        logger.warning(f"[DB] 检查/添加兼容列失败（可忽略）: {e}")
    
    # 检查并添加users表的新字段
    try:
        cursor = await db.execute("PRAGMA table_info(users)")
        existing = await cursor.fetchall()
        col_names = {row[1] for row in existing}
        
        # 检查并添加WIFI配置字段
        wifi_fields = [
            ('wifi_username', 'TEXT'),
            ('wifi_password', 'TEXT'),
            ('wifi_apikey', 'TEXT'),
            ('wifi_base_url', 'TEXT'),
            ('parent_user_id', 'INTEGER DEFAULT 0'),
            ('created_by', 'INTEGER DEFAULT 0')
        ]
        
        for field_name, field_type in wifi_fields:
            if field_name not in col_names:
                await db.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}")
                logger.info(f"[DB] 已添加列 users.{field_name}")
        
        # 检查并创建索引
        existing_idx = await db.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'")
        idx_names = {row[0] for row in await existing_idx.fetchall()}
        
        if 'idx_users_parent' not in idx_names:
            await db.execute("CREATE INDEX idx_users_parent ON users(parent_user_id)")
            logger.info("[DB] 已创建索引 idx_users_parent")
        if 'idx_users_role' not in idx_names:
            await db.execute("CREATE INDEX idx_users_role ON users(role)")
            logger.info("[DB] 已创建索引 idx_users_role")
        if 'idx_users_status' not in idx_names:
            await db.execute("CREATE INDEX idx_users_status ON users(status)")
            logger.info("[DB] 已创建索引 idx_users_status")
        
        await db.commit()
    except Exception as e:
        logger.warning(f"[DB] 检查/添加users表兼容列失败（可忽略）: {e}")

    # ── 插入默认数据 (仅当表为空时) ──
    await _seed_default_data(db)
    logger.info("数据库表结构初始化完成")


async def close_db():
    """关闭数据库连接"""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
        logger.info("数据库连接已关闭")


# ============================================================
# 默认种子数据
# ============================================================

async def _seed_default_data(db: aiosqlite.Connection):
    """首次启动时写入默认用户和系统配置"""

    # 默认管理员账号 (密码 admin123 的 SHA256 哈希)
    default_pwd_hash = hash_password("admin123")
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
    row = await cursor.fetchone()
    if row and row["cnt"] == 0:
        # 创建默认管理员账号，使用当前系统配置作为WIFI配置
        try:
            # 尝试加密WIFI密码
            encrypted_wifi_password = encrypt_wifi_password(settings.wifi_password)
        except Exception as e:
            logger.warning(f"WIFI密码加密失败，使用明文存储: {e}")
            encrypted_wifi_password = settings.wifi_password
        
        await db.execute(
            """INSERT INTO users (
                username, password, role, 
                wifi_username, wifi_password, wifi_apikey, wifi_base_url,
                parent_user_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "admin", default_pwd_hash, "admin",
                settings.wifi_username, 
                encrypted_wifi_password,    # 加密存储的WIFI密码
                settings.wifi_apikey,
                settings.wifi_base_url,
                0, 0  # 根用户，自己创建
            ),
        )
        logger.info("已创建默认管理员账号: admin / admin123")
        logger.info(f"管理员WIFI配置: 用户名={settings.wifi_username}, API地址={settings.wifi_base_url}")
    else:
        # 已有用户，检查并更新现有管理员的WIFI配置（如果为空）
        cursor = await db.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_user = await cursor.fetchone()
        if admin_user:
            # 检查WIFI配置是否为空
            cursor = await db.execute(
                "SELECT wifi_username FROM users WHERE id = ?", (admin_user['id'],)
            )
            wifi_username_exists = await cursor.fetchone()
            if wifi_username_exists and wifi_username_exists['wifi_username'] is None:
                # 更新现有管理员的WIFI配置
                try:
                    # 尝试加密WIFI密码
                    encrypted_wifi_password = encrypt_wifi_password(settings.wifi_password)
                except Exception as e:
                    logger.warning(f"WIFI密码加密失败，使用明文存储: {e}")
                    encrypted_wifi_password = settings.wifi_password
                
                await db.execute(
                    """UPDATE users SET 
                        wifi_username = ?, 
                        wifi_password = ?, 
                        wifi_apikey = ?, 
                        wifi_base_url = ?,
                        updated_at = datetime('now', 'localtime')
                    WHERE username = 'admin'""",
                    (
                        settings.wifi_username,
                        encrypted_wifi_password,  # 加密存储
                        settings.wifi_apikey,
                        settings.wifi_base_url
                    )
                )
                logger.info("已更新现有管理员用户的WIFI系统配置")

    # 默认系统配置 (从 .env 导入初始值)
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM system_config")
    row = await cursor.fetchone()
    if row and row["cnt"] == 0:
        defaults = [
            # category, key, value, description, is_secret
            ("wifi",     "base_url",    settings.wifi_base_url,           "WIFI标签系统地址",             0),
            ("wifi",     "username",    settings.wifi_username,            "WIFI系统登录用户名",            0),
            ("wifi",     "password",    settings.wifi_password,            "WIFI系统登录密码",              1),
            ("wifi",     "apikey",      settings.wifi_apikey,              "WIFI系统 API Key",             1),
            ("mqtt",     "broker_host", settings.mqtt_broker_host,         "MQTT Broker 地址",             0),
            ("mqtt",     "broker_port", str(settings.mqtt_broker_port),    "MQTT Broker 端口",             0),
            ("mqtt",     "tls_enable",  str(int(settings.mqtt_tls_enable)),"MQTT TLS 开关(1开/0关)",       0),
            ("mqtt",     "tls_insecure",str(int(settings.mqtt_tls_insecure)), "MQTT跳过证书验证(1是/0否)", 0),
            ("jwt",      "secret",      settings.jwt_secret,               "JWT 签名密钥",                 1),
            ("jwt",      "expire_hours", str(settings.jwt_expire_hours),    "JWT 有效期(小时)",              0),
            ("system",   "site_name",   "WIFI标签管理系统",                "站点名称",                      0),
        ]
        for cat, key, val, desc, secret in defaults:
            await db.execute(
                "INSERT INTO system_config (category, key, value, description, is_secret) VALUES (?, ?, ?, ?, ?)",
                (cat, key, val, desc, secret),
            )
        logger.info(f"已导入 {len(defaults)} 条默认系统配置")

    # 默认模板 (从现有 MOCK 数据导入)
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM templates")
    row = await cursor.fetchone()
    if row and row["cnt"] == 0:
        seed_templates = [
            # tid, tname, description
            ("tpl_001", "商品价格标签", "零售商品电子价签，含名称/价格/条码"),
            ("tpl_002", "促销活动标签", "促销活动信息展示"),
            ("tpl_003", "库存状态标签", "仓库库存管理标签"),
            ("tpl_004", "货架标识牌", "货架/区域标识牌"),
        ]
        seed_fields = {
            # template_index: [(key, label, type, required, default_val, placeholder, options_json, sort_order), ...]
            0: [
                ("product_name",   "product_name", "text",     1, "", "如：可口可乐330ml", "[]", 0),
                ("price",          "price(元)",       "text",     1, "", "如：3.50",          "[]", 1),
                ("original_price", "原价(元)",       "text",     0, "", "如：5.00",          "[]", 2),
                ("barcode",        "barcode",        "qrcode",   0, "", "",                  "[]", 3),
            ],
            1: [
                ("promo_title",    "promo_title",    "text",     1, "", "如：限时特惠",      "[]", 0),
                ("discount",       "折扣",           "text",     1, "", "如：8折",          "[]", 1),
                ("valid_until",    "有效期至",       "date",     0, "", "",                  "[]", 2),
                ("promo_image",    "促销图",         "image",    0, "", "",                  "[]", 3),
            ],
            2: [
                ("sku_code",       "sku_code",       "text",     1, "", "SKU编码",           "[]", 0),
                ("stock_qty",      "stock_qty",      "number",   1, "", "数量",             "[]", 1),
                ("location",       "location",       "text",     0, "", "库位号",            "[]", 2),
            ],
            3: [
                ("shelf_no",       "shelf_no",       "text",     1, "", "A-01-03",          "[]", 0),
                ("category",       "category",       "text",     1, "", "饮料/食品/日化",     "[]", 1),
                ("floor",          "floor",          "text",     0, "", "1F/2F/3F",         "[]", 2),
            ],
        }

        for tpl_idx, (tid, tname, desc) in enumerate(seed_templates):
            cur = await db.execute(
                "INSERT INTO templates (tid, tname, description) VALUES (?, ?, ?)",
                (tid, tname, desc),
            )
            tpl_id = cur.lastrowid
            for fk, fl, ft, req, dv, ph, opts, so in seed_fields[tpl_idx]:
                await db.execute(
                    """INSERT INTO template_fields 
                       (template_id, field_key, field_label, field_type, required, 
                        default_value, placeholder, options, sort_order) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (tpl_id, fk, fl, ft, req, dv, ph, opts, so),
                )
        logger.info(f"已导入 {len(seed_templates)} 个默认模板")

    await db.commit()


# ============================================================
# 工具函数
# ============================================================

def hash_password(password: str) -> str:
    """密码哈希 (SHA-256)"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == hashed


# ============================================================
# WIFI密码加密函数 (AES加密)
# ============================================================

import base64
import hashlib

# 导入pycryptodome的Crypto模块
try:
    # 标准pycryptodome导入
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    from Crypto.Random import get_random_bytes
    print("[OK] 使用Crypto模块 (pycryptodome)")
except ImportError:
    try:
        # 某些环境可能使用Cryptodome
        from Cryptodome.Cipher import AES
        from Cryptodome.Util.Padding import pad, unpad
        from Cryptodome.Random import get_random_bytes
        print("[OK] 使用Cryptodome模块")
    except ImportError:
        raise ImportError("请安装 pycryptodome 模块: pip install pycryptodome")

def _get_encryption_key() -> bytes:
    """获取加密密钥（基于JWT secret）"""
    from config import settings
    # 使用JWT secret作为基础，生成32字节AES密钥
    key_material = settings.jwt_secret.encode('utf-8')
    # 使用SHA256生成固定长度的密钥
    return hashlib.sha256(key_material).digest()

def encrypt_wifi_password(plaintext: str) -> str:
    """AES加密WIFI密码"""
    if not plaintext:
        return ""
    
    try:
        key = _get_encryption_key()
        iv = get_random_bytes(16)  # 随机初始化向量
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
        
        # 组合IV和密文: IV + ciphertext
        encrypted_data = iv + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    except Exception as e:
        logger.error(f"加密WIFI密码失败: {e}")
        # 如果加密失败，返回原始密码（不安全，但至少可用）
        return plaintext

def decrypt_wifi_password(encrypted: str) -> str:
    """AES解密WIFI密码"""
    if not encrypted:
        return ""
    
    try:
        # 检查是否是加密格式（base64）
        if not encrypted.startswith('eyJ'):  # 不是JWT格式，可能是加密的
            encrypted_data = base64.b64decode(encrypted)
            
            # 分离IV和密文
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            key = _get_encryption_key()
            cipher = AES.new(key, AES.MODE_CBC, iv)
            plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
            
            return plaintext.decode('utf-8')
        else:
            # 如果是JWT格式，直接返回（兼容旧数据）
            return encrypted
    except Exception as e:
        logger.error(f"解密WIFI密码失败: {e}")
        # 如果解密失败，尝试返回原始值（可能是明文）
        return encrypted


# ============================================================
# Users 表操作
# ============================================================

async def get_user_by_name(username: str) -> dict | None:
    """根据用户名查找用户"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM users WHERE username = ? AND status = 'active'", (username,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_all_users() -> list[dict]:
    """获取所有用户(不含密码哈希)"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, username, role, avatar, status, created_at, updated_at FROM users ORDER BY id"
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def create_user(username: str, password: str, role: str = "operator") -> int:
    """创建新用户, 返回新用户ID"""
    db = await get_db()
    pwd_hash = hash_password(password)
    cursor = await db.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, pwd_hash, role),
    )
    await db.commit()
    return cursor.lastrowid


async def update_user(user_id: int, **kwargs):
    """更新用户信息 (支持 username/password/role/avatar/status)"""
    db = await get_db()
    if "password" in kwargs:
        kwargs["password"] = hash_password(kwargs.pop("password"))
    kwargs["updated_at"] = "datetime('now','localtime')"
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    await db.execute(f"UPDATE users SET {sets} WHERE id = ?", values)
    await db.commit()


async def delete_user(user_id: int):
    """软删除用户 (设为 disabled)"""
    db = await get_db()
    await db.execute(
        "UPDATE users SET status = 'disabled', updated_at = datetime('now','localtime') WHERE id = ?",
        (user_id,),
    )
    await db.commit()


async def hard_delete_user(user_id: int) -> bool:
    """硬删除用户 - 从数据库中完全删除用户记录"""
    db = await get_db()
    try:
        # 首先检查用户是否存在
        cursor = await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row:
            logger.warning(f"尝试删除不存在的用户: id={user_id}")
            return False
        
        # 硬删除用户记录
        cursor = await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await db.commit()
        
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"已硬删除用户: id={user_id}")
        else:
            logger.warning(f"硬删除用户失败: id={user_id}")
            
        return deleted
        
    except Exception as e:
        logger.error(f"硬删除用户时发生错误: {e}")
        await db.rollback()
        return False


# ============================================================
# System Config 操作
# ============================================================

async def get_config(key: str | None = None) -> dict | str | None:
    """
    获取配置值
    - key=None → 返回全部配置 {category: {key: value}}
    - key=具体键 → 返回对应值字符串
    """
    db = await get_db()
    if key:
        cursor = await db.execute("SELECT value FROM system_config WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row["value"] if row else None
    else:
        cursor = await db.execute(
            "SELECT category, key, value, description, is_secret, updated_at FROM system_config ORDER BY category, key"
        )
        rows = await cursor.fetchall()
        result = {}
        for r in rows:
            d = dict(r)
            cat = d.pop("category")
            if cat not in result:
                result[cat] = {}
            result[cat][d.pop("key")] = d
        return result


async def set_config(key: str, value: str, updated_by: str = "system"):
    """
    设置单个配置项 (不存在则自动创建)
    """
    db = await get_db()
    await db.execute("""
        INSERT INTO system_config (key, value, updated_by, updated_at)
        VALUES (?, ?, ?, datetime('now','localtime'))
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_by = excluded.updated_by,
            updated_at = datetime('now','localtime')
    """, (key, value, updated_by))
    await db.commit()


async def set_configs(pairs: dict[str, str], updated_by: str = "system"):
    """批量设置配置"""
    db = await get_db()
    for key, value in pairs.items():
        await db.execute("""
            INSERT INTO system_config (key, value, updated_by, updated_at)
            VALUES (?, ?, ?, datetime('now','localtime'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_by = excluded.updated_by,
                updated_at = datetime('now','localtime')
        """, (key, value, updated_by))
    await db.commit()


async def get_config_category(category: str) -> dict:
    """获取某个分类下的所有配置"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT key, value, description, is_secret FROM system_config WHERE category = ? ORDER BY key",
        (category,)
    )
    rows = await cursor.fetchall()
    return {r["key"]: {"value": r["value"], "description": r["description"], "is_secret": bool(r["is_secret"])} for r in rows}


# ============================================================
# Operation Logs 操作
# ============================================================

async def add_log(
    username: str,
    action: str,
    target_type: str = "",
    target_id: str = "",
    detail: str = "",
    result: str = "success",
    ip_address: str = "",
):
    """记录一条操作日志"""
    db = await get_db()
    await db.execute("""
        INSERT INTO operation_logs (username, action, target_type, target_id, detail, result, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (username, action, target_type, target_id, detail, result, ip_address))
    await db.commit()


async def get_logs(
    page: int = 1,
    page_size: int = 20,
    action: str = "",
) -> tuple[list[dict], int]:
    """
    分页查询操作日志
    Returns: (items列表, total总数)
    """
    db = await get_db()

    where = ""
    params: list = []
    if action:
        where = "WHERE action LIKE ?"
        params.append(f"%{action}%")

    # 总数
    cnt_sql = f"SELECT COUNT(*) as total FROM operation_logs {where}"
    cursor = await db.execute(cnt_sql, params)
    total_row = await cursor.fetchone()
    total = total_row["total"]

    # 分页数据
    offset = (page - 1) * page_size
    sql = f"""
        SELECT * FROM operation_logs {where}
        ORDER BY created_at DESC LIMIT ? OFFSET ?
    """
    cursor = await db.execute(sql, params + [page_size, offset])
    rows = await cursor.fetchall()
    items = [dict(r) for r in rows]

    return items, total


# ============================================================
# Templates + TemplateFields 操作
# ============================================================

async def get_all_templates() -> list[dict]:
    """获取所有模板(含字段列表) — 返回前端期望的格式"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, tid, tname, description, screen_type, status, created_at, updated_at FROM templates WHERE status='active' ORDER BY id"
    )
    tpl_rows = await cursor.fetchall()
    result = []
    for t in tpl_rows:
        td = dict(t)
        # 获取该模板的所有字段
        fcur = await db.execute(
            "SELECT field_key, field_label, field_type, required, default_value, placeholder, options, sort_order "
            "FROM template_fields WHERE template_id=? ORDER BY sort_order",
            (td["id"],),
        )
        fields = []
        for f in await fcur.fetchall():
            fd = dict(f)
            fd["required"] = bool(fd["required"])
            fd["options"] = json.loads(fd["options"]) if fd.get("options") else []
            fields.append(fd)
        td["fields"] = fields
        result.append(td)
    return result


async def get_template_by_tid(tid: str) -> dict | None:
    """根据tid获取单个模板详情"""
    templates = await get_all_templates()
    for t in templates:
        if t["tid"] == tid:
            return t
    return None


async def create_template(
    tid: str,
    tname: str,
    description: str = "",
    screen_type: str = "",
    fields: list[dict] | None = None,
) -> int:
    """
    创建或更新模板（upsert：tid 存在则更新，否则创建）
    fields 格式: [{key, label, type, required, default_value, placeholder, options, sort_order}, ...]
    返回模板ID
    """
    db = await get_db()

    # 检查 tid 是否已存在
    cur = await db.execute("SELECT id FROM templates WHERE tid=?", (tid,))
    row = await cur.fetchone()

    tpl_id: int

    if row:
        # ── 更新已有模板 ──
        tpl_id = row["id"]
        await db.execute(
            """UPDATE templates SET tname=?, description=?, screen_type=?,
               status='active', updated_at=datetime('now','localtime')
               WHERE tid=?""",
            (tname, description, screen_type, tid),
        )
        # 删除旧字段，后续重新插入
        await db.execute("DELETE FROM template_fields WHERE template_id=?", (tpl_id,))
        logger.info(f"更新已有模板: {tid} (id={tpl_id})")
    else:
        # ── 创建新模板 ──
        cur = await db.execute(
            "INSERT INTO templates (tid, tname, description, screen_type) VALUES (?, ?, ?, ?)",
            (tid, tname, description, screen_type),
        )
        tpl_id = cur.lastrowid
        logger.info(f"创建新模板: {tid} (id={tpl_id})")

    # 写入字段定义
    if fields:
        for idx, f in enumerate(fields):
            opts_json = json.dumps(f.get("options", []), ensure_ascii=False)
            await db.execute(
                """INSERT INTO template_fields 
                   (template_id, field_key, field_label, field_type, required,
                    default_value, placeholder, options, sort_order) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tpl_id,
                 f.get("key", f.get("field_key", "")),
                 f.get("label", f.get("field_label", "")),
                 f.get("type", f.get("field_type", "text")),
                 int(bool(f.get("required", False))),
                 f.get("default_value", f.get("default_value", "")),
                 f.get("placeholder", f.get("placeholder", "")),
                 opts_json,
                 f.get("sort_order", f.get("order", idx))),
            )

    await db.commit()
    return tpl_id


async def update_template(tid: str, **kwargs):
    """
    更新模板信息 (tname/description/screen_type/status) 和/或字段列表
    传入 fields=[...] 时会替换全部字段
    """
    db = await get_db()
    # 更新模板主表
    update_cols = {k: v for k, v in kwargs.items() if k != "fields"}
    if update_cols:
        update_cols["updated_at"] = "datetime('now','localtime')"
        sets = ", ".join(f"{k} = ?" for k in update_cols)
        vals = list(update_cols.values()) + [tid]
        await db.execute(f"UPDATE templates SET {sets} WHERE tid=?", vals)

    # 替换字段
    if "fields" in kwargs and kwargs["fields"] is not None:
        # 先获取模板id
        cur = await db.execute("SELECT id FROM templates WHERE tid=?", (tid,))
        row = await cur.fetchone()
        if row:
            tpl_id = row["id"]
            await db.execute("DELETE FROM template_fields WHERE template_id=?", (tpl_id,))
            for idx, f in enumerate(kwargs["fields"]):
                opts_json = json.dumps(f.get("options", []), ensure_ascii=False)
                await db.execute(
                    """INSERT INTO template_fields 
                       (template_id, field_key, field_label, field_type, required,
                        default_value, placeholder, options, sort_order) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (tpl_id,
                     f.get("key", f.get("field_key", "")),
                     f.get("label", f.get("field_label", "")),
                     f.get("type", f.get("field_type", "text")),
                     int(bool(f.get("required", False))),
                     f.get("default_value", f.get("default_value", "")),
                     f.get("placeholder", f.get("placeholder", "")),
                     opts_json,
                     f.get("sort_order", f.get("order", idx))),
                )

    await db.commit()


async def delete_template(tid: str):
    """删除模板 (级联删除所有字段)"""
    db = await get_db()
    await db.execute("DELETE FROM templates WHERE tid=?", (tid,))
    await db.commit()


# ============================================================
# Devices 表操作
# ============================================================

async def upsert_device(mac: str, user_id: int = 0, **fields) -> dict:
    """
    新增或更新设备状态 (UPSERT)
    fields: is_online/voltage/rssi/device_type/screen_type/firmware_ver/name/ip/last_seen_at
    user_id: 所属用户ID（多租户隔离）
    返回更新后的完整记录
    """
    db = await get_db()
    # 检查是否已存在（按user_id和mac）
    cur = await db.execute("SELECT id FROM devices WHERE mac=? AND user_id=?", (mac, user_id))
    row = await cur.fetchone()

    if row:
        # UPDATE: 只传入的字段 + updated_at
        # 过滤掉 user_id 字段（不能更新）
        update_fields = {k: v for k, v in fields.items() if k != 'user_id'}
        sets = ", ".join(f"{k} = ?" for k in update_fields)
        vals = list(update_fields.values()) + [mac, user_id]
        if update_fields:
            sets += ", updated_at = datetime('now','localtime')"
            await db.execute(f"UPDATE devices SET {sets} WHERE mac=? AND user_id=?", vals)
    else:
        # INSERT: 新设备
        cols = ["mac", "user_id"] + list(fields.keys())
        placeholders = ",".join(["?" for _ in cols])
        vals = [mac, user_id] + list(fields.values())
        await db.execute(
            f"INSERT INTO devices ({','.join(cols)}) VALUES ({placeholders})",
            vals,
        )

    await db.commit()

    # 返回最新记录
    cur = await db.execute("SELECT * FROM devices WHERE mac=? AND user_id=?", (mac, user_id))
    result = await cur.fetchone()
    return dict(result)


async def get_all_devices(user_id: int = None, online_only: bool = False) -> list[dict]:
    """
    获取设备列表
    user_id: 指定用户ID则只返回该用户的设备，None则返回所有
    online_only: 是否只返回在线设备
    """
    db = await get_db()
    conditions = []
    params = []
    
    if user_id is not None:
        conditions.append("user_id = ?")
        params.append(user_id)
    if online_only:
        conditions.append("is_online = 1")
    
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"SELECT * FROM devices{where_clause} ORDER BY last_seen_at DESC"
    
    cursor = await db.execute(sql, params)
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_device_by_mac(mac: str) -> dict | None:
    """根据 MAC 查找单个设备"""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM devices WHERE mac=?", (mac,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_device_stats() -> dict:
    """获取设备统计摘要 (在线数/离线数/总数等)"""
    db = await get_db()
    total_cur = await db.execute("SELECT COUNT(*) as cnt FROM devices")
    online_cur = await db.execute("SELECT COUNT(*) as cnt FROM devices WHERE is_online=1")
    low_battery_cur = await db.execute("SELECT COUNT(*) as cnt FROM devices WHERE is_online=1 AND voltage < 350 AND voltage IS NOT NULL")

    total = (await total_cur.fetchone())["cnt"]
    online = (await online_cur.fetchone())["cnt"]
    low_battery = (await low_battery_cur.fetchone())["cnt"]

    return {
        "total": total,
        "online": online,
        "offline": total - online,
        "low_battery": low_battery,
        "online_rate": round((online / total * 100), 1) if total > 0 else 0,
    }


# ============================================================
# DeviceEvents 表操作
# ============================================================

async def add_device_event(mac: str, event_type: str, payload: dict | None = None):
    """记录一条设备事件"""
    db = await get_db()
    payload_json = json.dumps(payload, ensure_ascii=False) if payload else None
    await db.execute(
        "INSERT INTO device_events (mac, event_type, payload) VALUES (?, ?, ?)",
        (mac, event_type, payload_json),
    )
    await db.commit()


async def get_device_events(
    mac: str | None = None,
    event_type: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[dict], int]:
    """
    分页查询设备事件
    Returns: (事件列表, 总数)
    """
    db = await get_db()
    where_parts = []
    params: list = []

    if mac:
        where_parts.append("mac = ?")
        params.append(mac)
    if event_type:
        where_parts.append("event_type = ?")
        params.append(event_type)

    where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    # 总数
    cnt_sql = f"SELECT COUNT(*) as total FROM device_events {where_sql}"
    cur = await db.execute(cnt_sql, params)
    total = (await cur.fetchone())["total"]

    # 分页数据
    offset = (page - 1) * page_size
    sql = f"""SELECT * FROM device_events {where_sql} 
              ORDER BY created_at DESC LIMIT ? OFFSET ?"""
    cur = await db.execute(sql, params + [page_size, offset])
    rows = await cur.fetchall()

    return [dict(r) for r in rows], total


async def get_recent_events(limit: int = 100) -> list[dict]:
    """获取最近的N条设备事件 (用于仪表盘展示)"""
    db = await get_db()
    cur = await db.execute(
        f"SELECT * FROM device_events ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def cleanup_old_events(days: int = 30):
    """清理 N 天前的事件记录，返回清理数量"""
    db = await get_db()
    cur = await db.execute(
        "DELETE FROM device_events WHERE created_at < datetime('now', 'localtime', ? || ' days')",
        (str(-days),),
    )
    deleted = cur.rowcount
    await db.commit()
    return deleted


# ============================================================
# TemplateDeviceBindings 表操作（模板-设备关联持久化）
# ============================================================

async def save_template_bindings(tid: str, macs: list[str]) -> int:
    """
    批量保存模板-设备绑定关系 (UPSERT)
    传入完整的 macs 列表，会：
      - 新增不在表中的记录
      - 保留已在表中的记录（更新 updated_at）
      - 移除不再列表中的旧记录（如果 tid 已有其他 mac 绑定）
    返回保存的记录数
    """
    db = await get_db()
    saved = 0

    async with db.execute("BEGIN") as _cur:
        # Upsert 每个 mac
        for mac in macs:
            await db.execute("""
                INSERT INTO template_device_bindings (tid, mac, created_at, updated_at)
                VALUES (?, ?, datetime('now','localtime'), datetime('now','localtime'))
                ON CONFLICT(tid, mac) DO UPDATE SET
                    updated_at = datetime('now','localtime')
            """, (tid, mac))
            saved += 1

        # 清理不在新列表中的旧绑定（可选：是否要自动清理未选的？这里保留，由前端显式删除）
        # 不做自动清理，让 remove_template_binding 显式控制

        await db.commit()

    logger.info(f"已保存 {saved} 条模板-设备绑定 (tid={tid})")
    return saved


async def get_template_bound_macs(tid: str) -> list[str]:
    """查询某模板绑定的所有设备 MAC 地址列表"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT mac FROM template_device_bindings WHERE tid=? ORDER BY created_at",
        (tid,),
    )
    rows = await cursor.fetchall()
    return [r["mac"] for r in rows]


async def remove_template_binding(tid: str, mac: str) -> bool:
    """删除单条模板-设备绑定，返回是否成功"""
    db = await get_db()
    cur = await db.execute(
        "DELETE FROM template_device_bindings WHERE tid=? AND mac=?",
        (tid, mac),
    )
    await db.commit()
    removed = cur.rowcount > 0
    if removed:
        logger.info(f"已移除绑定: tid={tid}, mac={mac}")
    return removed


# ============================================================
# UpdateTasks 表操作（更新任务主表）
# ============================================================

async def create_update_task(name: str, tid: str, tname: str = "", user_id: int = 0) -> int:
    """创建新更新任务，返回 task_id"""
    db = await get_db()
    cursor = await db.execute(
        """INSERT INTO update_tasks (name, tid, tname, user_id, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, 'draft', datetime('now','localtime'), datetime('now','localtime'))""",
        (name, tid, tname, user_id),
    )
    await db.commit()
    task_id = cursor.lastrowid
    logger.info(f"创建更新任务: id={task_id}, name={name}, tid={tid}, user_id={user_id}")
    return task_id


async def get_task_list(
    page: int = 1,
    page_size: int = 20,
    status_filter: str = "",
    user_id: int = 0,
) -> tuple[list[dict], int]:
    """
    分页查询更新任务列表（含摘要统计）
    Returns: (items列表, total总数)
    """
    db = await get_db()

    where_parts = ["user_id = ?"]
    params: list = [user_id]
    if status_filter:
        where_parts.append("status = ?")
        params.append(status_filter)

    where_sql = f"WHERE {' AND '.join(where_parts)}"

    cnt_sql = f"SELECT COUNT(*) as total FROM update_tasks {where_sql}"
    cursor = await db.execute(cnt_sql, params)
    total = (await cursor.fetchone())["total"]

    offset = (page - 1) * page_size
    sql = f"""SELECT * FROM update_tasks {where_sql}
              ORDER BY updated_at DESC LIMIT ? OFFSET ?"""
    cursor = await db.execute(sql, params + [page_size, offset])
    rows = await cursor.fetchall()

    items = [dict(r) for r in rows]
    return items, total


async def get_task_detail(task_id: int, user_id: int = 0) -> dict | None:
    """获取单个任务详情（含设备列表和状态统计）"""
    db = await get_db()

    # 主表信息（带用户权限检查）
    cursor = await db.execute(
        "SELECT * FROM update_tasks WHERE id=? AND user_id=?", 
        (task_id, user_id)
    )
    row = await cursor.fetchone()
    if not row:
        return None

    task = dict(row)

    # 设备明细（含子表行数据）
    dcur = await db.execute(
        "SELECT * FROM task_devices WHERE task_id=? ORDER BY created_at",
        (task_id,),
    )
    devices = [dict(d) for d in await dcur.fetchall()]

    # 批量查询所有设备的子表行数据（避免 N+1）
    if devices:
        dev_ids = [str(d["id"]) for d in devices]
        rcur = await db.execute(
            f"SELECT * FROM task_device_rows WHERE task_device_id IN ({','.join(['?']*len(dev_ids))}) ORDER BY task_device_id, sort_order",
            dev_ids,
        )
        rows_map: dict[int, list[dict]] = {}
        for row in await rcur.fetchall():
            rd = dict(row)
            rows_map.setdefault(rd["task_device_id"], []).append(rd)
        for d in devices:
            d["rows"] = rows_map.get(d["id"], [])

    task["devices"] = devices

    # 状态统计
    task["progress"] = {
        "pending": sum(1 for d in devices if d["update_status"] == "pending"),
        "sent": sum(1 for d in devices if d["update_status"] == "sent"),
        "success": sum(1 for d in devices if d["update_status"] == "success"),
        "failed": sum(1 for d in devices if d["update_status"] == "failed"),
    }

    return task


async def update_task(task_id: int, **kwargs) -> bool:
    """更新任务字段（name/default_data/status/total_devices/success_count/failed_count/sent_at/completed_at）"""
    db = await get_db()
    kwargs["updated_at"] = "datetime('now','localtime')"
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [task_id]
    await db.execute(f"UPDATE update_tasks SET {sets} WHERE id=?", values)
    await db.commit()
    return True


async def delete_task(task_id: int) -> bool:
    """删除任务（级联删除所有设备明细），返回是否成功"""
    db = await get_db()
    # 先删除关联的设备明细（外键级联应该自动处理，但显式确保）
    await db.execute("DELETE FROM task_devices WHERE task_id=?", (task_id,))
    cur = await db.execute("DELETE FROM update_tasks WHERE id=?", (task_id,))
    await db.commit()
    deleted = cur.rowcount > 0
    if deleted:
        logger.info(f"已删除任务: id={task_id}")
    return deleted


# ============================================================
# TaskDevices 表操作（任务-设备明细）
# ============================================================

async def add_task_devices(
    task_id: int,
    macs: list[str],
    custom_data_map: dict | None = None,
) -> int:
    """
    批量添加设备到任务中，跳过已存在的
    custom_data_map: {mac: {...}} 可选，为每台设备预设自定义数据
    返回新增数量
    """
    db = await get_db()
    added = 0
    for mac in macs:
        custom_json = json.dumps(custom_data_map.get(mac), ensure_ascii=False) if (custom_data_map and mac in custom_data_map) else '{}'
        try:
            await db.execute(
                """INSERT OR IGNORE INTO task_devices (task_id, mac, custom_data)
                   VALUES (?, ?, ?)""",
                (task_id, mac, custom_json),
            )
            added += 1
        except Exception:
            pass  # 已存在则跳过

    # 更新任务的 total_devices
    ccur = await db.execute("SELECT COUNT(*) as cnt FROM task_devices WHERE task_id=?", (task_id,))
    total = (await ccur.fetchone())["cnt"]
    await db.execute("UPDATE update_tasks SET total_devices=?, updated_at=datetime('now','localtime') WHERE id=?", (total, task_id))

    await db.commit()
    logger.info(f"任务 {task_id} 新增 {added} 台设备 (当前共{total}台)")
    return added


async def remove_task_device(task_id: int, mac: str) -> bool:
    """从任务中移除单台设备"""
    db = await get_db()
    cur = await db.execute(
        "DELETE FROM task_devices WHERE task_id=? AND mac=?",
        (task_id, mac),
    )

    # 更新任务的 total_devices
    ccur = await db.execute("SELECT COUNT(*) as cnt FROM task_devices WHERE task_id=?", (task_id,))
    total = (await ccur.fetchone())["cnt"]
    await db.execute("UPDATE update_tasks SET total_devices=?, updated_at=datetime('now','localtime') WHERE id=?", (total, task_id))

    await db.commit()
    removed = cur.rowcount > 0
    if removed:
        logger.info(f"从任务 {task_id} 移除设备: mac={mac}")
    return removed


async def get_task_device_list(task_id: int) -> list[dict]:
    """获取任务的所有设备列表"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM task_devices WHERE task_id=? ORDER BY created_at",
        (task_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def update_task_device_custom_data(task_id: int, mac: str, custom_data: dict) -> bool:
    """更新单台设备的自定义数据"""
    db = await get_db()
    custom_json = json.dumps(custom_data, ensure_ascii=False)
    await db.execute(
        """UPDATE task_devices SET custom_data=?, updated_at=datetime('now','localtime')
           WHERE task_id=? AND mac=?""",
        (custom_json, task_id, mac),
    )
    await db.commit()
    return True


async def update_task_device_status(
    task_id: int,
    mac: str,
    status: str,
    error_msg: str = "",
) -> bool:
    """
    更新单台设备的推送状态（核心回调接口）
    status: pending / sent / success / failed
    """
    db = await get_db()
    now_col = "datetime('now','localtime')"

    if status in ("sent",):
        sql = f"""UPDATE task_devices SET update_status=?, sent_at=datetime('now','localtime')
                  WHERE task_id=? AND mac=?"""
        await db.execute(sql, (status, task_id, mac))
    elif status in ("success", "failed"):
        sql = f"""UPDATE task_devices SET update_status=?, error_msg=?,
                  finished_at=datetime('now','localtime')
                  WHERE task_id=? AND mac=?"""
        await db.execute(sql, (status, error_msg or "", task_id, mac))
    else:
        await db.execute(
            "UPDATE task_devices SET update_status=? WHERE task_id=? AND mac=?",
            (status, task_id, mac),
        )

    await db.commit()
    return True


async def update_device_status_by_mac(
    mac: str,
    status: str,
    error_msg: str = "",
) -> int:
    """
    根据 MAC 地址批量更新所有任务中该设备的状态
    只更新 update_status='sent' 的记录（避免重复标记已完成的设备）
    status: success / failed
    Returns: 更新的行数
    """
    db = await get_db()
    await db.execute(
        """UPDATE task_devices SET update_status=?, error_msg=?,
           finished_at=datetime('now','localtime')
           WHERE mac=? AND update_status='sent'""",
        (status, error_msg or "", mac),
    )
    await db.commit()

    # 查找受影响的 task_id 并刷新任务汇总
    cur = await db.execute(
        "SELECT DISTINCT task_id FROM task_devices WHERE mac=? AND update_status IN ('success', 'failed')",
        (mac,),
    )
    rows = await cur.fetchall()
    for row in rows:
        await _refresh_task_summary(db, row[0])

    # 返回影响行数
    cnt_cur = await db.execute("SELECT changes()")
    cnt_row = await cnt_cur.fetchone()
    return cnt_row[0] if cnt_row else 0


async def _refresh_task_summary(db, task_id: int):
    """根据 task_devices 各状态计数刷新 tasks 主表的状态"""
    cursor = await db.execute(
        """SELECT update_status, COUNT(*) as cnt FROM task_devices
           WHERE task_id=? GROUP BY update_status""",
        (task_id,),
    )
    counts = {"pending": 0, "sent": 0, "success": 0, "failed": 0}
    async for row in cursor:
        counts[row[0]] = row[1]

    total = sum(counts.values())
    if total == 0:
        return

    all_done = counts["sent"] == 0  # 没有 sent 说明全部有结果了
    if all_done and total > 0:
        new_task_status = "completed"
    elif counts["sent"] > 0:
        new_task_status = "sent"
    else:
        new_task_status = "pending"

    await db.execute(
        """UPDATE update_tasks SET status=?, success_count=?, failed_count=?
           WHERE id=?""",
        (new_task_status, counts["success"], counts["failed"], task_id),
    )
    await db.commit()


async def get_task_progress(task_id: int) -> dict:
    """获取任务各状态计数统计"""
    db = await get_db()
    cursor = await db.execute(
        """SELECT update_status, COUNT(*) as cnt
           FROM task_devices WHERE task_id=?
           GROUP BY update_status""",
        (task_id,),
    )
    rows = await cursor.fetchall()
    progress = {"pending": 0, "sent": 0, "success": 0, "failed": 0}
    for r in rows:
        progress[r["update_status"]] = r["cnt"]
    return progress


async def batch_update_device_statuses(
    task_id: int,
    results: list[dict],  # [{mac, success, error?}]
) -> dict:
    """
    批量更新设备状态并汇总任务状态（执行推送后调用）
    Returns: {success_count, failed_count, pending_count}
    """
    db = await get_db()
    success_cnt = 0
    failed_cnt = 0

    async with db.execute("BEGIN") as _cur:
        for r in results:
            mac = r.get("mac", "")
            ok = r.get("success", False)
            err = r.get("error", "")
            if ok:
                status = "success"
                success_cnt += 1
            else:
                status = "failed"
                failed_cnt += 1

            await db.execute(
                """UPDATE task_devices SET update_status=?, error_msg=?,
                   finished_at=datetime('now','localtime')
                   WHERE task_id=? AND mac=?""",
                (status, err or "", task_id, mac),
            )

        # 更新任务主表状态
        all_done = (success_cnt + failed_cnt) >= len(results)
        new_task_status = "completed" if all_done else "sent"
        sent_at_val = "datetime('now','localtime')" if new_task_status == "sent" else None
        completed_at_val = "datetime('now','localtime')" if new_task_status == "completed" else None

        set_parts = ["status=?", "success_count=?", "failed_count=?"]
        vals: list = [new_task_status, success_cnt, failed_cnt]
        if sent_at_val:
            set_parts.append("sent_at=datetime('now','localtime')")
        if completed_at_val:
            set_parts.append("completed_at=datetime('now','localtime')")
        set_parts.append("updated_at=datetime('now','localtime')")

        await db.execute(
            f"UPDATE update_tasks SET {','.join(set_parts)} WHERE id=?",
            vals + [task_id],
        )

        await db.commit()

    logger.info(f"任务 {task_id} 推送结果: 成功{success_cnt} 失败{failed_cnt}")

    pending_cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM task_devices WHERE task_id=? AND update_status='pending'",
        (task_id,),
    )
    pending_cnt = (await pending_cursor.fetchone())["cnt"]

    return {
        "success_count": success_cnt,
        "failed_count": failed_cnt,
        "pending_count": pending_cnt,
    }


# ============================================================
# TaskDeviceRows 表操作（设备多行数据子表）
# ============================================================

async def add_task_device_row(
    task_device_id: int,
    custom_data: dict,
    sort_order: int | None = None,
) -> int:
    """
    为某台任务设备添加一条子表数据行
    如果 sort_order 为 None，自动取当前最大值+1
    返回新行的 id
    """
    db = await get_db()
    if sort_order is None:
        cur = await db.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM task_device_rows WHERE task_device_id=?",
            (task_device_id,),
        )
        sort_order = (await cur.fetchone())[0]

    custom_json = json.dumps(custom_data, ensure_ascii=False)
    cur = await db.execute(
        """INSERT INTO task_device_rows (task_device_id, sort_order, custom_data, created_at)
           VALUES (?, ?, ?, datetime('now','localtime'))""",
        (task_device_id, sort_order, custom_json),
    )
    await db.commit()
    return cur.lastrowid


async def get_task_device_rows(task_device_id: int) -> list[dict]:
    """获取某台设备的所有子表行（按 sort_order 排序）"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM task_device_rows WHERE task_device_id=? ORDER BY sort_order",
        (task_device_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_first_task_device_row(task_device_id: int) -> dict | None:
    """获取某台设备排序第一的子表行（sort_order 最小），用于推送时合并数据"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM task_device_rows WHERE task_device_id=? ORDER BY sort_order ASC LIMIT 1",
        (task_device_id,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_task_device_row(row_id: int, custom_data: dict) -> bool:
    """更新单条子表行的自定义数据"""
    db = await get_db()
    custom_json = json.dumps(custom_data, ensure_ascii=False)
    cur = await db.execute(
        "UPDATE task_device_rows SET custom_data=? WHERE id=?",
        (custom_json, row_id),
    )
    await db.commit()
    return cur.rowcount > 0


async def delete_task_device_row(row_id: int) -> bool:
    """删除单条子表行"""
    db = await get_db()
    cur = await db.execute("DELETE FROM task_device_rows WHERE id=?", (row_id,))
    await db.commit()
    return cur.rowcount > 0


async def delete_all_task_device_rows(task_device_id: int) -> int:
    """清空某台设备的所有子表行，返回删除数量"""
    db = await get_db()
    cur = await db.execute(
        "DELETE FROM task_device_rows WHERE task_device_id=?", (task_device_id,)
    )
    await db.commit()
    deleted = cur.rowcount
    # 重新编排剩余行的 sort_order（如果有并发插入需注意，但此处简单处理）
    if deleted > 0:
        rows = await get_task_device_rows(task_device_id)
        for idx, r in enumerate(rows):
            await db.execute(
                "UPDATE task_device_rows SET sort_order=? WHERE id=?", (idx, r["id"])
            )
        await db.commit()
    return deleted


async def batch_add_task_device_rows(
    task_device_id: int,
    data_list: list[dict],
) -> int:
    """
    批量添加子表行数据
    data_list: [custom_data_dict, ...]
    从当前最大 sort_order 开始递增
    返回新增数量
    """
    db = await get_db()
    cur = await db.execute(
        "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM task_device_rows WHERE task_device_id=?",
        (task_device_id,),
    )
    base_sort = (await cur.fetchone())[0]

    added = 0
    for idx, data in enumerate(data_list):
        custom_json = json.dumps(data, ensure_ascii=False)
        await db.execute(
            """INSERT INTO task_device_rows (task_device_id, sort_order, custom_data, created_at)
               VALUES (?, ?, ?, datetime('now','localtime'))""",
            (task_device_id, base_sort + idx, custom_json),
        )
        added += 1

    await db.commit()
    return added
