"""
配置面板模块

该模块提供了配置选项的导入、编辑和管理功能。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import os

from utils.language_manager import language_manager
from utils.logger import Logger
from core.config_processor import ConfigProcessor
from utils.config_manager import config_manager

class ConfigPanel(ttk.Frame):
    """配置面板类"""
    
    def __init__(self, master, config_processor: ConfigProcessor):
        """初始化配置面板
        
        Args:
            master: 父窗口
            config_processor: 配置处理器实例
        """
        super().__init__(master)
        
        # 保存参数
        self.config_processor = config_processor
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 创建界面
        self._create_widgets()
        
    def _import_excel(self, file_path=None):
        """导入Excel文件
        
        Args:
            file_path: 文件路径,如果为None则弹出文件选择对话框
        """
        try:
            if file_path is None:
                # 检查是否有上次的配置文件路径
                last_config_path = config_manager.get_app_config("last_config_path")
                if last_config_path and os.path.exists(last_config_path):
                    self.logger.info(f"发现上次的配置文件路径: {last_config_path}")
                    if messagebox.askyesno(
                        language_manager.get_text("confirm"),
                        language_manager.get_text("load_last_config_confirm")
                    ):
                        self.logger.info("用户选择加载上次的配置文件")
                        file_path = last_config_path
                
                # 如果用户不想加载上次的文件或没有上次的文件，显示文件选择对话框
                if not file_path:
                    file_path = filedialog.askopenfilename(
                        title=language_manager.get_text("select_config_file"),
                        filetypes=[
                            (language_manager.get_text("excel_files"), "*.xlsx *.xlsm"),
                            (language_manager.get_text("all_files"), "*.*")
                        ]
                    )
                    if file_path:
                        self.logger.info(f"用户选择了新的配置文件: {file_path}")
                
            if file_path:
                # 导入Excel文件
                self.config_processor.import_excel(file_path)
                self.logger.info(f"成功导入配置文件: {file_path}")
                
                # 更新显示
                self._update_display()
                
                # 保存文件路径到app_config.json
                if hasattr(self.master, 'main_window'):
                    self.master.main_window._save_config_path(file_path)
                    self.logger.info(f"已保存配置文件路径到app_config.json: {file_path}")
                else:
                    # 尝试从根窗口获取MainWindow实例
                    root = self.winfo_toplevel()
                    if hasattr(root, 'main_window'):
                        root.main_window._save_config_path(file_path)
                        self.logger.info(f"已保存配置文件路径到app_config.json: {file_path}")
                    else:
                        self.logger.warning("无法保存配置文件路径：未找到MainWindow实例")
                
                # 显示成功消息
                messagebox.showinfo(
                    language_manager.get_text("success_title"),
                    language_manager.get_text("import_config_success")
                )
                
        except Exception as e:
            self.logger.error(f"导入配置文件失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error_title"),
                language_manager.get_text("import_config_error")
            )

    def _update_display(self):
        """更新显示"""
        try:
            # 刷新树状视图
            self._refresh_tree()
        except Exception as e:
            self.logger.error(f"更新显示失败: {str(e)}")
            messagebox.showerror(
                language_manager.get_text("error"),
                language_manager.get_text("update_display_error")
            )

    def _create_widgets(self):
        """创建界面组件"""
        # 创建标题标签
        self.title_label = ttk.Label(
            self,
            text=language_manager.get_text("config_panel_title"),
            style="Title.TLabel"
        )
        self.title_label.pack(fill=X, pady=(0, 10))
        
        # 创建工具栏框架
        self.toolbar_frame = ttk.LabelFrame(
            self,
            text=language_manager.get_text("tools"),
            style="Main.TLabelframe"
        )
        self.toolbar_frame.pack(fill=X, pady=(0, 10), padx=5)
        
        # 创建工具栏
        self._create_toolbar(self.toolbar_frame)
        
        # 创建树状视图框架
        self.tree_frame = ttk.LabelFrame(
            self,
            text=language_manager.get_text("config_tree"),
            style="Main.TLabelframe"
        )
        self.tree_frame.pack(fill=BOTH, expand=YES, padx=5)
        
        # 创建树状视图
        self._create_tree(self.tree_frame)
        
    def _create_toolbar(self, parent):
        """创建工具栏"""
        # 创建工具栏框架
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=X, pady=5)
        
        # 添加导入按钮
        self.import_btn = ttk.Button(
            toolbar,
            text=language_manager.get_text("import_config"),
            command=self._import_excel,
            style="Main.TButton",
            width=20
        )
        self.import_btn.pack(side=LEFT, padx=5)
        
        # 添加刷新按钮
        self.refresh_btn = ttk.Button(
            toolbar,
            text=language_manager.get_text("refresh"),
            command=self._refresh_tree,
            style="Main.TButton",
            width=20
        )
        self.refresh_btn.pack(side=LEFT, padx=5)
        
    def _create_tree(self, parent):
        """创建树状视图"""
        # 创建树状视图框架
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # 创建树状视图
        self.tree = ttk.Treeview(
            tree_frame,
            selectmode="browse",
            style="Main.Treeview",
            show="tree"  # 只显示树形结构，不显示列头
        )
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # 添加垂直滚动条
        vsb = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview
        )
        vsb.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=vsb.set)
        
        # 添加水平滚动条
        hsb = ttk.Scrollbar(
            parent,
            orient="horizontal",
            command=self.tree.xview
        )
        hsb.pack(fill=X, pady=(0, 5))
        self.tree.configure(xscrollcommand=hsb.set)
        
        # 绑定事件
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-1>", self._on_single_click)
        self.tree.bind("<Button-3>", self._on_right_click)
        
    def _refresh_tree(self):
        """刷新树状视图"""
        try:
            # 清空树状视图
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # 获取所有模块
            modules = self.config_processor.get_modules()
            
            # 添加模块节点
            for module_id, f_codes in modules.items():
                module_node = self.tree.insert(
                    "",
                    "end",
                    text=module_id,
                    tags=("module",)
                )
                
                # 添加F码节点
                for f_code in f_codes:
                    f_node = self.tree.insert(
                        module_node,
                        "end",
                        text=f"{f_code} {self.config_processor.get_name(f_code)}",
                        tags=("f_code",)
                    )
                    
                    # 添加K码节点
                    for k_code in self.config_processor.get_k_codes(f_code):
                        self.tree.insert(
                            f_node,
                            "end",
                            text=f"{k_code} {self.config_processor.get_name(k_code)}",
                            tags=("k_code",)
                        )
            
            # 配置标签样式 - 全部使用黑色
            self.tree.tag_configure("module", font=("Microsoft YaHei", 18, "bold"))
            self.tree.tag_configure("f_code", font=("Microsoft YaHei", 16))
            self.tree.tag_configure("k_code", font=("Microsoft YaHei", 16))
                        
        except Exception as e:
            from utils.message_utils_tk import show_error
            show_error("refresh_tree_error", error=str(e))
            
    def _on_right_click(self, event):
        """右键事件处理"""
        # 获取点击位置的项
        item = self.tree.identify_row(event.y)
        if item:
            # 选中该项
            self.tree.selection_set(item)
            
            # 创建右键菜单
            menu = tk.Menu(self, tearoff=0)
            menu.configure(font=("Microsoft YaHei", 16))  # 使用统一的菜单字体大小
            
            # 获取项的文本
            text = self.tree.item(item, "text")
            code = text.split()[0]
            
            # 如果是F码或K码，添加复制选项
            if code.startswith("F") or code.startswith("K"):
                menu.add_command(
                    label=language_manager.get_text("copy_code"),
                    command=lambda: self.insert_code(code)
                )
                
            # 显示菜单
            menu.post(event.x_root, event.y_root)
            
    def _on_single_click(self, event):
        """单击事件处理"""
        # 获取点击位置的项
        item = self.tree.identify_row(event.y)
        if item:
            # 如果项是关闭的，则打开它
            if not self.tree.item(item, "open"):
                self.tree.item(item, open=True)
            # 如果项是打开的，则关闭它
            else:
                self.tree.item(item, open=False)
            
    def _on_double_click(self, event):
        """双击事件处理"""
        try:
            # 获取选中的项
            item = self.tree.selection()[0]
            self.logger.debug(f"ConfigPanel: 双击选中项 ID: {item}")
            
            # 获取项的文本
            text = self.tree.item(item, "text")
            self.logger.debug(f"ConfigPanel: 选中项文本: {text}")
            
            # 提取K码
            code = text.split()[0]
            self.logger.debug(f"ConfigPanel: 提取的代码: {code}")
            
            # 如果是K码，发送到逻辑编辑区
            if code.startswith("K"):
                self.logger.info(f"ConfigPanel: 准备插入K码: {code}")
                self.insert_code(code)
            else:
                self.logger.debug(f"ConfigPanel: 忽略非K码: {code}")
                
        except Exception as e:
            self.logger.error(f"ConfigPanel: 双击处理出错: {str(e)}", exc_info=True)

    def insert_code(self, code: str):
        """插入代码到逻辑编辑区
        
        Args:
            code: 要插入的代码
        """
        try:
            # 获取主窗口
            root = self.winfo_toplevel()
            self.logger.debug("ConfigPanel: 获取根窗口成功")
            
            # 获取MainWindow实例
            if hasattr(root, 'main_window'):
                main_window = root.main_window
                self.logger.debug("ConfigPanel: 获取MainWindow实例成功")
                
                # 获取逻辑面板
                logic_panel = main_window.get_logic_panel()
                if logic_panel:
                    self.logger.debug("ConfigPanel: 找到逻辑面板")
                    logic_panel.insert_code(code)
                    self.logger.info(f"ConfigPanel: 成功发送代码到逻辑面板: {code}")
                else:
                    self.logger.warning("ConfigPanel: 未找到逻辑面板")
            else:
                self.logger.warning("ConfigPanel: 未找到MainWindow实例")
                
        except Exception as e:
            self.logger.error(f"ConfigPanel: 插入代码时出错: {str(e)}", exc_info=True)
            
    def refresh_texts(self):
        """刷新所有文本"""
        # 更新标题
        self.title_label.configure(text=language_manager.get_text("config_panel_title"))
        
        # 更新工具栏标题和按钮
        self.toolbar_frame.configure(text=language_manager.get_text("tools"))
        self.import_btn.configure(text=language_manager.get_text("import_config"))
        self.refresh_btn.configure(text=language_manager.get_text("refresh"))
        
        # 更新树状视图框架标题
        self.tree_frame.configure(text=language_manager.get_text("config_tree"))
        
        # 强制更新显示
        self.update_idletasks() 