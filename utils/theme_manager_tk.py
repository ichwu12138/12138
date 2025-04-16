"""
主题管理模块 (Tkinter + ttkbootstrap版本)

该模块提供了一个主题管理器，用于管理应用程序的主题。
"""
import json
import os
from typing import Dict, Any, Optional
import ttkbootstrap as ttk

from utils.logger import Logger
from utils.config_manager import config_manager
from utils.observer import Observable

# 获取日志记录器
logger = Logger.get_logger(__name__)

class ThemeManager(Observable):
    """主题管理器类"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'ThemeManager':
        """获取主题管理器实例（单例模式）"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """初始化主题管理器"""
        super().__init__()
        
        # 默认主题
        self.current_theme = "light"
        
        # 主题数据
        self.theme_data = {
            "light": {
                "name": "浅色主题",
                "colors": {
                    "background": "#f0f0f0",
                    "foreground": "#000000",
                    "button_bg": "#e1e1e1",
                    "button_fg": "#000000",
                    "success_bg": "#4CAF50",
                    "success_fg": "#ffffff",
                    "tree_bg": "#ffffff",
                    "tree_fg": "#000000",
                    "tree_selected_bg": "#0078D7",
                    "tree_selected_fg": "#ffffff"
                }
            },
            "dark": {
                "name": "深色主题",
                "colors": {
                    "background": "#2d2d2d",
                    "foreground": "#ffffff",
                    "button_bg": "#3d3d3d",
                    "button_fg": "#ffffff",
                    "success_bg": "#388E3C",
                    "success_fg": "#ffffff",
                    "tree_bg": "#2c2c2c",
                    "tree_fg": "#ffffff",
                    "tree_selected_bg": "#0078D7",
                    "tree_selected_fg": "#ffffff"
                }
            }
        }
        
        # 字体设置
        self.fonts = {
            "default": ("Microsoft YaHei", 10),
            "default_bold": ("Microsoft YaHei", 10, "bold"),
            "title": ("Microsoft YaHei", 20, "bold"),
            "button": ("Microsoft YaHei", 16, "bold"),
            "tree": ("Microsoft YaHei", 16),
            "tree_bold": ("Microsoft YaHei", 16, "bold")
        }
        
        # 加载保存的主题
        saved_theme = config_manager.get_app_config("theme.current_theme", "light")
        if saved_theme in self.theme_data:
            self.current_theme = saved_theme
    
    def get_theme_names(self) -> Dict[str, str]:
        """获取主题名称字典"""
        return {
            "light": self.theme_data["light"]["name"],
            "dark": self.theme_data["dark"]["name"]
        }
    
    def get_current_theme(self) -> str:
        """获取当前主题ID
        
        Returns:
            str: 当前主题ID
        """
        return self.current_theme
    
    def switch_theme(self, theme_id: str) -> bool:
        """切换主题
        
        Args:
            theme_id: 主题ID
            
        Returns:
            bool: 是否切换成功
        """
        if theme_id not in self.theme_data:
            return False
            
        self.current_theme = theme_id
        config_manager.set_app_config("theme.current_theme", theme_id)
        
        # 通知观察者
        self.notify_observers(theme_id)
        
        return True
    
    def apply_theme(self, root) -> None:
        """应用主题到窗口
        
        Args:
            root: 根窗口
        """
        try:
            style = ttk.Style()
            theme_colors = self.theme_data[self.current_theme]["colors"]
            
            # 配置基础样式
            style.configure(".",
                          background=theme_colors["background"],
                          foreground=theme_colors["foreground"])
            
            # 配置标题标签样式
            style.configure("Title.TLabel",
                          font=self.fonts["title"],
                          background=theme_colors["background"],
                          foreground=theme_colors["foreground"])
            
            # 配置按钮样式
            style.configure("TButton",
                          font=self.fonts["button"],
                          background=theme_colors["button_bg"],
                          foreground=theme_colors["button_fg"])
            
            style.configure("Main.TButton",
                          font=self.fonts["button"],
                          background=theme_colors["button_bg"],
                          foreground=theme_colors["button_fg"])
            
            style.configure("success.Main.TButton",
                          font=self.fonts["button"],
                          background=theme_colors["success_bg"],
                          foreground=theme_colors["success_fg"])
            
            # 配置标签样式
            style.configure("TLabel",
                          font=self.fonts["default"],
                          background=theme_colors["background"],
                          foreground=theme_colors["foreground"])
            
            # 配置树状视图样式
            style.configure("Treeview",
                          font=self.fonts["tree"],
                          background=theme_colors["tree_bg"],
                          foreground=theme_colors["tree_fg"],
                          fieldbackground=theme_colors["tree_bg"])
            
            style.configure("Treeview.Heading",
                          font=self.fonts["tree_bold"])
            
            style.map("Treeview",
                     background=[("selected", theme_colors["tree_selected_bg"])],
                     foreground=[("selected", theme_colors["tree_selected_fg"])])
            
            # 配置单选按钮样式
            style.configure("TRadiobutton",
                          font=self.fonts["default"],
                          background=theme_colors["background"],
                          foreground=theme_colors["foreground"])
            
            # 配置框架样式
            style.configure("TFrame",
                          background=theme_colors["background"])
            
            style.configure("TLabelframe",
                          background=theme_colors["background"])
            
            style.configure("TLabelframe.Label",
                          font=self.fonts["default_bold"],
                          background=theme_colors["background"],
                          foreground=theme_colors["foreground"])
            
            # 应用主题
            theme_name = "darkly" if self.current_theme == "dark" else "litera"
            style.theme_use(theme_name)
            
            logger.info(f"已应用主题: {self.current_theme}")
            
        except Exception as e:
            logger.error(f"应用主题失败: {str(e)}", exc_info=True)
            raise

# 创建全局主题管理器实例
theme_manager = ThemeManager.get_instance() 