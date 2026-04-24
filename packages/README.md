# MarkItDown 包结构说明

本目录包含 MarkItDown 项目的所有 Python 包。每个包都是独立的 Python 模块，可以单独安装和使用。

## 包列表

### 1. markitdown（核心包）

**路径**: `packages/markitdown/`

MarkItDown 的核心库，提供将各种文件格式转换为 Markdown 的功能。

**主要特性**:

- 支持 PDF、Word、Excel、PowerPoint、图片、音频等多种格式
- 提供命令行工具和 Python API
- 支持插件系统
- 可选依赖项按需安装

**安装**:

```bash
pip install markitdown[all]
```

**快速开始**:

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)
```

**详细信息**: 查看 [markitdown/README.md](markitdown/README.md)

---

### 2. markitdown-mcp（MCP 服务器）

**路径**: `packages/markitdown-mcp/`

为 MarkItDown 提供 Model Context Protocol (MCP) 服务器实现，允许 AI 助手通过 MCP 协议调用 MarkItDown 的转换功能。

**主要特性**:

- 支持 STDIO、Streamable HTTP 和 SSE 三种传输方式
- 暴露 `convert_to_markdown(uri)` 工具
- 支持 http:、https:、file:、data: 等 URI 方案
- 提供 Docker 镜像支持
- 可与 Claude Desktop 等 MCP 客户端集成

**安装**:

```bash
pip install markitdown-mcp
```

**使用方法**:

STDIO 模式（默认）:

```bash
markitdown-mcp
```

HTTP/SSE 模式:

```bash
markitdown-mcp --http --host 127.0.0.1 --port 3001
```

**Docker 使用**:

```bash
docker build -t markitdown-mcp:latest .
docker run -it --rm -v /path/to/data:/workdir markitdown-mcp:latest
```

**安全提示**: MCP 服务器默认绑定到 localhost，仅用于本地受信任环境。不要将其绑定到其他网络接口，除非您完全理解安全风险。

**详细信息**: 查看 [markitdown-mcp/README.md](markitdown-mcp/README.md)

---

### 3. markitdown-ocr（OCR 插件）

**路径**: `packages/markitdown-ocr/`

使用 LLM Vision 技术从 PDF、DOCX、PPTX 和 XLSX 文件中的图像提取文本的 OCR 插件。

**主要特性**:

- **增强 PDF 转换器**: 从 PDF 中提取图像文本，扫描文档支持整页 OCR
- **增强 DOCX 转换器**: Word 文档中的图像 OCR
- **增强 PPTX 转换器**: PowerPoint 演示文稿中的图像 OCR
- **增强 XLSX 转换器**: Excel 电子表格中的图像 OCR
- **上下文保留**: 保持文档结构和流程
- 使用与 MarkItDown 相同的 `llm_client` / `llm_model` 模式
- 无需额外的 ML 库或二进制依赖

**安装**:

```bash
pip install markitdown-ocr
pip install openai  # 或其他 OpenAI 兼容客户端
```

**使用方法**:

命令行:

```bash
markitdown document.pdf --use-plugins --llm-client openai --llm-model gpt-4o
```

Python API:

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

**支持的格式**:

- **PDF**: 提取嵌入图像，自动检测扫描文档并进行整页 OCR
- **DOCX**: 通过文档关系提取图像，保持文档流
- **PPTX**: 支持图片形状、占位符形状和组内图像
- **XLSX**: 按工作表提取图像，计算单元格位置

**输出格式**:

```
*[Image OCR]
<提取的文本>
[End OCR]*
```

**详细信息**: 查看 [markitdown-ocr/README.md](markitdown-ocr/README.md)

---

### 4. markitdown-sample-plugin（示例插件）

**路径**: `packages/markitdown-sample-plugin/`

展示如何为 MarkItDown 创建第三方插件的示例项目。适合作为开发自定义插件的模板。

**主要特性**:

- 完整的插件开发示例
- 展示如何实现 `DocumentConverter` 接口
- 演示插件注册机制
- 包含 RTF 文件转换示例

**插件开发关键步骤**:

1. 实现自定义 DocumentConverter:

```python
from markitdown import DocumentConverter, DocumentConverterResult, StreamInfo

class CustomConverter(DocumentConverter):
    def accepts(self, file_stream, stream_info, **kwargs):
        # 检查是否接受该文件
        return True/False

    def convert(self, file_stream, stream_info, **kwargs):
        # 转换为 Markdown
        return DocumentConverterResult(text_content="...")
```

2. 实现插件入口点:

```python
__plugin_interface_version__ = 1

def register_converters(markitdown, **kwargs):
    markitdown.register_converter(CustomConverter())
```

3. 在 `pyproject.toml` 中配置入口点:

```toml
[project.entry-points."markitdown.plugin"]
my_plugin = "my_package"
```

**安装**:

```bash
pip install markitdown-sample-plugin
```

**验证插件**:

```bash
markitdown --list-plugins
```

**使用插件**:

```bash
markitdown --use-plugins file.rtf
```

**详细信息**: 查看 [markitdown-sample-plugin/README.md](markitdown-sample-plugin/README.md)

---

## 包之间的关系

```
markitdown (核心包)
    ├── markitdown-mcp (依赖核心包，提供 MCP 服务)
    ├── markitdown-ocr (插件，扩展核心包的 OCR 能力)
    └── markitdown-sample-plugin (插件示例，展示如何扩展)
```

- **markitdown**: 基础核心，所有其他包都依赖它
- **markitdown-mcp**: 独立的服务层，通过 MCP 协议暴露核心功能
- **markitdown-ocr**: 通过插件系统增强核心功能
- **markitdown-sample-plugin**: 教学示例，展示插件开发模式

## 开发指南

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/microsoft/markitdown.git
cd markitdown

# 安装核心包
pip install -e packages/markitdown[all]

# 安装 MCP 服务器（可选）
pip install -e packages/markitdown-mcp

# 安装 OCR 插件（可选）
pip install -e packages/markitdown-ocr

# 安装示例插件（可选，用于学习）
pip install -e packages/markitdown-sample-plugin
```

### 运行测试

每个包都有自己的测试套件：

```bash
# 核心包测试
cd packages/markitdown
hatch test

# MCP 服务器测试
cd packages/markitdown-mcp
pytest tests/

# OCR 插件测试
cd packages/markitdown-ocr
pytest tests/

# 示例插件测试
cd packages/markitdown-sample-plugin
pytest tests/
```

### 构建包

```bash
# 构建核心包
cd packages/markitdown
python -m build

# 构建其他包类似
cd ../markitdown-mcp
python -m build
```

## 选择适合的包

- **只需要文件转 Markdown**: 安装 `markitdown`
- **需要 AI 助手集成**: 额外安装 `markitdown-mcp`
- **需要从图像提取文本**: 额外安装 `markitdown-ocr` + OpenAI 客户端
- **想开发自己的插件**: 参考 `markitdown-sample-plugin`

## 贡献

欢迎为任何包贡献代码！请参阅主仓库的贡献指南。

## 许可证

所有包均使用 MIT 许可证，详见各包目录中的 LICENSE 文件。
