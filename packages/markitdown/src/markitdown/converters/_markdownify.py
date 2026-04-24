import re
import markdownify
from bs4 import BeautifulSoup, Tag

from typing import Any, Optional
from urllib.parse import quote, unquote, urlparse, urlunparse


class _CustomMarkdownify(markdownify.MarkdownConverter):
    """
    A custom version of markdownify's MarkdownConverter. Changes include:

    - Altering the default heading style to use '#', '##', etc.
    - Removing javascript hyperlinks.
    - Truncating images with large data:uri sources.
    - Ensuring URIs are properly escaped, and do not conflict with Markdown syntax
    """

    def __init__(self, **options: Any):
        options["heading_style"] = options.get("heading_style", markdownify.ATX)
        options["keep_data_uris"] = options.get("keep_data_uris", False)
        # Explicitly cast options to the expected type if necessary
        super().__init__(**options)

    def convert_hn(
        self,
        n: int,
        el: Any,
        text: str,
        convert_as_inline: Optional[bool] = False,
        **kwargs,
    ) -> str:
        """Same as usual, but be sure to start with a new line"""
        if not convert_as_inline:
            if not re.search(r"^\n", text):
                return "\n" + super().convert_hn(n, el, text, convert_as_inline)  # type: ignore

        return super().convert_hn(n, el, text, convert_as_inline)  # type: ignore

    def convert_a(
        self,
        el: Any,
        text: str,
        convert_as_inline: Optional[bool] = False,
        **kwargs,
    ):
        """Same as usual converter, but removes Javascript links and escapes URIs."""
        prefix, suffix, text = markdownify.chomp(text)  # type: ignore
        if not text:
            return ""

        if el.find_parent("pre") is not None:
            return text

        href = el.get("href")
        title = el.get("title")

        # Escape URIs and skip non-http or file schemes
        if href:
            try:
                parsed_url = urlparse(href)  # type: ignore
                if parsed_url.scheme and parsed_url.scheme.lower() not in ["http", "https", "file"]:  # type: ignore
                    return "%s%s%s" % (prefix, text, suffix)
                href = urlunparse(parsed_url._replace(path=quote(unquote(parsed_url.path))))  # type: ignore
            except ValueError:  # It's not clear if this ever gets thrown
                return "%s%s%s" % (prefix, text, suffix)

        # For the replacement see #29: text nodes underscores are escaped
        if (
            self.options["autolinks"]
            and text.replace(r"\_", "_") == href
            and not title
            and not self.options["default_title"]
        ):
            # Shortcut syntax
            return "<%s>" % href
        if self.options["default_title"] and not title:
            title = href
        title_part = ' "%s"' % title.replace('"', r"\"") if title else ""
        return (
            "%s[%s](%s%s)%s" % (prefix, text, href, title_part, suffix)
            if href
            else text
        )

    def convert_img(
        self,
        el: Any,
        text: str,
        convert_as_inline: Optional[bool] = False,
        **kwargs,
    ) -> str:
        """Same as usual converter, but removes data URIs"""

        alt = el.attrs.get("alt", None) or ""
        src = el.attrs.get("src", None) or el.attrs.get("data-src", None) or ""
        title = el.attrs.get("title", None) or ""
        title_part = ' "%s"' % title.replace('"', r"\"") if title else ""
        # Remove all line breaks from alt
        alt = alt.replace("\n", " ")
        if (
            convert_as_inline
            and el.parent.name not in self.options["keep_inline_images_in"]
        ):
            return alt

        # Remove dataURIs
        if src.startswith("data:") and not self.options["keep_data_uris"]:
            src = src.split(",")[0] + "..."

        return "![%s](%s%s)" % (alt, src, title_part)

    def convert_input(
        self,
        el: Any,
        text: str,
        convert_as_inline: Optional[bool] = False,
        **kwargs,
    ) -> str:
        """Convert checkboxes to Markdown [x]/[ ] syntax."""

        if el.get("type") == "checkbox":
            return "[x] " if el.has_attr("checked") else "[ ] "
        return ""

    def convert_soup(self, soup: Any) -> str:
        return super().convert_soup(soup)  # type: ignore

    def convert_table(
        self,
        el: Any,
        text: str,
        convert_as_inline: Optional[bool] = False,
        **kwargs,
    ) -> str:
        """
        处理含合并单元格（colspan/rowspan）的表格。
        将合并单元格展开为独立格（重复填充内容），再转为标准 Markdown 表格。
        不含合并单元格时走默认逻辑。
        """
        # 检查是否含合并单元格
        has_merge = any(
            int(cell.get("colspan", 1)) > 1 or int(cell.get("rowspan", 1)) > 1
            for cell in el.find_all(["td", "th"])
        )
        if not has_merge:
            return super().convert_table(el, text, convert_as_inline)  # type: ignore

        # ── 展开合并单元格（参考 pandas 的实现方式） ──────────────────
        # 收集所有行（忽略 thead/tbody/tfoot 层级）
        rows = el.find_all("tr")
        if not rows:
            return super().convert_table(el, text, convert_as_inline)  # type: ignore

        # 计算展开后的最大列数
        max_cols = 0
        for row in rows:
            cols = sum(int(c.get("colspan", 1)) for c in row.find_all(["td", "th"]))
            max_cols = max(max_cols, cols)
        
        if max_cols == 0:
            return ""

        # 构建二维网格，记录每个单元格的文本内容
        grid: list[list[str]] = []
        
        for r_idx, row in enumerate(rows):
            # 确保 grid 有足够的行
            while len(grid) <= r_idx:
                grid.append([""] * max_cols)
            
            c_idx = 0
            for cell in row.find_all(["td", "th"]):
                # 跳过已被 rowspan 占用的列
                while c_idx < max_cols and grid[r_idx][c_idx] != "":
                    c_idx += 1
                
                if c_idx >= max_cols:
                    break
                    
                colspan = int(cell.get("colspan", 1))
                rowspan = int(cell.get("rowspan", 1))
                cell_text = cell.get_text(separator=" ", strip=True)
                
                # 填充 colspan × rowspan 区域
                for dr in range(rowspan):
                    for dc in range(colspan):
                        rr, cc = r_idx + dr, c_idx + dc
                        # 确保不越界
                        if rr < len(rows) + 10 and cc < max_cols:  # +10 是为了兼容 rowspan 超出原始行数的情况
                            # 扩展 grid 如果需要
                            while len(grid) <= rr:
                                grid.append([""] * max_cols)
                            # 只填充空白单元格（避免覆盖）
                            if grid[rr][cc] == "":
                                grid[rr][cc] = cell_text
                
                c_idx += colspan

        # 确保 grid 至少有数据行
        if not grid:
            return ""

        # 生成 Markdown 表格
        def _row_to_md(row_data: list[str]) -> str:
            return "| " + " | ".join(row_data) + " |"

        lines: list[str] = []
        # 第一行作为表头
        lines.append(_row_to_md(grid[0]))
        # 分隔行
        lines.append("| " + " | ".join(["---"] * max_cols) + " |")
        # 数据行
        for r_idx in range(1, len(grid)):
            lines.append(_row_to_md(grid[r_idx]))

        return "\n" + "\n".join(lines) + "\n\n"
