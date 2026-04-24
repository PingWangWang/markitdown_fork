# MarkItDown GUI 打包指南

## 🚀 快速开始

```bash
cd d:\Code\markitdown_fork\build
py -3 build_exe.py
```

## 📦 输出说明

打包完成后，产物在 `dist/` 目录（项目根目录）：

```
d:\Code\markitdown_fork\
├── build/                    ← 临时构建文件（打包后可删除）
├── dist/                     ← 最终产物
│   └── MarkItDown_v0.1.6b2_20260424-114409/
│       └── MarkItDown_v0.1.6b2_20260424-114409.exe  ← 可执行文件
└── MarkItDown_v0.1.6b2_20260424-114409.spec  ← PyInstaller 配置（可删除）
```

**直接拷贝 `dist/` 中的 exe 文件即可分发！**
