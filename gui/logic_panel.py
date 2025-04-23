"""
逻辑编辑面板模块

该模块提供了逻辑规则的编辑和管理功能。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from typing import List, Tuple

from utils.language_manager import language_manager
from utils.logger import Logger
from core.logic_builder import LogicBuilder
from utils.validator import ExpressionValidator

class LogicPanel(ttk.Frame):
    """逻辑编辑面板类"""
    
    def __init__(self, parent, logic_builder: LogicBuilder, config_processor=None, bom_processor=None):
        """初始化逻辑编辑面板
        
        Args:
            parent: 父窗口
            logic_builder: 逻辑构建器实例
            config_processor: 配置处理器实例
            bom_processor: BOM处理器实例
        """
        super().__init__(parent, style="Panel.TFrame")
        
        # 保存参数
        self.logic_builder = logic_builder
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 创建验证器实例
        self.validator = ExpressionValidator(config_processor, bom_processor)
        
        # 用于记录插入历史
        self.insert_history: List[Tuple[str, str, str]] = []  # [(start, end, content), ...]
        
        # 创建错误文本变量
        self.error_text = tk.StringVar()
        
        # 注册语言变化的回调函数
        language_manager.add_callback(self.refresh_texts)
        
        # 创建自定义样式
        self._create_custom_styles()
        
        # 创建界面
        self._create_widgets()
        
        # 添加表达式状态跟踪
        self.expression_state = {
            "has_implication": False,  # 是否包含→
            "last_token": "",         # 最后一个token
            "tokens": [],             # 所有tokens
            "parentheses_count": 0,   # 括号计数
            "current_position": "end"  # 当前插入位置
        }
        
        # 添加输入历史记录
        self.input_history = []
        
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
        
        # 配置错误标签样式
        style.configure(
            "Error.TLabel",
            foreground="red",
            font=("Microsoft YaHei", 10)
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
        
        operators = ["AND", "OR", "NOT", "→"]
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
        
        # 创建表达式文本框容器
        expr_container = ttk.Frame(self.expr_frame)
        expr_container.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # 创建表达式文本框
        self.expr_text = tk.Text(
            expr_container,
            height=10,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 18)
        )
        self.expr_text.pack(fill=BOTH, expand=YES)
        
        # 创建错误提示标签
        self.error_label = ttk.Label(
            expr_container,
            textvariable=self.error_text,
            style="Error.TLabel"
        )
        self.error_label.pack(fill=X, pady=(5, 0))
        
        # 绑定按键事件，用于实时验证
        self.expr_text.bind('<Key>', self._on_key_press)
        self.expr_text.bind('<KeyRelease>', self._on_key_release)
        
        # 创建按钮框架
        btn_frame = ttk.Frame(self.expr_frame)
        btn_frame.pack(fill=X, padx=5, pady=5)
        
        # 创建左侧按钮框架
        left_btn_frame = ttk.Frame(btn_frame)
        left_btn_frame.pack(side=LEFT)
        
        # 删除上一个内容按钮
        self.delete_last_btn = ttk.Button(
            left_btn_frame,
            text=language_manager.get_text("delete_last"),
            command=self._delete_last_content,
            style="Main.TButton",
            width=15
        )
        self.delete_last_btn.pack(side=LEFT, padx=5)
        
        # 清除全部按钮
        self.clear_all_btn = ttk.Button(
            left_btn_frame,
            text=language_manager.get_text("clear_all"),
            command=self._clear_expr,
            style="Main.TButton",
            width=15
        )
        self.clear_all_btn.pack(side=LEFT, padx=5)
        
        # 保存规则按钮
        self.save_btn = ttk.Button(
            btn_frame,
            text=language_manager.get_text("save_rule"),
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
        
        # 禁用文本框的鼠标点击
        self.expr_text.bind("<Button-1>", lambda e: "break")
        self.expr_text.bind("<Button-2>", lambda e: "break")
        self.expr_text.bind("<Button-3>", lambda e: "break")
        
        # 禁用键盘输入
        self.expr_text.bind("<Key>", lambda e: "break")
        
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
        
    def _log_input(self, input_type: str, content: str):
        """记录输入历史
        
        Args:
            input_type: 输入类型（K码、BOM码、操作符、括号等）
            content: 输入内容
        """
        current_expr = self.expr_text.get("1.0", "end-1c")
        self.input_history.append({
            "type": input_type,
            "content": content,
            "expression": current_expr
        })
        self.logger.info(f"LogicPanel: 输入历史 - 类型: {input_type}, 内容: {content}, 当前表达式: {current_expr}")
        
    def _add_operator(self, operator: str):
        """添加逻辑操作符"""
        try:
            # 更新表达式状态
            self._update_expression_state()
            
            # 验证操作符插入的合法性
            is_valid, error_msg = self._validate_token_sequence(operator)
            if not is_valid:
                messagebox.showerror(
                    language_manager.get_text("error"),
                    language_manager.get_text(error_msg)
                )
                return
                
            # 始终在末尾插入
            self.expr_text.mark_set(tk.INSERT, "end-1c")
            
            # 插入操作符
            self.expr_text.insert(tk.INSERT, f" {operator} ")
            
            # 记录输入
            self._log_input("operator", operator)
            
        except Exception as e:
            self.logger.error(f"添加操作符时出错: {str(e)}", exc_info=True)
            
    def _add_bracket(self, bracket: str):
        """添加括号"""
        try:
            # 更新表达式状态
            self._update_expression_state()
            
            # 验证括号插入的合法性
            is_valid, error_msg = self._validate_token_sequence(bracket)
            if not is_valid:
                messagebox.showerror(
                    language_manager.get_text("error"),
                    language_manager.get_text(error_msg)
                )
                return
                
            # 始终在末尾插入
            self.expr_text.mark_set(tk.INSERT, "end-1c")
            
            # 插入括号
            self.expr_text.insert(tk.INSERT, bracket)
            
            # 记录输入
            self._log_input("bracket", bracket)
            
        except Exception as e:
            self.logger.error(f"添加括号时出错: {str(e)}", exc_info=True)
            
    def _delete_last_content(self):
        """删除最后一个内容"""
        try:
            # 获取当前表达式
            current_text = self.expr_text.get("1.0", "end-1c")
            if not current_text:
                return
                
            # 分割成token
            tokens = current_text.split()
            if not tokens:
                return
                
            # 删除最后一个token和其后的空格
            new_text = " ".join(tokens[:-1])
            if new_text:
                new_text += "  "  # 保持两个空格的间隔
                
            # 更新文本
            self.expr_text.delete("1.0", "end")
            self.expr_text.insert("1.0", new_text)
            
            # 记录删除操作
            self._log_input("delete", tokens[-1])
            
            # 更新表达式状态
            self._update_expression_state()
            
        except Exception as e:
            self.logger.error(f"删除最后一个内容时出错: {str(e)}", exc_info=True)
        
    def _clear_expr(self):
        """清空表达式"""
        self.expr_text.delete("1.0", tk.END)
        # 清空插入历史
        self.insert_history.clear()
        # 重置最后有效状态
        self._last_valid_text = ""
        
    def _save_rule(self):
        """保存规则"""
        # TODO: 实现规则保存逻辑
        pass
        
    def _update_expression_state(self, text: str = None):
        """更新表达式状态
        
        Args:
            text: 要分析的文本，如果为None则使用当前文本
        """
        if text is None:
            text = self.expr_text.get("1.0", "end-1c")
            
        # 更新状态
        self.expression_state["has_implication"] = "→" in text
        tokens = [t for t in text.split() if t]
        self.expression_state["tokens"] = tokens
        self.expression_state["last_token"] = tokens[-1] if tokens else ""
        self.expression_state["parentheses_count"] = text.count("(") - text.count(")")
        
    def _validate_token_sequence(self, next_token: str) -> Tuple[bool, str]:
        """验证token序列的合法性
        
        Args:
            next_token: 下一个要插入的token
            
        Returns:
            Tuple[bool, str]: (是否合法, 错误消息)
        """
        try:
            # 获取当前表达式
            current_expr = self.expr_text.get("1.0", "end-1c").strip()
            current_tokens = current_expr.split() if current_expr else []
            
            # 如果是第一个token
            if not current_tokens:
                if next_token not in ["(", "NOT"] and not self.validator.is_k_code(next_token):
                    return False, "error_invalid_first_input"
                return True, ""
                
            last_token = current_tokens[-1]
            
            # 检查BOM码的插入位置
            if self.validator.is_bom_code(next_token):
                self.logger.debug(f"验证BOM码: {next_token}")
                # 检查是否已经出现了蕴含符号
                has_implication = "→" in current_tokens
                if not has_implication:
                    self.logger.debug("错误：在→之前插入BOM码")
                    return False, "error_bom_before_implication"
                # 检查BOM码的连续使用
                if self.validator.is_bom_code(last_token):
                    self.logger.debug("错误：连续插入BOM码")
                    return False, "error_consecutive_codes"
                # 检查BOM码前面的token
                if last_token not in ["→", "(", "AND", "OR", "NOT"]:
                    self.logger.debug(f"错误：BOM码前面的token无效: {last_token}")
                    return False, "error_invalid_before_bom"
                
            # 检查NOT的连用
            if next_token == "NOT":
                # 计算连续的NOT数量
                not_count = 1
                for i in range(len(current_tokens) - 1, -1, -1):
                    if current_tokens[i] == "NOT":
                        not_count += 1
                    else:
                        break
                if not_count > 1:
                    return False, "error_consecutive_not"
                    
            # 检查括号规则
            if next_token == "(":
                # 检查连续的左括号
                if last_token == "(":
                    return False, "error_consecutive_left_parentheses"
                # 检查左括号前的token
                if last_token not in ["AND", "OR", "NOT", "(", "→"]:
                    return False, "error_invalid_before_left_parenthesis"
                    
            elif next_token == ")":
                # 检查右括号数量不能超过左括号
                left_count = sum(1 for t in current_tokens if t == "(")
                right_count = sum(1 for t in current_tokens if t == ")")
                if right_count >= left_count:
                    return False, "error_missing_left_parenthesis"
                # 检查连续的右括号
                if last_token == ")":
                    return False, "error_consecutive_right_parentheses"
                # 检查右括号前的token
                if last_token in ["AND", "OR", "NOT", "(", "→"]:
                    return False, "error_invalid_before_right_parenthesis"
                
            # 检查操作符规则
            if next_token in ["AND", "OR"]:
                if last_token in ["AND", "OR", "NOT", "(", "→"]:
                    return False, "error_invalid_before_operator"
                
            # 检查K码规则
            if self.validator.is_k_code(next_token):
                if "→" in current_tokens:
                    return False, "error_k_after_implication"
                if last_token not in ["(", "AND", "OR", "NOT"]:
                    return False, "error_invalid_before_k"
                
            # 检查蕴含符号规则
            if next_token == "→":
                if last_token in ["AND", "OR", "NOT", "(", "→"]:
                    return False, "error_invalid_before_implication"
                
            return True, ""
            
        except Exception as e:
            self.logger.error(f"验证token序列时出错: {str(e)}", exc_info=True)
            return False, "error_validation_failed"
        
    def _on_key_press(self, event):
        """处理按键事件，在输入前验证"""
        if event.char and event.char.strip():
            # 更新表达式状态
            self._update_expression_state()
            
            # 获取当前正在输入的token
            current_line = self.expr_text.get("1.0", "end-1c")
            current_word = current_line.split()[-1] if current_line.split() else ""
            current_word = current_word + event.char
            
            # 预测可能形成的token
            possible_token = None
            if current_word.upper().startswith("K"):
                possible_token = "K"
            elif current_word.upper().startswith("BOM"):
                possible_token = "BOM"
            elif current_word.upper() in ["AND", "OR", "NOT"]:
                possible_token = current_word.upper()
            elif event.char in ["(", ")", "→"]:
                possible_token = event.char
                
            # 如果能预测出token，验证其合法性
            if possible_token:
                is_valid, error_msg = self._validate_token_sequence(possible_token)
                if not is_valid:
                    self.error_text.set(language_manager.get_text(error_msg))
                    return "break"
                    
            # 获取当前文本和即将插入的字符
            current_text = self.expr_text.get("1.0", "end-1c")
            cursor_pos = self.expr_text.index(INSERT)
            row, col = map(int, cursor_pos.split('.'))
            
            # 获取当前行的内容
            current_line = self.expr_text.get(f"{row}.0", f"{row}.{col}")
            after_cursor = self.expr_text.get(f"{row}.{col}", f"{row}.end")
            
            # 构建新文本
            new_text = current_line + event.char + after_cursor
            
            # 分割当前文本为token列表
            current_tokens = current_text.split()
            
            # 如果是第一个字符
            if not current_text.strip():
                if not (event.char in ["(", "K", "N"]):  # 允许左括号、K码开头或NOT开头
                    self.error_text.set(language_manager.get_text("error_must_start_with_k"))
                    return "break"
                    
            # 获取最后一个完整的token
            last_token = current_tokens[-1] if current_tokens else ""
            
            # 检查输入是否会形成有效token
            if event.char.isalpha():  # 字母输入
                # 检查是否可能形成有效的操作符或变量
                valid_starts = ["K", "BOM", "AND", "OR", "NOT"]
                current_word = current_line.split()[-1] if current_line.split() else ""
                current_word = current_word + event.char
                
                if not any(current_word.upper().startswith(token) for token in valid_starts):
                    self.error_text.set(language_manager.get_text("error_invalid_token"))
                    return "break"
                    
            # 特殊字符验证
            if event.char in ["(", ")", "→"]:
                # 检查括号匹配
                if event.char == ")":
                    left_count = current_text.count("(")
                    right_count = current_text.count(")")
                    if right_count >= left_count:
                        self.error_text.set(language_manager.get_text("error_unmatched_parentheses"))
                        return "break"
                
                # 检查→符号
                if event.char == "→":
                    if "→" in current_text:
                        self.error_text.set(language_manager.get_text("error_multiple_implications"))
                        return "break"
                    # 检查左边是否只有K码
                    if any(token.startswith("BOM") for token in current_tokens):
                        self.error_text.set(language_manager.get_text("error_bom_before_implication"))
                        return "break"
            
            # 根据上下文验证输入
            if last_token:
                # 变量后面的验证
                if self.validator.is_k_code(last_token) or self.validator.is_bom_code(last_token):
                    if not event.char in [" ", ")", "→"] and not current_line.endswith(("AND ", "OR ")):
                        self.error_text.set(language_manager.get_text("error_invalid_after_variable"))
                        return "break"
                
                # 操作符后面的验证
                if last_token in ["AND", "OR"]:
                    if not event.char in ["(", "K", "B", "N"]:  # 允许左括号、K码、BOM码或NOT
                        self.error_text.set(language_manager.get_text("error_invalid_after_operator"))
                        return "break"
                
                # NOT后面的验证
                if last_token == "NOT":
                    if not event.char in ["(", "K", "B"]:  # 允许左括号、K码或BOM码
                        self.error_text.set(language_manager.get_text("error_invalid_after_not"))
                        return "break"
                
                # →后面的验证
                if last_token == "→":
                    if not event.char in ["(", "B", "N"]:  # 允许左括号、BOM码或NOT
                        self.error_text.set(language_manager.get_text("error_invalid_after_implication"))
                        return "break"
            
            # 清除错误提示
            self.error_text.set("")
            
            # 保存最后有效状态
            self._last_valid_text = current_text
    
    def _on_key_release(self, event):
        """处理按键释放事件，用于处理复制粘贴等操作"""
        if event.keysym in ('v', 'V') and (event.state & 0x4):  # Ctrl+V
            # 获取当前文本
            current_text = self.expr_text.get("1.0", "end-1c")
            
            # 检查是否有连续的变量或操作符
            tokens = current_text.split()
            for i in range(len(tokens)-1):
                if (self.validator.is_k_code(tokens[i]) and self.validator.is_k_code(tokens[i+1])) or \
                   (self.validator.is_bom_code(tokens[i]) and self.validator.is_bom_code(tokens[i+1])):
                    messagebox.showerror(
                        language_manager.get_text("error"),
                        language_manager.get_text("consecutive_codes")
                    )
                    self.expr_text.delete("1.0", tk.END)
                    self.expr_text.insert("1.0", self._last_valid_text if hasattr(self, '_last_valid_text') else "")
                    return
                    
                if tokens[i] in ["AND", "OR", "NOT", "→"] and tokens[i+1] in ["AND", "OR", "NOT", "→"]:
                    messagebox.showerror(
                        language_manager.get_text("error"),
                        language_manager.get_text("consecutive_operators")
                    )
                    self.expr_text.delete("1.0", tk.END)
                    self.expr_text.insert("1.0", self._last_valid_text if hasattr(self, '_last_valid_text') else "")
                    return
            
            # 验证当前文本
            is_valid, error_msg = self.validator.validate_implication_expression(current_text)
            if not is_valid:
                # 显示错误消息
                messagebox.showerror(
                    language_manager.get_text("error"),
                    language_manager.get_text(error_msg)
                )
                # 恢复到上一个有效状态
                self.expr_text.delete("1.0", tk.END)
                self.expr_text.insert("1.0", self._last_valid_text if hasattr(self, '_last_valid_text') else "")
            else:
                # 保存有效状态
                self._last_valid_text = current_text
    
    def insert_code(self, code: str):
        """插入代码到表达式"""
        try:
            self.logger.debug(f"LogicPanel: 开始插入代码: {code}")
            
            # 更新表达式状态
            self._update_expression_state()
            
            # 验证插入的合法性
            is_valid, error_msg = self._validate_token_sequence(code)
            if not is_valid:
                messagebox.showerror(
                    language_manager.get_text("error"),
                    language_manager.get_text(error_msg)
                )
                return
                
            # 始终在末尾插入
            self.expr_text.mark_set(tk.INSERT, "end-1c")
            
            # 确定是否需要添加前导空格
            current_text = self.expr_text.get("1.0", "end-1c")
            if current_text and not current_text.endswith(" "):
                self.expr_text.insert(tk.INSERT, " ")
                
            # 插入代码
            self.expr_text.insert(tk.INSERT, code)
            
            # 确定是否需要添加后导空格
            self.expr_text.insert(tk.INSERT, " ")
            
            # 记录输入
            input_type = "K_code" if code.startswith("K") else "BOM_code"
            self._log_input(input_type, code)
            
            # 更新最后有效状态
            self._last_valid_text = self.expr_text.get("1.0", "end-1c")
            
            # 清除错误提示
            self.error_text.set("")
            
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
        
        # 更新新增的按钮文本
        self.delete_last_btn.configure(text=language_manager.get_text("delete_last"))
        self.clear_all_btn.configure(text=language_manager.get_text("clear_all"))
        
        # 更新按钮文本
        self.save_btn.configure(text=language_manager.get_text("save_rule"))
        
        # 强制更新显示
        self.update_idletasks() 