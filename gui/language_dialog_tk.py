"""
语言选择对话框模块 (Tkinter + ttkbootstrap版本)

该模块提供了一个语言选择对话框，用于选择应用程序的界面语言。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from utils.config_manager import config_manager
from utils.logger import Logger

# 获取日志记录器
logger = Logger.get_logger(__name__)

# 语言配置
LANGUAGES = {
    "zh": {
        "name": "简体中文"
    },
    "en": {
        "name": "English"
    },
    "de": {
        "name": "Deutsch"
    }
}

class LanguageDialog:
    """语言选择对话框类"""
    
    def __init__(self, parent=None):
        """初始化语言选择对话框
        
        Args:
            parent: 父窗口
        """
        # 储存父窗口引用
        self.parent = parent
        self.window = None
        self.result = None
        self.is_canceled = True
    
    def _create_window(self):
        """创建窗口"""
        # 创建一个顶层窗口
        self.window = tk.Toplevel(self.parent)
        
        # 设置对话框属性
        self.window.title("语言选择 / Language Selection / Sprachauswahl")
        self.window.minsize(300, 300)  # 调整最小尺寸
        self.window.resizable(False, False)  # 禁止调整大小
        
        # 设置窗口大小
        window_width = 300  # 调整窗口宽度
        window_height = 300  # 调整窗口高度
        
        # 获取屏幕尺寸
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # 计算居中位置
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        # 设置窗口位置和大小
        self.window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # 使对话框模态
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # 确保对话框显示在前台
        self.window.attributes('-topmost', True)
        self.window.update()
        self.window.attributes('-topmost', False)
        
        # 焦点设置
        self.window.focus_force()
        
        # 创建界面组件
        self._create_widgets()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主布局框架
        main_frame = ttk.Frame(self.window, padding=20)  # 减小内边距
        main_frame.pack(fill=BOTH, expand=YES)
        
        # 创建标题标签 - 分三行显示三种语言
        title_label = ttk.Label(
            main_frame, 
            text="请选择语言\nSelect Language\nSprache wählen",
            font=("Microsoft YaHei", 12, "bold"),  # 调整字体大小
            justify="center",
            wraplength=260  # 调整文本换行宽度
        )
        title_label.pack(pady=(0, 15))
        
        # 获取支持的语言列表
        supported_languages = config_manager.get_app_config("supported_languages", ["zh", "en", "de"])
        
        # 创建语言按钮 - 定义统一字体大小的按钮样式
        button_style = ttk.Style()
        button_style.configure(
            "Language.TButton", 
            font=("Microsoft YaHei", 11, "bold"),  # 调整字体大小
            padding=(8, 4)  # 调整按钮内边距
        )
        
        # 按钮容器
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, expand=YES, pady=5)
        
        for lang_code in supported_languages:
            if lang_code in LANGUAGES:
                # 创建语言按钮
                lang_button = ttk.Button(
                    button_frame,
                    text=LANGUAGES[lang_code]["name"],
                    command=lambda code=lang_code: self._on_language_selected(code),
                    width=15,  # 调整按钮宽度
                    style="Language.TButton"
                )
                lang_button.pack(pady=8, ipady=4)  # 调整按钮间距和内部高度
    
    def _on_language_selected(self, lang_code):
        """语言选择事件处理"""
        self.result = lang_code
        self.is_canceled = False
        logger.info(f"已选择语言: {self.result}")
        
        # 关闭对话框
        self.window.destroy()
    
    def _on_close(self):
        """窗口关闭事件处理"""
        self.result = None
        self.is_canceled = True
        self.window.destroy()
    
    def show(self):
        """显示对话框并等待结果
        
        Returns:
            str: 选择的语言代码，如果取消则为None
        """
        # 创建窗口
        self._create_window()
        
        # 等待窗口关闭
        if self.parent:
            self.parent.wait_window(self.window)
        else:
            self.window.wait_window()
        
        # 返回结果
        return None if self.is_canceled else self.result 