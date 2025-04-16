"""
主题切换对话框模块 (Tkinter + ttkbootstrap版本)

该模块提供了一个主题切换对话框，用于切换应用程序的主题。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from utils.theme_manager_tk import theme_manager
from utils.language_manager import language_manager
from utils.logger import Logger
from utils.config_manager import config_manager

# 获取日志记录器
logger = Logger.get_logger(__name__)

# 为简化版的主题管理器定义默认的主题数据
DEFAULT_THEME_DATA = {
    "light": {
        "background": "#f0f0f0",
        "foreground": "#000000",
        "button_bg": "#e1e1e1",
        "button_fg": "#000000",
        "success_bg": "#4CAF50",
        "success_fg": "#ffffff"
    },
    "dark": {
        "background": "#2d2d2d",
        "foreground": "#ffffff",
        "button_bg": "#3d3d3d",
        "button_fg": "#ffffff",
        "success_bg": "#388E3C",
        "success_fg": "#ffffff"
    }
}

class ThemePreviewFrame(ttk.Frame):
    """主题预览框架"""
    
    def __init__(self, parent, theme_id, theme_data):
        """初始化主题预览框架
        
        Args:
            parent: 父窗口
            theme_id: 主题ID
            theme_data: 主题数据
        """
        super().__init__(parent, width=100, height=30)
        self.theme_id = theme_id
        self.theme_data = theme_data
        
        # 设置固定大小
        self.pack_propagate(False)
        
        # 设置边框
        self.configure(relief="raised", borderwidth=1)
        
        # 获取主题颜色
        bg_color = theme_data.get("background", "#ffffff")
        fg_color = theme_data.get("foreground", "#000000")
        
        # 创建显示标签
        label = ttk.Label(
            self, 
            text="Aa", 
            font=("Microsoft YaHei", 12, "bold"),
            style=f"{theme_id}.TLabel"
        )
        label.pack(expand=YES, fill=BOTH)
        
        # 配置特定样式
        style = ttk.Style()
        style.configure(f"{theme_id}.TFrame", background=bg_color)
        style.configure(f"{theme_id}.TLabel", 
                       background=bg_color, 
                       foreground=fg_color,
                       font=("Microsoft YaHei", 12, "bold"))

class ThemeDialog(tk.Toplevel):
    """主题切换对话框类"""
    
    def __init__(self, parent=None, callback=None):
        """初始化主题切换对话框
        
        Args:
            parent: 父窗口
            callback: 主题变更后的回调函数
        """
        super().__init__(parent)
        
        # 保存回调函数
        self.callback = callback
        
        # 设置对话框属性
        self.title(language_manager.get_text("theme_dialog_title"))
        self.minsize(400, 300)
        
        # 居中显示（相对于父窗口）
        if parent:
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            
            window_width = 400
            window_height = 300
            
            x = parent_x + (parent_width - window_width) // 2
            y = parent_y + (parent_height - window_height) // 2
            
            # 确保窗口完全可见
            x = max(0, min(x, self.winfo_screenwidth() - window_width))
            y = max(0, min(y, self.winfo_screenheight() - window_height))
            
            self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 初始化结果
        self.result = None
        self.is_canceled = True
        
        # 创建界面
        self._create_widgets()
        
        # 使对话框模态
        self.transient(parent)
        self.grab_set()
        
        # 确保对话框显示在前台
        self.attributes('-topmost', True)
        self.update()
        self.attributes('-topmost', False)
        
        # 焦点设置
        self.focus_force()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 获取全局字体设置
        base_font_size = config_manager.get_app_config("ui.font.size", 8)
        base_font = ("Microsoft YaHei", base_font_size)
        title_font = ("Microsoft YaHei", base_font_size + 2, "bold")
        button_font = ("Microsoft YaHei", base_font_size, "bold")
        
        # 创建主布局框架
        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        # 创建标题标签
        self.title_label = ttk.Label(
            self.main_frame, 
            text=language_manager.get_text("theme_dialog_title"),
            font=title_font
        )
        self.title_label.pack(pady=(0, 15))
        
        # 创建主题选择变量和框架
        self.theme_var = tk.StringVar(value=theme_manager.get_current_theme())
        self.theme_frame = ttk.Frame(self.main_frame)
        self.theme_frame.pack(fill=X, expand=YES, pady=10)
        
        # 获取主题列表
        theme_names = {
            "light": language_manager.get_text("light_theme"),
            "dark": language_manager.get_text("dark_theme")
        }
        
        # 配置样式
        style = ttk.Style()
        style.configure("Theme.TRadiobutton", 
                       font=button_font,
                       padding=(10, 5))
        
        # 创建主题单选按钮
        self.theme_radios = {}
        for theme_id, theme_name in theme_names.items():
            # 创建主题行框架
            theme_row = ttk.Frame(self.theme_frame)
            theme_row.pack(fill=X, pady=5)
            
            # 创建主题单选按钮
            radio = ttk.Radiobutton(
                theme_row,
                text=theme_name,
                variable=self.theme_var,
                value=theme_id,
                style="Theme.TRadiobutton"
            )
            radio.pack(side=LEFT, padx=(0, 10))
            radio._theme_id = theme_id
            self.theme_radios[theme_id] = radio
            
            # 创建主题预览
            theme_data = DEFAULT_THEME_DATA.get(theme_id, 
                                              {"background": "#ffffff", 
                                               "foreground": "#000000"})
            preview = ThemePreviewFrame(theme_row, theme_id, theme_data)
            preview.pack(side=LEFT)
        
        # 创建按钮框架
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=X, pady=15)
        
        # 配置按钮样式
        style.configure("Dialog.TButton", 
                       font=button_font,
                       padding=(10, 5))
        style.configure("Dialog.success.TButton",
                       font=button_font,
                       padding=(10, 5))
        
        # 创建取消按钮
        self.cancel_button = ttk.Button(
            button_frame,
            text=language_manager.get_text("cancel"),
            command=self.destroy,
            width=15,
            style="Dialog.TButton"
        )
        self.cancel_button.pack(side=RIGHT, padx=5)
        
        # 创建确定按钮
        self.ok_button = ttk.Button(
            button_frame,
            text=language_manager.get_text("confirm"),
            command=self._on_ok,
            width=15,
            style="Dialog.success.TButton"
        )
        self.ok_button.pack(side=RIGHT, padx=5)
    
    def _on_ok(self):
        """确定按钮事件处理"""
        # 获取选中的主题
        selected_theme = self.theme_var.get()
        
        if selected_theme:
            # 切换主题
            if theme_manager.switch_theme(selected_theme):
                logger.info(f"已切换到主题: {selected_theme}")
                self.result = selected_theme
                self.is_canceled = False
                
                # 调用回调函数
                if self.callback:
                    self.callback(selected_theme)
        
        # 关闭对话框
        self.destroy()
    
    def show(self):
        """显示对话框并等待结果
        
        Returns:
            str: 选择的主题ID，如果取消则为None
        """
        # 等待窗口关闭
        self.wait_window()
        
        # 返回结果
        return None if self.is_canceled else self.result
    
    def refresh_texts(self):
        """刷新所有文本"""
        try:
            # 更新窗口标题
            self.title(language_manager.get_text("theme_dialog_title"))
            
            # 更新标题标签
            self.title_label.configure(text=language_manager.get_text("theme_dialog_title"))
            
            # 更新主题单选按钮文本
            theme_names = {
                "light": language_manager.get_text("light_theme"),
                "dark": language_manager.get_text("dark_theme")
            }
            for theme_id, radio in self.theme_radios.items():
                radio.configure(text=theme_names[theme_id])
            
            # 更新按钮文本
            self.cancel_button.configure(text=language_manager.get_text("cancel"))
            self.ok_button.configure(text=language_manager.get_text("confirm"))
            
        except Exception as e:
            logger.error(f"刷新主题对话框文本出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc()) 