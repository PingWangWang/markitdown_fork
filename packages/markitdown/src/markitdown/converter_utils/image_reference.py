"""
图片引用式嵌入辅助工具

提供统一的引用式图片嵌入功能，将 Base64 数据放在文档末尾，
正文中使用简洁的标识符引用。
"""
import base64
from typing import List, Tuple


class ImageReferenceCollector:
    """
    图片引用收集器
    
    用法：
        collector = ImageReferenceCollector()
        
        # 在转换过程中收集图片
        img_id = collector.add_image(image_bytes, content_type)
        # 返回的 img_id 用于在正文中引用
        
        # 转换完成后，获取引用定义并附加到文档末尾
        if collector.has_images():
            markdown = markdown + collector.get_references_markdown()
    """
    
    def __init__(self):
        self._counter = 0
        self._references: List[Tuple[str, str]] = []  # (img_id, data_uri)
    
    def add_image(self, image_bytes: bytes, content_type: str = "image/png") -> str:
        """
        添加图片并返回引用标识符
        
        Args:
            image_bytes: 图片的二进制数据
            content_type: 图片的 MIME 类型（如 image/png, image/jpeg）
            
        Returns:
            图片引用标识符（如 "img-1", "img-2"）
        """
        self._counter += 1
        img_id = f"img-{self._counter}"
        
        # 编码为 Base64
        b64_data = base64.b64encode(image_bytes).decode("ascii")
        data_uri = f"data:{content_type};base64,{b64_data}"
        
        # 保存引用
        self._references.append((img_id, data_uri))
        
        return img_id
    
    def has_images(self) -> bool:
        """检查是否收集了图片"""
        return len(self._references) > 0
    
    def get_references_markdown(self) -> str:
        """
        获取所有图片引用的 Markdown 定义
        
        Returns:
            Markdown 格式的引用定义，包含分隔线和所有图片引用
            格式：
            
            ---
            
            [img-1]: data:image/png;base64,...
            [img-2]: data:image/jpeg;base64,...
        """
        if not self._references:
            return ""
        
        lines = ["\n\n---\n"]
        for img_id, data_uri in self._references:
            lines.append(f"\n[{img_id}]: {data_uri}")
        lines.append("\n")
        
        return "".join(lines)
    
    def get_count(self) -> int:
        """获取已收集的图片数量"""
        return len(self._references)
    
    def reset(self):
        """重置收集器"""
        self._counter = 0
        self._references.clear()
