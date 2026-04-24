"""
MarkItDown GUI 应用程序
提供图形界面，让用户可以方便地将文件转换为 Markdown
"""

import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path

# PyInstaller 打包环境：将 _MEIPASS 加入 sys.path，确保 markitdown 可被正常导入
if getattr(sys, '_MEIPASS', None):
    _meipass = sys._MEIPASS
    if _meipass not in sys.path:
        sys.path.insert(0, _meipass)

# 获取 MarkItDown 版本号
def _get_version():
    """获取 MarkItDown 版本号，支持多种环境"""
    debug_info = []

    def _read_version_from_file(about_file):
        """从 __about__.py 文件中解析版本号"""
        with open(about_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"\'')
        return None

    # 方法1a: PyInstaller 打包环境 —— 从 sys._MEIPASS 中读取打包进去的 __about__.py
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

    # 方法1b: 开发环境 —— 从本地源码文件直接读取
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

    # 默认版本
    debug_info.append("✗ 所有方法失败，返回默认版本 unknown")
    return "unknown", '\n'.join(debug_info)

APP_VERSION, VERSION_DEBUG = _get_version()


class MarkItDownGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"MarkItDown v{APP_VERSION}")
        
        # 设置窗口尺寸
        window_width = 680
        window_height = 500
        
        # 计算居中位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)
        
        # 设置窗口图标（任务栏 & 标题栏）
        self._set_window_icon()
        
        # 变量
        self.input_files = []
        self.output_dir = tk.StringVar()
        self.is_processing = False
        self.last_output_file = None   # 最后一次转换输出的文件路径
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 延迟重新应用图标（窗口完全显示后任务栏图标才能正确生效）
        self.root.after(100, self._set_window_icon)
        
    def _get_icon_path(self):
        """获取图标文件路径（打包环境和开发环境均适用）"""
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            p = Path(meipass) / 'res' / 'ProductIcon.ico'
        else:
            p = Path(__file__).parent.parent / 'res' / 'ProductIcon.ico'
        return p if p.exists() else None

    def _set_window_icon(self):
        """设置窗口图标（任务栏 & 标题栏）"""
        try:
            if sys.platform == 'win32':
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('MarkItDown.GUI.App')

            icon_path = self._get_icon_path()
            if icon_path:
                # default= 参数确保后续所有子窗口也继承该图标，同时对任务栏更可靠
                self.root.iconbitmap(default=str(icon_path))
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(str(icon_path)).resize((32, 32), Image.LANCZOS)
                    self._taskbar_photo = ImageTk.PhotoImage(img)
                    self.root.wm_iconphoto(True, self._taskbar_photo)
                    img_small = Image.open(str(icon_path)).resize((16, 16), Image.LANCZOS)
                    self._icon_image = ImageTk.PhotoImage(img_small)
                except Exception:
                    self._icon_image = None
            else:
                self._icon_image = None
        except Exception:
            self._icon_image = None
    
    def setup_styles(self):
        """设置界面样式"""
        # 配色常量
        self.C_BG        = '#F5F7FA'   # 窗口背景：浅灰白
        self.C_HEADER_BG = '#4A90D9'   # 标题栏背景：蓝色
        self.C_HEADER_FG = '#FFFFFF'   # 标题栏文字：白色
        self.C_PANEL_BG  = '#FFFFFF'   # 面板背景：白色
        self.C_LABEL_FG  = '#374151'   # 普通标签：深灰
        self.C_ENTRY_BG  = '#EEF2FF'   # 输入框背景：淡蓝
        self.C_BTN_SEL   = '#4A90D9'   # 选择按钮：蓝色
        self.C_BTN_SEL_A = '#357ABD'   # 选择按钮 hover
        self.C_BTN_RUN   = '#27AE60'   # 开始处理：绿色
        self.C_BTN_RUN_A = '#1E8449'   # 开始处理 hover
        self.C_BTN_OPEN  = '#E67E22'   # 打开目录：橙色
        self.C_BTN_OPEN_A= '#CA6F1E'   # 打开目录 hover
        self.C_LOG_BG    = '#1E2533'   # 日志背景：深蓝灰
        self.C_LOG_FG    = '#D4E6F1'   # 日志文字：淡蓝白
        self.C_LINK      = '#2E86C1'   # 链接：蓝色
        self.C_LINK_RED  = '#E74C3C'   # 联系链接：红色
        self.C_BORDER    = '#D1D9E6'   # 分割线

        self.root.configure(bg=self.C_BG)

        style = ttk.Style()
        style.theme_use('clam')

        # 全局背景
        style.configure('.',
            background=self.C_BG,
            foreground=self.C_LABEL_FG,
            font=('Microsoft YaHei UI', 9))

        # Frame
        style.configure('TFrame', background=self.C_BG)
        style.configure('Panel.TFrame', background=self.C_PANEL_BG,
            relief='flat', borderwidth=1)
        style.configure('Header.TFrame', background=self.C_HEADER_BG)

        # Label
        style.configure('TLabel', background=self.C_BG, foreground=self.C_LABEL_FG)
        style.configure('Header.TLabel',
            background=self.C_HEADER_BG, foreground=self.C_HEADER_FG,
            font=('Microsoft YaHei UI', 13, 'bold'))
        style.configure('Field.TLabel',
            background=self.C_BG, foreground=self.C_LABEL_FG,
            font=('Microsoft YaHei UI', 9))
        style.configure('Log.TLabel',
            background=self.C_BG, foreground='#6B7280',
            font=('Microsoft YaHei UI', 9))
        style.configure('Link.TLabel',
            background=self.C_BG, foreground=self.C_LINK, cursor='hand2',
            font=('Microsoft YaHei UI', 9, 'underline'))
        style.configure('LinkRed.TLabel',
            background=self.C_BG, foreground=self.C_LINK_RED, cursor='hand2',
            font=('Microsoft YaHei UI', 9, 'underline'))

        # Entry
        style.configure('TEntry',
            fieldbackground=self.C_ENTRY_BG,
            foreground='#1F2937',
            bordercolor=self.C_BORDER,
            insertcolor=self.C_LABEL_FG)

        # 选择文件/保存位置按钮（蓝色）
        style.configure('Select.TButton',
            background=self.C_BTN_SEL, foreground='#FFFFFF',
            font=('Microsoft YaHei UI', 9, 'bold'),
            borderwidth=0, focusthickness=0, padding=(8, 4))
        style.map('Select.TButton',
            background=[('active', self.C_BTN_SEL_A), ('disabled', '#A0AEC0')],
            foreground=[('disabled', '#E2E8F0')])

        # 开始处理按钮（绿色）
        style.configure('Run.TButton',
            background=self.C_BTN_RUN, foreground='#FFFFFF',
            font=('Microsoft YaHei UI', 10, 'bold'),
            borderwidth=0, focusthickness=0, padding=(12, 6))
        style.map('Run.TButton',
            background=[('active', self.C_BTN_RUN_A), ('disabled', '#A0AEC0')],
            foreground=[('disabled', '#E2E8F0')])

        # 打开目录按钮（橙色）
        style.configure('Open.TButton',
            background=self.C_BTN_OPEN, foreground='#FFFFFF',
            font=('Microsoft YaHei UI', 10, 'bold'),
            borderwidth=0, focusthickness=0, padding=(12, 6))
        style.map('Open.TButton',
            background=[('active', self.C_BTN_OPEN_A)],
            foreground=[])
        
    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="14 10 14 6")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)

        row = 0

        # 选择待处理文件
        ttk.Label(main_frame, text="选择待处理文件:", style='Field.TLabel').grid(
            row=row, column=0, sticky=tk.W, pady=4, padx=(0, 8)
        )
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        file_frame.columnconfigure(0, weight=1)
        self.file_entry = ttk.Entry(file_frame, state='readonly')
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 6))
        ttk.Button(file_frame, text="选择文件", command=self.select_files,
                   style='Select.TButton', width=10).grid(row=0, column=1)

        row += 1

        # 选择保存位置
        ttk.Label(main_frame, text="选择保存位置:", style='Field.TLabel').grid(
            row=row, column=0, sticky=tk.W, pady=4, padx=(0, 8)
        )
        save_frame = ttk.Frame(main_frame)
        save_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        save_frame.columnconfigure(0, weight=1)
        ttk.Entry(save_frame, textvariable=self.output_dir, state='readonly').grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 6)
        )
        ttk.Button(save_frame, text="保存位置", command=self.select_output_dir,
                   style='Select.TButton', width=10).grid(row=0, column=1)

        row += 1

        # 分割线
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=6
        )
        row += 1

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=4)
        self.process_button = ttk.Button(button_frame, text="▶  开始处理",
                                         command=self.start_processing,
                                         style='Run.TButton', width=14)
        self.process_button.pack(side=tk.LEFT, padx=6)
        self.open_dir_button = ttk.Button(button_frame, text="📂  打开输出目录",
                                          command=self.open_output_dir,
                                          style='Open.TButton', width=14)
        self.open_dir_button.pack(side=tk.LEFT, padx=6)

        row += 1

        # 日志标签
        ttk.Label(main_frame, text="处理日志:", style='Log.TLabel').grid(
            row=row, column=0, sticky=tk.NW, pady=(8, 2), padx=(0, 8)
        )
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            main_frame, height=8, wrap=tk.WORD,
            font=('Consolas', 9),
            bg=self.C_LOG_BG, fg=self.C_LOG_FG,
            insertbackground=self.C_LOG_FG,
            selectbackground='#2E86C1', selectforeground='#FFFFFF',
            relief='flat', borderwidth=0,
            state='disabled')
        self.log_text.grid(row=row, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(8, 2))
        main_frame.rowconfigure(row, weight=1)
        # 日志配色标签
        self.log_text.tag_configure('success',  foreground='#2ECC71')   # 绿色 - 成功
        self.log_text.tag_configure('error',    foreground='#E74C3C')   # 红色 - 错误
        self.log_text.tag_configure('info',     foreground='#5DADE2')   # 蓝色 - 进度信息
        self.log_text.tag_configure('arrow',    foreground='#F0B429')   # 黄色 - 操作步骤
        self.log_text.tag_configure('complete', foreground='#A9CCE3')   # 淡蓝 - 完成汇总
        self.log_text.tag_configure('normal',   foreground=self.C_LOG_FG)

        row += 1

        # 底部链接
        link_frame = ttk.Frame(main_frame)
        link_frame.grid(row=row, column=0, columnspan=2, pady=(4, 2), sticky=(tk.W, tk.E))
        about_link = ttk.Label(link_frame, text="软件教程及注意事项>>",
                               style='Link.TLabel')
        about_link.pack(side=tk.LEFT)
        about_link.bind('<Button-1>', lambda e: self.show_about())
        
    def log_message(self, message):
        """输出日志消息"""
        self.log_text.configure(state='normal')
        # 根据内容自动选择颜色标签
        stripped = message.strip()
        if stripped.startswith('✓') or stripped.startswith('✅'):
            tag = 'success'
        elif stripped.startswith('✗') or stripped.startswith('❌'):
            tag = 'error'
        elif stripped.startswith('[') and ']' in stripped:  # [i/n] 进度行
            tag = 'info'
        elif stripped.startswith('→') or stripped.startswith('  →'):
            tag = 'arrow'
        elif stripped.startswith('处理完成') or stripped.startswith('开始处理'):
            tag = 'complete'
        else:
            tag = 'normal'
        self.log_text.insert(tk.END, message + '\n', tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
    
    def select_files(self):
        """选择文件"""
        filetypes = [
            ('所有支持的文件', '*.pdf *.docx *.xlsx *.pptx *.jpg *.jpeg *.png *.html *.csv *.json *.xml *.zip *.epub'),
            ('PDF 文件', '*.pdf'),
            ('Word 文件', '*.docx'),
            ('Excel 文件', '*.xlsx'),
            ('PowerPoint 文件', '*.pptx'),
            ('图片文件', '*.jpg *.jpeg *.png'),
            ('HTML 文件', '*.html'),
            ('所有文件', '*.*')
        ]
        
        files = filedialog.askopenfilenames(
            title="选择要转换的文件",
            filetypes=filetypes
        )
        
        if files:
            self.input_files = list(files)
            # 显示第一个文件，如果有多个则显示数量
            if len(files) == 1:
                self.file_entry.configure(state='normal')
                self.file_entry.delete(0, tk.END)
                self.file_entry.insert(0, files[0])
                self.file_entry.configure(state='readonly')
            else:
                self.file_entry.configure(state='normal')
                self.file_entry.delete(0, tk.END)
                self.file_entry.insert(0, f"已选择 {len(files)} 个文件")
                self.file_entry.configure(state='readonly')
            
            # 始终跟随所选文件更新输出目录
            self.output_dir.set(str(Path(files[0]).parent))
                
    def select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择保存位置")
        if directory:
            self.output_dir.set(directory)
    
    def open_output_dir(self):
        """打开输出目录"""
        output_dir = self.output_dir.get()
        
        if not output_dir:
            messagebox.showwarning("警告", "请先选择保存位置！")
            return
        
        if not os.path.exists(output_dir):
            messagebox.showerror("错误", f"目录不存在：{output_dir}")
            return
        
        try:
            # Windows 系统：若有最后输出文件则选中它，否则只打开目录
            if sys.platform == 'win32':
                if self.last_output_file and os.path.exists(self.last_output_file):
                    subprocess.run(['explorer', '/select,', self.last_output_file])
                else:
                    os.startfile(output_dir)
            # macOS 系统
            elif sys.platform == 'darwin':
                if self.last_output_file and os.path.exists(self.last_output_file):
                    subprocess.run(['open', '-R', self.last_output_file])
                else:
                    subprocess.run(['open', output_dir])
            # Linux 系统
            else:
                os.system(f'xdg-open "{output_dir}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录：{str(e)}")
            
    def start_processing(self):
        """开始处理"""
        if not self.input_files:
            messagebox.showwarning("警告", "请先选择要处理的文件！")
            return
            
        if not self.output_dir.get():
            messagebox.showwarning("警告", "请选择保存位置！")
            return
            
        # 禁用按钮
        self.process_button.configure(state='disabled')
        self.is_processing = True
        
        # 在新线程中处理
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()
        
    def process_files(self):
        """处理文件（在后台线程中运行）"""
        self._overwrite_all = False   # 每次批量开始时重置
        self._skip_all = False         # 每次批量开始时重置
        try:
            total = len(self.input_files)
            
            self.log_message(f"开始处理 {total} 个文件...")
            
            for i, file_path in enumerate(self.input_files, 1):
                if not self.is_processing:
                    self.log_message("处理已取消")
                    break
                    
                # 调用 MarkItDown 转换（自动识别文件类型）
                file_type = self._detect_file_type(file_path)
                self.log_message(f"[{i}/{total}] 正在转换: {Path(file_path).name} ({file_type})")
                
                self.convert_file(file_path)
                
                self.log_message(f"✓ 转换成功: {Path(file_path).stem}.md")
                
            # 完成
            self.log_message(f"\n处理完成！共处理 {total} 个文件。")
            self.root.after(0, self.processing_complete)
            
        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            self.log_message(f"\n✗ {error_msg}")
            self.root.after(0, self.processing_complete)
            
    def convert_file(self, file_path):
        """转换单个文件"""
        try:
            from markitdown import MarkItDown
            
            # 自动识别文件类型
            file_type = self._detect_file_type(file_path)
            
            self.log_message(f"  → 初始化 MarkItDown 转换器...")
            # 不使用 enable_plugins 参数，默认启用内置转换器
            md = MarkItDown()
            
            self.log_message(f"  → 开始转换文件...")
            result = md.convert(file_path)
            
            # 生成输出文件名
            input_path = Path(file_path)
            output_file = Path(self.output_dir.get()) / f"{input_path.stem}.md"
            
            # 保存结果
            self.log_message(f"  → 保存结果到: {output_file}")
            if output_file.exists():
                if not self._ask_overwrite(output_file.name):
                    self.log_message(f"  ✗ 已跳过: {output_file.name}")
                    return
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.text_content)
            self.last_output_file = str(output_file)
                
        except ImportError as e:
            raise Exception(f"模块导入失败: {str(e)}")
        except Exception as e:
            raise Exception(f"转换文件 {file_path} 失败: {str(e)}")
    
    def _detect_file_type(self, file_path):
        """自动识别文件类型"""
        from pathlib import Path
        
        ext = Path(file_path).suffix.lower()
        
        # 文件类型映射
        type_mapping = {
            '.pdf': 'PDF 文档',
            '.docx': 'Word 文档',
            '.xlsx': 'Excel 表格',
            '.xls': 'Excel 表格(旧版)',
            '.pptx': 'PowerPoint 演示文稿',
            '.jpg': 'JPEG 图片',
            '.jpeg': 'JPEG 图片',
            '.png': 'PNG 图片',
            '.gif': 'GIF 图片',
            '.bmp': 'BMP 图片',
            '.html': 'HTML 网页',
            '.htm': 'HTML 网页',
            '.csv': 'CSV 数据',
            '.json': 'JSON 数据',
            '.xml': 'XML 数据',
            '.zip': 'ZIP 压缩包',
            '.epub': 'EPUB 电子书',
            '.wav': 'WAV 音频',
            '.mp3': 'MP3 音频',
            '.msg': 'Outlook 邮件',
            '.ipynb': 'Jupyter Notebook',
            '.rss': 'RSS 订阅',
            '.rtf': 'RTF 文档',
        }
        
        return type_mapping.get(ext, f'{ext.upper()} 文件')
            
    def _ask_overwrite(self, filename):
        """在主线程弹出覆盖确认对话框（自定义风格），返回 True/False"""
        # 已选择「全部覆盖」则直接通过
        if getattr(self, '_overwrite_all', False):
            return True
        # 已选择「全部跳过」则直接跳过
        if getattr(self, '_skip_all', False):
            return False

        result = [False]
        event = threading.Event()
        is_multi = len(self.input_files) > 1

        def _show():
            dlg = tk.Toplevel(self.root)
            dlg.overrideredirect(True)
            dlg.configure(bg=self.C_BG)
            dlg.resizable(False, False)

            # 顶部标题栏
            header = tk.Frame(dlg, bg='#E67E22', height=36)
            header.pack(fill=tk.X)
            header.pack_propagate(False)
            tk.Label(header, text="文件已存在", bg='#E67E22', fg='#FFFFFF',
                     font=('Microsoft YaHei UI', 10, 'bold')).pack(side=tk.LEFT, padx=12, pady=6)

            # 内容区
            body = tk.Frame(dlg, bg=self.C_BG, padx=20, pady=16)
            body.pack(fill=tk.BOTH)
            tk.Label(body, text=f"「{filename}」已存在，是否覆盖？",
                     bg=self.C_BG, fg=self.C_LABEL_FG,
                     font=('Microsoft YaHei UI', 10),
                     wraplength=340, justify='left').pack(anchor=tk.W)

            # 按钮区
            btn_frame = tk.Frame(dlg, bg=self.C_BG, pady=10)
            btn_frame.pack()

            def on_overwrite_one():
                result[0] = True
                dlg.destroy()

            def on_overwrite_all():
                self._overwrite_all = True
                result[0] = True
                dlg.destroy()

            def on_skip():
                result[0] = False
                dlg.destroy()

            def on_skip_all():
                self._skip_all = True
                result[0] = False
                dlg.destroy()

            if is_multi:
                # 多文件：本次覆盖 | 全部覆盖 | 跳过
                btn1 = tk.Button(btn_frame, text="本次覆盖", width=8,
                    bg=self.C_BTN_RUN, fg='#FFFFFF', relief='flat',
                    font=('Microsoft YaHei UI', 9, 'bold'),
                    cursor='hand2', command=on_overwrite_one)
                btn1.pack(side=tk.LEFT, padx=6)
                btn1.bind('<Enter>', lambda e: btn1.config(bg=self.C_BTN_RUN_A))
                btn1.bind('<Leave>', lambda e: btn1.config(bg=self.C_BTN_RUN))

                btn2 = tk.Button(btn_frame, text="全部覆盖", width=8,
                    bg='#8E44AD', fg='#FFFFFF', relief='flat',
                    font=('Microsoft YaHei UI', 9, 'bold'),
                    cursor='hand2', command=on_overwrite_all)
                btn2.pack(side=tk.LEFT, padx=6)
                btn2.bind('<Enter>', lambda e: btn2.config(bg='#6C3483'))
                btn2.bind('<Leave>', lambda e: btn2.config(bg='#8E44AD'))

                btn3 = tk.Button(btn_frame, text="本次跳过", width=8,
                    bg=self.C_BTN_SEL, fg='#FFFFFF', relief='flat',
                    font=('Microsoft YaHei UI', 9, 'bold'),
                    cursor='hand2', command=on_skip)
                btn3.pack(side=tk.LEFT, padx=6)
                btn3.bind('<Enter>', lambda e: btn3.config(bg=self.C_BTN_SEL_A))
                btn3.bind('<Leave>', lambda e: btn3.config(bg=self.C_BTN_SEL))

                btn4 = tk.Button(btn_frame, text="全部跳过", width=8,
                    bg='#7F8C8D', fg='#FFFFFF', relief='flat',
                    font=('Microsoft YaHei UI', 9, 'bold'),
                    cursor='hand2', command=on_skip_all)
                btn4.pack(side=tk.LEFT, padx=6)
                btn4.bind('<Enter>', lambda e: btn4.config(bg='#626567'))
                btn4.bind('<Leave>', lambda e: btn4.config(bg='#7F8C8D'))
            else:
                # 单文件：覆盖 | 跳过
                btn1 = tk.Button(btn_frame, text="覆  盖", width=8,
                    bg=self.C_BTN_RUN, fg='#FFFFFF', relief='flat',
                    font=('Microsoft YaHei UI', 9, 'bold'),
                    cursor='hand2', command=on_overwrite_one)
                btn1.pack(side=tk.LEFT, padx=8)
                btn1.bind('<Enter>', lambda e: btn1.config(bg=self.C_BTN_RUN_A))
                btn1.bind('<Leave>', lambda e: btn1.config(bg=self.C_BTN_RUN))

                btn3 = tk.Button(btn_frame, text="跳  过", width=8,
                    bg=self.C_BTN_SEL, fg='#FFFFFF', relief='flat',
                    font=('Microsoft YaHei UI', 9, 'bold'),
                    cursor='hand2', command=on_skip)
                btn3.pack(side=tk.LEFT, padx=8)
                btn3.bind('<Enter>', lambda e: btn3.config(bg=self.C_BTN_SEL_A))
                btn3.bind('<Leave>', lambda e: btn3.config(bg=self.C_BTN_SEL))

            # 居中显示
            dlg.update_idletasks()
            w, h = dlg.winfo_width(), dlg.winfo_height()
            rx = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
            ry = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
            dlg.geometry(f'+{rx}+{ry}')

            dlg.grab_set()
            dlg.wait_window()
            event.set()

        self.root.after(0, _show)
        event.wait()
        return result[0]

    def processing_complete(self):
        """处理完成"""
        self.is_processing = False
        self.process_button.configure(state='normal')
        
    def show_about(self):
        """显示关于信息（自定义风格）"""
        dlg = tk.Toplevel(self.root)
        dlg.overrideredirect(True)
        dlg.configure(bg=self.C_BG)
        dlg.resizable(False, False)

        # 顶部标题栏
        header = tk.Frame(dlg, bg=self.C_HEADER_BG, height=46)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=f"关于  MarkItDown v{APP_VERSION}",
                 bg=self.C_HEADER_BG, fg=self.C_HEADER_FG,
                 font=('Microsoft YaHei UI', 12, 'bold')).pack(side=tk.LEFT, padx=16, pady=8)

        # 内容区
        body = tk.Frame(dlg, bg=self.C_BG, padx=24, pady=16)
        body.pack(fill=tk.BOTH)

        sections = [
            ("功能", [
                "支持 PDF、Word、Excel、PowerPoint 等格式转换为 Markdown",
                "批量文件处理",
                "简单易用的图形界面",
            ]),
            ("使用方法", [
                "1. 选择要转换的文件",
                "2. 选择保存位置",
                "3. 点击「开始处理」",
            ]),
            ("注意事项", [
                "本程序为独立可执行文件，无需安装 Python 或任何依赖",
                "转换大文件时请耐心等待，程序不会卡死",
                "输出的 Markdown 文件保存在所选的保存位置目录中",
            ]),
            ("项目来源", [
                "项目: https://github.com/microsoft/markitdown",
            ]),
        ]

        for title, items in sections:
            tk.Label(body, text=title, bg=self.C_BG, fg=self.C_HEADER_BG,
                     font=('Microsoft YaHei UI', 10, 'bold')).pack(anchor=tk.W, pady=(8, 2))
            for item in items:
                tk.Label(body, text=f"  • {item}", bg=self.C_BG, fg=self.C_LABEL_FG,
                         font=('Microsoft YaHei UI', 9), justify='left').pack(anchor=tk.W)

        # 底部分割线 + 确定按钮
        tk.Frame(dlg, bg=self.C_BORDER, height=1).pack(fill=tk.X, padx=0, pady=(8, 0))
        btn_frame = tk.Frame(dlg, bg=self.C_BG, pady=10)
        btn_frame.pack()
        ok_btn = tk.Button(btn_frame, text="确  定", width=10,
                           bg=self.C_BTN_SEL, fg='#FFFFFF', relief='flat',
                           font=('Microsoft YaHei UI', 9, 'bold'),
                           cursor='hand2', command=dlg.destroy)
        ok_btn.pack()
        ok_btn.bind('<Enter>', lambda e: ok_btn.config(bg=self.C_BTN_SEL_A))
        ok_btn.bind('<Leave>', lambda e: ok_btn.config(bg=self.C_BTN_SEL))

        # 居中显示
        dlg.update_idletasks()
        w, h = dlg.winfo_width(), dlg.winfo_height()
        rx = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        ry = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        dlg.geometry(f'+{rx}+{ry}')
        dlg.grab_set()
        
    def show_contact(self):
        """显示联系信息"""
        contact_text = """如有问题或建议，请访问：

GitHub: https://github.com/microsoft/markitdown

或提交 Issue 获取帮助。"""
        messagebox.showinfo("联系我们", contact_text)


def main():
    root = tk.Tk()
    app = MarkItDownGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
