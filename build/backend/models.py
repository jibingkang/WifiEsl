"""
WIFI标签管理系统 - Pydantic数据模型
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# ========== 通用响应格式 ==========

class ApiResponse(BaseModel):
    """统一API响应格式 (与前端 api/index.ts 拦截器约定一致)"""
    code: int = 20000
    message: str = ""
    data: Any = None


class PaginatedData(BaseModel):
    """分页数据 (前端 PaginatedResponse 格式)"""
    total: int = 0
    page: int = 1
    pageSize: int = 20
    items: list = []


# ========== 认证相关 ==========

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=2, max_length=20)
    password: str = Field(..., min_length=6, max_length=30)


class UserInfo(BaseModel):
    """用户信息"""
    id: str
    username: str
    role: str = "admin"
    avatar: str = ""
    apiKey: str


class LoginResponse(BaseModel):
    """登录响应 (前端 TokenInfo 格式)"""
    token: str
    expiresIn: int
    user: UserInfo


# ========== 设备相关 ==========

class Device(BaseModel):
    """设备数据模型"""
    id: Optional[str] = None
    mac: str
    ip: str = ""
    name: Optional[str] = None
    is_online: bool = False
    voltage: Optional[int] = None
    rssi: Optional[int] = None
    usb_state: Optional[int] = None
    device_type: Optional[str] = None
    screen_type: Optional[str] = None
    sn: Optional[str] = None
    sw_version: Optional[int] = None
    hw_version: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        extra = "allow"  # 允许真实系统返回额外字段


class DeviceListParams(BaseModel):
    """设备查询参数"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: Optional[str] = None
    search: Optional[str] = None


# ========== 设备控制相关 ==========

class LEDControlRequest(BaseModel):
    """LED控制请求"""
    red: int = Field(ge=0, le=255)
    green: int = Field(ge=0, le=255)
    blue: int = Field(ge=0, le=255)


class DisplayUpdateRequest(BaseModel):
    """屏幕更新请求"""
    algorithm: Optional[str] = "floyd-steinberg"
    imgsrc: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None


class TemplateApplyRequest(BaseModel):
    """模板调用请求"""
    data: Dict[str, Any] = {}


# ========== 模板相关 ==========

class TemplateField(BaseModel):
    """模板字段定义"""
    name: str
    label: str
    type: str = "text"  # text/number/image/qrcode
    required: bool = False
    default: Optional[Any] = None


class Template(BaseModel):
    """模板数据模型"""
    tid: str
    tname: str
    data: Dict[str, Any] = {}
    fields: List[TemplateField] = []


# ========== 批量操作相关 ==========

class BatchApplyRequest(BaseModel):
    """批量模板应用请求"""
    macs: List[str]
    template_id: str
    data_list: List[Dict[str, Any]]


class BatchResult(BaseModel):
    """批量操作结果"""
    total: int
    success: int
    failed: int
    results: List[Dict[str, Any]]


# ========== WebSocket 消息 ==========

class WSMessage(BaseModel):
    """WebSocket推送消息"""
    type: str  # device_online/device_offline/battery_reply/control_reply 等
    data: Dict[str, Any]
    timestamp: float
