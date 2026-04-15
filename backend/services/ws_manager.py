"""
WebSocket连接管理器
维护所有前端WebSocket连接池，支持广播消息、心跳检测
"""
import time
import json
import asyncio
import logging
from collections import defaultdict
from typing import Dict, Set

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接池管理"""

    def __init__(self):
        # 活跃连接: {connection_id: websocket}
        self._connections: Dict[str, any] = {}
        # 按类型分组: Set[connection_id]
        self._groups: Dict[str, Set[str]] = defaultdict(set)
        self._counter = 0
        self._lock = asyncio.Lock()

    async def connect(self, websocket) -> str:
        """注册新的WS连接，返回连接ID"""
        async with self._lock:
            cid = f"ws-{self._counter}"
            self._counter += 1
            self._connections[cid] = websocket
            self._groups["all"].add(cid)
            logger.info(f"[WS] 新连接: {cid}, 总数: {len(self._connections)}")
            return cid

    async def disconnect(self, connection_id: str):
        """移除WS连接"""
        async with self._lock:
            if connection_id in self._connections:
                del self._connections[connection_id]
                for g in list(self._groups.values()):
                    g.discard(connection_id)
                logger.info(f"[WS] 断开: {connection_id}, 总数: {len(self._connections)}")

    async def send_to(self, connection_id: str, message: dict):
        """向指定连接发消息"""
        ws = self._connections.get(connection_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"[WS] 发送失败({connection_id}): {e}")
                await self.disconnect(connection_id)

    async def broadcast(self, message: dict, group: str = "all"):
        """向指定组或所有连接广播消息"""
        cids = self._groups.get(group, set()).copy()
        disconnected = []

        for cid in cids:
            ws = self._connections.get(cid)
            if ws:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.debug(f"[WS] 广播失败({cid}): {e}")
                    disconnected.append(cid)

        # 清理失效连接
        for cid in disconnected:
            await self.disconnect(cid)

    async def broadcast_to_user(self, user_id: int, message: dict):
        """向特定用户的所有连接广播消息"""
        group_name = f"user_{user_id}"
        async with self._lock:
            cids = self._groups.get(group_name, set()).copy()
            all_groups = list(self._groups.keys())
        if not cids:
            raise RuntimeError(f"用户 {user_id} 没有活跃的WebSocket连接 (组名={group_name}, 现有组={all_groups})")
        logger.info(f"[WS] 广播到用户 {user_id}: {len(cids)} 个连接, 消息类型={message.get('type')}")
        await self.broadcast(message, group_name)

    async def add_to_user_group(self, connection_id: str, user_id: int):
        """将连接添加到用户组"""
        async with self._lock:
            group_name = f"user_{user_id}"
            self._groups[group_name].add(connection_id)
            logger.debug(f"[WS] 连接 {connection_id} 添加到用户组 {user_id}")

    async def remove_from_user_group(self, connection_id: str, user_id: int):
        """将连接从用户组移除"""
        async with self._lock:
            group_name = f"user_{user_id}"
            self._groups[group_name].discard(connection_id)
            logger.debug(f"[WS] 连接 {connection_id} 从用户组 {user_id} 移除")

    def count(self) -> int:
        """当前活跃连接数"""
        return len(self._connections)

    async def close(self):
        """关闭所有连接，清理资源"""
        async with self._lock:
            for cid, ws in list(self._connections.items()):
                try:
                    await ws.close()
                except Exception:
                    pass
            self._connections.clear()
            self._groups.clear()
            logger.info("[WS] 所有连接已清理")


# 全局单例
ws_manager = WebSocketManager()


async def ws_endpoint(websocket):
    """
    WebSocket端点处理函数
    路径: /ws/device-status
    """
    from services.multi_user_mqtt_manager import multi_user_mqtt_manager
    from services.auth_service import get_current_user_id_from_token
    
    cid = None
    user_id = None
    
    logger.info(f"[WS] ws_endpoint被调用，client: {websocket.client}")
    
    try:
        # 注意：accept() 已经在 main.py 的 websocket_endpoint 中调用过了
        # 这里不需要再调用，直接开始处理业务逻辑
        logger.info("[WS] WebSocket开始处理业务逻辑")
        
        cid = await ws_manager.connect(websocket)
        logger.info(f"[WS] 前端连接建立: {cid}")
        
        user_id = None
        
        # 等待第一条消息，应该是身份验证消息
        raw_data = await websocket.receive_text()
        try:
            data = json.loads(raw_data)
            if data.get("type") == "auth":
                token = data.get("data", {}).get("token")
                if token:
                    user_id = get_current_user_id_from_token(token)
                    if user_id:
                        # 添加到用户组
                        await ws_manager.add_to_user_group(cid, user_id)
                        logger.info(f"[WS] 连接 {cid} 认证为用户 {user_id}, 已添加到组 user_{user_id}")
                        
                        # 启动用户的MQTT连接
                        mqtt_connected = await multi_user_mqtt_manager.start_user_connection(user_id)
                        logger.info(f"[WS] 用户 {user_id} MQTT连接状态: {mqtt_connected}")
                        
                        # 发送欢迎消息+MQTT状态
                        await websocket.send_json({
                            "type": "connected",
                            "data": {
                                "connection_id": cid,
                                "user_id": user_id,
                                "mqtt_connected": mqtt_connected,
                            },
                            "timestamp": time.time(),
                        })
                        logger.info(f"[WS] 已发送connected消息，mqtt_connected={mqtt_connected}")
                        
                        # 如果MQTT已连接，额外发送一次mqtt_status确保前端收到
                        if mqtt_connected:
                            await websocket.send_json({
                                "type": "mqtt_status",
                                "data": {"connected": True},
                                "timestamp": time.time(),
                            })
                            logger.info(f"[WS] 已发送mqtt_status消息")
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": "无效的token"},
                            "timestamp": time.time(),
                        })
                        return
            else:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "请先发送auth消息"},
                    "timestamp": time.time(),
                })
                return
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "data": {"message": "无效的消息格式"},
                "timestamp": time.time(),
            })
            return

        # 保持连接，持续接收前端消息
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
                # 处理前端发来的消息
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time(),
                    })
                elif data.get("type") == "subscribe_mqtt":
                    # 可扩展: 指定订阅特定设备的MQTT topic
                    mac = data.get("data", {}).get("mac")
                    if mac:
                        await websocket.send_json({
                            "type": "subscribed",
                            "data": {"mac": mac},
                            "timestamp": time.time(),
                        })
                elif data.get("type") == "start_mqtt":
                    # 启动用户的MQTT连接
                    if user_id:
                        mqtt_connected = await multi_user_mqtt_manager.start_user_connection(user_id)
                        await websocket.send_json({
                            "type": "mqtt_status",
                            "data": {"connected": mqtt_connected},
                            "timestamp": time.time(),
                        })
            except json.JSONDecodeError:
                pass  # 忽略非JSON消息

    except Exception as e:
        logger.debug(f"[WS] 连接关闭/异常 ({cid}): {e}")
    finally:
        # 从用户组移除
        if user_id:
            await ws_manager.remove_from_user_group(cid, user_id)
        if cid:
            await ws_manager.disconnect(cid)
