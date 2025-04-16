"""
逻辑编辑面板模块

该模块提供了逻辑规则的编辑和管理功能。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox

from utils.language_manager import language_manager
from utils.logger import Logger
from core.logic_builder import LogicBuilder

class LogicPanel(ttk.Frame):
    """逻辑编辑面板类"""
    
    def __init__(self, parent, logic_builder: LogicBuilder):
        """初始化逻辑编辑面板
        
        Args:
            parent: 父窗口
            logic_builder: 逻辑构建器实例
        """
        super().__init__(parent, style="Panel.TFrame")
        
        # 保存参数
        self.logic_builder = logic_builder
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 创建界面
        self._create_widgets()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 创建标题标签
        title_label = ttk.Label(
            self,
            text=language_manager.get_text("logic_panel_title"),
            style="Title.TLabel"
        )
        title_label.pack(fill=X, pady=(0, 10))
        
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # 创建逻辑操作符框架
        self._create_logic_operators_frame(main_frame)
        
        # 创建括号框架
        self._create_bracket_frame(main_frame)
        
        # 创建规则状态框架
        self._create_rule_status_frame(main_frame)
        
        # 创建表达式编辑区域
        self._create_expression_frame(main_frame)
        
        # 创建已保存规则区域
        self._create_saved_rules_frame(main_frame)
        
    def _create_logic_operators_frame(self, parent):
        """创建逻辑操作符框架"""
        frame = ttk.LabelFrame(
            parent,
            text=language_manager.get_text("logic_operators"),
            style="Main.TLabelframe"
        )
        frame.pack(fill=X, pady=(0, 5))
        
        operators = ["AND", "OR", "NOT", "XOR"]
        for op in operators:
            btn = ttk.Button(
                frame,
                text=op,
                command=lambda x=op: self._add_operator(x),
                style="Main.TButton",
                width=10
            )
            btn.pack(side=LEFT, padx=5, pady=2)
            
    def _create_bracket_frame(self, parent):
        """创建括号框架"""
        frame = ttk.LabelFrame(
            parent,
            text=language_manager.get_text("brackets"),
            style="Main.TLabelframe"
        )
        frame.pack(fill=X, pady=(0, 5))
        
        brackets = ["(", ")"]
        for bracket in brackets:
            btn = ttk.Button(
                frame,
                text=bracket,
                command=lambda x=bracket: self._add_bracket(x),
                style="Main.TButton",
                width=10
            )
            btn.pack(side=LEFT, padx=5, pady=2)
            
    def _create_rule_status_frame(self, parent):
        """创建规则状态框架"""
        frame = ttk.LabelFrame(
            parent,
            text=language_manager.get_text("rule_status"),
            style="Main.TLabelframe"
        )
        frame.pack(fill=X, pady=(0, 5))
        
        # 创建状态单选按钮
        self.status_var = tk.StringVar(value="enabled")
        statuses = [
            ("enabled", language_manager.get_text("enabled")),
            ("testing", language_manager.get_text("testing")),
            ("disabled", language_manager.get_text("disabled"))
        ]
        
        for value, text in statuses:
            rb = ttk.Radiobutton(
                frame,
                text=text,
                value=value,
                variable=self.status_var,
                style="Main.TRadiobutton"
            )
            rb.pack(side=LEFT, padx=5, pady=2)
            
    def _create_expression_frame(self, parent):
        """创建表达式编辑区域"""
        frame = ttk.LabelFrame(
            parent,
            text=language_manager.get_text("expression"),
            style="Main.TLabelframe"
        )
        frame.pack(fill=BOTH, expand=YES, pady=(0, 5))
        
        # 创建表达式文本框
        self.expr_text = tk.Text(
            frame,
            height=5,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 16)
        )
        self.expr_text.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # 创建按钮框架
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=X, padx=5, pady=(0, 5))
        
        # 清除按钮
        self.clear_btn = ttk.Button(
            btn_frame,
            text=language_manager.get_text("clear"),
            command=self._clear_expr,
            style="Main.TButton",
            width=15
        )
        self.clear_btn.pack(side=LEFT, padx=5)
        
        # 保存按钮
        self.save_btn = ttk.Button(
            btn_frame,
            text=language_manager.get_text("save"),
            command=self._save_rule,
            style="success.Main.TButton",
            width=15
        )
        self.save_btn.pack(side=RIGHT, padx=5)
        
    def _create_saved_rules_frame(self, parent):
        """创建已保存规则区域"""
        frame = ttk.LabelFrame(
            parent,
            text=language_manager.get_text("saved_rules"),
            style="Main.TLabelframe"
        )
        frame.pack(fill=BOTH, expand=YES)
        
        # 创建树状视图
        self.rules_tree = ttk.Treeview(
            frame,
            selectmode="browse",
            style="Main.Treeview",
            columns=("status",),
            show="tree headings"
        )
        self.rules_tree.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # 添加滚动条
        vsb = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.rules_tree.yview
        )
        vsb.pack(side=RIGHT, fill=Y)
        self.rules_tree.configure(yscrollcommand=vsb.set)
        
    def _add_operator(self, operator: str):
        """添加逻辑操作符"""
        self.expr_text.insert(tk.INSERT, f" {operator} ")
        
    def _add_bracket(self, bracket: str):
        """添加括号"""
        self.expr_text.insert(tk.INSERT, bracket)
        
    def _clear_expr(self):
        """清空表达式"""
        self.expr_text.delete("1.0", tk.END)
        
    def _save_rule(self):
        """保存规则"""
        # TODO: 实现规则保存逻辑
        pass
        
    def insert_code(self, code: str):
        """插入代码到表达式
        
        Args:
            code: 要插入的代码
        """
        self.expr_text.insert(tk.INSERT, code)
        
    def refresh_texts(self):
        """刷新所有文本"""
        # 刷新标题
        for child in self.winfo_children():
            if isinstance(child, ttk.Label) and "Title.TLabel" in str(child.cget("style")):
                child.configure(text=language_manager.get_text("logic_panel_title"))
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
                                btn.configure(text=language_manager.get_text("import_logic"))
                            elif "refresh" in current_btn_text:
                                btn.configure(text=language_manager.get_text("refresh"))
                                
                # 更新逻辑状态框架
                elif "logic_status" in current_text:
                    frame.configure(text=language_manager.get_text("logic_status"))
                    # 更新单选按钮文本
                    for child in frame.winfo_children():
                        if isinstance(child, ttk.Radiobutton):
                            current_value = str(child.cget("value")).lower()
                            if "all" in current_value:
                                child.configure(text=language_manager.get_text("all"))
                            elif "pass" in current_value:
                                child.configure(text=language_manager.get_text("pass"))
                            elif "fail" in current_value:
                                child.configure(text=language_manager.get_text("fail"))
                                
                # 更新逻辑树框架
                elif "logic_tree" in current_text:
                    frame.configure(text=language_manager.get_text("logic_tree"))
                    
                # 更新逻辑操作符框架
                if "logic_operators" in current_text:
                    frame.configure(text=language_manager.get_text("logic_operators"))
                    
                # 更新括号框架
                elif "brackets" in current_text:
                    frame.configure(text=language_manager.get_text("brackets"))
                    
                # 更新规则状态框架
                elif "rule_status" in current_text:
                    frame.configure(text=language_manager.get_text("rule_status"))
                    # 更新单选按钮文本
                    for widget in frame.winfo_children():
                        if isinstance(widget, ttk.Radiobutton):
                            value = str(widget.cget("value"))
                            if value == "enabled":
                                widget.configure(text=language_manager.get_text("enabled"))
                            elif value == "testing":
                                widget.configure(text=language_manager.get_text("testing"))
                            elif value == "disabled":
                                widget.configure(text=language_manager.get_text("disabled"))
                                
                # 更新表达式框架
                elif "expression" in current_text:
                    frame.configure(text=language_manager.get_text("expression"))
                    # 更新按钮文本
                    for btn_frame in frame.winfo_children():
                        if isinstance(btn_frame, ttk.Frame):
                            for btn in btn_frame.winfo_children():
                                if isinstance(btn, ttk.Button):
                                    current_btn_text = str(btn.cget("text")).lower()
                                    if "clear" in current_btn_text:
                                        btn.configure(text=language_manager.get_text("clear"))
                                    elif "save" in current_btn_text:
                                        btn.configure(text=language_manager.get_text("save"))
                                        
                # 更新已保存规则框架
                elif "saved_rules" in current_text:
                    frame.configure(text=language_manager.get_text("saved_rules")) 