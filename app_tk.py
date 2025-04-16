"""
ZK配置器应用程序入口点 (Tkinter + ttkbootstrap版本)

该模块是应用程序的入口点，负责初始化应用程序并显示主窗口。
"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent
sys.path.append(str(src_dir))

# 导入tkinter和ttkbootstrap
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# 导入配置管理器
from utils.config_manager import config_manager

# 导入日志模块
from utils.logger import Logger
# 获取根日志记录器
logger = Logger.get_logger(__name__)

from utils.language_manager import language_manager
from gui.main_window_tk import MainWindow
from gui.language_dialog_tk import LanguageDialog
from gui.theme_dialog_tk import SimpleThemeDialog

def main():
    """应用程序主函数"""
    try:
        logger.info("正在启动程序...")
        logger.debug(f"Python版本: {sys.version}")
        logger.debug(f"当前工作目录: {os.getcwd()}")
        logger.debug(f"src_dir路径: {src_dir}")
        
        # 创建临时根窗口
        temp_root = tk.Tk()
        # 设置一个很小的尺寸并移到屏幕外
        temp_root.geometry("1x1+0+0")
        
        # 设置为无框架窗口
        temp_root.overrideredirect(True)
        
        # 设置DPI感知
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # 创建并显示语言选择对话框
        logger.info("正在创建语言选择对话框...")
        try:
            # 使用自定义的LanguageDialog类
            dialog = LanguageDialog(temp_root)
            # 显示对话框并获取选择结果
            selected_lang = dialog.show()
            logger.info(f"语言选择结果: {selected_lang}")
            
        except Exception as e:
            logger.error(f"创建语言选择对话框失败: {str(e)}", exc_info=True)
            temp_root.destroy()
            raise
        
        # 如果没有选择语言，退出程序
        if not selected_lang:
            logger.info("用户取消了语言选择，程序退出")
            temp_root.destroy()
            return 0
        
        # 设置语言
        language_manager.set_language(selected_lang)
        
        # 显示主题选择对话框
        logger.info("正在创建主题选择对话框...")
        try:
            theme_dialog = SimpleThemeDialog(temp_root)
            selected_theme = theme_dialog.show()
            logger.info(f"主题选择结果: {selected_theme}")
            
            # 保存主题选择到配置文件
            config_manager.set_app_config("theme.current_theme", selected_theme)
            
        except Exception as e:
            logger.error(f"创建主题选择对话框失败: {str(e)}", exc_info=True)
            selected_theme = "light"  # 默认使用浅色主题
        
        # 【关键改动1】创建主窗口前，先确保处理所有事件
        temp_root.update()
        
        # 【关键改动2】不销毁临时窗口，而是将其转换为主窗口
        logger.info("正在配置主窗口...")
        
        # 配置主窗口属性
        temp_root.title("ZK配置器")
        temp_root.overrideredirect(False)  # 取消无边框模式
        
        # 应用ttkbootstrap样式 - 根据用户选择设置主题
        theme_name = "litera" if selected_theme == "light" else "darkly"
        style = ttk.Style(theme=theme_name)
        
        # 从配置文件获取基础字体大小
        base_font_size = config_manager.get_app_config("ui.font.size", 16)
        font_family = config_manager.get_app_config("ui.font.family", "Microsoft YaHei")

        # 定义字体
        base_font = (font_family, base_font_size)
        bold_font = (font_family, base_font_size, "bold")
        title_font = (font_family, base_font_size + 4, "bold")
        large_font = (font_family, base_font_size + 2)
        large_bold_font = (font_family, base_font_size + 2, "bold")

        # 配置基础样式
        style.configure("TButton", 
                       font=base_font, 
                       padding=(10, 5),
                       foreground="white")  # 设置按钮文字颜色为白色
        
        style.map('TButton',
                 foreground=[('active', 'white'),  # 鼠标悬停时保持白色
                            ('disabled', 'gray75')],  # 禁用时使用浅灰色
                 background=[('active', '!disabled', 'focus', '#005fb8'),  # 鼠标悬停时的背景色
                            ('!disabled', '!focus', '#007bff')])  # 默认背景色
        
        style.configure("TLabel", 
                       font=base_font)
        
        style.configure("TEntry", 
                       font=base_font)
        
        style.configure("TCheckbutton", 
                       font=base_font)
        
        style.configure("TRadiobutton", 
                       font=base_font)
        
        # 标题和标签框架样式
        style.configure("TLabelframe.Label", 
                       font=bold_font)
        
        style.configure("Title.TLabel", 
                       font=title_font)
        
        style.configure("TNotebook.Tab", 
                       font=bold_font, 
                       padding=(10, 5))

        # 菜单字体
        temp_root.option_add("*Menu.font", bold_font)
        
        # 树状视图样式
        style.configure("Treeview", 
                       rowheight=60, 
                       font=large_bold_font)
        
        style.configure("Treeview.Heading", 
                       font=bold_font)
        
        # 大按钮样式
        style.configure("Large.TButton", 
                       font=large_bold_font, 
                       padding=(15, 10), 
                       width=15,
                       foreground="white")  # 设置大按钮文字颜色为白色
        
        style.map('Large.TButton',
                 foreground=[('active', 'white'),  # 鼠标悬停时保持白色
                            ('disabled', 'gray75')],  # 禁用时使用浅灰色
                 background=[('active', '!disabled', 'focus', '#005fb8'),  # 鼠标悬停时的背景色
                            ('!disabled', '!focus', '#007bff')])  # 默认背景色
        
        # 成功按钮样式
        style.configure("success.Large.TButton", 
                       font=large_bold_font, 
                       padding=(15, 10), 
                       width=15,
                       foreground="white")  # 设置成功按钮文字颜色为白色
        
        style.map('success.Large.TButton',
                 foreground=[('active', 'white'),  # 鼠标悬停时保持白色
                            ('disabled', 'gray75')],  # 禁用时使用浅灰色
                 background=[('active', '!disabled', 'focus', '#218838'),  # 鼠标悬停时的背景色
                            ('!disabled', '!focus', '#28a745')])  # 默认背景色
        
        style.configure("success.TButton", 
                       font=bold_font, 
                       padding=(10, 5),
                       foreground="white")  # 设置成功按钮文字颜色为白色
        
        style.map('success.TButton',
                 foreground=[('active', 'white'),
                            ('disabled', 'gray75')],
                 background=[('active', '!disabled', 'focus', '#218838'),
                            ('!disabled', '!focus', '#28a745')])
        
        # 标签框架标题样式
        style.configure("Large.TLabelframe.Label", 
                       font=large_bold_font)
        
        # 大单选按钮样式
        style.configure("Large.TRadiobutton", 
                       font=large_bold_font)
        
        # 大标签样式
        style.configure("Large.TLabel", 
                       font=large_bold_font)
        
        # 树状视图大字体样式
        style.configure("Large.Treeview", 
                       font=("Microsoft YaHei", 20, "bold"), 
                       rowheight=60)
        
        style.configure("Large.Treeview.Heading", 
                       font=large_bold_font)
        
        # 强制更新样式 - 重要！
        temp_root.update_idletasks()
        
        # 设置为最大化窗口（但非全屏），且可调整大小
        try:
            # Windows平台
            if sys.platform == 'win32':
                # 设置为最大化状态，但不是全屏
                temp_root.state('zoomed')
            # macOS平台
            elif sys.platform == 'darwin':
                # macOS使用几何大小设置
                w, h = temp_root.winfo_screenwidth() * 0.9, temp_root.winfo_screenheight() * 0.9
                x, y = (temp_root.winfo_screenwidth() - w) / 2, (temp_root.winfo_screenheight() - h) / 2
                temp_root.geometry('%dx%d+%d+%d' % (w, h, x, y))
            # Linux平台
            else:
                temp_root.attributes('-zoomed', True)
            
            # 允许调整窗口大小
            temp_root.resizable(True, True)
        except Exception as e:
            logger.warning(f"无法设置窗口最大化: {str(e)}")
            # 如果失败，使用屏幕分辨率的80%
            screen_width = temp_root.winfo_screenwidth()
            screen_height = temp_root.winfo_screenheight()
            window_width = int(screen_width * 0.8)
            window_height = int(screen_height * 0.8)
            temp_root.geometry(f"{window_width}x{window_height}+{(screen_width-window_width)//2}+{(screen_height-window_height)//2}")
            # 允许调整窗口大小
            temp_root.resizable(True, True)
        
        # 强制更新窗口以确保存在并可见
        temp_root.update_idletasks()
        
        try:
            # 添加全局异常处理
            def report_callback_exception(exc, val, tb):
                logger.critical(f"未捕获的异常: {val}", exc_info=(exc, val, tb))
                import traceback
                logger.critical(f"详细错误栈:\n{traceback.format_exception(exc, val, tb)}")
                
            temp_root.report_callback_exception = report_callback_exception
            
            # 创建主窗口实例
            logger.info("开始创建MainWindow实例...")
            main_window = MainWindow(temp_root)
            logger.info("MainWindow实例创建完成")
            
            # 确保窗口在前台
            temp_root.deiconify()
            temp_root.lift()
            temp_root.focus_force()  # 强制获取焦点
            
            # 设置置顶再取消置顶，确保窗口显示
            temp_root.attributes('-topmost', True)
            temp_root.after(500, lambda: temp_root.attributes('-topmost', False))
            
            # 确保更新显示
            temp_root.update()
            
            # 运行主循环
            logger.info("开始mainloop()...")
            temp_root.mainloop()
            return 0
            
        except Exception as e:
            logger.critical(f"创建主窗口失败: {str(e)}", exc_info=True)
            import traceback
            logger.critical(f"详细错误：\n{traceback.format_exc()}")
            raise
            
    except Exception as e:
        logger.critical(f"启动程序时出错: {str(e)}", exc_info=True)
        import traceback
        logger.critical(f"详细错误：\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    sys.exit(main())