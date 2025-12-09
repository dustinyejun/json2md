"""
文件处理和验证模块
负责文件上传验证、临时文件管理和安全检查
"""

import os
import uuid
import logging
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    """文件验证错误"""
    pass


class FileHandler:
    """文件处理器"""
    
    # MIME类型映射
    MIME_TYPES = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    }
    
    def __init__(self, temp_dir: str, allowed_extensions: list, max_size: int):
        """
        初始化文件处理器
        
        Args:
            temp_dir: 临时文件目录
            allowed_extensions: 允许的文件扩展名列表
            max_size: 最大文件大小(字节)
        """
        self.temp_dir = Path(temp_dir)
        self.allowed_extensions = [ext.lower().strip('.') for ext in allowed_extensions]
        self.max_size = max_size
        
        # 确保临时目录存在
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"文件处理器初始化: temp_dir={temp_dir}, max_size={max_size}")
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        验证文件
        
        Args:
            filename: 文件名
            file_size: 文件大小(字节)
            
        Returns:
            Tuple[bool, Optional[str]]: (是否验证通过, 错误消息)
        """
        # 验证文件名
        if not filename:
            return False, "文件名不能为空"
        
        # 验证文件名安全性(防止路径遍历)
        if '..' in filename or '/' in filename or '\\' in filename:
            return False, "文件名包含非法字符"
        
        # 验证文件扩展名
        file_ext = Path(filename).suffix.lower().strip('.')
        if file_ext not in self.allowed_extensions:
            return False, f"不支持的文件类型: .{file_ext}, 仅支持: {', '.join(['.' + ext for ext in self.allowed_extensions])}"
        
        # 验证文件大小
        if file_size > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return False, f"文件大小超过限制: {actual_mb:.2f}MB > {max_mb:.2f}MB"
        
        if file_size <= 0:
            return False, "文件大小无效"
        
        return True, None
    
    def save_temp_file(self, file_content: bytes, original_filename: str) -> str:
        """
        保存临时文件
        
        Args:
            file_content: 文件内容(字节)
            original_filename: 原始文件名
            
        Returns:
            str: 临时文件路径
            
        Raises:
            FileValidationError: 文件验证失败
        """
        # 验证文件
        is_valid, error_msg = self.validate_file(original_filename, len(file_content))
        if not is_valid:
            raise FileValidationError(error_msg)
        
        # 生成唯一的临时文件名
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(original_filename).suffix
        temp_filename = f"{timestamp}_{unique_id}{file_ext}"
        
        # 创建临时子目录(按日期)
        date_dir = self.temp_dir / datetime.now().strftime("%Y%m%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        temp_path = date_dir / temp_filename
        
        # 保存文件
        try:
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"临时文件已保存: {temp_path}")
            return str(temp_path)
        
        except Exception as e:
            logger.error(f"保存临时文件失败: {e}")
            raise
    
    def cleanup_file(self, file_path: str):
        """
        清理临时文件
        
        Args:
            file_path: 文件路径
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.info(f"临时文件已清理: {file_path}")
            else:
                logger.warning(f"文件不存在或不是文件: {file_path}")
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
    
    def cleanup_old_files(self, days: int = 1):
        """
        清理旧的临时文件
        
        Args:
            days: 清理多少天前的文件
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            deleted_count = 0
            
            for file_path in self.temp_dir.rglob('*'):
                if file_path.is_file():
                    # 检查文件修改时间
                    if file_path.stat().st_mtime < cutoff_timestamp:
                        file_path.unlink()
                        deleted_count += 1
            
            logger.info(f"清理了 {deleted_count} 个旧临时文件(>{days}天)")
            
            # 清理空目录
            for dir_path in self.temp_dir.rglob('*'):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
        
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")
    
    def get_safe_filename(self, original_filename: str, prefix: str = "converted") -> str:
        """
        生成安全的输出文件名
        
        Args:
            original_filename: 原始文件名
            prefix: 前缀(默认: converted)
            
        Returns:
            str: 安全的文件名
        """
        # 获取不含扩展名的文件名
        base_name = Path(original_filename).stem
        
        # 移除不安全的字符
        safe_chars = []
        for char in base_name:
            if char.isalnum() or char in ('-', '_', ' '):
                safe_chars.append(char)
            else:
                safe_chars.append('_')
        
        safe_base_name = ''.join(safe_chars).strip()
        
        # 如果文件名为空或过长,使用默认名称
        if not safe_base_name or len(safe_base_name) > 100:
            safe_base_name = prefix
        
        return f"{safe_base_name}_converted.md"
    
    def get_strategy_for_file(self, filename: str, enable_ocr: bool = False) -> str:
        """
        根据文件类型和OCR选项决定strategy
        
        Args:
            filename: 文件名
            enable_ocr: 是否启用OCR(仅PDF有效)
            
        Returns:
            str: strategy策略 (fast 或 hi_res)
        """
        file_ext = Path(filename).suffix.lower().strip('.')
        
        # PDF根据OCR选项决定
        if file_ext == 'pdf':
            return 'hi_res' if enable_ocr else 'fast'
        
        # Word、Excel、PowerPoint默认使用fast
        if file_ext in ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']:
            return 'fast'
        
        # 其他类型使用fast
        return 'fast'
    
    def verify_mime_type(self, file_path: str, expected_extension: str) -> bool:
        """
        验证文件的MIME类型是否与扩展名匹配
        
        Args:
            file_path: 文件路径
            expected_extension: 期望的扩展名(如 .pdf)
            
        Returns:
            bool: 是否匹配
        """
        try:
            # 使用python-magic库进行更准确的MIME类型检测
            # 这里使用mimetypes作为基础实现
            guessed_type, _ = mimetypes.guess_type(file_path)
            expected_type = self.MIME_TYPES.get(expected_extension.lower())
            
            if not expected_type:
                logger.warning(f"未知的扩展名: {expected_extension}")
                return True  # 对于未知类型,不进行严格验证
            
            # 某些文件类型可能有多个MIME类型,这里做宽松验证
            if guessed_type:
                return guessed_type == expected_type or guessed_type.startswith(expected_type.split('/')[0])
            
            return True  # 无法确定时不阻止
        
        except Exception as e:
            logger.warning(f"MIME类型验证失败: {e}")
            return True  # 验证失败时不阻止
