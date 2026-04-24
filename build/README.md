# MarkItDown GUI 打包指南

## �️ 环境要求

- Windows 10/11 x64
- Python 3.11 或以上（建议 3.12+），需加入 PATH
- 网络畅通（首次安装依赖时需要）

---

## 📦 第一步：安装依赖

在新电脑上首次打包前，需安装以下所有 Python 库。

### 1. 打包工具（必须）

```bash
pip install pyinstaller==6.19.0
pip install pyinstaller-hooks-contrib==2026.4
```

### 2. MarkItDown 核心及其依赖

```bash
pip install markitdown==0.0.2
pip install magika==0.6.2
pip install onnxruntime==1.24.4
pip install onnx==1.21.0
```

> `onnx` 不是运行时必需，但打包时 PyInstaller 分析 `onnxruntime.quantization` 子模块需要它，
> 缺少则会出现 WARNING 并导致部分模块收集不完整。

### 3. 文件格式转换依赖

```bash
pip install requests==2.33.1
pip install beautifulsoup4==4.14.3
pip install markdownify==1.2.2
pip install lxml==6.0.4
pip install defusedxml==0.7.1
pip install charset-normalizer==3.4.7
pip install pillow==12.2.0
pip install pdfminer.six==20251230
pip install pdfplumber==0.11.9
pip install mammoth==1.11.0
pip install openpyxl==3.1.5
pip install xlrd==2.0.2
pip install python-pptx==1.0.2
pip install pandas==2.3.3
pip install olefile==0.47
pip install pydub==0.25.1
pip install SpeechRecognition==3.16.0
pip install youtube-transcript-api==1.2.4
```

### 一键安装（复制整段执行）

```bash
pip install ^
  pyinstaller==6.19.0 ^
  pyinstaller-hooks-contrib==2026.4 ^
  markitdown==0.0.2 ^
  magika==0.6.2 ^
  onnxruntime==1.24.4 ^
  onnx==1.21.0 ^
  requests==2.33.1 ^
  beautifulsoup4==4.14.3 ^
  markdownify==1.2.2 ^
  lxml==6.0.4 ^
  defusedxml==0.7.1 ^
  charset-normalizer==3.4.7 ^
  pillow==12.2.0 ^
  "pdfminer.six==20251230" ^
  pdfplumber==0.11.9 ^
  mammoth==1.11.0 ^
  openpyxl==3.1.5 ^
  xlrd==2.0.2 ^
  python-pptx==1.0.2 ^
  pandas==2.3.3 ^
  olefile==0.47 ^
  pydub==0.25.1 ^
  SpeechRecognition==3.16.0 ^
  youtube-transcript-api==1.2.4
```

---

## 🚀 第二步：执行打包

```bash
cd d:\Code\markitdown_fork
py -3 build\build_exe.py
```

> **注意**：若终端中文乱码，请先执行：
> ```powershell
> $OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
> ```

---

## 📂 第三步：获取产物

打包完成后，exe 在项目根目录的 `dist/` 下：

```
d:\Code\markitdown_fork\
├── build\                 ← 临时构建文件（打包后可删除）
└── dist\
    └── MarkItDown_v0.1.6b2_20260424-xxxxxx.exe  ← 直接发给对方即可
```

**单文件模式，对方无需安装 Python，直接运行 exe 即可。**

---

## ⚠️ 常见问题

| 现象 | 原因 | 解决方法 |
|------|------|----------|
| `DLL load failed while importing onnxruntime_pybind11_state` | onnxruntime DLL 路径未注入 | 已由 `hook_onnxruntime.py` 自动处理，确保打包时该文件存在于 `build\` 目录 |
| `WARNING: Failed to collect submodules for 'onnxruntime.quantization'` | 未安装 `onnx` 包 | `pip install onnx` |
| 终端中文乱码 | PowerShell 默认 GBK 编码 | 执行 `$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8` |
| 对方电脑运行报 VCRUNTIME 错误 | 缺少 Visual C++ 运行库 | 对方安装 [Visual C++ Redistributable 2019+](https://aka.ms/vs/17/release/vc_redist.x64.exe) |
