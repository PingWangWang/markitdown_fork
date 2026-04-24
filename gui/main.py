"""
MarkItDown GUI - 程序入口

模块结构：
  _version.py   版本检测
  _dialogs.py   对话框（关于、覆盖确认）
  _app.py       主应用类 MarkItDownGUI
"""
import sys
import os

# 确保 gui/ 目录在 sys.path（开发环境 & PyInstaller 均适用）
_gui_dir = os.path.dirname(os.path.abspath(__file__))
if _gui_dir not in sys.path:
    sys.path.insert(0, _gui_dir)

# PyInstaller 打包环境：将 _MEIPASS 加入 sys.path
if getattr(sys, '_MEIPASS', None) and sys._MEIPASS not in sys.path:
    sys.path.insert(0, sys._MEIPASS)

import tkinter as tk
from _app import MarkItDownGUI


def main():
    root = tk.Tk()
    MarkItDownGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
