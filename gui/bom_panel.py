"""
BOM面板模块

该模块提供了BOM文件的加载和展示功能。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox

from utils.language_manager import language_manager
from utils.logger import Logger
from core.bom_processor import BomProcessor

class BomPanel(ttk.Frame):
    """BOM面板类"""
    
    def __init__(self, parent, bom_processor: BomProcessor):
        """初始化BOM面板
        
        Args:
            parent: 父窗口
            bom_processor: BOM处理器实例
        """
        super().__init__(parent, style="Panel.TFrame")
        
        # 保存参数
        self.bom_processor = bom_processor
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 注册语言变化的回调函数
        language_manager.add_callback(self.refresh_texts)
        
        # 创建界面
        self._create_widgets()
        
    def destroy(self):
        """销毁面板时移除回调函数"""
        language_manager.remove_callback(self.refresh_texts)
        super().destroy()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 创建标题标签
        self.title_label = ttk.Label(
            self,
            text=language_manager.get_text("bom_panel_title"),
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
            text=language_manager.get_text("bom_tree"),
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
            text=language_manager.get_text("import_bom"),
            command=self._import_bom,
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
                
            # 获取所有BOM数据
            bom_data = self.bom_processor.get_bom_data()
            
            # 添加BOM节点
            for item_id, item_data in bom_data.items():
                # 创建主项节点
                main_node = self.tree.insert(
                    "",
                    "end",
                    text=f"{item_id} {item_data['name']}",
                    tags=("main_item",)
                )
                
                # 添加子项节点
                for sub_id, sub_data in item_data.get('sub_items', {}).items():
                    sub_node = self.tree.insert(
                        main_node,
                        "end",
                        text=f"{sub_id} {sub_data['name']}",
                        tags=("sub_item",)
                    )
                    
                    # 添加属性节点
                    for attr_name, attr_value in sub_data.get('attributes', {}).items():
                        self.tree.insert(
                            sub_node,
                            "end",
                            text=f"{attr_name}: {attr_value}",
                            tags=("attribute",)
                        )
            
            # 配置标签样式
            self.tree.tag_configure("main_item", font=("Microsoft YaHei", 18, "bold"))
            self.tree.tag_configure("sub_item", foreground="blue")
            self.tree.tag_configure("attribute", foreground="green")
                        
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
            
            # 添加菜单项
            menu.add_command(
                label=language_manager.get_text("copy_item"),
                command=lambda: self._copy_item(text)
            )
                
            # 显示菜单
            menu.post(event.x_root, event.y_root)
            
    def _import_bom(self):
        """导入BOM文件"""
        try:
            # 打开文件选择对话框
            file_path = filedialog.askopenfilename(
                title=language_manager.get_text("select_bom_file"),
                filetypes=[
                    (language_manager.get_text("excel_files"), "*.xlsx *.xlsm"),
                    (language_manager.get_text("all_files"), "*.*")
                ]
            )
            
            if file_path:
                # 导入BOM文件
                self.bom_processor.import_bom(file_path)
                
                # 刷新树状视图
                self._refresh_tree()
                
                # 显示成功消息
                from utils.message_utils_tk import show_info
                show_info("bom_imported_successfully")
                
        except Exception as e:
            from utils.message_utils_tk import show_error
            show_error("bom_import_error", error=str(e))
            
    def _on_double_click(self, event):
        """双击事件处理"""
        # 获取选中的项
        item = self.tree.selection()[0]
        
        # 获取项的文本
        text = self.tree.item(item, "text")
        
        # 复制项目文本
        self._copy_item(text)
            
    def _copy_item(self, text: str):
        """复制项目文本到剪贴板
        
        Args:
            text: 要复制的文本
        """
        self.clipboard_clear()
        self.clipboard_append(text)
            
    def refresh_texts(self):
        """刷新所有文本"""
        # 更新标题
        self.title_label.configure(text=language_manager.get_text("bom_panel_title"))
        
        # 更新工具栏标题和按钮
        self.toolbar_frame.configure(text=language_manager.get_text("tools"))
        self.import_btn.configure(text=language_manager.get_text("import_bom"))
        self.refresh_btn.configure(text=language_manager.get_text("refresh"))
        
        # 更新树状视图框架标题
        self.tree_frame.configure(text=language_manager.get_text("bom_tree"))
        
        # 强制更新显示
        self.update_idletasks() 