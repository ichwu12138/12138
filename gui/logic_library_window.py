"""
逻辑关系库窗口模块

该模块提供了一个独立窗口来展示所有保存的逻辑规则。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from utils.language_manager import language_manager
from utils.logger import Logger
from core.logic_builder import LogicBuilder

class LogicLibraryWindow(tk.Toplevel):
    """逻辑关系库窗口类"""
    
    def __init__(self, parent, logic_builder: LogicBuilder):
        """初始化逻辑关系库窗口
        
        Args:
            parent: 父窗口
            logic_builder: 逻辑构建器实例
        """
        super().__init__(parent)
        
        # 保存参数
        self.logic_builder = logic_builder
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 设置窗口属性
        self.title(language_manager.get_text("logic_library"))
        self.minsize(1024, 768)  # 设置更大的最小尺寸
        
        # 设置初始窗口大小为屏幕的80%
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # 居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 允许调整大小
        self.resizable(True, True)
        
        # 创建界面
        self._create_widgets()
        
        # 确保窗口显示在前台
        self.lift()
        self.focus_force()
        
        # 添加最大化按钮
        if hasattr(self, 'attributes'):
            try:
                # Windows平台
                self.attributes('-toolwindow', 0)  # 显示最大化按钮
                self.state('normal')  # 初始状态为正常
            except:
                pass
        
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # 创建搜索框架
        self._create_search_frame(main_frame)
        
        # 创建规则列表框架
        self._create_rules_frame(main_frame)
        
    def _create_search_frame(self, parent):
        """创建搜索框架"""
        frame = ttk.LabelFrame(
            parent,
            text=language_manager.get_text("search"),
            padding=5
        )
        frame.pack(fill=X, pady=(0, 10))
        
        # 创建搜索输入框
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            frame,
            textvariable=self.search_var,
            font=("Microsoft YaHei", 16)
        )
        search_entry.pack(side=LEFT, fill=X, expand=YES, padx=5)
        
        # 创建清除按钮
        clear_btn = ttk.Button(
            frame,
            text=language_manager.get_text("clear"),
            command=self._clear_search,
            width=10
        )
        clear_btn.pack(side=LEFT, padx=5)
        
        # 绑定搜索事件
        self.search_var.trace_add("write", self._on_search_changed)
        
    def _create_rules_frame(self, parent):
        """创建规则列表框架"""
        frame = ttk.LabelFrame(
            parent,
            text=language_manager.get_text("rules"),
            padding=5
        )
        frame.pack(fill=BOTH, expand=YES)
        
        # 创建树状视图
        columns = ("rule_id", "type", "condition", "action", "status")
        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Main.Treeview"
        )
        
        # 设置列标题
        self.tree.heading("rule_id", text=language_manager.get_text("rule_id"))
        self.tree.heading("type", text=language_manager.get_text("rule_type"))
        self.tree.heading("condition", text=language_manager.get_text("condition"))
        self.tree.heading("action", text=language_manager.get_text("action"))
        self.tree.heading("status", text=language_manager.get_text("status"))
        
        # 设置列宽
        self.tree.column("rule_id", width=100, minwidth=100)
        self.tree.column("type", width=100, minwidth=100)
        self.tree.column("condition", width=400, minwidth=250)
        self.tree.column("action", width=400, minwidth=250)
        self.tree.column("status", width=100, minwidth=100)
        
        # 添加滚动条
        vsb = ttk.Scrollbar(frame, orient=VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # 布局
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        vsb.pack(side=RIGHT, fill=Y)
        hsb.pack(side=BOTTOM, fill=X)
        
        # 创建右键菜单
        self._create_context_menu()
        
        # 绑定事件
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)
        
    def _create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label=language_manager.get_text("edit"),
            command=self._edit_selected_rule
        )
        self.context_menu.add_command(
            label=language_manager.get_text("delete"),
            command=self._delete_selected_rule
        )
        self.context_menu.add_separator()
        
        # 创建状态子菜单
        self.status_menu = tk.Menu(self.context_menu, tearoff=0)
        self.status_menu.add_command(
            label=language_manager.get_text("enabled"),
            command=lambda: self._change_rule_status("enabled")
        )
        self.status_menu.add_command(
            label=language_manager.get_text("testing"),
            command=lambda: self._change_rule_status("testing")
        )
        self.status_menu.add_command(
            label=language_manager.get_text("disabled"),
            command=lambda: self._change_rule_status("disabled")
        )
        
        self.context_menu.add_cascade(
            label=language_manager.get_text("status"),
            menu=self.status_menu
        )
        
    def _show_context_menu(self, event):
        """显示右键菜单"""
        # TODO: 实现右键菜单显示逻辑
        pass
        
    def _edit_selected_rule(self):
        """编辑选中的规则"""
        # TODO: 实现规则编辑逻辑
        pass
        
    def _delete_selected_rule(self):
        """删除选中的规则"""
        # TODO: 实现规则删除逻辑
        pass
        
    def _change_rule_status(self, status: str):
        """更改规则状态"""
        # TODO: 实现规则状态更改逻辑
        pass
        
    def _clear_search(self):
        """清空搜索"""
        self.search_var.set("")
        
    def _on_search_changed(self, *args):
        """搜索内容变化事件处理"""
        # TODO: 实现搜索逻辑
        pass
        
    def _on_double_click(self, event):
        """双击事件处理"""
        # TODO: 实现双击事件处理逻辑
        pass
        
    def refresh_texts(self):
        """刷新所有文本"""
        # 更新窗口标题
        self.title(language_manager.get_text("logic_library"))
        
        # 更新列标题
        self.tree.heading("rule_id", text=language_manager.get_text("rule_id"))
        self.tree.heading("type", text=language_manager.get_text("rule_type"))
        self.tree.heading("condition", text=language_manager.get_text("condition"))
        self.tree.heading("action", text=language_manager.get_text("action"))
        self.tree.heading("status", text=language_manager.get_text("status"))
        
        # 更新菜单文本
        self.context_menu.entryconfig(0, label=language_manager.get_text("edit"))
        self.context_menu.entryconfig(1, label=language_manager.get_text("delete"))
        self.context_menu.entryconfig(3, label=language_manager.get_text("status"))
        
        self.status_menu.entryconfig(0, label=language_manager.get_text("enabled"))
        self.status_menu.entryconfig(1, label=language_manager.get_text("testing"))
        self.status_menu.entryconfig(2, label=language_manager.get_text("disabled")) 