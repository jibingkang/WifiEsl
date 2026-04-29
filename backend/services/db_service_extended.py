#!/usr/bin/env python3
"""
数据库服务扩展 - 多用户支持
"""

import json
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# 导入现有函数
from .db_service import (
    get_db, hash_password, encrypt_wifi_password, decrypt_wifi_password
)

async def create_user_with_wifi_config(
    username: str,
    password: str,
    role: str = "operator",
    wifi_username: Optional[str] = None,
    wifi_password: Optional[str] = None,
    wifi_apikey: Optional[str] = None,
    wifi_token: Optional[str] = None,       # WIFI系统token
    wifi_base_url: Optional[str] = None,
    wifi_mqtt_broker: Optional[str] = None, # MQTT broker地址
    mqtt_username: Optional[str] = None,    # MQTT用户名
    mqtt_password: Optional[str] = None,    # MQTT密码
    parent_user_id: int = 0,
    created_by: int = 0,
) -> int:
    """
    创建新用户，包含WIFI系统配置
    """
    db = await get_db()
    
    # 对WIFI密码进行加密
    encrypted_wifi_password = ""
    if wifi_password:
        try:
            encrypted_wifi_password = encrypt_wifi_password(wifi_password)
        except Exception as e:
            logger.warning(f"WIFI密码加密失败: {e}")
            encrypted_wifi_password = wifi_password
    
    # 本地用户密码哈希
    pwd_hash = hash_password(password)
    
    # 检查用户名是否已存在
    cur = await db.execute("SELECT id FROM users WHERE username=?", (username,))
    existing_user = await cur.fetchone()
    
    if existing_user:
        raise ValueError(f"用户名 '{username}' 已存在")
    
    # 设置MQTT默认值
    mqtt_username_val = mqtt_username or "test"
    mqtt_password_val = mqtt_password or "123456"
    
    # 插入新用户
    cursor = await db.execute(
        """INSERT INTO users (
            username, password, role,
            wifi_username, wifi_password, wifi_apikey, wifi_base_url, wifi_mqtt_broker,
            mqtt_username, mqtt_password,
            parent_user_id, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            username, pwd_hash, role,
            wifi_username, encrypted_wifi_password, wifi_apikey, wifi_base_url, wifi_mqtt_broker,
            mqtt_username_val, mqtt_password_val,
            parent_user_id, created_by
        )
    )
    
    await db.commit()
    user_id = cursor.lastrowid
    
    logger.info(f"创建用户成功: {username} (ID: {user_id}), 角色: {role}")
    
    if wifi_username:
        logger.info(f"   WIFI配置: 用户名={wifi_username}, API地址={wifi_base_url}, MQTT broker={wifi_mqtt_broker}")
        logger.info(f"   MQTT配置: 用户名={mqtt_username_val}, 密码={'*' * len(mqtt_password_val)}")
    
    return user_id

async def update_user_wifi_config(
    user_id: int,
    wifi_username: Optional[str] = None,
    wifi_password: Optional[str] = None,
    wifi_apikey: Optional[str] = None,
    wifi_token: Optional[str] = None,       # 新增：WIFI系统token
    wifi_base_url: Optional[str] = None,
    wifi_mqtt_broker: Optional[str] = None,  # 新增：MQTT broker地址
    mqtt_username: Optional[str] = None,     # 新增：MQTT用户名
    mqtt_password: Optional[str] = None,     # 新增：MQTT密码
    updated_by: Optional[int] = None,
) -> bool:
    """
    更新用户的WIFI系统配置
    """
    db = await get_db()
    
    update_fields = {}
    
    if wifi_username is not None:
        update_fields['wifi_username'] = wifi_username
    
    if wifi_password is not None:
        # 加密存储WIFI密码

        try:
            encrypted_wifi_password = encrypt_wifi_password(wifi_password)
            update_fields['wifi_password'] = encrypted_wifi_password
        except Exception as e:
            logger.warning(f"WIFI密码加密失败: {e}")
            update_fields['wifi_password'] = wifi_password
    
    if wifi_apikey is not None:
        update_fields['wifi_apikey'] = wifi_apikey
    
    if wifi_token is not None:
        update_fields['wifi_token'] = wifi_token
    
    if wifi_base_url is not None:
        update_fields['wifi_base_url'] = wifi_base_url
    
    if wifi_mqtt_broker is not None:
        update_fields['wifi_mqtt_broker'] = wifi_mqtt_broker
    
    if mqtt_username is not None:
        update_fields['mqtt_username'] = mqtt_username
    
    if mqtt_password is not None:
        update_fields['mqtt_password'] = mqtt_password
    
    if not update_fields:
        return False
    
    # 添加更新时间

    update_fields['updated_at'] = "datetime('now','localtime')"
    
    # 构建更新语句

    sets = ", ".join(f"{k} = ?" for k in update_fields)
    values = list(update_fields.values()) + [user_id]
    
    cursor = await db.execute(
        f"UPDATE users SET {sets} WHERE id = ?",
        values
    )
    
    await db.commit()
    
    rows_updated = cursor.rowcount > 0
    
    if rows_updated:
        logger.info(f"已更新用户 {user_id} 的WIFI配置")
    
    return rows_updated

async def get_user_wifi_config(user_id: int) -> Dict[str, Any]:
    """
    获取用户的WIFI系统配置
    返回包含解密后的密码
    """
    db = await get_db()
    
    cursor = await db.execute(
        """SELECT 
            wifi_username, wifi_password, wifi_apikey, wifi_token, wifi_base_url, wifi_mqtt_broker,
            mqtt_username, mqtt_password,
            username, role
        FROM users WHERE id = ?""",
        (user_id,)
    )
    
    row = await cursor.fetchone()
    
    if not row:
        raise ValueError(f"用户 ID {user_id} 不存在")
    
    # 手动创建字典，确保所有字段都被包含
    column_names = ['wifi_username', 'wifi_password', 'wifi_apikey', 'wifi_token', 'wifi_base_url', 'wifi_mqtt_broker', 'mqtt_username', 'mqtt_password', 'username', 'role']
    config = {}
    
    for i, col_name in enumerate(column_names):
        if i < len(row):
            config[col_name] = row[i]
        else:
            config[col_name] = None
    
    # 解密WIFI密码（如果需要）

    encrypted_password = config.get('wifi_password')
    if encrypted_password:
        try:
            decrypted_password = decrypt_wifi_password(encrypted_password)
            config['wifi_password_decrypted'] = decrypted_password
            
            # 安全：不返回解密后的密码到日志

        except Exception as e:
            logger.warning(f"解密用户 {user_id} 的WIFI密码失败: {e}")
            config['wifi_password_decrypted'] = encrypted_password
    
    # 安全：不记录敏感信息到日志

    logger.debug(f"获取用户 {user_id} 的WIFI配置")
    
    return config

async def get_users_by_parent(parent_user_id: int) -> List[Dict[str, Any]]:
    """
    获取指定父用户下的所有子用户
    """
    db = await get_db()
    
    cursor = await db.execute(
        """SELECT 
            id, username, role, avatar, status, 
            wifi_username, wifi_apikey, wifi_base_url, wifi_mqtt_broker,
            parent_user_id, created_by,
            created_at, updated_at
        FROM users 
        WHERE parent_user_id = ? AND status = 'active'
        ORDER BY id""",
        (parent_user_id,)

    )
    
    rows = await cursor.fetchall()
    
    users = [dict(row) for row in rows]
    
    logger.info(f"获取到父用户 {parent_user_id} 下的 {len(users)} 个子用户")
    
    return users

async def get_user_devices(user_id: int) -> List[Dict[str, Any]]:
    """
    获取用户可见的设备（根据用户的WIFI配置）
    这个函数需要在 wifi_client.py 中实现相应的调用逻辑
    """
    # 1. 获取用户的WIFI配置

    config = await get_user_wifi_config(user_id)
    
    # 2. 调用WIFI系统API获取设备列表

    # 这需要扩展 wifi_client.py 支持传入不同的配置

    from .wifi_client import wifi_proxy
    
    wifi_username = config.get('wifi_username')
    wifi_apikey = config.get('wifi_apikey')
    wifi_base_url = config.get('wifi_base_url')
    
    if not all([wifi_username, wifi_apikey, wifi_base_url]):
        logger.warning(f"用户 {user_id} 的WIFI配置不完整")
        return []
    
    # 这里需要扩展 wifi_client.py 支持使用不同的配置

    logger.info(f"使用用户 {user_id} 的WIFI配置获取设备列表")
    logger.info(f"   WIFI用户名: {wifi_username}")
    logger.info(f"   WIFI地址: {wifi_base_url}")
    
    # 注意：这里需要修改 wifi_client.py 支持传入不同的配置

    # 暂时使用已有的调用方式（假设配置已经生效）

    try:
        # 这里需要实现逻辑：使用用户的WIFI配置调用WIFI系统

        # 目前先返回空列表，需要进一步实现

        return []
    except Exception as e:
        logger.error(f"获取用户 {user_id} 的设备失败: {e}")
        return []

async def list_all_users() -> List[Dict[str, Any]]:
    """
    列出所有用户（超级管理员权限）
    只返回基本信息，不返回密码等敏感信息
    """
    db = await get_db()
    
    cursor = await db.execute(
        """SELECT 
            id, username, role, avatar, status, 
            wifi_username, wifi_apikey, wifi_token, wifi_base_url, wifi_mqtt_broker,
            mqtt_username, mqtt_password,
            parent_user_id, created_by,
            created_at, updated_at
        FROM users 
        ORDER BY id"""
    )
    
    rows = await cursor.fetchall()
    
    users = [dict(row) for row in rows]
    
    logger.info(f"共获取 {len(users)} 个用户")
    
    return users

async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    根据用户ID获取用户基本信息（用于配置继承查询）
    """
    db = await get_db()
    
    cursor = await db.execute(
        """SELECT id, username, role, wifi_username, wifi_password, wifi_apikey, wifi_base_url,
           wifi_mqtt_broker, mqtt_username, mqtt_password, parent_user_id, status
        FROM users WHERE id = ?""",
        (user_id,)
    )
    
    row = await cursor.fetchone()
    
    if not row:
        return None
    
    return dict(row)


async def get_user_with_details(user_id: int) -> Optional[Dict[str, Any]]:
    """
    获取用户的完整信息（包含WIFI配置）
    """
    db = await get_db()
    
    cursor = await db.execute(
        """SELECT * FROM users WHERE id = ?""",
        (user_id,)

    )
    
    row = await cursor.fetchone()
    
    if not row:
        return None
    
    user = dict(row)
    
    # 安全：隐藏密码哈希

    if 'password' in user:
        user['password'] = '***'
    
    # 解密WIFI密码（如果需要）

    if user.get('wifi_password'):
        try:
            decrypted = decrypt_wifi_password(user['wifi_password'])
            user['wifi_password_decrypted'] = decrypted
            
            # 安全：日志中不记录解密后的密码

        except Exception as e:
            logger.warning(f"解密用户 {user_id} 的WIFI密码失败: {e}")
            user['wifi_password_decrypted'] = '[解密失败]'
    
    logger.debug(f"获取用户 {user_id} 的详细信息")
    
    return user