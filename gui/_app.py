"""
MarkItDown GUI - 主应用类

包含 MarkItDownGUI 类，负责：
  - 窗口初始化与图标设置
  - 界面样式（颜色常量 + ttk 主题）
  - 界面构建（输入/输出区域、日志、底部链接）
  - 文件选择、目录操作
  - 文件处理（多线程转换）
  - 对话框委托（关于、覆盖确认）
"""
import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path

from _version import APP_VERSION
from _dialogs import show_about, ask_overwrite


# 文件后缀 → 可读类型名
_FILE_TYPE_MAP = {
    '.pdf':   'PDF 文档',
    '.docx':  'Word 文档',
    '.doc':   'Word 文档(旧版)',
    '.xlsx':  'Excel 表格',
    '.xls':   'Excel 表格(旧版)',
    '.pptx':  'PowerPoint 演示文稿',
    '.jpg':   'JPEG 图片',
    '.jpeg':  'JPEG 图片',
    '.png':   'PNG 图片',
    '.gif':   'GIF 图片',
    '.bmp':   'BMP 图片',
    '.html':  'HTML 网页',
    '.htm':   'HTML 网页',
    '.csv':   'CSV 数据',
    '.json':  'JSON 数据',
    '.xml':   'XML 数据',
    '.zip':   'ZIP 压缩包',
    '.epub':  'EPUB 电子书',
    '.wav':   'WAV 音频',
    '.mp3':   'MP3 音频',
    '.msg':   'Outlook 邮件',
    '.ipynb': 'Jupyter Notebook',
    '.rss':   'RSS 订阅',
    '.rtf':   'RTF 文档',
}


class MarkItDownGUI:

    # ── 初始化 ────────────────────────────────────────────────────────────────

    def __init__(self, root):
        self.root = root
        self.root.title(f"MarkItDown v{APP_VERSION}")

        window_width, window_height = 680, 500
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{window_width}x{window_height}+{(sw-window_width)//2}+{(sh-window_height)//2}")
        self.root.resizable(False, False)

        self._set_window_icon()

        self.input_files     = []
        self.output_dir      = tk.StringVar()
        self.image_mode = tk.StringVar(value='embed')  # 'file' | 'embed' | 'none'
        self.is_processing   = False
        self.last_output_file = None  # 最后一次转换的输出路径（用于"打开文件夹并选中"）

        self.setup_styles()
        self.create_widgets()
        self.setup_drag_drop()

        # 窗口完全显示后再次应用图标，确保任务栏图标生效
        self.root.after(100, self._set_window_icon)

    # ── 图标 ──────────────────────────────────────────────────────────────────

    def _get_icon_path(self):
        """返回 ProductIcon.ico 的路径，打包/开发环境均适用；找不到则返回 None"""
        meipass = getattr(sys, '_MEIPASS', None)
        p = Path(meipass) / 'res' / 'ProductIcon.ico' if meipass \
            else Path(__file__).parent.parent / 'res' / 'ProductIcon.ico'
        return p if p.exists() else None

    def _set_window_icon(self):
        """设置窗口图标（标题栏 & 任务栏）"""
        try:
            if sys.platform == 'win32':
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('MarkItDown.GUI.App')

            icon_path = self._get_icon_path()
            if icon_path:
                self.root.iconbitmap(default=str(icon_path))
                try:
                    from PIL import Image, ImageTk
                    img32 = Image.open(str(icon_path)).resize((32, 32), Image.LANCZOS)
                    self._taskbar_photo = ImageTk.PhotoImage(img32)
                    self.root.wm_iconphoto(True, self._taskbar_photo)
                except Exception:
                    pass
        except Exception:
            pass

    # ── 样式 ──────────────────────────────────────────────────────────────────

    def setup_styles(self):
        """定义配色常量并配置 ttk 主题"""
        self.C_BG         = '#F5F7FA'
        self.C_HEADER_BG  = '#4A90D9'
        self.C_HEADER_FG  = '#FFFFFF'
        self.C_PANEL_BG   = '#FFFFFF'
        self.C_LABEL_FG   = '#374151'
        self.C_ENTRY_BG   = '#EEF2FF'
        self.C_BTN_SEL    = '#4A90D9'
        self.C_BTN_SEL_A  = '#357ABD'
        self.C_BTN_RUN    = '#27AE60'
        self.C_BTN_RUN_A  = '#1E8449'
        self.C_BTN_OPEN   = '#E67E22'
        self.C_BTN_OPEN_A = '#CA6F1E'
        self.C_LOG_BG     = '#FFFFFF'
        self.C_LOG_FG     = '#000000'
        self.C_LINK       = '#2E86C1'
        self.C_LINK_RED   = '#E74C3C'
        self.C_BORDER     = '#D1D9E6'

        self.root.configure(bg=self.C_BG)
        s = ttk.Style()
        s.theme_use('clam')

        s.configure('.', background=self.C_BG, foreground=self.C_LABEL_FG,
                    font=('Microsoft YaHei UI', 9))
        s.configure('TFrame',       background=self.C_BG)
        s.configure('Panel.TFrame', background=self.C_PANEL_BG, relief='flat', borderwidth=1)
        s.configure('TLabel',       background=self.C_BG, foreground=self.C_LABEL_FG)
        s.configure('Field.TLabel', background=self.C_BG, foreground=self.C_LABEL_FG,
                    font=('Microsoft YaHei UI', 9))
        s.configure('Log.TLabel',   background=self.C_BG, foreground='#6B7280',
                    font=('Microsoft YaHei UI', 9))
        s.configure('Link.TLabel',  background=self.C_BG, foreground=self.C_LINK,
                    cursor='hand2', font=('Microsoft YaHei UI', 9, 'underline'))
        s.configure('TEntry', fieldbackground=self.C_ENTRY_BG, foreground='#1F2937',
                    bordercolor=self.C_BORDER, insertcolor=self.C_LABEL_FG)

        s.configure('Select.TButton', background=self.C_BTN_SEL, foreground='#FFFFFF',
                    font=('Microsoft YaHei UI', 9, 'bold'),
                    borderwidth=0, focusthickness=0, padding=(8, 4))
        s.map('Select.TButton',
              background=[('active', self.C_BTN_SEL_A), ('disabled', '#A0AEC0')],
              foreground=[('disabled', '#E2E8F0')])

        s.configure('Run.TButton', background=self.C_BTN_RUN, foreground='#FFFFFF',
                    font=('Microsoft YaHei UI', 10, 'bold'),
                    borderwidth=0, focusthickness=0, padding=(12, 6))
        s.map('Run.TButton',
              background=[('active', self.C_BTN_RUN_A), ('disabled', '#A0AEC0')],
              foreground=[('disabled', '#E2E8F0')])

        s.configure('Open.TButton', background=self.C_BTN_OPEN, foreground='#FFFFFF',
                    font=('Microsoft YaHei UI', 10, 'bold'),
                    borderwidth=0, focusthickness=0, padding=(12, 6))
        s.map('Open.TButton',
              background=[('active', self.C_BTN_OPEN_A)],
              foreground=[])

    # ── 界面构建 ──────────────────────────────────────────────────────────────

    def create_widgets(self):
        """构建主界面所有控件"""
        mf = ttk.Frame(self.root, padding="14 10 14 6")
        mf.pack(fill=tk.BOTH, expand=True)
        mf.columnconfigure(1, weight=1)
        row = 0

        # 选择待处理文件（改为列表）
        ttk.Label(mf, text="选择待处理文件:", style='Field.TLabel').grid(
            row=row, column=0, sticky=tk.NW, pady=4, padx=(0, 8))
        ff = ttk.Frame(mf);  ff.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        ff.columnconfigure(0, weight=1)
        
        # 文件列表框
        self.file_listbox = tk.Listbox(ff, height=5, font=('Microsoft YaHei UI', 9),
                                        bg=self.C_ENTRY_BG, fg='#1F2937',
                                        selectbackground=self.C_BTN_SEL,
                                        selectforeground='#FFFFFF',
                                        relief='flat', borderwidth=0)
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 6))
        
        # 右侧按钮
        btn_frame = ttk.Frame(ff)
        btn_frame.grid(row=0, column=1, sticky=tk.N)
        ttk.Button(btn_frame, text="添加文件", command=self.select_files,
                   style='Select.TButton', width=10).pack(pady=2)
        ttk.Button(btn_frame, text="删除选中", command=self.remove_selected_files,
                   style='Select.TButton', width=10).pack(pady=2)
        ttk.Button(btn_frame, text="清空列表", command=self.clear_file_list,
                   style='Select.TButton', width=10).pack(pady=2)
        
        ff.rowconfigure(0, weight=1)
        row += 1

        # 选择保存位置
        ttk.Label(mf, text="选择保存位置:", style='Field.TLabel').grid(
            row=row, column=0, sticky=tk.W, pady=4, padx=(0, 8))
        sf = ttk.Frame(mf);  sf.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        sf.columnconfigure(0, weight=1)
        ttk.Entry(sf, textvariable=self.output_dir, state='readonly').grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 6))
        ttk.Button(sf, text="保存位置", command=self.select_output_dir,
                   style='Select.TButton', width=10).grid(row=0, column=1)
        row += 1

        # 图片处理方式（适用于 DOCX / PPTX 等含图文档）
        ttk.Label(mf, text="图片处理方式:", style='Field.TLabel').grid(
            row=row, column=0, sticky=tk.W, pady=4, padx=(0, 8))
        rf = ttk.Frame(mf);  rf.grid(row=row, column=1, sticky=tk.W, pady=4)
        ttk.Radiobutton(rf, text="提取为文件（推荐）", variable=self.image_mode,
                        value='file').pack(side=tk.LEFT, padx=(0, 12))
        ttk.Radiobutton(rf, text="嵌入 base64",       variable=self.image_mode,
                        value='embed').pack(side=tk.LEFT, padx=(0, 12))
        ttk.Radiobutton(rf, text="忽略图片",           variable=self.image_mode,
                        value='none').pack(side=tk.LEFT)
        row += 1

        # 分割线
        ttk.Separator(mf, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=6)
        row += 1

        # 操作按钮
        bf = ttk.Frame(mf);  bf.grid(row=row, column=0, columnspan=2, pady=4)
        self.process_button = ttk.Button(bf, text="▶  开始处理",
                                         command=self.start_processing,
                                         style='Run.TButton', width=14)
        self.process_button.pack(side=tk.LEFT, padx=6)
        ttk.Button(bf, text="📂  打开输出目录",
                   command=self.open_output_dir,
                   style='Open.TButton', width=14).pack(side=tk.LEFT, padx=6)
        self.open_doc_button = ttk.Button(bf, text="📄  打开文档",
                                          command=self.open_last_document,
                                          style='Open.TButton', width=14,
                                          state='disabled')
        self.open_doc_button.pack(side=tk.LEFT, padx=6)
        row += 1

        # 日志区域
        ttk.Label(mf, text="处理日志:", style='Log.TLabel').grid(
            row=row, column=0, sticky=tk.NW, pady=(8, 2), padx=(0, 8))
        self.log_text = scrolledtext.ScrolledText(
            mf, height=8, wrap=tk.WORD, font=('Consolas', 9),
            bg=self.C_LOG_BG, fg=self.C_LOG_FG,
            insertbackground=self.C_LOG_FG,
            selectbackground='#2E86C1', selectforeground='#FFFFFF',
            relief='flat', borderwidth=0, state='disabled')
        self.log_text.grid(row=row, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(8, 2))
        mf.rowconfigure(row, weight=1)
        for tag, color in [('success', '#27AE60'), ('error',    '#E74C3C'),
                           ('info',    '#F39C12'), ('arrow',    '#F39C12'),
                           ('complete','#2980B9'), ('normal',   self.C_LOG_FG)]:
            self.log_text.tag_configure(tag, foreground=color)
        row += 1

        # 底部链接
        lf = ttk.Frame(mf)
        lf.grid(row=row, column=0, columnspan=2, pady=(4, 2), sticky=(tk.W, tk.E))
        lbl = ttk.Label(lf, text="软件教程及注意事项>>", style='Link.TLabel')
        lbl.pack(side=tk.LEFT)
        lbl.bind('<Button-1>', lambda e: self.show_about())

    # ── 日志 ──────────────────────────────────────────────────────────────────

    def log_message(self, message):
        self.log_text.configure(state='normal')
        s = message.strip()
        if   s.startswith(('✓', '✅')):                      tag = 'success'
        elif s.startswith(('✗', '❌')):                      tag = 'error'
        elif s.startswith('[') and ']' in s:                  tag = 'info'
        elif s.startswith(('→', '  →')):                     tag = 'arrow'
        elif s.startswith(('处理完成', '开始处理')):          tag = 'complete'
        else:                                                  tag = 'normal'
        self.log_text.insert(tk.END, message + '\n', tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    # ── 文件选择 & 目录操作 ───────────────────────────────────────────────────

    def select_files(self):
        filetypes = [
            ('所有支持的文件',
             '*.pdf *.docx *.doc *.xlsx *.pptx *.jpg *.jpeg *.png *.html *.csv *.json *.xml *.zip *.epub'),
            ('PDF 文件', '*.pdf'), ('Word 文件', '*.docx *.doc'), ('Excel 文件', '*.xlsx'),
            ('PowerPoint 文件', '*.pptx'), ('图片文件', '*.jpg *.jpeg *.png'),
            ('HTML 文件', '*.html'), ('所有文件', '*.*'),
        ]
        files = filedialog.askopenfilenames(title="选择要转换的文件", filetypes=filetypes)
        if not files:
            return
        # 添加到现有文件列表
        for f in files:
            if f not in self.input_files:
                self.input_files.append(f)
        self.update_file_listbox()
        # 如果还没有设置输出目录，使用第一个文件的目录
        if not self.output_dir.get() and self.input_files:
            self.output_dir.set(str(Path(self.input_files[0]).parent))

    def select_output_dir(self):
        d = filedialog.askdirectory(title="选择保存位置")
        if d:
            self.output_dir.set(d)

    def update_file_listbox(self):
        """更新文件列表框的显示"""
        self.file_listbox.delete(0, tk.END)
        for f in self.input_files:
            # 显示文件名，如果太长则截断
            name = Path(f).name
            if len(name) > 50:
                name = name[:47] + "..."
            self.file_listbox.insert(tk.END, name)

    def remove_selected_files(self):
        """删除选中的文件"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        # 从后往前删除，避免索引变化
        for index in reversed(selection):
            del self.input_files[index]
        self.update_file_listbox()

    def clear_file_list(self):
        """清空文件列表"""
        self.input_files.clear()
        self.output_dir.set('')
        self.update_file_listbox()

    def setup_drag_drop(self):
        """设置拖拽支持（Windows 平台）"""
        if sys.platform != 'win32':
            return
        
        try:
            # 使用 tkinterdnd2 库实现拖拽
            from tkinterdnd2 import DND_FILES
            
            # 为文件列表框绑定拖拽事件
            self.file_listbox.drop_target_register(DND_FILES)
            self.file_listbox.dnd_bind('<<Drop>>', self._handle_drop)
            
            # 也为整个窗口绑定拖拽
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self._handle_drop)
        except Exception:
            # 如果 tkinterdnd2 不可用，拖拽功能将不可用，但不影响其他功能
            pass

    def _handle_drop(self, event):
        """处理文件拖拽事件"""
        try:
            # 获取拖拽的文件路径
            files = self.root.splitlist(event.data)
            
            # 添加有效的文件
            added = False
            for file_path in files:
                # 检查是否是支持的文件格式
                ext = Path(file_path).suffix.lower()
                if ext in _FILE_TYPE_MAP or ext in ('.txt', '.md', '.rtf'):
                    if file_path not in self.input_files:
                        self.input_files.append(file_path)
                        added = True
            
            if added:
                self.update_file_listbox()
                # 如果还没有设置输出目录，使用第一个文件的目录
                if not self.output_dir.get() and self.input_files:
                    self.output_dir.set(str(Path(self.input_files[0]).parent))
        except Exception as e:
            self.log_message(f"拖拽文件失败: {e}")

    def open_output_dir(self):
        out = self.output_dir.get()
        if not out:
            messagebox.showwarning("警告", "请先选择保存位置！");  return
        if not os.path.exists(out):
            messagebox.showerror("错误", f"目录不存在：{out}");  return
        try:
            if sys.platform == 'win32':
                if self.last_output_file and os.path.exists(self.last_output_file):
                    subprocess.run(['explorer', '/select,', self.last_output_file])
                else:
                    os.startfile(out)
            elif sys.platform == 'darwin':
                if self.last_output_file and os.path.exists(self.last_output_file):
                    subprocess.run(['open', '-R', self.last_output_file])
                else:
                    subprocess.run(['open', out])
            else:
                os.system(f'xdg-open "{out}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录：{e}")

    # ── 文件处理 ──────────────────────────────────────────────────────────────

    def start_processing(self):
        if not self.input_files:
            messagebox.showwarning("警告", "请先选择要处理的文件！");  return
        if not self.output_dir.get():
            messagebox.showwarning("警告", "请选择保存位置！");  return
        self.process_button.configure(state='disabled')
        self.is_processing = True
        t = threading.Thread(target=self.process_files, daemon=True)
        t.start()

    def process_files(self):
        """后台线程：批量转换文件"""
        self._overwrite_all = False
        self._skip_all      = False
        try:
            total = len(self.input_files)
            self.log_message(f"开始处理 {total} 个文件...")
            for i, file_path in enumerate(self.input_files, 1):
                if not self.is_processing:
                    self.log_message("处理已取消");  break
                ext = Path(file_path).suffix.lower()
                file_type = _FILE_TYPE_MAP.get(ext, f'{ext.upper()} 文件')
                self.log_message(f"[{i}/{total}] 正在转换: {Path(file_path).name} ({file_type})")
                self.convert_file(file_path)
                self.log_message(f"✓ 转换成功: {Path(file_path).stem}.md")
            self.log_message(f"\n处理完成！共处理 {total} 个文件。")
        except Exception as e:
            self.log_message(f"\n✗ 处理失败: {e}")
        finally:
            self.root.after(0, self.processing_complete)

    def convert_file(self, file_path):
        """转换单个文件并写入输出目录"""
        try:
            from markitdown import MarkItDown
            self.log_message("  → 初始化 MarkItDown 转换器...")

            stem = Path(file_path).stem
            ext  = Path(file_path).suffix.lower()
            convert_kwargs = {}

            # 根据用户选择的图片处理方式，对含图片的格式传入对应参数
            mode = self.image_mode.get()
            if ext in ('.docx', '.doc'):
                if mode == 'file':
                    images_dir = Path(self.output_dir.get()) / f"{stem}_images"
                    convert_kwargs['docx_images_dir'] = str(images_dir)
                elif mode == 'embed':
                    convert_kwargs['docx_embed_images'] = True
            elif ext in ('.pptx',):
                if mode == 'file':
                    images_dir = Path(self.output_dir.get()) / f"{stem}_images"
                    convert_kwargs['pptx_images_dir'] = str(images_dir)
                elif mode == 'embed':
                    convert_kwargs['pptx_embed_images'] = True
            elif ext in ('.epub',):
                if mode == 'file':
                    images_dir = Path(self.output_dir.get()) / f"{stem}_images"
                    convert_kwargs['epub_images_dir'] = str(images_dir)
                elif mode == 'embed':
                    convert_kwargs['epub_embed_images'] = True
            else:
                # 其他格式（HTML 等）：嵌入模式透传 keep_data_uris
                if mode == 'embed':
                    convert_kwargs['keep_data_uris'] = True

            result = MarkItDown().convert(file_path, **convert_kwargs)
            output_file = Path(self.output_dir.get()) / f"{stem}.md"
            self.log_message(f"  → 保存结果到: {output_file}")
            if output_file.exists() and not self._ask_overwrite(output_file.name):
                self.log_message(f"  ✗ 已跳过: {output_file.name}");  return
            output_file.write_text(result.text_content, encoding='utf-8')
            self.last_output_file = str(output_file)
        except ImportError as e:
            raise RuntimeError(f"模块导入失败: {e}")
        except Exception as e:
            raise RuntimeError(f"转换文件 {file_path} 失败: {e}")

    def processing_complete(self):
        self.is_processing = False
        self.process_button.configure(state='normal')
        # 如果只转换了一个文件且成功，启用"打开文档"按钮
        if len(self.input_files) == 1 and self.last_output_file and os.path.exists(self.last_output_file):
            self.open_doc_button.configure(state='normal')
        else:
            self.open_doc_button.configure(state='disabled')

    # ── 对话框（委托给 _dialogs 模块）────────────────────────────────────────

    def _ask_overwrite(self, filename):
        return ask_overwrite(self, filename)

    def show_about(self):
        show_about(self)

    def open_last_document(self):
        """打开最后转换的文档"""
        if not self.last_output_file or not os.path.exists(self.last_output_file):
            messagebox.showwarning("警告", "没有可打开的文档！");  return
        try:
            if sys.platform == 'win32':
                os.startfile(self.last_output_file)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self.last_output_file])
            else:
                subprocess.run(['xdg-open', self.last_output_file])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文档：{e}")

    def show_contact(self):
        messagebox.showinfo("联系我们",
            "如有问题或建议，请访问：\n\n"
            "GitHub: https://github.com/microsoft/markitdown\n\n"
            "或提交 Issue 获取帮助。")
