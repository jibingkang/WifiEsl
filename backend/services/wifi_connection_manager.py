#!/usr/bin/env python3
"""
WIFI连接管理器 - 多用户WIFI系统连接管理
为每个用户管理WIFI系统的登录状态和token
"""
import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .db_service_extended import get_user_wifi_config
from .wifi_client import WifiSystemProxy

logger = logging.getLogger(__name__)


@dataclass
class WifiConnection:
    """WIFI连接信息"""
    user_id: int
    wifi_username: str
    wifi_password: str
    wifi_apikey: str = ""         # 用于MQTT订阅的API Key
    wifi_base_url: str = ""
    wifi_mqtt_broker: str = ""     # MQTT broker地址
    mqtt_username: str = "test"    # MQTT连接用户名（默认test）
    mqtt_password: str = "123456"  # MQTT连接密码（默认123456）
    token: str = ""                # WIFI系统登录返回的token（用于API调用）
    api_key: str = ""              # 兼容字段
    last_login_time: float = 0
    is_valid: bool = False
    
    def is_expired(self) -> bool:
        """检查token是否过期（假设30分钟过期）"""
        if not self.last_login_time or not self.token:
            return True
        # 检查是否超过30分钟
        return time.time() - self.last_login_time > 1800


class WifiConnectionManager:
    """WIFI连接管理器 - 单例"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connections: Dict[int, WifiConnection] = {}
            cls._instance._user_tokens: Dict[int, str] = {}  # 用户ID -> token映射
        return cls._instance
    
    async def get_connection(self, user_id: int) -> Optional[WifiConnection]:
        """获取用户的WIFI连接，如果不存在则创建"""
        async with self._lock:
            # 检查是否已有连接
            if user_id in self._connections:
                conn = self._connections[user_id]
                # 检查连接是否有效且未过期
                if conn.is_valid and not conn.is_expired():
                    return conn
                # 连接已失效或过期，需要重新登录
                logger.info(f"用户 {user_id} 的WIFI连接已失效或过期，重新登录...")
            
            # 获取用户WIFI配置
            try:
                config = await get_user_wifi_config(user_id)
            except Exception as e:
                logger.error(f"获取用户 {user_id} 的WIFI配置失败: {e}")
                return None
            
            # 检查配置是否完整
            wifi_username = config.get('wifi_username')
            wifi_password = config.get('wifi_password_decrypted', config.get('wifi_password', ''))
            wifi_apikey = config.get('wifi_apikey', '')
            wifi_base_url = config.get('wifi_base_url', '')
            
            if not all([wifi_username, wifi_password, wifi_base_url]):
                logger.warning(f"用户 {user_id} 的WIFI配置不完整")
                return None
            
            # 尝试登录WIFI系统
            try:
                logger.info(f"正在为用户 {user_id} 登录WIFI系统: {wifi_base_url}")
                login_result = await WifiSystemProxy.login(
                    username=wifi_username,
                    password=wifi_password,
                    base_url=wifi_base_url
                )
                
                # 从登录结果中提取token
                # 根据用户说明，WIFI系统只返回token，不返回apiKey
                logger.info(f"用户 {user_id} WIFI登录结果: {json.dumps(login_result)[:200]}")
                
                token = login_result.get('token', '')
                
                if not token:
                    # 如果token字段不存在，尝试从其他可能字段获取
                    token = login_result.get('data', {}).get('token', '')
                    logger.info(f"  从data.token获取token: {token[:8] if token else 'None'}")
                    if not token:
                        # 最后尝试使用apiKey作为token（兼容旧逻辑）
                        token = login_result.get('apiKey', '')
                        logger.info(f"  从apiKey获取token: {token[:8] if token else 'None'}")
                
                if not token:
                    logger.error(f"用户 {user_id} WIFI登录失败：未获取到token")
                    return None
                
                logger.info(f"用户 {user_id} 获取到token: {token[:8]}...")
                
                # 对于WIFI系统，token就是api_key，用于后续API调用
                api_key = token
                
                # 创建连接对象
                conn = WifiConnection(
                    user_id=user_id,
                    wifi_username=wifi_username,
                    wifi_password=wifi_password,
                    wifi_apikey=wifi_apikey or api_key,
                    wifi_base_url=wifi_base_url,
                    wifi_mqtt_broker=config.get('wifi_mqtt_broker', ''),
                    mqtt_username=config.get('mqtt_username', 'test'),
                    mqtt_password=config.get('mqtt_password', '123456'),
                    token=token,
                    api_key=api_key,
                    last_login_time=time.time(),
                    is_valid=True
                )
                
                # 保存连接
                self._connections[user_id] = conn
                self._user_tokens[user_id] = token
                
                # 将token保存到数据库
                try:
                    from .db_service_extended import update_user_wifi_config
                    await update_user_wifi_config(
                        user_id=user_id,
                        wifi_token=token
                    )
                    logger.info(f"用户 {user_id} WIFI token已保存到数据库")
                except Exception as db_err:
                    logger.warning(f"保存WIFI token到数据库失败: {db_err}")
                
                logger.info(f"用户 {user_id} WIFI登录成功，token: {token[:8]}...")
                return conn
                
            except Exception as e:
                logger.error(f"用户 {user_id} WIFI系统登录失败: {e}")
                return None
    
    async def get_token_for_user(self, user_id: int) -> Optional[str]:
        """获取用户的WIFI系统token"""
        conn = await self.get_connection(user_id)
        if conn:
            return conn.token
        return None
    
    async def get_api_key_for_user(self, user_id: int) -> Optional[str]:
        """获取用户的WIFI系统api_key"""
        conn = await self.get_connection(user_id)
        if conn:
            return conn.api_key or conn.token
        return None
    
    async def get_base_url_for_user(self, user_id: int) -> Optional[str]:
        """获取用户的WIFI系统base_url"""
        conn = await self.get_connection(user_id)
        if conn:
            return conn.wifi_base_url
        return None
    
    async def get_mqtt_broker_for_user(self, user_id: int) -> Optional[str]:
        """获取用户的MQTT broker地址"""
        conn = await self.get_connection(user_id)
        if conn:
            return conn.wifi_mqtt_broker
        return None
    
    def invalidate_connection(self, user_id: int):
        """使指定用户的连接失效"""
        if user_id in self._connections:
            del self._connections[user_id]
        if user_id in self._user_tokens:
            del self._user_tokens[user_id]
        logger.info(f"用户 {user_id} 的WIFI连接已失效")
    
    def get_all_connections(self) -> Dict[int, WifiConnection]:
        """获取所有连接"""
        return self._connections.copy()


# 全局连接管理器实例
wifi_connection_manager = WifiConnectionManager()