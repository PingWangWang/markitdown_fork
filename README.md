# MarkItDown

[![PyPI](https://img.shields.io/pypi/v/markitdown.svg)](https://pypi.org/project/markitdown/)
![PyPI - Downloads](https://img.shields.io/pypi/dd/markitdown)
[![Built by AutoGen Team](https://img.shields.io/badge/Built%20by-AutoGen%20Team-blue)](https://github.com/microsoft/autogen)

> [!IMPORTANT]
> MarkItDown 以当前进程的权限执行 I/O 操作。与 open() 或 requests.get() 类似，它将访问进程本身可以访问的资源。在不受信任的环境中，请对输入进行清理，并调用最适合您用例的 `convert_*` 函数（例如，`convert_stream()` 或 `convert_local()`）。有关更多信息，请参阅文档中的[安全注意事项](#安全注意事项)部分。

MarkItDown 是一个轻量级的 Python 工具，用于将各种文件格式转换为 Markdown，以便用于 LLM 和相关的文本分析管道。在这方面，它与 [textract](https://github.com/deanmalmgren/textract) 最为相似，但侧重于将重要的文档结构和内容保留为 Markdown 格式（包括：标题、列表、表格、链接等）。虽然输出通常相当可观且对人类友好，但它旨在供文本分析工具使用——可能不是高保真文档转换以供人类消费的最佳选择。

MarkItDown 目前支持从以下格式转换：

- PDF
- PowerPoint
- Word
- Excel
- 图片（EXIF 元数据和 OCR）
- 音频（EXIF 元数据和语音转录）
- HTML
- 基于文本的格式（CSV、JSON、XML）
- ZIP 文件（迭代处理内容）
- YouTube URL
- EPub
- ... 以及更多！

## 为什么选择 Markdown？

Markdown 非常接近平面文本，几乎没有标记或格式化，但仍然提供了一种表示重要文档结构的方式。主流 LLM，如 OpenAI 的 GPT-4o，原生"_说_" Markdown，并且经常在其响应中未经提示地加入 Markdown。这表明它们已经接受了大量 Markdown 格式文本的训练，并且对其理解良好。作为附带好处，Markdown 约定也非常节省 token。

## 前置要求

MarkItDown 需要 Python 3.10 或更高版本。建议使用虚拟环境以避免依赖冲突。

使用标准 Python 安装，您可以使用以下命令创建和激活虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
```

如果使用 `uv`，您可以使用以下命令创建虚拟环境：

```bash
uv venv --python=3.12 .venv
source .venv/bin/activate
# 注意：务必使用 'uv pip install' 而不是 'pip install' 来在此虚拟环境中安装包
```

如果您使用的是 Anaconda，可以使用以下命令创建虚拟环境：

```bash
conda create -n markitdown python=3.12
conda activate markitdown
```

## 安装

要安装 MarkItDown，请使用 pip：`pip install 'markitdown[all]'`。或者，您可以从源代码安装：

```bash
git clone git@github.com:microsoft/markitdown.git
cd markitdown
pip install -e 'packages/markitdown[all]'
```

## 使用方法

### 命令行

```bash
markitdown path-to-file.pdf > document.md
```

或使用 `-o` 指定输出文件：

```bash
markitdown path-to-file.pdf -o document.md
```

您也可以管道输入内容：

```bash
cat path-to-file.pdf | markitdown
```

### 可选依赖项

MarkItDown 具有可选依赖项，用于激活各种文件格式。在本文档前面，我们使用 `[all]` 选项安装了所有可选依赖项。但是，您也可以单独安装它们以获得更多控制。例如：

```bash
pip install 'markitdown[pdf, docx, pptx]'
```

将仅安装 PDF、DOCX 和 PPTX 文件的依赖项。

目前，以下可选依赖项可用：

- `[all]` 安装所有可选依赖项
- `[pptx]` 安装 PowerPoint 文件的依赖项
- `[docx]` 安装 Word 文件的依赖项
- `[xlsx]` 安装 Excel 文件的依赖项
- `[xls]` 安装旧版 Excel 文件的依赖项
- `[pdf]` 安装 PDF 文件的依赖项
- `[outlook]` 安装 Outlook 消息的依赖项
- `[az-doc-intel]` 安装 Azure Document Intelligence 的依赖项
- `[audio-transcription]` 安装 wav 和 mp3 文件音频转录的依赖项
- `[youtube-transcription]` 安装获取 YouTube 视频转录的依赖项

### 插件

MarkItDown 还支持第三方插件。默认情况下禁用插件。要列出已安装的插件：

```bash
markitdown --list-plugins
```

要启用插件，请使用：

```bash
markitdown --use-plugins path-to-file.pdf
```

要查找可用插件，请在 GitHub 上搜索标签 `#markitdown-plugin`。要开发插件，请参阅 `packages/markitdown-sample-plugin`。

#### markitdown-ocr 插件

`markitdown-ocr` 插件为 PDF、DOCX、PPTX 和 XLSX 转换器添加 OCR 支持，使用 LLM Vision 从嵌入图像中提取文本——与 MarkItDown 已用于图像描述的相同 `llm_client` / `llm_model` 模式。不需要新的 ML 库或二进制依赖项。

**安装：**

```bash
pip install markitdown-ocr
pip install openai  # 或任何 OpenAI 兼容客户端
```

**使用方法：**

传递与用于图像描述相同的 `llm_client` 和 `llm_model`：

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

如果未提供 `llm_client`，插件仍会加载，但 OCR 会被静默跳过，并使用标准的内置转换器。

有关详细文档，请参阅 [`packages/markitdown-ocr/README.md`](packages/markitdown-ocr/README.md)。

### Azure Document Intelligence

要使用 Microsoft Document Intelligence 进行转换：

```bash
markitdown path-to-file.pdf -o document.md -d -e "<document_intelligence_endpoint>"
```

有关如何设置 Azure Document Intelligence 资源的更多信息，可以在[此处](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/create-document-intelligence-resource?view=doc-intel-4.0.0)找到

### Python API

基本用法：

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False) # 设置为 True 以启用插件
result = md.convert("test.xlsx")
print(result.text_content)
```

Document Intelligence 转换：

```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="<document_intelligence_endpoint>")
result = md.convert("test.pdf")
print(result.text_content)
```

要使用大型语言模型进行图像描述（目前仅适用于 pptx 和图片文件），请提供 `llm_client` 和 `llm_model`：

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o", llm_prompt="可选的自定义提示")
result = md.convert("example.jpg")
print(result.text_content)
```

### Docker

```sh
docker build -t markitdown:latest .
docker run --rm -i markitdown:latest < ~/your-file.pdf > output.md
```

## 贡献

本项目欢迎贡献和建议。大多数贡献需要您同意一份贡献者许可协议（CLA），声明您有权并且确实授予我们使用您的贡献的权利。有关详情，请访问 https://cla.opensource.microsoft.com。

当您提交拉取请求时，CLA 机器人将自动确定您是否需要提供 CLA 并适当地装饰 PR（例如，状态检查、评论）。只需按照机器人提供的说明操作即可。您只需要在使用我们的 CLA 的所有仓库中执行一次此操作。

本项目采用了 [Microsoft 开源行为准则](https://opensource.microsoft.com/codeofconduct/)。
有关更多信息，请参阅 [行为准则常见问题解答](https://opensource.microsoft.com/codeofconduct/faq/) 或通过 [opencode@microsoft.com](mailto:opencode@microsoft.com) 联系，如有其他问题或意见。

### 如何贡献

您可以通过查看问题或帮助审查 PR 来提供帮助。任何问题或 PR 都受欢迎，但我们也标记了一些为"开放贡献"和"开放审查"的问题，以帮助促进社区贡献。这些当然只是建议，欢迎您以任何方式做出贡献。

<div align="center">

|          | 全部                                                       | 特别需要社区帮助                                                                                                            |
| -------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **问题** | [所有问题](https://github.com/microsoft/markitdown/issues) | [开放贡献的问题](https://github.com/microsoft/markitdown/issues?q=is%3Aissue+is%3Aopen+label%3A%22open+for+contribution%22) |
| **PR**   | [所有 PR](https://github.com/microsoft/markitdown/pulls)   | [开放审查的 PR](https://github.com/microsoft/markitdown/pulls?q=is%3Apr+is%3Aopen+label%3A%22open+for+reviewing%22)         |

</div>

### 运行测试和检查

- 导航到 MarkItDown 包：

  ```sh
  cd packages/markitdown
  ```

- 在您的环境中安装 `hatch` 并运行测试：

  ```sh
  pip install hatch  # 其他安装 hatch 的方法：https://hatch.pypa.io/dev/install/
  hatch shell
  hatch test
  ```

  （替代方法）使用已安装所有依赖项的 Devcontainer：

  ```sh
  # 在 Devcontainer 中重新打开项目并运行：
  hatch test
  ```

- 在提交 PR 之前运行 pre-commit 检查：`pre-commit run --all-files`

### 安全注意事项

MarkItDown 以当前进程的权限执行 I/O 操作。与 `open()` 或 `requests.get()` 类似，它将访问进程本身可以访问的资源。

**清理您的输入：** 不要将不受信任的输入直接传递给 MarkItDown。如果输入的任何部分可能由不受信任的用户或系统控制，例如在托管或服务器端应用程序中，必须在调用 MarkItDown 之前对其进行验证和限制。根据您的环境，这可能包括限制文件路径、限制 URI 方案和网络目标，以及阻止访问私有、环回、链路本地或元数据服务地址。

**仅调用您需要的转换方法：** 优先选择最适合您用例的最窄转换 API。MarkItDown 的 `convert()` 方法故意宽松，可以处理本地文件、远程 URI 和字节流。如果您的应用程序只需要读取本地文件，请调用 `convert_local()`。如果您需要对 URI 获取进行更多控制，请自己调用 `requests.get()` 并将响应对象传递给 `convert_response()`。为了获得最大控制权，打开到您想要转换的输入的流并调用 `convert_stream()`。

### 贡献第三方插件

您还可以通过创建和分享第三方插件来做出贡献。有关更多详细信息，请参阅 `packages/markitdown-sample-plugin`。

## 商标

本项目可能包含项目、产品或服务的商标或徽标。授权使用微软商标或徽标必须遵守并遵循 [Microsoft 的商标和品牌指南](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general)。
在本项目的修改版本中使用微软商标或徽标不得引起混淆或暗示微软赞助。
任何使用第三方商标或徽标均须遵守这些第三方的政策。
