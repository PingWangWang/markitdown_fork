# MarkItDown-MCP

> [!IMPORTANT]
> MarkItDown-MCP 包专为**本地使用**而设计，配合本地受信任的代理使用。特别是，当使用 Streamable HTTP 或 SSE 运行 MCP 服务器时，它默认绑定到 `localhost`，不会暴露给网络或互联网上的其他机器。在此配置中，它是 STDIO 传输的直接替代方案，在某些情况下可能更方便。除非您理解这样做的[安全影响](#安全注意事项)，否则不要将服务器绑定到其他接口。

[![PyPI](https://img.shields.io/pypi/v/markitdown-mcp.svg)](https://pypi.org/project/markitdown-mcp/)
![PyPI - Downloads](https://img.shields.io/pypi/dd/markitdown-mcp)
[![Built by AutoGen Team](https://img.shields.io/badge/Built%20by-AutoGen%20Team-blue)](https://github.com/microsoft/autogen)

`markitdown-mcp` 包提供了一个轻量级的 STDIO、Streamable HTTP 和 SSE MCP 服务器，用于调用 MarkItDown。

它公开一个工具：`convert_to_markdown(uri)`，其中 uri 可以是任何 `http:`、`https:`、`file:` 或 `data:` URI。

## 安装

要安装此包，请使用 pip：

```bash
pip install markitdown-mcp
```

## 使用方法

要使用 STDIO（默认）运行 MCP 服务器，请使用以下命令：

```bash
markitdown-mcp
```

要使用 Streamable HTTP 和 SSE 运行 MCP 服务器，请使用以下命令：

```bash
markitdown-mcp --http --host 127.0.0.1 --port 3001
```

## 在 Docker 中运行

要在 Docker 中运行 `markitdown-mcp`，请使用提供的 Dockerfile 构建 Docker 镜像：

```bash
docker build -t markitdown-mcp:latest .
```

并使用以下命令运行：

```bash
docker run -it --rm markitdown-mcp:latest
```

这对于远程 URI 已经足够。要访问本地文件，您需要将本地目录挂载到容器中。例如，如果您想访问 `/home/user/data` 中的文件，可以运行：

```bash
docker run -it --rm -v /home/user/data:/workdir markitdown-mcp:latest
```

挂载后，data 下的所有文件将在容器中的 `/workdir` 下可访问。例如，如果您在 `/home/user/data` 中有一个文件 `example.txt`，它将可以在容器中的 `/workdir/example.txt` 访问。

## 从 Claude Desktop 访问

为 Claude Desktop 运行 MCP 服务器时，建议使用 Docker 镜像。

按照[这些说明](https://modelcontextprotocol.io/quickstart/user#for-claude-desktop-users)访问 Claude 的 `claude_desktop_config.json` 文件。

编辑它以包含以下 JSON 条目：

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "markitdown-mcp:latest"]
    }
  }
}
```

如果您想挂载目录，请相应调整：

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v",
        "/home/user/data:/workdir",
        "markitdown-mcp:latest"
      ]
    }
  }
}
```

## 调试

您可以使用 `MCP Inspector` 工具来调试 MCP 服务器。

```bash
npx @modelcontextprotocol/inspector
```

然后您可以通过指定的主机和端口连接到检查器（例如，`http://localhost:5173/`）。

如果使用 STDIO：

- 选择 `STDIO` 作为传输类型，
- 输入 `markitdown-mcp` 作为命令，并
- 点击 `Connect`

如果使用 Streamable HTTP：

- 选择 `Streamable HTTP` 作为传输类型，
- 输入 `http://127.0.0.1:3001/mcp` 作为 URL，并
- 点击 `Connect`

如果使用 SSE：

- 选择 `SSE` 作为传输类型，
- 输入 `http://127.0.0.1:3001/sse` 作为 URL，并
- 点击 `Connect`

最后：

- 点击 `Tools` 标签，
- 点击 `List Tools`，
- 点击 `convert_to_markdown`，并
- 在任何有效的 URI 上运行该工具。

## 安全注意事项

服务器不支持身份验证，并以运行它的用户权限运行。因此，当以 SSE 或 Streamable HTTP 模式运行时，服务器默认绑定到 `localhost`。即便如此，重要的是要认识到同一台本地机器上的任何进程或用户都可以访问服务器，并且 `convert_to_markdown` 工具可用于读取服务器用户可以访问的任何文件或来自网络的任何数据。如果您需要额外的安全性，请考虑在沙盒环境中运行服务器，例如虚拟机或容器，并确保正确配置用户权限以限制对敏感文件和网络段的访问。最重要的是，除非您理解这样做的安全影响，否则不要将服务器绑定到其他接口（非 localhost）。

## 商标

本项目可能包含项目、产品或服务的商标或徽标。授权使用微软商标或徽标必须遵守并遵循 [Microsoft 的商标和品牌指南](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general)。
在本项目的修改版本中使用微软商标或徽标不得引起混淆或暗示微软赞助。
任何使用第三方商标或徽标均须遵守这些第三方的政策。
