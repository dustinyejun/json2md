"""
配置管理模块
负责加载和管理应用程序配置
"""

import os
import yaml
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class UnstructuredConfig(BaseModel):
    """Unstructured API配置"""
    api_url: str = Field(..., description="API服务地址")
    timeout: int = Field(default=60, description="请求超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    default_strategy: str = Field(default="fast", description="默认解析策略")


class UploadConfig(BaseModel):
    """文件上传配置"""
    max_size: int = Field(default=52428800, description="最大上传大小(字节)")
    allowed_extensions: List[str] = Field(
        default=["doc", "docx", "xls", "xlsx", "ppt", "pptx", "pdf"],
        description="允许的文件扩展名"
    )
    temp_dir: str = Field(default="./temp", description="临时文件目录")


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = Field(default="0.0.0.0", description="监听地址")
    port: int = Field(default=8000, description="服务端口")


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    file: str = Field(default="./logs/app.log", description="日志文件路径")


class AppConfig(BaseModel):
    """应用程序总配置"""
    unstructured: UnstructuredConfig
    upload: UploadConfig
    server: ServerConfig
    logging: LoggingConfig


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: Optional[AppConfig] = None
        
    def load_config(self) -> AppConfig:
        """
        加载配置文件
        
        Returns:
            AppConfig: 应用程序配置对象
            
        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置验证失败
        """
        # 支持从环境变量指定配置文件路径
        config_path = os.getenv("CONFIG_PATH", self.config_path)
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 支持环境变量覆盖配置
        if os.getenv("UNSTRUCTURED_API_URL"):
            config_data.setdefault("unstructured", {})
            config_data["unstructured"]["api_url"] = os.getenv("UNSTRUCTURED_API_URL")
        
        # 验证并创建配置对象
        self.config = AppConfig(**config_data)
        
        # 确保必要的目录存在
        self._ensure_directories()
        
        return self.config
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        if self.config:
            # 创建临时文件目录
            os.makedirs(self.config.upload.temp_dir, exist_ok=True)
            
            # 创建日志目录
            log_dir = os.path.dirname(self.config.logging.file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
    
    def get_config(self) -> AppConfig:
        """
        获取配置对象
        
        Returns:
            AppConfig: 应用程序配置对象
            
        Raises:
            RuntimeError: 配置尚未加载
        """
        if self.config is None:
            raise RuntimeError("配置尚未加载,请先调用 load_config()")
        return self.config


# 全局配置管理器实例
config_manager = ConfigManager()
