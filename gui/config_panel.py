"""
配置面板模块

该模块提供了配置选项的加载和展示功能。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox

from utils.language_manager import language_manager
from utils.logger import Logger
from core.config_processor import ConfigProcessor

class ConfigPanel(ttk.Frame):
    """配置面板类"""
    
    def __init__(self, parent, config_processor: ConfigProcessor):
        """初始化配置面板
        
        Args:
            parent: 父窗口
            config_processor: 配置选项处理器实例
        """
        super().__init__(parent, style="Panel.TFrame")
        
        # 保存参数
        self.config_processor = config_processor
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 创建界面
        self._create_widgets()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 创建标题标签
        title_label = ttk.Label(
            self,
            text=language_manager.get_text("config_panel_title"),
            style="Title.TLabel"
        )
        title_label.pack(fill=X, pady=(0, 10))
        
        # 创建工具栏框架
        toolbar_frame = ttk.LabelFrame(
            self,
            text=language_manager.get_text("tools"),
            style="Main.TLabelframe"
        )
        toolbar_frame.pack(fill=X, pady=(0, 10), padx=5)
        
        # 创建工具栏
        self._create_toolbar(toolbar_frame)
        
        # 创建树状视图框架
        tree_frame = ttk.LabelFrame(
            self,
            text=language_manager.get_text("config_tree"),
            style="Main.TLabelframe"
        )
        tree_frame.pack(fill=BOTH, expand=YES, padx=5)
        
        # 创建树状视图
        self._create_tree(tree_frame)
        
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
            
            # 配置标签样式
            self.tree.tag_configure("module", font=("Microsoft YaHei", 18, "bold"))
            self.tree.tag_configure("f_code", foreground="blue")
            self.tree.tag_configure("k_code", foreground="green")
                        
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
            
    def _import_excel(self):
        """导入Excel文件"""
        try:
            # 打开文件选择对话框
            file_path = filedialog.askopenfilename(
                title=language_manager.get_text("select_excel_file"),
                filetypes=[
                    (language_manager.get_text("excel_files"), "*.xlsx *.xlsm"),
                    (language_manager.get_text("all_files"), "*.*")
                ]
            )
            
            if file_path:
                # 导入Excel文件
                self.config_processor.import_excel(file_path)
                
                # 刷新树状视图
                self._refresh_tree()
                
                # 显示成功消息
                from utils.message_utils_tk import show_info
                show_info("excel_imported_successfully")
                
        except Exception as e:
            from utils.message_utils_tk import show_error
            show_error("excel_import_error", error=str(e))
            
    def _on_double_click(self, event):
        """双击事件处理"""
        # 获取选中的项
        item = self.tree.selection()[0]
        
        # 获取项的文本
        text = self.tree.item(item, "text")
        
        # 提取F码或K码
        code = text.split()[0]
        
        # 如果是F码或K码，发送到逻辑编辑区
        if code.startswith("F") or code.startswith("K"):
            self.insert_code(code)
            
    def insert_code(self, code: str):
        """插入代码到逻辑编辑区
        
        Args:
            code: 要插入的代码
        """
        # 获取主窗口
        main_window = self.winfo_toplevel()
        
        # 获取逻辑面板
        if hasattr(main_window, 'logic_panel'):
            main_window.logic_panel.insert_code(code)
            
    def refresh_texts(self):
        """刷新所有文本"""
        # 刷新标题
        for child in self.winfo_children():
            if isinstance(child, ttk.Label) and "Title.TLabel" in str(child.cget("style")):
                child.configure(text=language_manager.get_text("config_panel_title"))
                break
        
        # 遍历所有 LabelFrame
        for frame in self.winfo_children():
            if isinstance(frame, ttk.LabelFrame):
                current_text = str(frame.cget("text")).lower()
                
                # 更新工具栏框架
                if "tools" in current_text:
                    frame.configure(text=language_manager.get_text("tools"))
                    # 更新按钮文本
                    toolbar = frame.winfo_children()[0]  # 获取工具栏Frame
                    for btn in toolbar.winfo_children():
                        if isinstance(btn, ttk.Button):
                            current_btn_text = str(btn.cget("text")).lower()
                            if "import" in current_btn_text:
                                btn.configure(text=language_manager.get_text("import_config"))
                            elif "refresh" in current_btn_text:
                                btn.configure(text=language_manager.get_text("refresh"))
                                
                # 更新配置树框架
                elif "config_tree" in current_text:
                    frame.configure(text=language_manager.get_text("config_tree")) 