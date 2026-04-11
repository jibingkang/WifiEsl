"""
WebSocket端点 - 实时设备状态推送
路径: /ws/device-status
由 ws_manager.ws_endpoint() 实现，此处仅做导入导出供 main.py 引用
"""

# WS端点实现在 services/ws_manager.py 中定义的 ws_endpoint() 函数
# 在 main.py 中通过 app.websocket() 注册
from services.ws_manager import ws_endpoint

__all__ = ["ws_endpoint"]
