#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DOCX 文档转换器模块

本模块提供将 Microsoft Word (.docx) 文档转换为 Markdown 格式的功能。
支持以下特性：
- 保留样式信息（标题、表格等）
- 自动为标题添加层级编号（如 1.1.2）
- 三种图片处理模式：
  * 提取为独立文件并用相对路径引用
  * 嵌入为 base64 并使用引用式语法
  * 忽略图片

依赖项：
- mammoth: DOCX 到 HTML 的转换
- python-docx: DOCX 文档的读取和修改

作者: MarkItDown Team
版本: 参见项目版本信息
"""

import sys
import io
import re
from pathlib import Path
from warnings import warn

from typing import BinaryIO, Any, Optional

from ._html_converter import HtmlConverter
from ..converter_utils.docx.pre_process import pre_process_docx
from ..converter_utils.image_reference import ImageReferenceCollector
from .._base_converter import DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException, MISSING_DEPENDENCY_MESSAGE

# 尝试加载可选依赖（但在此情况下是必需的）
# 保存任何异常信息供后续使用
_dependency_exc_info = None
try:
    import mammoth
    import docx

except ImportError:
    # 保留错误信息和堆栈跟踪供后续使用
    _dependency_exc_info = sys.exc_info()


# 接受的 MIME 类型前缀列表
ACCEPTED_MIME_TYPE_PREFIXES = [
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

# 接受的文件扩展名列表
ACCEPTED_FILE_EXTENSIONS = [".docx"]


class DocxConverter(HtmlConverter):
    """
    DOCX 文档转换器类
    
    将 Microsoft Word (.docx) 文档转换为 Markdown 格式。
    尽可能保留样式信息（如标题层级）和表格结构。
    
    支持的图片处理模式：
    - 提取模式：将图片提取为独立文件，在 Markdown 中使用相对路径引用
    - 嵌入模式：将图片嵌入为 base64 编码，使用引用式语法
    - 忽略模式：不处理图片
    
    继承自 HtmlConverter，通过先将 DOCX 转为 HTML，再将 HTML 转为 Markdown 的方式实现转换。
    """

    def __init__(self):
        """
        初始化 DOCX 转换器
        
        调用父类构造函数并创建 HTML 转换器实例，用于后续的 HTML 到 Markdown 转换。
        """
        super().__init__()
        self._html_converter = HtmlConverter()

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # 传递给转换器的选项
    ) -> bool:
        """
        检查是否接受给定的文件流进行转换
        
        通过检查文件的 MIME 类型或扩展名来判断是否为有效的 DOCX 文件。
        
        Args:
            file_stream: 文件的二进制流
            stream_info: 流信息对象，包含 MIME 类型、扩展名等元数据
            **kwargs: 其他选项参数
            
        Returns:
            bool: 如果文件是 DOCX 格式则返回 True，否则返回 False
        """
        mimetype = (stream_info.mimetype or "").lower()
        extension = (stream_info.extension or "").lower()

        # 首先检查文件扩展名
        if extension in ACCEPTED_FILE_EXTENSIONS:
            return True

        # 然后检查 MIME 类型前缀
        for prefix in ACCEPTED_MIME_TYPE_PREFIXES:
            if mimetype.startswith(prefix):
                return True

        return False

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # 传递给转换器的选项
    ) -> DocumentConverterResult:
        """
        将 DOCX 文件转换为 Markdown 格式
        
        这是转换器的主要入口方法。执行以下步骤：
        1. 检查依赖项是否可用
        2. 提取转换选项（样式映射、图片处理方式等）
        3. 预处理文档（为标题添加自动编号）
        4. 根据图片处理模式选择相应的转换方法
        
        Args:
            file_stream: DOCX 文件的二进制流
            stream_info: 流信息对象，包含文件的元数据（MIME 类型、扩展名等）
            **kwargs: 转换选项，包括：
                - style_map: 自定义 mammoth 样式映射规则
                - docx_images_dir: 图片提取目录（文件模式）
                - docx_embed_images: 是否将图片嵌入为 base64（嵌入模式）
        
        Returns:
            DocumentConverterResult: 包含转换后的 Markdown 内容和标题信息的 result 对象
            
        Raises:
            MissingDependencyException: 当必需的依赖项（mammoth 或 python-docx）未安装时抛出
        """
        # 检查依赖项
        if _dependency_exc_info is not None:
            raise MissingDependencyException(
                MISSING_DEPENDENCY_MESSAGE.format(
                    converter=type(self).__name__,
                    extension=".docx",
                    feature="docx",
                )
            ) from _dependency_exc_info[
                1
            ].with_traceback(  # type: ignore[union-attr]
                _dependency_exc_info[2]
            )

        # 提取转换选项
        style_map = kwargs.get("style_map", None)
        images_dir: Optional[str] = kwargs.pop("docx_images_dir", None)
        embed_images: bool = kwargs.pop("docx_embed_images", False)
        
        # 预处理：为标题文本注入自动编号
        pre_process_stream = self._preprocess_with_numbering(file_stream)
        
        # 根据图片处理模式选择转换方法
        if embed_images:
            # 嵌入模式：图片以 base64 形式嵌入
            return self._convert_with_embedded_images(pre_process_stream, style_map, **kwargs)
        elif images_dir:
            # 提取模式：图片保存为独立文件
            return self._convert_with_extracted_images(pre_process_stream, style_map, images_dir, **kwargs)
        else:
            # 忽略模式：不处理图片
            return self._convert_without_images(pre_process_stream, style_map, **kwargs)
    
    def _preprocess_with_numbering(self, file_stream: BinaryIO) -> BinaryIO:
        """
        预处理 DOCX 文档，为标题注入自动编号
        
        此方法会为没有手动编号的标题添加层级编号（如 "1.1.2"）。
        编号规则遵循标准的层级结构：
        - 一级标题：1, 2, 3...
        - 二级标题：1.1, 1.2, 2.1...
        - 三级标题：1.1.1, 1.1.2, 1.2.1...
        
        如果检测到标题已有手动编号（如 "1."、"第一章"、"①" 等），则不会添加自动编号。
        
        Args:
            file_stream: 原始 DOCX 文件的二进制流
            
        Returns:
            BinaryIO: 经过预处理的文件流，已准备好进行转换
            
        Note:
            - 如果 python-docx 库不可用，将直接使用原始流
            - 如果处理过程中出现异常，将回退到使用原始流
            - 预处理后的流会经过标准的 pre_process_docx 处理
        """
        try:
            # 读取文档
            file_stream.seek(0)
            doc = docx.Document(file_stream)
            
            # 跟踪每个标题层级的计数器（最多支持 10 级标题）
            heading_counters = [0] * 10
            
            # 遍历所有段落
            for para in doc.paragraphs:
                if para.style.name.startswith('Heading'):
                    # 为标题段落添加编号
                    self._add_numbering_to_heading(para, heading_counters)
            
            # 将修改后的文档保存到 BytesIO
            modified_stream = io.BytesIO()
            doc.save(modified_stream)
            modified_stream.seek(0)
            
            # 应用标准预处理
            return pre_process_docx(modified_stream)
            
        except ImportError:
            # python-docx 库不可用，使用原始流
            return pre_process_docx(file_stream)
        except Exception:
            # 处理失败，使用原始流
            file_stream.seek(0)
            return pre_process_docx(file_stream)
    
    def _add_numbering_to_heading(self, para, heading_counters: list):
        """
        为标题段落添加层级编号（如果没有手动编号）
        
        此方法会：
        1. 提取标题级别（Heading 1 -> 0, Heading 2 -> 1, 以此类推）
        2. 更新对应级别的计数器
        3. 重置更低级别的计数器
        4. 生成编号字符串（如 "1.2.3"）
        5. 检查是否已有手动编号，如无则将编号添加到文本开头
        
        Args:
            para: python-docx 的段落对象
            heading_counters: 跟踪每个标题层级计数器的列表
            
        Example:
            假设有以下标题结构：
            - Heading 1: "引言" -> "1 引言"
            - Heading 2: "背景" -> "1.1 背景"
            - Heading 1: "方法" -> "2 方法"
            - Heading 2: "实验设计" -> "2.1 实验设计"
        """
        # 提取标题级别（Heading 1 -> 0, Heading 2 -> 1, 等等）
        level = int(para.style.name.split()[-1]) - 1
        
        # 更新当前级别的计数器
        heading_counters[level] += 1
        # 重置更低级别的计数器
        for i in range(level + 1, len(heading_counters)):
            heading_counters[i] = 0
        
        # 生成编号字符串（如 "1.2.3"）
        number_parts = [
            str(heading_counters[i]) 
            for i in range(level + 1) 
            if heading_counters[i] > 0
        ]
        number_str = '.'.join(number_parts)
        
        # 如果段落有 runs 且没有手动编号，则添加编号
        if para.runs:
            original_text = para.text.strip()
            
            # 检查标题是否已有手动编号
            if not self._has_manual_numbering(original_text):
                # 清空所有 runs 并添加带编号的文本
                for run in para.runs:
                    run.text = ''
                if para.runs:
                    para.runs[0].text = f"{number_str} {original_text}"
    
    def _has_manual_numbering(self, text: str) -> bool:
        """
        检查文本是否已包含手动编号
        
        检测以下编号模式：
        - 数字加点或顿号："1.", "1.1.", "1.1.1.", "1、", "1、1、" 等
        - 中文章节标记："第一章", "第一节", "第一篇" 等
        - 带圈数字或括号数字："①", "②", "(1)", "（1）" 等
        
        Args:
            text: 要检查的标题文本
            
        Returns:
            bool: 如果检测到手动编号返回 True，否则返回 False
            
        Regex 说明：
            r'^(\d+[.、]\s*)+'          # 匹配 "1." 或 "1.1." 或 "1、" 等
            r'|^(第[\u4e00-\u9fa5]+[章节篇])'  # 匹配 "第一章" "第一节" 等
            r'|^([\u2460-\u24ff]|[(\uff08]\d+[)\uff09])'  # 匹配 "①" 或 "(1)" 等
        """
        return bool(re.match(
            r'^(\d+[.、]\s*)+'  # "1." 或 "1.1." 或 "1、" 等
            r'|^(第[\u4e00-\u9fa5]+[章节篇])'  # "第一章" "第一节" 等
            r'|^([\u2460-\u24ff]|[(\uff08]\d+[)\uff09])',  # "①" 或 "(1)" 等
            text
        ))
    
    def _convert_with_embedded_images(
        self, 
        pre_process_stream: BinaryIO, 
        style_map: Optional[str],
        **kwargs
    ) -> DocumentConverterResult:
        """
        使用 base64 嵌入图片并以引用式语法转换 DOCX
        
        此方法会将文档中的图片转换为 base64 编码，并在 Markdown 中使用
        引用式语法（![alt][ref] 和 [ref]: data:image/...;base64,...）表示。
        
        转换流程：
        1. 创建图片引用收集器
        2. 定义图片嵌入回调函数，将图片转为 base64 data URI
        3. 使用 mammoth 将 DOCX 转为 HTML，同时处理图片
        4. 使用 HTML 转换器将 HTML 转为 Markdown
        5. 在文末添加图片引用定义
        
        Args:
            pre_process_stream: 经过预处理的 DOCX 流
            style_map: 可选的 mammoth 样式映射规则
            **kwargs: 其他转换选项
            
        Returns:
            DocumentConverterResult: 包含嵌入图片的 Markdown 结果
            
        Note:
            - 使用占位符 PLACEHOLDER_{img_id} 让 markdownify 的引用式逻辑生效
            - 图片引用定义会自动添加到文档末尾
        """
        collector = ImageReferenceCollector()
        
        def _embed_image(image):
            """将图片转换为带占位符的 base64 data URI"""
            with image.open() as f:
                image_bytes = f.read()
            mime = image.content_type or "image/png"
            img_id = collector.add_image(image_bytes, mime)
            # 使用占位符，后续会被 markdownify 的引用式逻辑替换
            return {"src": f"data:{mime};base64,PLACEHOLDER_{img_id}"}

        # 将 DOCX 转换为 HTML，同时嵌入图片
        html = mammoth.convert_to_html(
            pre_process_stream,
            style_map=style_map,
            convert_image=mammoth.images.img_element(_embed_image),
        ).value
        
        # 将 HTML 转换为 Markdown
        kwargs["image_collector"] = collector
        result = self._html_converter.convert_string(html, **kwargs)
        
        # 在文末追加图片引用定义
        if collector.has_images():
            references_text = collector.get_references_markdown()
            result = DocumentConverterResult(
                markdown=result.markdown + references_text,
                title=result.title
            )
        
        return result
    
    def _convert_with_extracted_images(
        self,
        pre_process_stream: BinaryIO,
        style_map: Optional[str],
        images_dir: str,
        **kwargs
    ) -> DocumentConverterResult:
        """
        将 DOCX 转换为 Markdown，并将图片提取为独立文件
        
        图片会被保存到指定的目录中，并在 Markdown 中使用相对路径引用。
        图片文件命名规则：image001.png, image002.jpg, 等（三位数序号）。
        
        转换流程：
        1. 创建图片保存目录
        2. 定义图片保存回调函数，保存图片并返回相对路径
        3. 使用 mammoth 将 DOCX 转为 HTML，同时保存图片
        4. 使用 HTML 转换器将 HTML 转为 Markdown
        
        Args:
            pre_process_stream: 经过预处理的 DOCX 流
            style_map: 可选的 mammoth 样式映射规则
            images_dir: 保存图片的目录路径
            **kwargs: 其他转换选项
            
        Returns:
            DocumentConverterResult: 包含相对路径图片引用的 Markdown 结果
            
        Example:
            如果 images_dir 为 "output/doc_images"，则：
            - 图片保存在 output/doc_images/ 目录下
            - Markdown 中引用为 ![alt](doc_images/image001.png)
        """
        images_path = Path(images_dir)
        images_path.mkdir(parents=True, exist_ok=True)
        images_dir_name = images_path.name
        image_counter = [0]

        def _save_image(image):
            """保存图片到文件并返回相对路径"""
            image_counter[0] += 1
            # 从 content_type 推断扩展名（如 image/png → png）
            ext = (image.content_type or "image/png").split("/")[-1].lower()
            if ext == "jpeg":
                ext = "jpg"
            filename = f"image{image_counter[0]:03d}.{ext}"
            with image.open() as f:
                (images_path / filename).write_bytes(f.read())
            return {"src": f"{images_dir_name}/{filename}"}

        # 将 DOCX 转换为 HTML，同时提取图片
        html = mammoth.convert_to_html(
            pre_process_stream,
            style_map=style_map,
            convert_image=mammoth.images.img_element(_save_image),
        ).value
        
        return self._html_converter.convert_string(html, **kwargs)
    
    def _convert_without_images(
        self,
        pre_process_stream: BinaryIO,
        style_map: Optional[str],
        **kwargs
    ) -> DocumentConverterResult:
        """
        转换 DOCX 为 Markdown，不处理图片（图片将被忽略）
        
        这是最简单的转换模式，直接将 DOCX 转为 HTML 再转为 Markdown，
        不执行任何图片相关的操作。适用于不需要图片的场景。
        
        Args:
            pre_process_stream: 经过预处理的 DOCX 流
            style_map: 可选的 mammoth 样式映射规则
            **kwargs: 其他转换选项
            
        Returns:
            DocumentConverterResult: 不包含图片的 Markdown 结果
        """
        html = mammoth.convert_to_html(pre_process_stream, style_map=style_map).value
        return self._html_converter.convert_string(html, **kwargs)
