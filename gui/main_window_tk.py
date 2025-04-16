"""
主窗口模块 (Tkinter + ttkbootstrap版本)

该模块提供了应用程序的主窗口，采用三栏式布局设计。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox

from utils.config_manager import config_manager
from utils.language_manager import language_manager
from utils.logger import Logger
from core.logic_builder import LogicBuilder
from core.config_processor import ConfigProcessor
from core.bom_processor import BomProcessor
from gui.logic_panel import LogicPanel
from gui.config_panel import ConfigPanel
from gui.bom_panel import BomPanel
from gui.language_dialog_tk import LanguageDialog
from gui.logic_library_window import LogicLibraryWindow

class MainWindow:
    """主窗口类"""
    
    def __init__(self, root):
        """初始化主窗口
        
        Args:
            root: 根窗口
        """
        self.root = root
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 创建配置选项处理器
        self.config_processor = ConfigProcessor()
        
        # 创建BOM处理器
        self.bom_processor = BomProcessor()
        
        # 创建逻辑构建器
        self.logic_builder = LogicBuilder(self.config_processor)
        
        # 配置全局样式
        self._configure_global_styles()
        
        # 创建界面
        self._create_widgets()
        
        # 创建菜单
        self._create_menu()
        
        # 创建状态栏
        self._create_statusbar()
        
        # 绑定事件
        self._bind_events()
        
        # 设置窗口标题
        self.root.title(language_manager.get_text("app_title"))
        
    def _configure_global_styles(self):
        """配置全局样式"""
        style = ttk.Style()
        
        # 定义统一的字体大小
        FONT_SIZES = {
            "menu": 16,           # 菜单字体大小
            "title": 20,          # 标题字体大小
            "frame_title": 18,    # 框架标题字体大小
            "button": 16,         # 按钮字体大小
            "tree": 18,           # 树状图字体大小
            "tree_title": 18,     # 树状图标题字体大小
            "status": 14,         # 状态栏字体大小
            "label": 16,          # 标签字体大小
            "text": 16            # 文本字体大小
        }
        
        # 定义统一的内边距
        PADDINGS = {
            "button": (15, 10),   # 按钮内边距
            "frame": 10,          # 框架内边距
            "tree": 5             # 树状图内边距
        }
        
        # 定义统一的颜色
        COLORS = {
            "frame_bg": "#f0f0f0",      # 框架背景色
            "title_fg": "#000000",      # 标题前景色
            "button_bg": "#e1e1e1",     # 按钮背景色
            "tree_select": "#0078D7",   # 树状图选中色
            "f_code": "blue",           # F码颜色
            "k_code": "green"           # K码颜色
        }
        
        # 配置菜单样式
        self.root.option_add("*Menu.font", ("Microsoft YaHei", FONT_SIZES["menu"], "bold"))
        
        # 配置标题样式
        style.configure(
            "Title.TLabel",
            font=("Microsoft YaHei", FONT_SIZES["title"], "bold"),
            padding=10
        )
        
        # 配置框架标题样式
        style.configure(
            "FrameTitle.TLabel",
            font=("Microsoft YaHei", FONT_SIZES["frame_title"], "bold"),
            padding=5
        )
        
        # 配置按钮样式 - 使用统一的粗体样式
        style.configure(
            "Main.TButton",
            font=("Microsoft YaHei", FONT_SIZES["button"], "bold"),
            padding=PADDINGS["button"]
        )
        
        # 配置成功按钮样式
        style.configure(
            "success.Main.TButton",
            font=("Microsoft YaHei", FONT_SIZES["button"], "bold"),
            padding=PADDINGS["button"]
        )
        
        # 配置树状视图样式
        style.configure(
            "Main.Treeview",
            font=("Microsoft YaHei", FONT_SIZES["tree"], "bold"),
            rowheight=50,
            padding=PADDINGS["tree"]
        )
        
        # 配置树状视图标题样式
        style.configure(
            "Main.Treeview.Heading",
            font=("Microsoft YaHei", FONT_SIZES["tree_title"], "bold"),
            padding=5
        )
        
        # 配置标签样式
        style.configure(
            "Main.TLabel",
            font=("Microsoft YaHei", FONT_SIZES["label"], "bold"),
            padding=5
        )
        
        # 配置框架样式
        style.configure(
            "Main.TFrame",
            padding=PADDINGS["frame"],
            relief="solid",
            borderwidth=1
        )
        
        # 配置LabelFrame样式
        style.configure(
            "Main.TLabelframe",
            padding=PADDINGS["frame"],
            font=("Microsoft YaHei", FONT_SIZES["frame_title"], "bold")
        )
        style.configure(
            "Main.TLabelframe.Label",
            font=("Microsoft YaHei", FONT_SIZES["frame_title"], "bold")
        )
        
        # 配置状态栏样式
        style.configure(
            "Status.TLabel",
            font=("Microsoft YaHei", FONT_SIZES["status"], "bold"),
            padding=5
        )
        
        # 配置树状图标签样式
        style.map(
            "Main.Treeview",
            background=[("selected", COLORS["tree_select"])],
            foreground=[("selected", "white")]
        )
        
        # 配置特殊代码样式
        style.configure(
            "FCode.TLabel",
            foreground=COLORS["f_code"],
            font=("Microsoft YaHei", FONT_SIZES["text"], "bold")
        )
        style.configure(
            "KCode.TLabel",
            foreground=COLORS["k_code"],
            font=("Microsoft YaHei", FONT_SIZES["text"], "bold")
        )
        
        # 配置面板样式
        style.configure(
            "Panel.TFrame",
            relief="solid",
            borderwidth=1,
            padding=PADDINGS["frame"]
        )
        
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主布局框架
        self.main_frame = ttk.Frame(self.root, padding=5, style="Main.TFrame")
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        # 创建水平布局的Panedwindow
        self.paned = ttk.PanedWindow(self.main_frame, orient=HORIZONTAL)
        self.paned.pack(fill=BOTH, expand=YES)
        
        # 创建左侧配置面板
        self.left_panel = ttk.Frame(self.paned, style="Panel.TFrame")
        self.paned.add(self.left_panel, weight=1)
        
        # 创建中间逻辑编辑面板
        self.center_panel = ttk.Frame(self.paned, style="Panel.TFrame")
        self.paned.add(self.center_panel, weight=2)
        
        # 创建右侧BOM面板
        self.right_panel = ttk.Frame(self.paned, style="Panel.TFrame")
        self.paned.add(self.right_panel, weight=1)
        
        # 创建各个面板的标题
        ttk.Label(
            self.main_frame,
            text=language_manager.get_text("panels_title"),
            style="Title.TLabel"
        ).pack(side=TOP, fill=X, pady=(0, 10))
        
        # 创建各个面板的内容
        self._create_left_panel()
        self._create_center_panel()
        self._create_right_panel()
        
    def _create_left_panel(self):
        """创建左侧配置面板内容"""
        # 创建配置面板
        self.config_panel = ConfigPanel(self.left_panel, self.config_processor)
        self.config_panel.pack(fill=BOTH, expand=YES)
        
    def _create_center_panel(self):
        """创建中间逻辑编辑面板内容"""
        # 创建逻辑编辑面板
        self.logic_panel = LogicPanel(self.center_panel, self.logic_builder)
        self.logic_panel.pack(fill=BOTH, expand=YES)
        
    def _create_right_panel(self):
        """创建右侧BOM面板内容"""
        # 创建BOM面板
        self.bom_panel = BomPanel(self.right_panel, self.bom_processor)
        self.bom_panel.pack(fill=BOTH, expand=YES)
    
    def _create_menu(self):
        """创建菜单栏"""
        # 创建菜单栏
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # 文件菜单
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=language_manager.get_text("menu_file"), menu=self.file_menu)
        self.file_menu.add_command(label=language_manager.get_text("import_config"), 
                                 command=self._import_config)
        self.file_menu.add_command(label=language_manager.get_text("import_bom"), 
                                 command=self._import_bom)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=language_manager.get_text("exit"), 
                                 command=self._on_closing)
        
        # 视图菜单
        self.view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=language_manager.get_text("menu_view"), menu=self.view_menu)
        self.view_menu.add_command(label=language_manager.get_text("logic_library"), 
                                 command=self._show_logic_library)
        self.view_menu.add_separator()
        self.view_menu.add_command(label=language_manager.get_text("language"), 
                                 command=self._show_language_dialog)
        
        # 帮助菜单
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=language_manager.get_text("menu_help"), menu=self.help_menu)
        self.help_menu.add_command(label=language_manager.get_text("view_log"), 
                                 command=self._show_log_viewer)
        self.help_menu.add_command(label=language_manager.get_text("about"), 
                                 command=self._show_about)
    
    def _create_statusbar(self):
        """创建状态栏"""
        self.statusbar = ttk.Frame(self.root, style="Main.TFrame")
        self.statusbar.pack(side=BOTTOM, fill=X)
        
        self.status_label = ttk.Label(
            self.statusbar,
            text=language_manager.get_text("ready"),
            style="Status.TLabel"
        )
        self.status_label.pack(side=LEFT)
        
    def _bind_events(self):
        """绑定事件"""
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _on_closing(self):
        """窗口关闭事件处理"""
        if messagebox.askokcancel(
            language_manager.get_text("confirm_exit"),
            language_manager.get_text("confirm_exit_message")
        ):
            self.root.destroy()
            
    def _import_config(self):
        """导入配置文件"""
        if hasattr(self, 'config_panel'):
            self.config_panel._import_excel()
            
    def _import_bom(self):
        """导入BOM文件"""
        if hasattr(self, 'bom_panel'):
            self.bom_panel._import_bom()
            
    def refresh_texts(self):
        """刷新所有文本"""
        # 刷新配置面板文本
        if hasattr(self, 'config_panel'):
            self.config_panel.refresh_texts()
            
        # 刷新逻辑面板文本
        if hasattr(self, 'logic_panel'):
            self.logic_panel.refresh_texts()
            
        # 刷新菜单文本
        self._refresh_menu_texts()
        
    def _refresh_menu_texts(self):
        """刷新菜单文本"""
        # 文件菜单
        self.file_menu.entryconfig(0, label=language_manager.get_text("import_config"))
        self.file_menu.entryconfig(1, label=language_manager.get_text("import_bom"))
        self.file_menu.entryconfig(3, label=language_manager.get_text("exit"))
        
        # 视图菜单
        self.view_menu.entryconfig(0, label=language_manager.get_text("logic_library"))
        self.view_menu.entryconfig(2, label=language_manager.get_text("language"))
        
        # 帮助菜单
        self.help_menu.entryconfig(0, label=language_manager.get_text("view_log"))
        self.help_menu.entryconfig(1, label=language_manager.get_text("about"))
        
        # 菜单标签
        self.menubar.entryconfig(0, label=language_manager.get_text("menu_file"))
        self.menubar.entryconfig(1, label=language_manager.get_text("menu_view"))
        self.menubar.entryconfig(2, label=language_manager.get_text("menu_help"))
        
    def _show_logic_library(self):
        """显示逻辑关系库窗口"""
        window = LogicLibraryWindow(self.root, self.logic_builder)
        window.wait_window()  # 等待窗口关闭
    
    def _show_language_dialog(self):
        """显示语言选择对话框"""
        dialog = LanguageDialog(self.root)
        selected_lang = dialog.show()
        if selected_lang:
            language_manager.set_language(selected_lang)
            # 刷新所有面板的文本
            self.refresh_all_panels()
            
    def refresh_all_panels(self):
        """刷新所有面板的文本"""
        # 刷新窗口标题
        self.root.title(language_manager.get_text("app_title"))
        
        # 刷新主标题
        for child in self.main_frame.winfo_children():
            if isinstance(child, ttk.Label):
                child.configure(text=language_manager.get_text("panels_title"))
                break
        
        # 刷新各个面板
        if hasattr(self, 'config_panel'):
            self.config_panel.refresh_texts()
        if hasattr(self, 'logic_panel'):
            self.logic_panel.refresh_texts()
        if hasattr(self, 'bom_panel'):
            self.bom_panel.refresh_texts()
            
        # 刷新菜单文本
        self._refresh_menu_texts()
        
        # 刷新状态栏
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=language_manager.get_text("ready"))

    def _show_log_viewer(self):
        """显示日志查看器"""
        log_file = Logger.get_current_log_file()
        if log_file:
            try:
                import os
                os.startfile(log_file)  # 在Windows上使用默认文本编辑器打开
            except Exception as e:
                self.logger.error(f"打开日志文件失败: {str(e)}")
                messagebox.showerror(
                    language_manager.get_text("error"),
                    language_manager.get_text("open_log_error")
                )
                
    def _show_about(self):
        """显示关于对话框"""
        # TODO: 实现关于对话框显示
        pass