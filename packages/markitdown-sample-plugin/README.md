# MarkItDown 示例插件

[![PyPI](https://img.shields.io/pypi/v/markitdown-sample-plugin.svg)](https://pypi.org/project/markitdown-sample-plugin/)
![PyPI - Downloads](https://img.shields.io/pypi/dd/markitdown-sample-plugin)
[![Built by AutoGen Team](https://img.shields.io/badge/Built%20by-AutoGen%20Team-blue)](https://github.com/microsoft/autogen)

本项目展示如何为 MarkItDown 创建示例插件。最重要的部分如下：

接下来，实现您的自定义 DocumentConverter：

```python
from typing import BinaryIO, Any
from markitdown import MarkItDown, DocumentConverter, DocumentConverterResult, StreamInfo

class RtfConverter(DocumentConverter):

    def __init__(
        self, priority: float = DocumentConverter.PRIORITY_SPECIFIC_FILE_FORMAT
    ):
        super().__init__(priority=priority)

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:

	# 实现检查文件流是否为 RTF 文件的逻辑
	# ...
	raise NotImplementedError()


    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:

	# 实现将文件流转换为 Markdown 的逻辑
	# ...
	raise NotImplementedError()
```

接下来，确保您的包实现并导出以下内容：

```python
# 此插件使用的插件接口版本。
# 目前唯一支持的版本是 1
__plugin_interface_version__ = 1

# 插件的主要入口点。每次创建 MarkItDown 实例时都会调用此函数。
def register_converters(markitdown: MarkItDown, **kwargs):
    """
    在构造 MarkItDown 实例期间调用，以注册插件提供的转换器。
    """

    # 简单创建并附加一个 RtfConverter 实例
    markitdown.register_converter(RtfConverter())
```

最后，在 `pyproject.toml` 文件中创建一个入口点：

```toml
[project.entry-points."markitdown.plugin"]
sample_plugin = "markitdown_sample_plugin"
```

这里，`sample_plugin` 的值可以是任何键，但理想情况下应该是插件的名称。该值是实现插件的包的完全限定名称。

## 安装

要将插件与 MarkItDown 一起使用，必须安装它。要从当前目录安装插件，请使用：

```bash
pip install -e .
```

安装插件包后，通过运行以下命令验证它在 MarkItDown 中可用：

```bash
markitdown --list-plugins
```

要在转换中使用插件，请使用 `--use-plugins` 标志。例如，要转换 RTF 文件：

```bash
markitdown --use-plugins path-to-file.rtf
```

在 Python 中，可以按以下方式启用插件：

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=True)
result = md.convert("path-to-file.rtf")
print(result.text_content)
```

## 商标

本项目可能包含项目、产品或服务的商标或徽标。授权使用微软商标或徽标必须遵守并遵循 [Microsoft 的商标和品牌指南](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general)。
在本项目的修改版本中使用微软商标或徽标不得引起混淆或暗示微软赞助。
任何使用第三方商标或徽标均须遵守这些第三方的政策。
