"""
MarkItDown GUI - 版本检测
"""
import sys
from pathlib import Path


def _get_version():
    """获取 MarkItDown 版本号，支持打包环境和开发环境"""
    debug_info = []

    def _read_version_from_file(about_file):
        with open(about_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"\'')
        return None

    # 方法1a: PyInstaller 打包环境 —— 从 _MEIPASS 读取 __about__.py
    try:
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            about_file = Path(meipass) / 'markitdown' / '__about__.py'
            if about_file.exists():
                v = _read_version_from_file(about_file)
                if v:
                    debug_info.append(f"✓ 方法1a成功(MEIPASS): {v}")
                    return v, '\n'.join(debug_info)
    except Exception as e:
        debug_info.append(f"✗ 方法1a失败: {e}")

    # 方法1b: 开发环境 —— 从源码目录读取
    try:
        project_root = Path(__file__).parent.parent
        about_file = project_root / 'packages' / 'markitdown' / 'src' / 'markitdown' / '__about__.py'
        if about_file.exists():
            v = _read_version_from_file(about_file)
            if v:
                debug_info.append(f"✓ 方法1b成功(源码): {v}")
                return v, '\n'.join(debug_info)
    except Exception as e:
        debug_info.append(f"✗ 方法1b失败: {e}")

    debug_info.append("✗ 所有方法失败，返回默认版本 unknown")
    return "unknown", '\n'.join(debug_info)


APP_VERSION, VERSION_DEBUG = _get_version()
