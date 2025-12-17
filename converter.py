"""
JSON到Markdown转换引擎
负责将Unstructured API返回的JSON数据转换为Markdown格式
"""

import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class MarkdownConverter:
    """JSON到Markdown转换器"""
    
    # 元素类型到Markdown格式的映射
    TYPE_MAPPING = {
        "Title": "h1",
        "Header": "h2",
        "UncategorizedText": "text",
        "NarrativeText": "text",
        "ListItem": "list",
        "Table": "table",
        "Image": "image",
        "Footer": "footer",
        "PageBreak": "break",
    }
    
    def __init__(self):
        self.output_lines = []
        self.last_type = None
    
    def convert(self, json_data: List[Dict[str, Any]]) -> str:
        """
        将JSON数据转换为Markdown格式
        
        Args:
            json_data: Unstructured API返回的JSON数据(元素列表)
            
        Returns:
            str: Markdown格式的文本
        """
        self.output_lines = []
        self.last_type = None
        
        logger.info(f"开始转换JSON数据,共 {len(json_data)} 个元素")
        
        for element in json_data:
            self._process_element(element)
        
        # 生成最终的Markdown文本
        markdown_text = self._format_output()
        
        logger.info(f"转换完成,生成 {len(markdown_text)} 字符的Markdown文本")
        
        return markdown_text
    
    def _process_element(self, element: Dict[str, Any]):
        """
        处理单个JSON元素
        
        Args:
            element: 单个元素对象
        """
        element_type = element.get("type", "")
        text = (element.get("text") or "").strip()
        
        if not text:
            return
        
        # 获取映射的格式类型
        format_type = self.TYPE_MAPPING.get(element_type, "text")
        
        # 根据类型生成相应的Markdown格式
        if format_type == "h1":
            self._add_heading(text, 1)
        elif format_type == "h2":
            self._add_heading(text, 2)
        elif format_type == "list":
            self._add_list_item(text)
        elif format_type == "table":
            self._add_table(element)
        elif format_type == "image":
            self._add_image(element)
        elif format_type == "footer":
            self._add_footer(text)
        elif format_type == "break":
            self._add_page_break()
        else:  # text
            self._add_paragraph(text)
        
        self.last_type = format_type
    
    def _add_heading(self, text: str, level: int):
        """添加标题"""
        # 如果上一个元素不是同类型,添加空行
        if self.output_lines and self.last_type != f"h{level}":
            self.output_lines.append("")
        
        prefix = "#" * level
        self.output_lines.append(f"{prefix} {text}")
        self.output_lines.append("")  # 标题后添加空行
    
    def _add_paragraph(self, text: str):
        """添加段落"""
        # 如果上一个元素不是文本,添加空行
        if self.output_lines and self.last_type not in ["text", None]:
            self.output_lines.append("")
        
        self.output_lines.append(text)
        self.output_lines.append("")  # 段落后添加空行
    
    def _add_list_item(self, text: str):
        """添加列表项"""
        # 如果上一个不是列表项,添加空行
        if self.output_lines and self.last_type != "list":
            self.output_lines.append("")
        
        self.output_lines.append(f"- {text}")
        
        # 注意:不立即添加空行,等下一个非列表项时再添加
    
    def _add_table(self, element: Dict[str, Any]):
        """
        添加表格
        
        Note: 这是一个简化实现,实际的表格解析需要根据Unstructured API的具体响应格式调整
        """
        text = element.get("text") or ""
        metadata = element.get("metadata", {})
        
        # 如果上一个不是表格,添加空行
        if self.output_lines and self.last_type != "table":
            self.output_lines.append("")
        
        # 简单处理:将表格文本直接输出
        # TODO: 根据实际API响应解析表格结构
        self.output_lines.append("```")
        self.output_lines.append(text)
        self.output_lines.append("```")
        self.output_lines.append("")
    
    def _add_image(self, element: Dict[str, Any]):
        """添加图片引用"""
        text = element.get("text") or ""
        metadata = element.get("metadata", {})
        
        # 尝试从元数据获取图片路径
        image_path = metadata.get("image_path", "")
        
        if self.output_lines:
            self.output_lines.append("")
        
        if image_path:
            self.output_lines.append(f"![{text}]({image_path})")
        else:
            self.output_lines.append(f"![图片: {text}]")
        
        self.output_lines.append("")
    
    def _add_footer(self, text: str):
        """添加页脚"""
        if self.output_lines:
            self.output_lines.append("")
        
        self.output_lines.append(f"*{text}*")
        self.output_lines.append("")
    
    def _add_page_break(self):
        """添加分页符"""
        if self.output_lines:
            self.output_lines.append("")
        
        self.output_lines.append("---")
        self.output_lines.append("")
    
    def _format_output(self) -> str:
        """
        格式化输出,清理多余的空行
        
        Returns:
            str: 格式化后的Markdown文本
        """
        # 移除开头和结尾的空行
        while self.output_lines and not self.output_lines[0]:
            self.output_lines.pop(0)
        
        while self.output_lines and not self.output_lines[-1]:
            self.output_lines.pop()
        
        # 合并连续的多个空行为一个
        formatted_lines = []
        prev_empty = False
        
        for line in self.output_lines:
            is_empty = not line.strip()
            
            if is_empty and prev_empty:
                continue  # 跳过连续的空行
            
            formatted_lines.append(line)
            prev_empty = is_empty
        
        return "\n".join(formatted_lines)


def convert_json_to_markdown(json_data: Any) -> str:
    """
    将JSON数据转换为Markdown格式的便捷函数
    
    Args:
        json_data: JSON数据,可以是字符串、列表或字典
        
    Returns:
        str: Markdown格式的文本
        
    Raises:
        ValueError: JSON数据格式不正确
    """
    # 如果是字符串,先解析为JSON
    if isinstance(json_data, str):
        try:
            json_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {e}")
    
    # 确保是列表格式
    if not isinstance(json_data, list):
        raise ValueError("JSON数据必须是元素列表格式")
    
    converter = MarkdownConverter()
    return converter.convert(json_data)
