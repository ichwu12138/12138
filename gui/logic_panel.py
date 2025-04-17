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
        
        # 注册语言变化的回调函数
        language_manager.add_callback(self.refresh_texts)
        
        # 创建自定义样式
        self._create_custom_styles()
        
        # 创建界面
        self._create_widgets()
        
    def destroy(self):
        """销毁面板时移除回调函数"""
        language_manager.remove_callback(self.refresh_texts)
        super().destroy()
        
    def _create_custom_styles(self):
        """创建自定义样式"""
        style = ttk.Style()
        
        # 获取框架标题的字体大小
        frame_title_size = style.lookup("Main.TLabelframe.Label", "font")
        if isinstance(frame_title_size, str):
            # 如果是字符串格式，解析字体大小
            import re
            size_match = re.search(r'\d+', frame_title_size)
            if size_match:
                frame_title_size = int(size_match.group())
            else:
                frame_title_size = 18  # 默认大小
        elif isinstance(frame_title_size, tuple):
            # 如果是元组格式，直接获取大小
            frame_title_size = frame_title_size[1]
        else:
            frame_title_size = 18  # 默认大小
        
        # 配置单选按钮样式，使用与框架标题相同的字体大小
        style.configure(
            "Status.TRadiobutton",
            font=("Microsoft YaHei", frame_title_size)
        )
        
    def _create_widgets(self):
        """创建界面组件"""
        # 创建标题标签
        self.title_label = ttk.Label(
            self,
            text=language_manager.get_text("logic_panel_title"),
            style="Title.TLabel"
        )
        self.title_label.pack(fill=X, pady=(0, 10))
        
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # 创建逻辑操作符框架
        self.operators_frame = ttk.LabelFrame(
            main_frame,
            text=language_manager.get_text("logic_operators"),
            style="Main.TLabelframe"
        )
        self.operators_frame.pack(fill=X, pady=(0, 5))
        
        operators = ["AND", "OR", "NOT", "XOR"]
        for op in operators:
            btn = ttk.Button(
                self.operators_frame,
                text=op,
                command=lambda x=op: self._add_operator(x),
                style="Main.TButton",
                width=10
            )
            btn.pack(side=LEFT, padx=5, pady=2)
        
        # 创建括号框架
        self.brackets_frame = ttk.LabelFrame(
            main_frame,
            text=language_manager.get_text("brackets"),
            style="Main.TLabelframe"
        )
        self.brackets_frame.pack(fill=X, pady=(0, 5))
        
        brackets = ["(", ")"]
        for bracket in brackets:
            btn = ttk.Button(
                self.brackets_frame,
                text=bracket,
                command=lambda x=bracket: self._add_bracket(x),
                style="Main.TButton",
                width=10
            )
            btn.pack(side=LEFT, padx=5, pady=2)
        
        # 创建规则状态框架
        self.status_frame = ttk.LabelFrame(
            main_frame,
            text=language_manager.get_text("rule_status"),
            style="Main.TLabelframe"
        )
        self.status_frame.pack(fill=X, pady=(0, 5))
        
        # 创建状态单选按钮
        self.status_var = tk.StringVar(value="enabled")
        self.status_buttons = {}
        
        # 创建启用按钮
        self.enabled_rb = ttk.Radiobutton(
            self.status_frame,
            text=language_manager.get_text("enabled"),
            value="enabled",
            variable=self.status_var,
            style="Status.TRadiobutton"  # 使用自定义样式
        )
        self.enabled_rb.pack(side=LEFT, padx=5, pady=2)
        
        # 创建测试按钮
        self.testing_rb = ttk.Radiobutton(
            self.status_frame,
            text=language_manager.get_text("testing"),
            value="testing",
            variable=self.status_var,
            style="Status.TRadiobutton"  # 使用自定义样式
        )
        self.testing_rb.pack(side=LEFT, padx=5, pady=2)
        
        # 创建禁用按钮
        self.disabled_rb = ttk.Radiobutton(
            self.status_frame,
            text=language_manager.get_text("disabled"),
            value="disabled",
            variable=self.status_var,
            style="Status.TRadiobutton"  # 使用自定义样式
        )
        self.disabled_rb.pack(side=LEFT, padx=5, pady=2)
        
        # 创建表达式框架
        self.expr_frame = ttk.LabelFrame(
            main_frame,
            text=language_manager.get_text("expression"),
            style="Main.TLabelframe"
        )
        self.expr_frame.pack(fill=BOTH, expand=YES, pady=(0, 5))
        
        # 创建表达式文本框
        self.expr_text = tk.Text(
            self.expr_frame,
            height=5,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 16)
        )
        self.expr_text.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # 创建按钮框架
        btn_frame = ttk.Frame(self.expr_frame)
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
        
        # 创建已保存规则框架
        self.saved_rules_frame = ttk.LabelFrame(
            main_frame,
            text=language_manager.get_text("saved_rules"),
            style="Main.TLabelframe"
        )
        self.saved_rules_frame.pack(fill=BOTH, expand=YES)
        
        # 创建树状视图
        self._create_tree(self.saved_rules_frame)
        
    def _create_tree(self, parent):
        """创建树状视图"""
        # 创建树状视图
        self.rules_tree = ttk.Treeview(
            parent,
            selectmode="browse",
            style="Main.Treeview",
            columns=("status",),
            show="tree headings"
        )
        self.rules_tree.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # 添加滚动条
        vsb = ttk.Scrollbar(
            parent,
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
        try:
            self.logger.debug(f"LogicPanel: 开始插入代码: {code}")
            
            # 获取当前光标位置
            current_pos = self.expr_text.index(tk.INSERT)
            self.logger.debug(f"LogicPanel: 当前光标位置: {current_pos}")
            
            # 获取当前行的内容
            current_line = self.expr_text.get(f"{current_pos.split('.')[0]}.0", f"{current_pos.split('.')[0]}.end")
            self.logger.debug(f"LogicPanel: 当前行内容: {current_line}")
            
            # 确定是否需要添加前导空格
            if current_line and not current_line.endswith(" "):
                self.logger.debug("LogicPanel: 添加前导空格")
                self.expr_text.insert(tk.INSERT, " ")
                
            # 插入代码
            self.expr_text.insert(tk.INSERT, code)
            self.logger.info(f"LogicPanel: 成功插入代码: {code}")
            
            # 确定是否需要添加后导空格
            next_char = self.expr_text.get(tk.INSERT)
            if next_char and not next_char.isspace():
                self.logger.debug("LogicPanel: 添加后导空格")
                self.expr_text.insert(tk.INSERT, " ")
            
            # 让文本框获得焦点
            self.expr_text.focus_set()
            self.logger.debug("LogicPanel: 文本框获得焦点")
            
        except Exception as e:
            self.logger.error(f"LogicPanel: 插入代码时出错: {str(e)}", exc_info=True)
        
    def refresh_texts(self):
        """刷新所有文本"""
        # 更新标题
        self.title_label.configure(text=language_manager.get_text("logic_panel_title"))
        
        # 更新框架标题
        self.operators_frame.configure(text=language_manager.get_text("logic_operators"))
        self.brackets_frame.configure(text=language_manager.get_text("brackets"))
        self.status_frame.configure(text=language_manager.get_text("rule_status"))
        self.expr_frame.configure(text=language_manager.get_text("expression"))
        self.saved_rules_frame.configure(text=language_manager.get_text("saved_rules"))
        
        # 更新单选按钮文本
        self.enabled_rb.configure(text=language_manager.get_text("enabled"))
        self.testing_rb.configure(text=language_manager.get_text("testing"))
        self.disabled_rb.configure(text=language_manager.get_text("disabled"))
        
        # 更新按钮文本
        self.clear_btn.configure(text=language_manager.get_text("clear"))
        self.save_btn.configure(text=language_manager.get_text("save"))
        
        # 强制更新显示
        self.update_idletasks() 