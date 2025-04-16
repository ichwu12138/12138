"""
主题选择对话框模块

该模块提供了一个简单的对话框用于选择应用程序的主题（仅在启动时显示一次）。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from utils.logger import Logger
from utils.config_manager import config_manager
from utils.language_manager import language_manager

logger = Logger.get_logger(__name__)

class SimpleThemeDialog(tk.Toplevel):
    """简单主题选择对话框"""
    
    def __init__(self, parent):
        """初始化主题选择对话框
        
        Args:
            parent: 父窗口
        """
        logger.debug("创建主题选择对话框")
        super().__init__(parent)
        
        # 设置对话框属性
        self.title(language_manager.get_text("theme_dialog_title"))
        self.minsize(400, 400)  # 调整最小尺寸
        self.resizable(False, False)
        
        # 居中显示
        window_width = 400  # 调整窗口宽度
        window_height = 400  # 调整窗口高度
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # 设置模态
        self.transient(parent)
        self.grab_set()
        
        # 存储选择结果
        self.selected_theme = None
        
        # 创建界面
        self._create_widgets()
        
        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        logger.debug("主题选择对话框创建完成")
        
    def _create_widgets(self):
        """创建对话框控件"""
        # 创建主布局框架
        main_frame = ttk.Frame(self, padding=30)  # 调整内边距
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text=language_manager.get_text("theme_dialog_header"),
            font=("Microsoft YaHei", 16, "bold"),  # 设置字体大小为16
            justify="center"  # 居中对齐
        )
        title_label.pack(pady=(0, 20))  # 调整上下间距
        
        # 创建按钮样式
        style = ttk.Style()
        style.configure(
            "Theme.TButton",
            font=("Microsoft YaHei", 16, "bold"),  # 设置字体大小为16
            padding=(10, 5),  # 调整按钮内边距
            foreground="white"  # 设置按钮文字颜色为白色
        )
        
        # 配置按钮鼠标悬停等状态的样式
        style.map(
            "Theme.TButton",
            foreground=[
                ('active', 'white'),  # 鼠标悬停时保持白色
                ('disabled', 'gray75')  # 禁用时使用浅灰色
            ],
            background=[
                ('active', '!disabled', 'focus', '#005fb8'),  # 鼠标悬停时的背景色
                ('!disabled', '!focus', '#007bff')  # 默认背景色
            ]
        )
        
        # 按钮容器
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, expand=YES, pady=5)
        
        # 浅色主题按钮
        light_btn = ttk.Button(
            button_frame,
            text=language_manager.get_text("light_theme"),
            style="Theme.TButton",
            width=20,  # 调整按钮宽度
            command=lambda: self._on_select("light")
        )
        light_btn.pack(pady=10, ipady=10)  # 增加按钮内部高度
        
        # 深色主题按钮
        dark_btn = ttk.Button(
            button_frame,
            text=language_manager.get_text("dark_theme"),
            style="Theme.TButton",
            width=20,  # 调整按钮宽度
            command=lambda: self._on_select("dark")
        )
        dark_btn.pack(pady=10, ipady=10)  # 增加按钮内部高度
        
    def _on_select(self, theme):
        """处理主题选择
        
        Args:
            theme: 选择的主题("light"或"dark")
        """
        logger.debug(f"用户选择了{theme}主题")
        self.selected_theme = theme
        self.destroy()
        
    def _on_cancel(self):
        """处理取消操作"""
        logger.debug("用户取消了主题选择")
        self.selected_theme = "light"  # 默认使用浅色主题
        self.destroy()
        
    def show(self):
        """显示对话框并返回选择的主题
        
        Returns:
            str: 选择的主题("light"或"dark")
        """
        self.wait_window()
        return self.selected_theme 