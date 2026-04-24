import sys
import io
from pathlib import Path
from warnings import warn

from typing import BinaryIO, Any, Optional

from ._html_converter import HtmlConverter
from ..converter_utils.docx.pre_process import pre_process_docx
from .._base_converter import DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException, MISSING_DEPENDENCY_MESSAGE

# Try loading optional (but in this case, required) dependencies
# Save reporting of any exceptions for later
_dependency_exc_info = None
try:
    import mammoth

except ImportError:
    # Preserve the error and stack trace for later
    _dependency_exc_info = sys.exc_info()


ACCEPTED_MIME_TYPE_PREFIXES = [
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

ACCEPTED_FILE_EXTENSIONS = [".docx"]


class DocxConverter(HtmlConverter):
    """
    Converts DOCX files to Markdown. Style information (e.g.m headings) and tables are preserved where possible.
    """

    def __init__(self):
        super().__init__()
        self._html_converter = HtmlConverter()

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> bool:
        mimetype = (stream_info.mimetype or "").lower()
        extension = (stream_info.extension or "").lower()

        if extension in ACCEPTED_FILE_EXTENSIONS:
            return True

        for prefix in ACCEPTED_MIME_TYPE_PREFIXES:
            if mimetype.startswith(prefix):
                return True

        return False

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> DocumentConverterResult:
        # Check: the dependencies
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

        import base64

        style_map = kwargs.get("style_map", None)
        images_dir: Optional[str] = kwargs.pop("docx_images_dir", None)
        embed_images: bool = kwargs.pop("docx_embed_images", False)
        pre_process_stream = pre_process_docx(file_stream)

        if embed_images:
            # 将图片以 base64 data URI 形式直接嵌入 Markdown，单文件无依赖
            def _embed_image(image):
                with image.open() as f:
                    data = base64.b64encode(f.read()).decode("ascii")
                mime = image.content_type or "image/png"
                return {"src": f"data:{mime};base64,{data}"}

            html = mammoth.convert_to_html(
                pre_process_stream,
                style_map=style_map,
                convert_image=mammoth.images.img_element(_embed_image),
            ).value
            # 告知下游 markdownify 保留 data URI，不截断
            kwargs["keep_data_uris"] = True
        elif images_dir:
            # 将图片提取为独立文件，在 Markdown 中用相对路径引用
            images_path = Path(images_dir)
            images_path.mkdir(parents=True, exist_ok=True)
            images_dir_name = images_path.name
            image_counter = [0]

            def _save_image(image):
                image_counter[0] += 1
                # 从 content_type 推断扩展名（如 image/png → png）
                ext = (image.content_type or "image/png").split("/")[-1].lower()
                if ext == "jpeg":
                    ext = "jpg"
                filename = f"image{image_counter[0]:03d}.{ext}"
                with image.open() as f:
                    (images_path / filename).write_bytes(f.read())
                return {"src": f"{images_dir_name}/{filename}"}

            html = mammoth.convert_to_html(
                pre_process_stream,
                style_map=style_map,
                convert_image=mammoth.images.img_element(_save_image),
            ).value
        else:
            html = mammoth.convert_to_html(pre_process_stream, style_map=style_map).value

        return self._html_converter.convert_string(html, **kwargs)
