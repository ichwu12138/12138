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
        self.window.minsize(400, 400)  # 调整最小尺寸
        self.window.resizable(False, False)  # 禁止调整大小
        
        # 设置窗口大小
        window_width = 400  # 调整窗口宽度
        window_height = 400  # 调整窗口高度
        
        # 获取所有屏幕的信息
        if self.parent:
            # 获取父窗口所在的屏幕
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            # 检查父窗口是否太小或在屏幕外
            is_parent_invalid = (
                parent_width <= 1 or 
                parent_height <= 1 or 
                parent_x <= 0 or 
                parent_y <= 0 or
                parent_x >= self.window.winfo_screenwidth() or
                parent_y >= self.window.winfo_screenheight()
            )
            
            if not is_parent_invalid:
                # 如果父窗口正常，相对于父窗口居中
                x = parent_x + (parent_width - window_width) // 2
                y = parent_y + (parent_height - window_height) // 2
            else:
                # 如果父窗口无效，获取鼠标所在屏幕并在该屏幕居中
                try:
                    # 获取鼠标位置
                    mouse_x = self.window.winfo_pointerx()
                    mouse_y = self.window.winfo_pointery()
                    
                    # 获取鼠标所在屏幕的信息
                    screen_width = self.window.winfo_screenwidth()
                    screen_height = self.window.winfo_screenheight()
                    
                    # 计算居中位置
                    x = (screen_width - window_width) // 2
                    y = (screen_height - window_height) // 2
                    
                    # 如果系统支持，尝试获取多显示器信息
                    try:
                        if hasattr(self.window, 'winfo_vrootwidth'):
                            total_width = self.window.winfo_vrootwidth()
                            total_height = self.window.winfo_vrootheight()
                            
                            # 确定鼠标在哪个屏幕
                            if mouse_x > screen_width:
                                x += screen_width
                    except:
                        pass
                        
                except:
                    # 如果无法获取鼠标位置，就在主屏幕居中
                    screen_width = self.window.winfo_screenwidth()
                    screen_height = self.window.winfo_screenheight()
                    x = (screen_width - window_width) // 2
                    y = (screen_height - window_height) // 2
        else:
            # 如果没有父窗口，在主屏幕居中
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
        
        # 确保窗口完全可见
        x = max(0, min(x, self.window.winfo_screenwidth() - window_width))
        y = max(0, min(y, self.window.winfo_screenheight() - window_height))
        
        # 设置位置和大小
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 使对话框模态
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # 确保对话框显示在前台
        self.window.attributes('-topmost', True)
        self.window.update()
        self.window.attributes('-topmost', False)
        
        # 焦点设置
        self.window.focus_force()
        
        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 创建界面组件
        self._create_widgets()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主布局框架
        main_frame = ttk.Frame(self.window, padding=30)  # 调整内边距
        main_frame.pack(fill=BOTH, expand=YES)
        
        # 创建标题标签 - 分三行显示三种语言
        title_label = ttk.Label(
            main_frame, 
            text="请选择语言\nSelect Language\nSprache wählen",  # 三行显示
            font=("Microsoft YaHei", 16, "bold"),  # 设置字体大小为16
            justify="center",  # 居中对齐
            wraplength=360  # 调整文本换行宽度
        )
        title_label.pack(pady=(0, 20))  # 调整上下间距
        
        # 获取支持的语言列表
        supported_languages = config_manager.get_app_config("supported_languages", ["zh", "en", "de"])
        
        # 创建语言按钮 - 定义统一字体大小的按钮样式
        button_style = ttk.Style()
        button_style.configure("Language.TButton", 
                             font=("Microsoft YaHei", 16, "bold"),  # 设置字体大小为16
                             padding=(10, 5))  # 调整按钮内边距
        
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
                    width=20,  # 调整按钮宽度
                    style="Language.TButton"  # 使用自定义样式
                )
                # 配置按钮布局
                lang_button.pack(pady=10, ipady=5)  # 调整按钮间距和内部高度
        
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