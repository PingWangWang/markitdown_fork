# -*- mode: python ; coding: utf-8 -*-
"""
MarkItDown GUI 打包脚本
直接运行: py -3 build_exe.py
"""

import sys
import subprocess
import os
import glob
from pathlib import Path
from datetime import datetime

# 强制 stdout/stderr 使用 UTF-8，避免 Windows GBK 终端报 UnicodeEncodeError
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 日志美化函数
def log_info(msg):
    print(f"  [INFO] {datetime.now().strftime('%H:%M:%S')} | {msg}")

def log_step(msg):
    print(f"\n{'='*60}")
    print(f"  STEP: {msg}")
    print(f"{'='*60}")

def log_success(msg):
    print(f"\n  [OK] {msg}")

def log_error(msg):
    print(f"\n  [FAIL] {msg}")

# 获取项目根目录（build_exe.py 在 build/ 目录，需要向上一级）
project_root = Path(__file__).parent.parent

# 从 __about__.py 读取版本号
version_file = project_root / 'packages' / 'markitdown' / 'src' / 'markitdown' / '__about__.py'
app_version = "0.0.0"
if version_file.exists():
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    app_version = line.split('=')[1].strip().strip('"\'')
                    break
    except Exception:
        pass

# 生成时间戳
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

# 生成 exe 文件名：MarkItDown_v0.1.6b2_20250602-143025
exe_name = f"MarkItDown_v{app_version}_{timestamp}"

log_step("MarkItDown 打包配置")
print(f"  版本号   : {app_version}")
print(f"  时间戳   : {timestamp}")
print(f"  输出文件 : {exe_name}")
print(f"{'='*60}")

# 清理旧的构建文件（在项目根目录）
log_step("步骤 1/3: 清理旧文件")
log_info("正在清理旧的构建目录...")
import importlib.util
import shutil

# 清理项目根目录的 build（除了 build_exe.py 和 README.md）和 dist
build_dir = project_root / 'build'
if build_dir.exists():
    # 只删除 build/ 目录中的 PyInstaller 临时文件，保留脚本和文档
    for item in build_dir.iterdir():
        if item.name not in ['build_exe.py', 'README.md', 'hook_onnxruntime.py']:
            if item.is_dir():
                shutil.rmtree(item)
                log_info(f"已删除 {item.name}/")
            else:
                item.unlink()
                log_info(f"已删除 {item.name}")

# 清理 dist 目录
dist_dir = project_root / 'dist'
if dist_dir.exists():
    shutil.rmtree(dist_dir)
    log_info("已删除 dist/ 目录")

# 删除旧的 .spec 文件（在项目根目录和 build/ 目录）
for spec_file in list(project_root.glob('*.spec')) + list(build_dir.glob('*.spec')):
    if spec_file.exists():
        spec_file.unlink()
        log_info(f"已删除 {spec_file.name}")

log_success("清理完成")

# 动态获取 magika 包路径
magika_spec = importlib.util.find_spec('magika')
if magika_spec is None or magika_spec.origin is None:
    log_error("未找到 magika 包，请先安装: pip install magika")
    sys.exit(1)
log_info(f"magika 已找到: {magika_spec.origin}")
sep = ';' if sys.platform == 'win32' else ':'

# 构建 PyInstaller 命令
# 注意：使用 --distpath 和 --workpath 指定输出目录，避免覆盖 build/ 目录
cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--name', exe_name,
    '--onefile',
    '--noconfirm',
    '--clean',
    '--distpath', str(project_root / 'dist'),  # 输出到项目根目录的 dist/
    '--workpath', str(project_root / 'build'),  # 临时文件在项目根目录的 build/
    '--specpath', str(project_root / 'build'),  # spec 文件在项目根目录的 build/
    '--hidden-import', 'markitdown',
    '--hidden-import', '_version',
    '--hidden-import', '_dialogs',
    '--hidden-import', '_app',
    '--hidden-import', 'markitdown.__about__',
    '--hidden-import', 'markitdown.__main__',
    '--hidden-import', 'markitdown._base_converter',
    '--hidden-import', 'markitdown._exceptions',
    '--hidden-import', 'markitdown._markitdown',
    '--hidden-import', 'markitdown._stream_info',
    '--hidden-import', 'markitdown._uri_utils',
    '--hidden-import', 'markitdown.converter_utils',
    '--hidden-import', 'markitdown.converters',
    '--hidden-import', 'markitdown.converters._audio_converter',
    '--hidden-import', 'markitdown.converters._bing_serp_converter',
    '--hidden-import', 'markitdown.converters._csv_converter',
    '--hidden-import', 'markitdown.converters._doc_intel_converter',
    '--hidden-import', 'markitdown.converters._docx_converter',
    '--hidden-import', 'markitdown.converters._epub_converter',
    '--hidden-import', 'markitdown.converters._exiftool',
    '--hidden-import', 'markitdown.converters._html_converter',
    '--hidden-import', 'markitdown.converters._image_converter',
    '--hidden-import', 'markitdown.converters._ipynb_converter',
    '--hidden-import', 'markitdown.converters._llm_caption',
    '--hidden-import', 'markitdown.converters._markdownify',
    '--hidden-import', 'markitdown.converters._outlook_msg_converter',
    '--hidden-import', 'markitdown.converters._pdf_converter',
    '--hidden-import', 'markitdown.converters._plain_text_converter',
    '--hidden-import', 'markitdown.converters._pptx_converter',
    '--hidden-import', 'markitdown.converters._rss_converter',
    '--hidden-import', 'markitdown.converters._transcribe_audio',
    '--hidden-import', 'markitdown.converters._wikipedia_converter',
    '--hidden-import', 'markitdown.converters._xlsx_converter',
    '--hidden-import', 'markitdown.converter_utils',
    '--hidden-import', 'markitdown.converter_utils.docx',
    '--hidden-import', 'markitdown.converter_utils.docx.pre_process',
    '--hidden-import', 'markitdown.converter_utils.docx.math',
    '--hidden-import', 'markitdown.converter_utils.docx.math.omml',
    '--hidden-import', 'markitdown.converter_utils.docx.math.latex_dict',
    '--hidden-import', 'markitdown.converters._youtube_converter',
    '--hidden-import', 'markitdown.converters._zip_converter',
    '--hidden-import', 'requests',
    '--hidden-import', 'bs4',  # beautifulsoup4 的正确包名
    '--hidden-import', 'markdownify',
    '--hidden-import', 'magika',
    '--hidden-import', 'charset_normalizer',
    '--hidden-import', 'defusedxml',
    '--hidden-import', 'pdfminer',
    '--hidden-import', 'pdfplumber',
    '--hidden-import', 'mammoth',
    '--hidden-import', 'docx',
    '--hidden-import', 'openpyxl',
    '--hidden-import', 'xlrd',
    '--hidden-import', 'lxml',
    '--hidden-import', 'pptx',
    '--hidden-import', 'PIL',
    '--hidden-import', 'PIL.Image',
    '--hidden-import', 'pydub',
    '--hidden-import', 'speech_recognition',
    '--hidden-import', 'youtube_transcript_api',
    '--hidden-import', 'olefile',
    '--hidden-import', 'pandas',
    '--hidden-import', 'azure.ai.documentintelligence',
    '--hidden-import', 'azure.identity',
    '--hidden-import', 'azure.core',
    '--hidden-import', 'azure.core.credentials',
    '--exclude-module', 'matplotlib',
    '--exclude-module', 'jupyter',
    '--exclude-module', 'notebook',
    '--exclude-module', 'tkinter.test',
    '--collect-all', 'onnxruntime',
    '--collect-all', 'magika',
    '--runtime-hook', str(project_root / 'build' / 'hook_onnxruntime.py'),
    '--icon', str(project_root / 'res' / 'ProductIcon.ico'),
    '--add-data', f"{project_root / 'packages' / 'markitdown' / 'src' / 'markitdown'}{sep}markitdown",
    '--add-data', f"{project_root / 'res' / 'ProductIcon.ico'}{sep}res",
    '--paths', str(project_root / 'packages' / 'markitdown' / 'src'),
    '--windowed',
    str(project_root / 'gui' / 'main.py')
]

log_step("步骤 2/3: 执行打包")
log_info(f"PyInstaller 正在构建 {exe_name}...\n")

# 执行 PyInstaller
try:
    result = subprocess.run(cmd, cwd=str(project_root))
    
    if result.returncode == 0:
        log_step("步骤 3/3: 打包结果")
        log_success(f"打包成功！")
        
        # 单文件模式：exe 直接生成在 dist/ 目录下
        dist_output = project_root / 'dist'
        exe_file = dist_output / f"{exe_name}.exe"
        
        if exe_file.exists():
            file_size = exe_file.stat().st_size
            size_mb = file_size / (1024 * 1024)
            
            print(f"\n{'='*60}")
            log_info(f"输出位置: {exe_file}")
            log_info(f"文件大小: {size_mb:.2f} MB ({file_size:,} bytes)")
            log_info("单文件模式：直接将 exe 发给对方即可使用，无需安装 Python")
            print(f"{'='*60}\n")
        else:
            log_error("未找到生成的 exe 文件")
            print(f"{'='*60}\n")
    else:
        log_error(f"打包失败，退出码: {result.returncode}")
        sys.exit(result.returncode)
        
except FileNotFoundError:
    log_error("未找到 PyInstaller")
    log_info("请先安装: pip install pyinstaller")
    sys.exit(1)
except KeyboardInterrupt:
    log_error("用户取消打包")
    sys.exit(1)
