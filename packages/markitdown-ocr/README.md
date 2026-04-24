# MarkItDown OCR 插件

MarkItDown 的 LLM Vision 插件，从 PDF、DOCX、PPTX 和 XLSX 文件中嵌入的图像提取文本。

使用 MarkItDown 已经支持的相同 `llm_client` / `llm_model` 模式进行图像描述——无需新的 ML 库或二进制依赖。

## 特性

- **增强 PDF 转换器**：从 PDF 中的图像提取文本，扫描文档支持整页 OCR 回退
- **增强 DOCX 转换器**：Word 文档中图像的 OCR
- **增强 PPTX 转换器**：PowerPoint 演示文稿中图像的 OCR
- **增强 XLSX 转换器**：Excel 电子表格中图像的 OCR
- **上下文保留**：在插入提取的文本时保持文档结构和流程

## 安装

```bash
pip install markitdown-ocr
```

该插件使用您已经拥有的任何 OpenAI 兼容客户端。如果还没有，请安装一个：

```bash
pip install openai
```

## 使用方法

### 命令行

```bash
markitdown document.pdf --use-plugins --llm-client openai --llm-model gpt-4o
```

### Python API

将 `llm_client` 和 `llm_model` 传递给 `MarkItDown()`，就像用于图像描述一样：

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),
    llm_model="gpt-4o",
)

result = md.convert("document_with_images.pdf")
print(result.text_content)
```

如果未提供 `llm_client`，插件仍会加载，但 OCR 会被静默跳过——回退到标准的内置转换器。

### 自定义提示

为 specialized 文档覆盖默认提取提示：

```python
md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),
    llm_model="gpt-4o",
    llm_prompt="从此图像中提取所有文本，保留表格结构。",
)
```

### 任何 OpenAI 兼容客户端

适用于任何遵循 OpenAI API 的客户端：

```python
from openai import AzureOpenAI

md = MarkItDown(
    enable_plugins=True,
    llm_client=AzureOpenAI(
        api_key="...",
        azure_endpoint="https://your-resource.openai.azure.com/",
        api_version="2024-02-01",
    ),
    llm_model="gpt-4o",
)
```

## 工作原理

当调用 `MarkItDown(enable_plugins=True, llm_client=..., llm_model=...)` 时：

1. MarkItDown 通过 `markitdown.plugin` 入口点组发现插件
2. 它调用 `register_converters()`，转发所有 kwargs，包括 `llm_client` 和 `llm_model`
3. 插件从这些 kwargs 创建 `LLMVisionOCRService`
4. 四个 OCR 增强转换器以**优先级 -1.0** 注册——在优先级 0.0 的内置转换器之前

转换文件时：

1. OCR 转换器接受文件
2. 它从文档中提取嵌入的图像
3. 每个图像都带有提取提示发送到 LLM
4. 返回的文本以内联方式插入，保持文档结构
5. 如果 LLM 调用失败，转换将继续，但不包含该图像的文本

## 支持的文件格式

### PDF

- 嵌入图像按位置提取（通过 `page.images` / 页面 XObjects）并进行内联 OCR，以垂直阅读顺序与周围文本交错。
- **扫描的 PDF**（没有可提取文本的页面）会自动检测：每页以 300 DPI 渲染并作为整页图像发送到 LLM。
- **格式错误的 PDF**（pdfplumber/pdfminer 无法打开，例如截断的 EOF）会使用 PyMuPDF 页面渲染重试，因此仍可恢复内容。

### DOCX

- 图像通过文档部分关系（`doc.part.rels`）提取。
- OCR 在 DOCX→HTML→Markdown 管道执行之前运行：占位符令牌注入到 HTML 中，以便 markdown 转换器不会转义 OCR 标记，最终的占位符在转换后替换为格式化的 `*[Image OCR]...[End OCR]*` 块。
- 文档流（标题、段落、表格）在 OCR 块周围完全保留。

### PPTX

- 支持图片形状、带图像的占位符形状以及组内的图像。
- 每页幻灯片按从上到左的阅读顺序处理形状。
- 如果配置了 `llm_client`，LLM 首先被要求提供描述；当没有返回描述时使用 OCR 作为回退。

### XLSX

- 工作表中嵌入的图像（`sheet._images`）按工作表提取。
- 单元格位置从图像锚点坐标计算（列/行 → Excel 字母表示法）。
- 图像在工作表的数据表之后的 `### Images in this sheet:` 部分下列出——它们不会交错到表格行中。

### 输出格式

每个提取的 OCR 块都包装为：

```text
*[Image OCR]
<提取的文本>
[End OCR]*
```

## 故障排除

### 输出中缺少 OCR 文本

最可能的原因是缺少 `llm_client` 或 `llm_model`。验证：

```python
from openai import OpenAI
from markitdown import MarkItDown

md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),   # 必需
    llm_model="gpt-4o",    # 必需
)
```

### 插件未加载

确认插件已安装并被发现：

```bash
markitdown --list-plugins   # 应该显示：ocr
```

### API 错误

插件将 LLM API 错误作为警告传播并继续转换。检查您的 API 密钥、配额，以及所选模型是否支持视觉输入。

## 开发

### 运行测试

```bash
cd packages/markitdown-ocr
pytest tests/ -v
```

### 从源码构建

```bash
git clone https://github.com/microsoft/markitdown.git
cd markitdown/packages/markitdown-ocr
pip install -e .
```

## 贡献

欢迎贡献！请参阅 [MarkItDown 仓库](https://github.com/microsoft/markitdown)了解指南。

## 许可证

MIT — 参见 [LICENSE](LICENSE)。

## 变更日志

### 0.1.0（初始版本）

- PDF、DOCX、PPTX、XLSX 的 LLM Vision OCR
- 扫描 PDF 的整页 OCR 回退
- 上下文感知的内联文本插入
- 基于优先级的转换器替换（无需代码更改）
