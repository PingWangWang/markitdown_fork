# PyInstaller 运行时 Hook —— 确保 onnxruntime 能找到其 Provider DLL
#
# --onefile 模式下所有文件解压到 sys._MEIPASS 临时目录。
# onnxruntime_pybind11_state.pyd 初始化时需要 onnxruntime.dll /
# onnxruntime_providers_shared.dll，若这些 DLL 未被提前加载进进程，
# Windows loader 找不到它们就会报"初始化例程失败"。
#
# 修复策略（三层保障，缺一不可）：
#   1. PATH 注入：让后续 LoadLibrary 能找到目录
#   2. AddDllDirectory：更高优先级的搜索路径（必须持有返回对象！）
#   3. ctypes 提前显式加载：在 onnxruntime 模块 import 之前把核心 DLL
#      加载进进程地址空间，之后 pyd 初始化时 loader 直接复用已加载的句柄
import os
import sys

if hasattr(sys, '_MEIPASS'):
    meipass = sys._MEIPASS

    # 可能存放 onnxruntime DLL 的目录（按优先级排列）
    dll_dirs = [
        meipass,
        os.path.join(meipass, 'onnxruntime', 'capi'),
        os.path.join(meipass, 'onnxruntime', 'backend'),
    ]
    dll_dirs = [d for d in dll_dirs if os.path.isdir(d)]

    # ── 层 1：PATH 注入 ──────────────────────────────────────────────
    os.environ['PATH'] = os.pathsep.join(dll_dirs) + os.pathsep + os.environ.get('PATH', '')

    if sys.platform == 'win32':
        import ctypes
        import ctypes.wintypes

        # ── 层 2：AddDllDirectory（必须持有返回对象） ─────────────────
        _dll_dir_handles = []
        for d in dll_dirs:
            try:
                _dll_dir_handles.append(os.add_dll_directory(d))
            except (AttributeError, OSError):
                pass

        # ── 层 3：ctypes 提前显式加载核心 DLL ────────────────────────
        # 加载顺序很重要：先加载被依赖的，再加载依赖方
        _core_dlls = [
            'onnxruntime_providers_shared.dll',  # 被 onnxruntime.dll 依赖
            'onnxruntime.dll',                   # 被 pybind11_state 依赖
        ]
        _preloaded = []  # 持有句柄，防止 GC 卸载
        for dll_name in _core_dlls:
            for d in dll_dirs:
                dll_path = os.path.join(d, dll_name)
                if os.path.isfile(dll_path):
                    try:
                        _preloaded.append(ctypes.WinDLL(dll_path))
                    except OSError:
                        pass
                    break  # 找到第一个即可，不重复加载
