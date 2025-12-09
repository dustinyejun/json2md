"""
Unstructured API调用模块
负责与远程Unstructured API通信,发送文件并获取JSON响应
"""

import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)


class UnstructuredAPIError(Exception):
    """Unstructured API调用错误"""
    pass


class UnstructuredAPIClient:
    """Unstructured API客户端"""
    
    def __init__(self, api_url: str, timeout: int = 60, max_retries: int = 3, default_strategy: str = "fast"):
        """
        初始化API客户端
        
        Args:
            api_url: API服务地址
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            default_strategy: 默认解析策略
        """
        self.api_url = api_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_strategy = default_strategy
        
        logger.info(f"初始化Unstructured API客户端: {api_url}")
    
    def process_file(self, file_path: str, strategy: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        处理文件并获取JSON响应
        
        Args:
            file_path: 文件路径
            strategy: 解析策略 (auto, fast, hi_res, ocr_only), 不指定则使用默认策略
            
        Returns:
            List[Dict[str, Any]]: 解析后的JSON数据(元素列表)
            
        Raises:
            UnstructuredAPIError: API调用失败
            FileNotFoundError: 文件不存在
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 使用指定的strategy或默认strategy
        strategy_to_use = strategy if strategy else self.default_strategy
        
        logger.info(f"开始处理文件: {file_path_obj.name}, strategy: {strategy_to_use}")
        
        # 重试逻辑
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = self._send_request(file_path_obj, strategy_to_use)
                logger.info(f"文件处理成功: {file_path_obj.name}")
                return result
            except httpx.HTTPError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # 指数退避策略
                    wait_time = 2 ** attempt
                    logger.warning(f"请求失败,{wait_time}秒后重试 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"请求失败,已达最大重试次数: {e}")
            except Exception as e:
                last_error = e
                logger.error(f"处理文件时发生错误: {e}")
                break
        
        # 所有重试都失败
        raise UnstructuredAPIError(f"调用Unstructured API失败: {last_error}")
    
    def _send_request(self, file_path: Path, strategy: str) -> List[Dict[str, Any]]:
        """
        发送HTTP请求到API
        
        Args:
            file_path: 文件路径对象
            strategy: 解析策略
            
        Returns:
            List[Dict[str, Any]]: API响应的JSON数据
            
        Raises:
            httpx.HTTPError: HTTP请求错误
            UnstructuredAPIError: API返回错误响应
        """
        # 打开文件
        with open(file_path, 'rb') as f:
            files = {
                'files': (file_path.name, f, self._get_content_type(file_path))
            }
            
            # 准备表单数据
            data = {
                'strategy': strategy
            }
            
            # 发送请求
            with httpx.Client(timeout=self.timeout) as client:
                logger.debug(f"发送请求到: {self.api_url}, strategy: {strategy}")
                response = client.post(
                    self.api_url,
                    files=files,
                    data=data
                )
        
        # 检查响应状态
        if response.status_code != 200:
            error_msg = f"API返回错误状态码: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f", 详细信息: {error_detail}"
            except:
                error_msg += f", 响应内容: {response.text[:200]}"
            
            raise UnstructuredAPIError(error_msg)
        
        # 解析JSON响应
        try:
            json_data = response.json()
        except Exception as e:
            raise UnstructuredAPIError(f"解析API响应失败: {e}")
        
        # 验证响应格式
        if not isinstance(json_data, list):
            raise UnstructuredAPIError(f"API响应格式不正确,期望列表,实际: {type(json_data)}")
        
        logger.debug(f"收到 {len(json_data)} 个元素")
        
        return json_data
    
    def _get_content_type(self, file_path: Path) -> str:
        """
        根据文件扩展名获取Content-Type
        
        Args:
            file_path: 文件路径对象
            
        Returns:
            str: Content-Type字符串
        """
        extension = file_path.suffix.lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    async def process_file_async(self, file_path: str) -> List[Dict[str, Any]]:
        """
        异步处理文件(用于未来扩展)
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[Dict[str, Any]]: 解析后的JSON数据(元素列表)
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"开始异步处理文件: {file_path_obj.name}")
        
        # 重试逻辑
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = await self._send_request_async(file_path_obj)
                logger.info(f"文件处理成功: {file_path_obj.name}")
                return result
            except httpx.HTTPError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"请求失败,{wait_time}秒后重试 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"请求失败,已达最大重试次数: {e}")
            except Exception as e:
                last_error = e
                logger.error(f"处理文件时发生错误: {e}")
                break
        
        raise UnstructuredAPIError(f"调用Unstructured API失败: {last_error}")
    
    async def _send_request_async(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        异步发送HTTP请求到API
        
        Args:
            file_path: 文件路径对象
            
        Returns:
            List[Dict[str, Any]]: API响应的JSON数据
        """
        with open(file_path, 'rb') as f:
            files = {
                'files': (file_path.name, f, self._get_content_type(file_path))
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"发送异步请求到: {self.api_url}")
                response = await client.post(
                    self.api_url,
                    files=files
                )
        
        if response.status_code != 200:
            error_msg = f"API返回错误状态码: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f", 详细信息: {error_detail}"
            except:
                error_msg += f", 响应内容: {response.text[:200]}"
            
            raise UnstructuredAPIError(error_msg)
        
        try:
            json_data = response.json()
        except Exception as e:
            raise UnstructuredAPIError(f"解析API响应失败: {e}")
        
        if not isinstance(json_data, list):
            raise UnstructuredAPIError(f"API响应格式不正确,期望列表,实际: {type(json_data)}")
        
        logger.debug(f"收到 {len(json_data)} 个元素")
        
        return json_data
