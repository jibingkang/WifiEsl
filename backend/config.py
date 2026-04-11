"""
WIFI标签管理系统 - 配置管理
从 .env 文件加载所有可配置项
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置 - 全部从环境变量/.env文件加载"""

    # --- 真实WIFI标签系统连接 ---
    wifi_base_url: str = "http://192.168.1.172:4000"
    wifi_username: str = "test"
    wifi_password: str = "123456"
    wifi_apikey: str = ""

    # --- MQTT Broker 配置 ---
    mqtt_broker_host: str = "192.168.1.172"
    mqtt_broker_port: int = 8883
    mqtt_tls_enable: bool = True
    mqtt_tls_insecure: bool = True
    mqtt_username: str = ""       # MQTT连接用户名 (留空则使用wifi_apikey)
    mqtt_password: str = ""       # MQTT连接密码

    # --- 后端服务配置 ---
    backend_port: int = 8000
    backend_host: str = "0.0.0.0"

    # --- JWT 认证配置 ---
    jwt_secret: str = "wifi-esl-manager-secret-key-2026"
    jwt_expire_hours: int = 24

    # --- CORS ---
    cors_origins: str = "*"  # 开发环境允许所有来源

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置单例
settings = Settings()
