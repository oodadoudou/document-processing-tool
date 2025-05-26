# gui_app.py
import sys
import os
import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path

# --- 全局日志设置 ---
# 此日志器将被 LoggerStream 和 GUI 的 TextHandler 使用
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# 清除可能存在的默认控制台处理器，避免重复输出
for handler in logger.handlers[:]:
    if isinstance(handler, logging.StreamHandler):
        logger.removeHandler(handler)

# --- 自定义流，用于将 stdout/stderr 重定向到日志器 ---
class LoggerStream:
    """一个文件类对象，将写入操作重定向到指定的日志器。"""
    def __init__(self, logger_instance, level=logging.INFO):
        self.logger = logger_instance
        self.level = level
        self._buffer = '' # 用于存储不完整行

    def write(self, message):
        # 过滤掉空消息和纯换行符
        if not message.strip():
            return

        self._buffer += message
        if '\n' in self._buffer:
            lines = self._buffer.split('\n')
            for line in lines[:-1]: # 处理所有完整行
                if line.strip(): # 只记录非空行
                    self.logger.log(self.level, line.strip())
            self._buffer = lines[-1] # 将最后（不完整）的行保留在缓冲区

    def flush(self):
        # 记录缓冲区中剩余的任何内容
        if self._buffer.strip():
            self.logger.log(self.level, self._buffer.strip())
            self._buffer = ''

# --- 自定义日志处理器，用于将日志消息重定向到 Tkinter scrolled text widget ---
class TextHandler(logging.Handler):
    """自定义日志处理器，将日志消息重定向到 Tkinter scrolled text widget。"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        # 确保 GUI 更新发生在主线程
        def _update_text_widget():
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, self.format(record) + "\n")
            self.text_widget.see(tk.END) # 自动滚动到末尾
            self.text_widget.config(state=tk.DISABLED)
        self.text_widget.after(0, _update_text_widget) # 使用 after 方法进行线程安全更新

# 在程序启动时全局重定向 stdout 和 stderr
# 这确保了 tqdm 和任何 print 语句都会被捕获
sys.stdout = LoggerStream(logger, logging.INFO)
sys.stderr = LoggerStream(logger, logging.ERROR)

# --- 导入您的模块 ---
# 确保 'modules' 文件夹与 'gui_app.py' 在同一目录
try:
    from modules import file_organizer
    from modules import filename_manager # filename_manager 现在包含 flatten_directories
    from modules import folder_processor
    from modules import pdf_processor
    from modules import pdf_security_processor
    from modules import image_converter
    from modules import text_converter
    from modules import file_combiner
    from modules import report_generator # report_generator 被其他模块使用，因此保持可访问性
except ImportError as e:
    # 即使 stdout/stderr 已重定向，此 messagebox 仍应正常工作
    messagebox.showerror("模块导入错误", f"无法导入必要的模块。请确保 'modules' 文件夹与 'gui_app.py' 在同一目录。\n错误: {e}")
    sys.exit(1)

# --- 全局常量 ---
INPUT_DIR_DEFAULT = os.getcwd()
PROCESSED_FILES_DIR_NAME = "processed_files"

class DocumentToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文档处理工具 GUI")
        self.root.geometry("1200x800") # 初始窗口大小
        self.root.resizable(True, True) # 允许调整大小

        # 配置现代风格的样式
        self.style = ttk.Style()
        self.style.theme_use('clam') # 可选主题：'clam', 'alt', 'default', 'classic'

        # 设置整体背景为白色
        self.root.configure(bg='white')
        self.style.configure('.', background='white', foreground='black') # 默认应用于所有 Tkinter 控件

        # 配置 TButton 样式，悬停时变为粉色
        self.style.configure('TButton',
                             background='#E0E0E0', # 默认按钮背景
                             foreground='black',
                             relief='flat',
                             padding=8,
                             font=('Inter', 10, 'bold'))
        self.style.map('TButton',
                       background=[('active', 'pink')]) # 悬停时变为粉色

        # 配置 TNotebook (选项卡) 样式，悬停时变为粉色
        self.style.configure('TNotebook', background='white', borderwidth=0)
        self.style.configure('TNotebook.Tab',
                             background='#E0E0E0', # 默认选项卡背景
                             foreground='black',
                             padding=[10, 5],
                             font=('Inter', 10, 'bold'))
        self.style.map('TNotebook.Tab',
                       background=[('selected', 'white'), ('active', 'pink')], # 选中时为白色，悬停时为粉色
                       foreground=[('selected', 'black'), ('active', 'black')])
        
        # 确保其他 ttk 控件的背景也是白色
        self.style.configure('TFrame', background='white')
        self.style.configure('TLabel', background='white', foreground='black', font=('Inter', 10))
        self.style.configure('TEntry', padding=5, font=('Inter', 10))
        self.style.configure('TCheckbutton', background='white', font=('Inter', 10))
        self.style.configure('TLabelframe', background='white')
        self.style.configure('TLabelframe.Label', background='white', font=('Inter', 11, 'bold'))


        self.input_dir_var = tk.StringVar(value=INPUT_DIR_DEFAULT)
        self.processed_files_dir = os.path.join(self.input_dir_var.get(), PROCESSED_FILES_DIR_NAME)

        self._create_widgets()
        self._setup_logging_to_gui()
        self.input_dir_var.trace_add("write", self._update_processed_dir) # 监听目录变化

    def _update_processed_dir(self, *args):
        """当输入目录改变时，更新 processed_files_dir 路径。"""
        self.processed_files_dir = os.path.join(self.input_dir_var.get(), PROCESSED_FILES_DIR_NAME)

    def _create_widgets(self):
        # --- 顶部：目录选择 ---
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill="x", pady=(5, 0))

        ttk.Label(top_frame, text="当前操作目录:").pack(side="left", padx=5)
        ttk.Entry(top_frame, textvariable=self.input_dir_var, width=80).pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(top_frame, text="选择目录", command=self._select_directory).pack(side="left", padx=5)

        # --- 主内容区域：Notebook (选项卡) ---
        notebook = ttk.Notebook(self.root)
        notebook.pack(pady=10, padx=10, fill="both", expand=True)

        # 创建各个选项卡
        self.file_organizer_tab = ttk.Frame(notebook)
        self.filename_manager_tab = ttk.Frame(notebook)
        self.folder_processor_tab = ttk.Frame(notebook)
        self.pdf_processor_tab = ttk.Frame(notebook)
        self.pdf_security_processor_tab = ttk.Frame(notebook)
        self.image_converter_tab = ttk.Frame(notebook)
        self.text_converter_tab = ttk.Frame(notebook)
        self.file_combiner_tab = ttk.Frame(notebook)

        notebook.add(self.file_organizer_tab, text="文件组织")
        notebook.add(self.filename_manager_tab, text="文件名管理")
        notebook.add(self.folder_processor_tab, text="文件夹处理")
        notebook.add(self.pdf_processor_tab, text="PDF处理")
        notebook.add(self.pdf_security_processor_tab, text="PDF安全")
        notebook.add(self.image_converter_tab, text="图片转换")
        notebook.add(self.text_converter_tab, text="文本转换")
        notebook.add(self.file_combiner_tab, text="文件合并")

        # 填充各个选项卡的内容
        self._populate_file_organizer_tab(self.file_organizer_tab)
        self._populate_filename_manager_tab(self.filename_manager_tab)
        self._populate_folder_processor_tab(self.folder_processor_tab)
        self._populate_pdf_processor_tab(self.pdf_processor_tab)
        self._populate_pdf_security_processor_tab(self.pdf_security_processor_tab)
        self._populate_image_converter_tab(self.image_converter_tab)
        self._populate_text_converter_tab(self.text_converter_tab)
        self._populate_file_combiner_tab(self.file_combiner_tab)

        # --- 底部：日志输出 ---
        log_frame = ttk.LabelFrame(self.root, text="日志输出", padding="10")
        log_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # 设置日志文本框的背景和前景颜色以适应白色主题
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10, state=tk.DISABLED, font=('Inter', 9), bg='lightgray', fg='black', insertbackground='black')
        self.log_text.pack(fill="both", expand=True)

        # --- 底部：署名和 ASCII 猫 ---
        footer_frame = ttk.Frame(self.root, padding="5")
        footer_frame.pack(fill="x", pady=(0, 5))

        # ASCII 猫图案
        ascii_cat = tk.Label(footer_frame, text="""
 /\\_/\\
( o.o )
 > ^ <
""", font=('Courier New', 8), justify='left', anchor='sw', bg='white', fg='#555555') # 确保背景为白色
        ascii_cat.pack(side="left", padx=10)

        # 署名
        ttk.Label(footer_frame, text="Developed by Dadoudouoo", font=('Inter', 9, 'italic'), foreground='#555555').pack(side="right", padx=10)

    def _setup_logging_to_gui(self):
        """设置自定义日志处理器，将日志定向到 GUI。"""
        gui_handler = TextHandler(self.log_text)
        logger.addHandler(gui_handler)

    def _select_directory(self):
        """打开目录选择对话框并更新输入目录变量。"""
        directory = filedialog.askdirectory()
        if directory:
            self.input_dir_var.set(directory)
            logger.info(f"输入目录已更新为: {directory}")

    def _run_in_thread(self, func, *args, **kwargs):
        """在单独线程中运行函数，防止 GUI 卡死。"""
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True # 允许程序在线程仍在运行时退出
        thread.start()

    # --- 各个选项卡的内容填充函数 ---

    def _populate_file_organizer_tab(self, tab):
        """填充文件组织选项卡的功能。"""
        frame = ttk.Frame(tab, padding="15")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="文件组织功能:", font=('Inter', 11, 'bold')).pack(pady=(0, 10), anchor='w')

        # 按组组织文件
        ttk.Button(frame, text="按组组织文件 (PDF/TXT/EPUB)", command=lambda: self._run_in_thread(self._organize_files_by_group)).pack(pady=5, fill="x")
        ttk.Label(frame, text="根据文件名中的共同子字符串将文件分组到子文件夹中。").pack(pady=(0, 10), anchor='w')

        # 扁平化目录 (已从 folder_processor 移动到此处，并调用 filename_manager)
        ttk.Button(frame, text="扁平化目录", command=lambda: self._run_in_thread(self._flatten_directories)).pack(pady=5, fill="x")
        ttk.Label(frame, text="将所有文件从子目录提取到根目录，然后删除空子目录。").pack(pady=(0, 10), anchor='w')


    def _populate_filename_manager_tab(self, tab):
        """填充文件名管理选项卡的功能。"""
        frame = ttk.Frame(tab, padding="15")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="文件名管理功能:", font=('Inter', 11, 'bold')).pack(pady=(0, 10), anchor='w')

        # 添加前缀
        prefix_frame = ttk.Frame(frame)
        prefix_frame.pack(pady=5, fill="x")
        ttk.Label(prefix_frame, text="添加前缀:").pack(side="left", padx=5)
        self.add_prefix_entry = ttk.Entry(prefix_frame, width=40)
        self.add_prefix_entry.pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(prefix_frame, text="添加前缀", command=lambda: self._run_in_thread(self._add_filename_prefix)).pack(side="left")
        ttk.Label(frame, text="为文件名（PDF/TXT/EPUB 文件和目录）添加指定前缀。").pack(pady=(0, 10), anchor='w')

        # 提取文件名中的数字
        ttk.Button(frame, text="提取文件名中的数字", command=lambda: self._run_in_thread(self._extract_numbers_in_filenames)).pack(pady=5, fill="x")
        ttk.Label(frame, text="将文件重命名为仅包含提取的数字和原始扩展名。跳过纯数字名称。").pack(pady=(0, 10), anchor='w')

        # 反向重命名 (移除前缀)
        ttk.Button(frame, text="反向重命名 (移除前缀)", command=lambda: self._run_in_thread(self._reverse_rename)).pack(pady=5, fill="x")
        ttk.Label(frame, text="从文件名中移除 'X-' 前缀（例如，'A-file.pdf' 变为 'file.pdf'）。").pack(pady=(0, 10), anchor='w')

        # 删除文件名中的字符
        delete_char_frame = ttk.Frame(frame)
        delete_char_frame.pack(pady=5, fill="x")
        ttk.Label(delete_char_frame, text="删除字符/模式:").pack(side="left", padx=5)
        self.delete_char_entry = ttk.Entry(delete_char_frame, width=40)
        self.delete_char_entry.pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(delete_char_frame, text="删除字符", command=lambda: self._run_in_thread(self._delete_filename_chars)).pack(side="left")
        ttk.Label(frame, text="从文件名中删除指定的字符或正则表达式模式。").pack(pady=(0, 10), anchor='w')

        # 重命名项目 (标准化)
        rename_items_frame = ttk.Frame(frame)
        rename_items_frame.pack(pady=5, fill="x")
        ttk.Label(rename_items_frame, text="标准化重命名模式:").pack(side="left", padx=5)
        self.rename_mode_var = tk.StringVar(value="both")
        ttk.OptionMenu(rename_items_frame, self.rename_mode_var, "both", "both", "folders", "files").pack(side="left", padx=5)
        ttk.Button(rename_items_frame, text="标准化重命名", command=lambda: self._run_in_thread(self._rename_items)).pack(side="left")
        ttk.Label(frame, text="根据第一个字符将文件名标准化为 '前缀-原始名称' 格式。").pack(pady=(0, 10), anchor='w')

    def _populate_folder_processor_tab(self, tab):
        """填充文件夹处理选项卡的功能。"""
        frame = ttk.Frame(tab, padding="15")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="文件夹处理功能:", font=('Inter', 11, 'bold')).pack(pady=(0, 10), anchor='w')

        # 编码文件夹 (双重压缩)
        encode_frame = ttk.Frame(frame)
        encode_frame.pack(pady=5, fill="x")
        ttk.Button(encode_frame, text="编码文件夹 (双重压缩)", command=lambda: self._run_in_thread(self._encode_folders_with_double_compression)).pack(side="left", expand=False)
        ttk.Label(encode_frame, text="密码:").pack(side="left", padx=5)
        self.encode_password_entry = ttk.Entry(encode_frame, width=20, show="*")
        self.encode_password_entry.insert(0, "1111") # 默认密码
        self.encode_password_entry.pack(side="left", expand=True)
        ttk.Label(frame, text="将文件夹/文件压缩为带密码的 .z删ip 档案。需要安装 7-Zip 和 Zip 命令。").pack(pady=(0, 10), anchor='w')

        # 解码文件夹 (双重解压)
        decode_frame = ttk.Frame(frame)
        decode_frame.pack(pady=5, fill="x")
        ttk.Button(decode_frame, text="解码文件夹 (双重解压)", command=lambda: self._run_in_thread(self._decode_folders_with_double_decompression)).pack(side="left", expand=False)
        ttk.Label(decode_frame, text="密码:").pack(side="left", padx=5)
        self.decode_password_entry = ttk.Entry(decode_frame, width=20, show="*")
        self.decode_password_entry.insert(0, "1111") # 默认密码
        self.decode_password_entry.pack(side="left", expand=True)
        ttk.Label(frame, text="将 .z删ip 档案解压回原始内容。需要安装 Unzip 和 7-Zip 命令。").pack(pady=(0, 10), anchor='w')

        # 扁平化目录功能已移动到文件组织选项卡

    def _populate_pdf_processor_tab(self, tab):
        """填充 PDF 处理选项卡的功能。"""
        frame = ttk.Frame(tab, padding="15")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="PDF 处理功能:", font=('Inter', 11, 'bold')).pack(pady=(0, 10), anchor='w')

        # 移除 PDF 页面 (裁剪)
        trim_pdf_frame = ttk.Frame(frame)
        trim_pdf_frame.pack(pady=5, fill="x")
        ttk.Label(trim_pdf_frame, text="裁剪 PDF 页面:").pack(side="left", padx=5)
        self.trim_pdf_type_var = tk.StringVar(value="f") # 'f' (开头), 'l' (结尾), 'lf' (开头和结尾)
        ttk.OptionMenu(trim_pdf_frame, self.trim_pdf_type_var, "f", "f", "l", "lf").pack(side="left", padx=5)
        ttk.Label(trim_pdf_frame, text="页数 (或 'lf' 用于开头和结尾):").pack(side="left", padx=5)
        self.trim_pdf_num_pages_entry = ttk.Entry(trim_pdf_frame, width=10)
        self.trim_pdf_num_pages_entry.insert(0, "1")
        self.trim_pdf_num_pages_entry.pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(trim_pdf_frame, text="裁剪页面", command=lambda: self._run_in_thread(self._remove_pdf_pages)).pack(side="left")
        ttk.Label(frame, text="从 PDF 文件的开头 ('f')、结尾 ('l') 或两者 ('lf') 移除页面。").pack(pady=(0, 10), anchor='w')

        # 移除 PDF 中的特定页面
        remove_specific_pages_frame = ttk.Frame(frame)
        remove_specific_pages_frame.pack(pady=5, fill="x")
        ttk.Label(remove_specific_pages_frame, text="移除特定页面 (0-索引，例如：0 2 4):").pack(side="left", padx=5)
        self.specific_pages_to_remove_entry = ttk.Entry(remove_specific_pages_frame, width=40)
        self.specific_pages_to_remove_entry.pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(remove_specific_pages_frame, text="移除特定页面", command=lambda: self._run_in_thread(self._process_pdfs_for_specific_page_removal_in_directory)).pack(side="left")
        ttk.Label(frame, text="从目录中所有 PDF 文件中移除指定的 0-索引页面。").pack(pady=(0, 10), anchor='w')

        # 修复 PDF
        ttk.Button(frame, text="通过重建修复 PDF", command=lambda: self._run_in_thread(self._repair_pdfs_by_rebuilding)).pack(pady=5, fill="x")
        ttk.Label(frame, text="尝试通过重新保存来修复 PDF 内部结构。").pack(pady=(0, 10), anchor='w')

    def _populate_pdf_security_processor_tab(self, tab):
        """填充 PDF 安全处理选项卡的功能。"""
        frame = ttk.Frame(tab, padding="15")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="PDF 安全功能:", font=('Inter', 11, 'bold')).pack(pady=(0, 10), anchor='w')

        # 加密 PDF
        encrypt_pdf_frame = ttk.Frame(frame)
        encrypt_pdf_frame.pack(pady=5, fill="x")
        ttk.Label(encrypt_pdf_frame, text="加密 PDF 密码:").pack(side="left", padx=5)
        self.encrypt_pdf_password_entry = ttk.Entry(encrypt_pdf_frame, width=30, show="*")
        self.encrypt_pdf_password_entry.pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(encrypt_pdf_frame, text="加密 PDF", command=lambda: self._run_in_thread(self._encode_pdfs)).pack(side="left")
        ttk.Label(frame, text="使用密码加密 PDF 并限制权限（禁止打印/复制/修改）。").pack(pady=(0, 10), anchor='w')

        # 解密 PDF
        decrypt_pdf_frame = ttk.Frame(frame)
        decrypt_pdf_frame.pack(pady=5, fill="x")
        ttk.Label(decrypt_pdf_frame, text="解密 PDF 密码:").pack(side="left", padx=5)
        self.decrypt_pdf_password_entry = ttk.Entry(decrypt_pdf_frame, width=30, show="*")
        self.decrypt_pdf_password_entry.pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(decrypt_pdf_frame, text="解密 PDF", command=lambda: self._run_in_thread(self._decode_pdfs)).pack(side="left")
        ttk.Label(frame, text="使用提供的密码解密 PDF，并覆盖原始文件。").pack(pady=(0, 10), anchor='w')

    def _populate_image_converter_tab(self, tab):
        """填充图片转换选项卡的功能。"""
        frame = ttk.Frame(tab, padding="15")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="图片转换功能:", font=('Inter', 11, 'bold')).pack(pady=(0, 10), anchor='w')

        # 图片转 PDF
        img_to_pdf_frame = ttk.Frame(frame)
        img_to_pdf_frame.pack(pady=5, fill="x")
        ttk.Label(img_to_pdf_frame, text="图片转 PDF (输出文件名: combined_images.pdf)").pack(side="left", padx=5)
        ttk.Button(img_to_pdf_frame, text="转换图片为 PDF", command=lambda: self._run_in_thread(self._images_to_pdf)).pack(side="left")
        ttk.Label(frame, text="将目录中所有图片转换为单个 PDF 文件。").pack(pady=(0, 10), anchor='w')

        # PDF 转图片
        pdf_to_img_frame = ttk.Frame(frame)
        pdf_to_img_frame.pack(pady=5, fill="x")
        ttk.Label(pdf_to_img_frame, text="PDF 转图片 (输出格式:").pack(side="left", padx=5)
        self.pdf_to_img_format_var = tk.StringVar(value="png")
        ttk.OptionMenu(pdf_to_img_frame, self.pdf_to_img_format_var, "png", "png", "jpg").pack(side="left", padx=5)
        ttk.Label(pdf_to_img_frame, text="DPI:").pack(side="left", padx=5)
        self.pdf_to_img_dpi_entry = ttk.Entry(pdf_to_img_frame, width=5)
        self.pdf_to_img_dpi_entry.insert(0, "300")
        self.pdf_to_img_dpi_entry.pack(side="left", padx=5)
        ttk.Label(pdf_to_img_frame, text="质量 (仅 JPG):").pack(side="left", padx=5)
        self.pdf_to_img_quality_entry = ttk.Entry(pdf_to_img_frame, width=5)
        self.pdf_to_img_quality_entry.insert(0, "90")
        self.pdf_to_img_quality_entry.pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(pdf_to_img_frame, text="转换 PDF 为图片", command=lambda: self._run_in_thread(self._pdf_to_images)).pack(side="left")
        ttk.Label(frame, text="将 PDF 的每一页转换为单独的图片文件。").pack(pady=(0, 10), anchor='w')

        # 压缩图片 (到 PDF)
        compress_img_frame = ttk.Frame(frame)
        compress_img_frame.pack(pady=5, fill="x")
        ttk.Label(compress_img_frame, text="压缩图片到 PDF (输出文件名):").pack(side="left", padx=5)
        self.compress_img_filename_entry = ttk.Entry(compress_img_frame, width=20)
        self.compress_img_filename_entry.insert(0, "compressed_output.pdf")
        self.compress_img_filename_entry.pack(side="left", padx=5)
        ttk.Label(compress_img_frame, text="目标宽度:").pack(side="left", padx=5)
        self.compress_img_width_entry = ttk.Entry(compress_img_frame, width=8)
        self.compress_img_width_entry.insert(0, "1500")
        self.compress_img_width_entry.pack(side="left", padx=5)
        ttk.Label(compress_img_frame, text="质量:").pack(side="left", padx=5)
        self.compress_img_quality_entry = ttk.Entry(compress_img_frame, width=5)
        self.compress_img_quality_entry.insert(0, "90")
        self.compress_img_quality_entry.pack(side="left", padx=5)
        ttk.Label(compress_img_frame, text="DPI:").pack(side="left", padx=5)
        self.compress_img_dpi_entry = ttk.Entry(compress_img_frame, width=5)
        self.compress_img_dpi_entry.insert(0, "300")
        self.compress_img_dpi_entry.pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(compress_img_frame, text="压缩图片", command=lambda: self._run_in_thread(self._compress_images)).pack(side="left")
        ttk.Label(frame, text="压缩图片并将其合并为单个优化后的 PDF。").pack(pady=(0, 10), anchor='w')

    def _populate_text_converter_tab(self, tab):
        """填充文本转换选项卡的功能。"""
        frame = ttk.Frame(tab, padding="15")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="文本转换功能:", font=('Inter', 11, 'bold')).pack(pady=(0, 10), anchor='w')

        # EPUB 转 TXT
        ttk.Button(frame, text="EPUB 转 TXT", command=lambda: self._run_in_thread(self._epub_to_txt)).pack(pady=5, fill="x")
        ttk.Label(frame, text="将 EPUB 文件转换为纯文本 (.txt) 文件。").pack(pady=(0, 10), anchor='w')

        # PDF 转 TXT
        pdf_to_txt_frame = ttk.Frame(frame)
        pdf_to_txt_frame.pack(pady=5, fill="x")
        ttk.Label(pdf_to_txt_frame, text="PDF 转 TXT (输出格式:").pack(side="left", padx=5)
        self.pdf_to_txt_format_var = tk.StringVar(value="standard")
        ttk.OptionMenu(pdf_to_txt_frame, self.pdf_to_txt_format_var, "standard", "standard", "compact", "clean").pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(pdf_to_txt_frame, text="转换 PDF 为 TXT", command=lambda: self._run_in_thread(self._pdf_to_txt)).pack(side="left")
        ttk.Label(frame, text="从 PDF 文件中提取文本内容。选择 '标准'、'紧凑' 或 '清理' 格式。").pack(pady=(0, 10), anchor='w')

    def _populate_file_combiner_tab(self, tab):
        """填充文件合并选项卡的功能。"""
        frame = ttk.Frame(tab, padding="15")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="文件合并功能:", font=('Inter', 11, 'bold')).pack(pady=(0, 10), anchor='w')

        # 合并文件
        combine_files_frame = ttk.Frame(frame)
        combine_files_frame.pack(pady=5, fill="x")
        ttk.Label(combine_files_frame, text="合并文件类型:").pack(side="left", padx=5)
        self.combine_file_type_var = tk.StringVar(value="p") # 'p' 用于 PDF, 't' 用于 TXT
        ttk.OptionMenu(combine_files_frame, self.combine_file_type_var, "p", "p", "t").pack(side="left", padx=5)
        ttk.Label(combine_files_frame, text="输出文件名:").pack(side="left", padx=5)
        self.combine_output_name_entry = ttk.Entry(combine_files_frame, width=30)
        self.combine_output_name_entry.insert(0, "combined_output")
        self.combine_output_name_entry.pack(side="left", padx=5, expand=True, fill="x")
        ttk.Button(combine_files_frame, text="合并文件", command=lambda: self._run_in_thread(self._combine_files)).pack(side="left")
        ttk.Label(frame, text="将多个 PDF 或 TXT 文件合并为单个输出文件。").pack(pady=(0, 10), anchor='w')

    # --- 对应每个模块功能的执行函数 ---

    # file_organizer 函数
    def _organize_files_by_group(self):
        current_dir = self.input_dir_var.get()
        logger.info(f"开始在: {current_dir} 中组织文件...")
        try:
            # file_organizer.organize_files_by_group 的默认目标扩展名
            target_extensions = {'.pdf', '.epub', '.txt'}
            file_organizer.organize_files_by_group(current_dir, target_extensions)
            logger.info("文件组织完成。")
        except Exception as e:
            logger.error(f"文件组织失败: {e}")

    # filename_manager 函数
    def _add_filename_prefix(self):
        current_dir = self.input_dir_var.get()
        prefix = self.add_prefix_entry.get()
        if not prefix:
            messagebox.showwarning("输入错误", "请输入要添加的前缀。")
            return
        logger.info(f"开始在: {current_dir} 中为文件添加前缀 '{prefix}'...")
        try:
            filename_manager.add_filename_prefix(current_dir, prefix)
            logger.info("添加前缀完成。")
        except Exception as e:
            logger.error(f"添加前缀失败: {e}")

    def _extract_numbers_in_filenames(self):
        current_dir = self.input_dir_var.get()
        logger.info(f"开始在: {current_dir} 中从文件名提取数字...")
        try:
            filename_manager.extract_numbers_in_filenames(current_dir)
            logger.info("从文件名提取数字完成。")
        except Exception as e:
            logger.error(f"从文件名提取数字失败: {e}")

    def _reverse_rename(self):
        current_dir = self.input_dir_var.get()
        logger.info(f"开始在: {current_dir} 中执行反向重命名操作...")
        try:
            filename_manager.reverse_rename(current_dir)
            logger.info("反向重命名完成。")
        except Exception as e:
            logger.error(f"反向重命名失败: {e}")

    def _delete_filename_chars(self):
        current_dir = self.input_dir_var.get()
        char_to_delete = self.delete_char_entry.get()
        if not char_to_delete:
            messagebox.showwarning("输入错误", "请输入要删除的字符或正则表达式模式。")
            return
        logger.info(f"开始在: {current_dir} 中从文件名删除字符 '{char_to_delete}'...")
        try:
            filename_manager.delete_filename_chars(current_dir, char_to_delete)
            logger.info("从文件名删除字符完成。")
        except Exception as e:
            logger.error(f"从文件名删除字符失败: {e}")

    def _rename_items(self):
        current_dir = self.input_dir_var.get()
        mode = self.rename_mode_var.get()
        logger.info(f"开始在: {current_dir} 中以模式 '{mode}' 标准化重命名项目...")
        try:
            filename_manager.rename_items(current_dir, mode)
            logger.info("标准化重命名完成。")
        except Exception as e:
            logger.error(f"标准化重命名失败: {e}")

    # folder_processor 函数
    def _encode_folders_with_double_compression(self):
        current_dir = self.input_dir_var.get()
        password = self.encode_password_entry.get()
        if not password:
            messagebox.showwarning("输入错误", "请输入编码密码。")
            return
        logger.info(f"开始在: {current_dir} 中双重压缩和编码文件夹...")
        try:
            folder_processor.encode_folders_with_double_compression(current_dir, password=password)
            logger.info("文件夹编码完成。")
        except Exception as e:
            logger.error(f"文件夹编码失败: {e}")
            messagebox.showerror("编码失败", f"请确保已安装 7-Zip 和 Zip 命令并将其添加到系统 PATH。\n错误: {e}")

    def _decode_folders_with_double_decompression(self):
        current_dir = self.input_dir_var.get()
        password = self.decode_password_entry.get()
        if not password:
            messagebox.showwarning("输入错误", "请输入解码密码。")
            return
        # 确保 processed_files_dir 存在用于输出
        os.makedirs(self.processed_files_dir, exist_ok=True)
        logger.info(f"开始在: {current_dir} 中双重解压和解码文件夹到: {self.processed_files_dir}...")
        try:
            folder_processor.decode_folders_with_double_decompression(current_dir, self.processed_files_dir, password=password)
            logger.info("文件夹解码完成。")
        except Exception as e:
            logger.error(f"文件夹解码失败: {e}")
            messagebox.showerror("解码失败", f"请检查密码，并确保已安装 Unzip 和 7-Zip 命令并将其添加到系统 PATH。\n错误: {e}")

    # 扁平化目录功能已移动到文件组织选项卡，并调用 filename_manager
    def _flatten_directories(self):
        current_dir = self.input_dir_var.get()
        logger.info(f"开始在: {current_dir} 中展平目录...")
        try:
            # 调用 filename_manager 中的 flatten_directories
            filename_manager.flatten_directories(current_dir)
            logger.info("目录展平完成。")
        except Exception as e:
            logger.error(f"目录展平失败: {e}")


    # pdf_processor 函数
    def _remove_pdf_pages(self):
        current_dir = self.input_dir_var.get()
        trim_type = self.trim_pdf_type_var.get()
        num_pages_str = self.trim_pdf_num_pages_entry.get()

        num_pages = None
        if trim_type == 'lf':
            num_pages = 1 # 对于 'lf' 模式，页数通常为 1（第一页和最后一页），或者如果函数是标志则可以忽略
        else:
            try:
                num_pages = int(num_pages_str)
                if num_pages <= 0:
                    raise ValueError("页数必须是正整数。")
            except ValueError:
                messagebox.showwarning("输入错误", "页数必须是大于 0 的整数。")
                return

        os.makedirs(self.processed_files_dir, exist_ok=True)
        logger.info(f"开始在: {current_dir} 中裁剪 PDF 页面 (类型: '{trim_type}', 页数: {num_pages}) 到: {self.processed_files_dir}...")
        try:
            pdf_processor.remove_pdf_pages(current_dir, self.processed_files_dir, trim_type, num_pages)
            logger.info("PDF 页面裁剪完成。")
        except Exception as e:
            logger.error(f"PDF 页面裁剪失败: {e}")

    def _process_pdfs_for_specific_page_removal_in_directory(self):
        current_dir = self.input_dir_var.get()
        pages_str = self.specific_pages_to_remove_entry.get()
        if not pages_str:
            messagebox.showwarning("输入错误", "请输入特定页码（0-索引，例如：0 2 4）。")
            return

        try:
            pages_to_remove = [int(p) for p in pages_str.split()]
            if not all(p >= 0 for p in pages_to_remove):
                raise ValueError("页码必须是非负整数。")
        except ValueError:
            messagebox.showwarning("输入错误", "页码格式不正确。请使用空格分隔的整数（0-索引）。")
            return

        os.makedirs(self.processed_files_dir, exist_ok=True)
        logger.info(f"开始在: {current_dir} 中移除特定 PDF 页面 ({[p+1 for p in pages_to_remove]} 作为 1-索引) 到: {self.processed_files_dir}...")
        try:
            pdf_processor.process_pdfs_for_specific_page_removal_in_directory(
                Path(current_dir),
                pages_to_remove,
                Path(self.processed_files_dir)
            )
            logger.info("特定 PDF 页面移除完成。")
        except Exception as e:
            logger.error(f"特定 PDF 页面移除失败: {e}")

    def _repair_pdfs_by_rebuilding(self):
        current_dir = self.input_dir_var.get()
        os.makedirs(self.processed_files_dir, exist_ok=True)
        logger.info(f"开始在: {current_dir} 中修复 PDF 文件到: {self.processed_files_dir}...")
        try:
            pdf_processor.repair_pdfs_by_rebuilding(current_dir, self.processed_files_dir)
            logger.info("PDF 修复完成。")
        except Exception as e:
            logger.error(f"PDF 修复失败: {e}")

    # pdf_security_processor 函数
    def _encode_pdfs(self):
        current_dir = self.input_dir_var.get()
        password = self.encrypt_pdf_password_entry.get()
        if not password:
            messagebox.showwarning("输入错误", "请输入加密密码。")
            return
        os.makedirs(self.processed_files_dir, exist_ok=True)
        logger.info(f"开始在: {current_dir} 中加密 PDF 文件到: {self.processed_files_dir}...")
        try:
            pdf_security_processor.encode_pdfs(current_dir, self.processed_files_dir, password)
            logger.info("PDF 加密完成。")
        except Exception as e:
            logger.error(f"PDF 加密失败: {e}")

    def _decode_pdfs(self):
        current_dir = self.input_dir_var.get()
        password = self.decrypt_pdf_password_entry.get()
        if not password:
            messagebox.showwarning("输入错误", "请输入解密密码。")
            return
        # 解密会覆盖原始文件，因此此处不需要 output_dir
        logger.info(f"开始在: {current_dir} 中解密 PDF 文件...")
        try:
            pdf_security_processor.decode_pdfs(current_dir, password)
            logger.info("PDF 解密完成。")
        except Exception as e:
            logger.error(f"PDF 解密失败: {e}")
            messagebox.showerror("解密失败", f"请检查密码或文件是否损坏。\n错误: {e}")

    # image_converter 函数
    def _images_to_pdf(self):
        current_dir = self.input_dir_var.get()
        os.makedirs(self.processed_files_dir, exist_ok=True)
        logger.info(f"开始在: {current_dir} 中将图片转换为 PDF 到: {self.processed_files_dir}...")
        try:
            # 目标宽度和 DPI 默认由函数使用
            image_converter.images_to_pdf(current_dir, self.processed_files_dir)
            logger.info("图片转 PDF 完成。")
        except Exception as e:
            logger.error(f"图片转 PDF 失败: {e}")

    def _pdf_to_images(self):
        current_dir = self.input_dir_var.get()
        fmt = self.pdf_to_img_format_var.get()
        dpi_str = self.pdf_to_img_dpi_entry.get()
        quality_str = self.pdf_to_img_quality_entry.get()

        try:
            dpi = int(dpi_str)
            quality = int(quality_str)
            if not (1 <= dpi <= 1000) or not (0 <= quality <= 100):
                raise ValueError("DPI 必须在 1-1000 之间，质量必须在 0-100 之间。")
        except ValueError:
            messagebox.showwarning("输入错误", "DPI 和质量必须是有效的整数。")
            return

        os.makedirs(self.processed_files_dir, exist_ok=True)
        logger.info(f"开始在: {current_dir} 中将 PDF 转换为 {fmt.upper()} 图片到: {self.processed_files_dir} (DPI: {dpi}, 质量: {quality})...")
        try:
            image_converter.pdf_to_images(current_dir, self.processed_files_dir, fmt=fmt, dpi=dpi, quality=quality)
            logger.info("PDF 转图片完成。")
        except Exception as e:
            logger.error(f"PDF 转图片失败: {e}")

    def _compress_images(self):
        current_dir = self.input_dir_var.get()
        filename = self.compress_img_filename_entry.get()
        target_width_str = self.compress_img_width_entry.get()
        quality_str = self.compress_img_quality_entry.get()
        dpi_str = self.compress_img_dpi_entry.get()

        if not filename:
            messagebox.showwarning("输入错误", "请输入压缩后 PDF 的输出文件名。")
            return

        try:
            target_width = int(target_width_str)
            quality = int(quality_str)
            dpi = int(dpi_str)
            if not (target_width > 0 and 0 <= quality <= 100 and dpi > 0):
                raise ValueError("宽度、质量或 DPI 的输入无效。")
        except ValueError:
            messagebox.showwarning("输入错误", "目标宽度、质量和 DPI 必须是有效的整数。")
            return

        os.makedirs(self.processed_files_dir, exist_ok=True)
        logger.info(f"开始在: {current_dir} 中将图片压缩为 '{filename}' (宽度: {target_width}, 质量: {quality}, DPI: {dpi}) 到: {self.processed_files_dir}...")
        try:
            image_converter.compress_images(current_dir, self.processed_files_dir, filename=filename, target_width=target_width, quality=quality, dpi=dpi)
            logger.info("图片压缩为 PDF 完成。")
        except Exception as e:
            logger.error(f"图片压缩为 PDF 失败: {e}")

    # text_converter 函数
    def _epub_to_txt(self):
        current_dir = self.input_dir_var.get()
        os.makedirs(self.processed_files_dir, exist_ok=True)
        logger.info(f"开始在: {current_dir} 中将 EPUB 转换为 TXT 到: {self.processed_files_dir}...")
        try:
            text_converter.epub_to_txt(current_dir, self.processed_files_dir)
            logger.info("EPUB 转 TXT 完成。")
        except Exception as e:
            logger.error(f"EPUB 转 TXT 失败: {e}")

    def _pdf_to_txt(self):
        current_dir = self.input_dir_var.get()
        output_format = self.pdf_to_txt_format_var.get()
        os.makedirs(self.processed_files_dir, exist_ok=True)
        logger.info(f"开始在: {current_dir} 中将 PDF 转换为 TXT (格式: '{output_format}') 到: {self.processed_files_dir}...")
        try:
            text_converter.pdf_to_txt(current_dir, self.processed_files_dir, output_format=output_format)
            logger.info("PDF 转 TXT 完成。")
        except Exception as e:
            logger.error(f"PDF 转 TXT 失败: {e}")

    # file_combiner 函数
    def _combine_files(self):
        current_dir = self.input_dir_var.get()
        file_type = self.combine_file_type_var.get()
        output_name = self.combine_output_name_entry.get()
        if not output_name:
            messagebox.showwarning("输入错误", "请输入输出文件名。")
            return

        # file_combiner.combine_files 期望 args_list
        # output_name 可能需要由 combine_files 函数本身添加扩展名
        args_list = [file_type, output_name]

        os.makedirs(self.processed_files_dir, exist_ok=True)
        logger.info(f"开始在: {current_dir} 中合并 {file_type.upper()} 文件到: {self.processed_files_dir}/{output_name}...")
        try:
            file_combiner.combine_files(current_dir, self.processed_files_dir, args_list)
            logger.info("文件合并完成。")
        except Exception as e:
            logger.error(f"文件合并失败: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DocumentToolApp(root)
    root.mainloop()