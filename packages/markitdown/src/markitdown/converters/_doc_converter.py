import sys
import tempfile
import os
from pathlib import Path
from typing import BinaryIO, Any

from ._docx_converter import DocxConverter
from .._base_converter import DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException, MISSING_DEPENDENCY_MESSAGE

# Try loading optional win32com dependency
_dependency_exc_info = None
try:
    import win32com.client
    import pythoncom
except ImportError:
    _dependency_exc_info = sys.exc_info()


ACCEPTED_MIME_TYPE_PREFIXES = [
    "application/msword",
    "application/vnd.ms-word",
]

ACCEPTED_FILE_EXTENSIONS = [".doc"]


class DocConverter(DocxConverter):
    """
    Converts legacy .doc (Word 97-2003) files to Markdown.
    Uses Word COM automation (win32com) to convert .doc → .docx in a temp file,
    then delegates to DocxConverter (including image extraction support).
    Requires Microsoft Word to be installed on the system.
    """

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
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
        **kwargs: Any,
    ) -> DocumentConverterResult:
        # 检查 win32com 依赖
        if _dependency_exc_info is not None:
            raise MissingDependencyException(
                MISSING_DEPENDENCY_MESSAGE.format(
                    converter=type(self).__name__,
                    extension=".doc",
                    feature="doc",
                )
            ) from _dependency_exc_info[1].with_traceback(  # type: ignore[union-attr]
                _dependency_exc_info[2]
            )

        # 将 file_stream 写入临时 .doc 文件
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_doc  = Path(tmpdir) / "input.doc"
            tmp_docx = Path(tmpdir) / "input.docx"

            tmp_doc.write_bytes(file_stream.read())

            # 用 Word COM 将 .doc 转为 .docx
            pythoncom.CoInitialize()
            try:
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                try:
                    doc = word.Documents.Open(str(tmp_doc.resolve()))
                    # wdFormatXMLDocument = 12
                    doc.SaveAs2(str(tmp_docx.resolve()), FileFormat=12)
                    doc.Close(False)
                finally:
                    word.Quit()
            finally:
                pythoncom.CoUninitialize()

            # 用 DocxConverter 处理转换后的 .docx（含图片提取参数）
            with open(tmp_docx, "rb") as docx_stream:
                docx_info = StreamInfo(
                    mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    extension=".docx",
                    filename=stream_info.filename,
                )
                return super().convert(docx_stream, docx_info, **kwargs)
