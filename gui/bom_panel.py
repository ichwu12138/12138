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
        
        # 配置样式
        style = ttk.Style()
        style.configure("Treeview", rowheight=100)  # 设置足够的行高以容纳两行文本
        
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
                # 只处理一级节点
                if item_data.get("level", 1) == 1:
                    self._add_tree_node("", item_id, item_data)
            
            # 配置标签样式 - 一级用18号，其他级别统一用16号
            self.tree.tag_configure("level_1", font=("Microsoft YaHei", 18, "bold"))
            self.tree.tag_configure("other_level", font=("Microsoft YaHei", 16, "bold"))
            
            # 设置行高
            style = ttk.Style()
            style.configure("Main.Treeview", rowheight=100)  # 设置行高为100像素
            
            # 绑定鼠标悬停事件
            self.tree.bind("<Motion>", self._on_mouse_motion)
            
            # 创建工具提示窗口（但暂不显示）
            self.tooltip = None
                        
        except Exception as e:
            from utils.message_utils_tk import show_error
            show_error("refresh_tree_error", error=str(e))
            
    def _add_tree_node(self, parent: str, item_id: str, item_data: dict):
        """递归添加树节点
        
        Args:
            parent: 父节点ID
            item_id: 当前节点ID
            item_data: 节点数据
        """
        # 获取层级
        level = item_data.get("level", 1)
        
        # 创建主节点文本 - 显示层级、编号和描述
        main_text = f"[{level}] {item_id}"
        if item_data.get("name"):
            main_text += f" - {item_data['name']}"
            
        # 如果有长文本，添加到下一行（使用换行符）
        if item_data.get("long_text"):
            main_text += f"\n{item_data['long_text']}"
            
        # 一级用level_1标签，其他级别用other_level标签
        level_tag = "level_1" if level == 1 else "other_level"
        
        # 创建节点
        node = self.tree.insert(
            parent,
            "end",
            text=main_text,
            tags=(level_tag,)
        )
        
        # 递归添加子节点
        for sub_id, sub_data in item_data.get("sub_items", {}).items():
            self._add_tree_node(node, sub_id, sub_data)
            
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
            
    def _on_mouse_motion(self, event):
        """处理鼠标移动事件"""
        # 获取鼠标下的项
        item = self.tree.identify_row(event.y)
        
        # 如果鼠标不在任何项上，隐藏工具提示
        if not item:
            self._hide_tooltip()
            return
            
        # 获取项的long_text
        values = self.tree.item(item)["values"]
        long_text = values[0] if values else ""
        
        # 如果没有long_text，隐藏工具提示
        if not long_text:
            self._hide_tooltip()
            return
            
        # 显示工具提示
        self._show_tooltip(event.x_root, event.y_root, long_text)
        
    def _show_tooltip(self, x, y, text):
        """显示工具提示
        
        Args:
            x: 屏幕X坐标
            y: 屏幕Y坐标
            text: 显示文本
        """
        # 如果工具提示窗口不存在，创建它
        if not self.tooltip:
            self.tooltip = tk.Toplevel(self)
            self.tooltip.wm_overrideredirect(True)  # 无边框窗口
            
            # 创建标签
            self.tooltip_label = ttk.Label(
                self.tooltip,
                text="",
                style="Tooltip.TLabel",
                padding=(8, 8),  # 适当的内边距
                justify="left",  # 文本左对齐
                anchor="w",      # 文本左对齐（west）
                wraplength=600   # 适当的文本换行宽度
            )
            self.tooltip_label.pack(fill=BOTH, expand=YES)
            
            # 创建工具提示样式
            style = ttk.Style()
            style.configure(
                "Tooltip.TLabel",
                font=("Microsoft YaHei", 24, "bold"),  # 调整为与 Treeview 相近的字体大小
                background="#FFFFCC",
                foreground="black"
            )
        
        # 更新文本并显示
        self.tooltip_label.configure(text=text)
        self.tooltip.deiconify()  # 确保窗口显示
        
        # 更新窗口以获取实际尺寸
        self.tooltip.update_idletasks()
        
        # 设置最小和最大尺寸
        min_width = 300   # 适当减小最小宽度
        max_width = 600   # 适当减小最大宽度
        min_height = 100  # 适当减小最小高度
        
        # 获取文本的像素宽度和高度
        text_width = self.tooltip_label.winfo_reqwidth()
        text_height = self.tooltip_label.winfo_reqheight()
        
        # 计算合适的窗口尺寸
        width = max(min_width, min(text_width + 16, max_width))
        height = max(min_height, text_height + 16)
        
        # 应用新的尺寸
        self.tooltip.geometry(f"{width}x{height}")
        
        # 调整位置（在鼠标右侧显示）
        screen_width = self.tooltip.winfo_screenwidth()
        screen_height = self.tooltip.winfo_screenheight()
        
        # 计算位置（在鼠标右侧15像素处）
        tooltip_x = min(x + 15, screen_width - width)
        tooltip_y = min(y - height//2, screen_height - height)  # 垂直居中于鼠标位置
        
        # 确保工具提示不会超出屏幕边界
        if tooltip_y < 0:
            tooltip_y = 0
        if tooltip_x < 0:
            tooltip_x = 0
            
        self.tooltip.wm_geometry(f"+{tooltip_x}+{tooltip_y}")
        self.tooltip.lift()  # 保持在最上层
        
    def _hide_tooltip(self):
        """隐藏工具提示"""
        if self.tooltip:
            self.tooltip.withdraw()
            
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