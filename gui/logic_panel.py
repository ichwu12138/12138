"""
逻辑编辑面板模块

该模块提供了逻辑规则的编辑和管理功能。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from typing import List, Tuple, Set

from utils.language_manager import language_manager
from utils.logger import Logger
from core.logic_builder import LogicBuilder
from utils.validator import ExpressionValidator
from models.logic_rule import RuleStatus, RuleType, LogicRule
from gui.logic_rule_editor import LogicRuleEditor

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
        
        # 初始化规则计数器和已使用的ID集合
        self.rule_counter = 1
        self.used_rule_ids: Set[int] = set()
        
        # 注册语言变化的回调函数
        language_manager.add_callback(self.refresh_texts)
        
        # 注册规则变化的观察者
        self.logic_builder.add_rule_observer(self._on_rule_change)
        
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
        
        # 加载现有规则
        self._load_existing_rules()
        
    def destroy(self):
        """销毁面板时移除回调函数"""
        language_manager.remove_callback(self.refresh_texts)
        self.logic_builder.remove_rule_observer(self._on_rule_change)
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
        
        # 创建树形视图
        self._create_tree(self.saved_rules_frame)
        
        # 禁用文本框的鼠标点击
        self.expr_text.bind("<Button-1>", lambda e: "break")
        self.expr_text.bind("<Button-2>", lambda e: "break")
        self.expr_text.bind("<Button-3>", lambda e: "break")
        
        # 禁用键盘输入
        self.expr_text.bind("<Key>", lambda e: "break")
        
    def _create_tree(self, parent):
        """创建规则树形视图"""
        # 创建树形视图框架
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # 创建树形视图
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("rule_id", "condition", "effect", "status"),
            show="headings",
            selectmode="browse",
            style="Large.Treeview"
        )
        
        # 设置列标题
        self.tree.heading("rule_id", text=language_manager.get_text("rule_id"), anchor=CENTER)
        self.tree.heading("condition", text=language_manager.get_text("edit_rule_condition"), anchor=CENTER)
        self.tree.heading("effect", text=language_manager.get_text("edit_rule_effect"), anchor=CENTER)
        self.tree.heading("status", text=language_manager.get_text("edit_rule_status"), anchor=CENTER)
        
        # 设置列宽度和对齐方式
        self.tree.column("rule_id", width=100, anchor=CENTER)
        self.tree.column("condition", width=300, anchor=CENTER)
        self.tree.column("effect", width=300, anchor=CENTER)
        self.tree.column("status", width=100, anchor=CENTER)
        
        # 配置大字体样式
        style = ttk.Style()
        style.configure(
            "Large.Treeview",
            font=("Microsoft YaHei", 18),
            rowheight=100  # 调整行高以适应更大的字体
        )
        style.configure(
            "Large.Treeview.Heading",
            font=("Microsoft YaHei", 18, "bold"),
            rowheight=100
        )
        
        # 创建右键菜单
        self.rule_menu = tk.Menu(self, tearoff=0, font=("Microsoft YaHei", 18))
        self.rule_menu.add_command(
            label=language_manager.get_text("edit"),
            command=lambda: self._edit_rule(None)
        )
        
        # 添加状态子菜单
        self.status_menu = tk.Menu(self.rule_menu, tearoff=0, font=("Microsoft YaHei", 18))
        self._update_status_menu()  # 创建状态菜单项
        
        self.rule_menu.add_cascade(
            label=language_manager.get_text("status"),
            menu=self.status_menu
        )
        
        # 添加删除选项
        self.rule_menu.add_separator()
        self.rule_menu.add_command(
            label=language_manager.get_text("delete"),
            command=self._delete_rule
        )
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 打包组件
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 绑定右键菜单
        self.tree.bind("<Button-3>", self._show_rule_menu)
        
        # 绑定双击事件
        self.tree.bind("<Double-1>", self._edit_rule)

    def _update_status_menu(self):
        """更新状态菜单项"""
        # 清空现有菜单项
        self.status_menu.delete(0, tk.END)
        
        # 重新添加菜单项
        for status in RuleStatus:
            self.status_menu.add_command(
                label=language_manager.get_text(status.value),
                command=lambda s=status: self._change_rule_status(s)
            )

    def _change_rule_status(self, new_status: RuleStatus):
        """更改规则状态"""
        # 获取选中的项目
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.tree.item(item)["values"]
        if not values:
            return
            
        # 更新规则状态
        rule_id = values[0]
        condition = values[1]
        effect = values[2]
        
        # 更新树形视图显示
        self.tree.item(
            item,
            values=(
                rule_id,
                condition,
                effect,
                language_manager.get_text(new_status.value)
            )
        )
        
        # 更新逻辑构建器中的规则
        rule = self.logic_builder.get_rule_by_id(rule_id)
        if rule:
            rule.status = new_status
            self.logic_builder._save_rules()  # 保存更改
            
            # 通知规则变更
            self.logic_builder.notify_rule_change("modified", rule_id, rule)

    def _edit_rule(self, event):
        """编辑规则"""
        # 获取选中的项目
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.tree.item(item)["values"]
        if not values:
            return
            
        # 解析当前值
        rule_id = values[0]
        condition = values[1]
        effect = values[2]
        status_text = values[3]
        
        # 从effect中提取实际的表达式（去掉箭头前缀）
        if effect.startswith("→ "):
            effect = effect[2:].strip()
        
        # 获取当前状态枚举值
        current_status = None
        for status in RuleStatus:
            if language_manager.get_text(status.value) == status_text:
                current_status = status
                break
        
        # 创建规则对象
        rule = LogicRule(
            rule_id=rule_id,
            rule_type=RuleType.STATIC,
            condition=condition,
            action=effect,
            relation="→",
            status=current_status or RuleStatus.ENABLED
        )
        
        # 创建编辑对话框
        dialog = LogicRuleEditor(self, rule, self.logic_builder)
        result = dialog.show()
        
        if result:
            # 更新树形视图中的显示
            effect_text = f"→ {result['effect']}"
            self.tree.item(
                item,
                values=(
                    rule_id,
                    result["condition"],
                    effect_text,
                    language_manager.get_text(result["status"].value)
                )
            )
            
            # 更新逻辑构建器中的规则
            rule = self.logic_builder.get_rule_by_id(rule_id)
            if rule:
                rule.condition = result["condition"]
                rule.action = result["effect"]
                rule.status = result["status"]
                self.logic_builder._save_rules()  # 保存更改
                
                # 通知规则变更
                self.logic_builder.notify_rule_change("modified", rule_id, rule)

    def _show_rule_menu(self, event):
        """显示规则右键菜单"""
        # 获取点击位置的项目
        item = self.tree.identify_row(event.y)
        if item:
            # 选中被点击的项目
            self.tree.selection_set(item)
            # 显示菜单
            self.rule_menu.post(event.x_root, event.y_root)
            
    def _delete_rule(self):
        """删除规则"""
        # 获取选中的项目
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        
        # 确认删除
        if not messagebox.askyesno(
            language_manager.get_text("confirm"),
            language_manager.get_text("confirm_delete_rule")
        ):
            return
            
        # 从LogicBuilder中删除规则
        self.logic_builder.delete_rule(item)
        
        # 获取规则ID编号
        values = self.tree.item(item)["values"]
        if values:
            rule_id_str = values[0]  # 格式为"BLxx"
            try:
                rule_number = int(rule_id_str[2:])  # 提取数字部分
                self.used_rule_ids.remove(rule_number)  # 从已使用集合中移除
            except (ValueError, IndexError):
                self.logger.error(f"无法解析规则ID: {rule_id_str}")
        
        # 从树形视图中删除
        self.tree.delete(item)
        
        # 保存更改到临时文件
        self.logic_builder.save_to_temp_file()
        
        # 通知规则变更
        self.logic_builder.notify_rule_change("deleted", item)

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
        try:
            # 获取当前表达式
            expr = self.expr_text.get("1.0", "end-1c").strip()
            if not expr:
                messagebox.showerror(
                    language_manager.get_text("error"),
                    language_manager.get_text("error_empty_expression")
                )
                return
                
            # 验证表达式
            if "→" not in expr:
                messagebox.showerror(
                    language_manager.get_text("error"),
                    language_manager.get_text("error_missing_implication")
                )
                return
                
            # 分割表达式
            parts = expr.split("→")
            if len(parts) != 2:
                messagebox.showerror(
                    language_manager.get_text("error"),
                    language_manager.get_text("error_invalid_expression_format")
                )
                return
                
            condition = parts[0].strip()
            effect = parts[1].strip()
            
            # 获取下一个可用的规则ID
            rule_number = self._get_next_rule_id()
            rule_id = f"BL{rule_number:02d}"
            
            # 检查规则ID是否已存在
            if rule_id in self.tree.get_children():
                # 如果存在，继续寻找下一个可用ID
                while f"BL{rule_number:02d}" in self.tree.get_children():
                    rule_number += 1
                rule_id = f"BL{rule_number:02d}"
            
            self.used_rule_ids.add(rule_number)
            
            # 获取当前状态
            status = self.status_var.get()
            status_text = language_manager.get_text(status)
            
            # 创建新规则
            rule = LogicRule(
                rule_id=rule_id,
                rule_type=RuleType.STATIC,
                condition=condition,
                action=effect,
                relation="→",
                status=RuleStatus(status)
            )
            
            # 添加到逻辑构建器
            self.logic_builder.add_rule(rule)
            
            # 添加到树状视图
            self.tree.insert(
                "",
                "end",
                iid=rule_id,
                values=(rule_id, condition, f"→ {effect}", status_text)
            )
            
            # 保存到临时文件
            self.logic_builder.save_to_temp_file()
            
            # 记录日志
            self.logger.info(f"已保存新的BOM逻辑关系规则: ID={rule_id}, 选择项={condition}, 影响项={effect}, 状态={status}")
            
            # 清空表达式
            self.expr_text.delete("1.0", "end")
            
            # 通知规则变更
            self.logic_builder.notify_rule_change("added", rule_id, rule)
            
            # 显示成功消息
            messagebox.showinfo(
                language_manager.get_text("success"),
                language_manager.get_text("rule_saved_successfully")
            )
            
        except Exception as e:
            self.logger.error(f"保存规则时出错: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                language_manager.get_text("error_saving_rule")
            )
        
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
                if next_token == "→":  # 不能以蕴含符号开始
                    return False, "error_implication_at_start"
                return True, ""
                
            last_token = current_tokens[-1]
            
            # 检查蕴含符号的使用
            if next_token == "→":
                # 检查是否已经存在蕴含符号
                if "→" in current_tokens:
                    return False, "error_multiple_implications"
                # 检查前面的token是否合法
                if last_token in ["AND", "OR", "NOT", "(", "→"]:
                    return False, "error_invalid_before_implication"
                # 检查前面是否只有特征值
                if any(self.validator.is_bom_code(token) for token in current_tokens):
                    return False, "error_bom_before_implication"
            
            # 检查NOT的使用
            if next_token == "NOT":
                # 检查NOT前面的token
                if self.validator.is_k_code(last_token) or self.validator.is_bom_code(last_token) or last_token == ")":
                    return False, "error_invalid_before_not"
                # 计算连续的NOT数量
                not_count = 1
                for i in range(len(current_tokens) - 1, -1, -1):
                    if current_tokens[i] == "NOT":
                        not_count += 1
                    else:
                        break
                if not_count > 1:
                    return False, "error_consecutive_not"
                    
            # 检查变量后面的token
            if self.validator.is_k_code(last_token) or self.validator.is_bom_code(last_token):
                if next_token not in ["AND", "OR", "→", ")"]:
                    return False, "error_invalid_after_variable"
                    
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
                
            # 检查特征值的使用
            if self.validator.is_k_code(next_token):
                if "→" in current_tokens:
                    return False, "error_k_after_implication"
                if last_token not in ["(", "AND", "OR", "NOT"]:
                    return False, "error_invalid_before_k"
                
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
                
            return True, ""
            
        except Exception as e:
            self.logger.error(f"验证token序列时出错: {str(e)}", exc_info=True)
            return False, "error_validation_failed"
        
    def _on_key_press(self, event):
        """处理按键事件，在输入前验证"""
        # 禁止所有键盘输入，包括复制粘贴
        return "break"
        
    def _on_key_release(self, event):
        """处理按键释放事件"""
        # 禁止所有键盘输入，包括复制粘贴
        return "break"
    
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
        
        # 更新右键菜单文本
        self.rule_menu.entryconfigure(0, label=language_manager.get_text("edit"))
        self.rule_menu.entryconfigure(1, label=language_manager.get_text("status"))
        self.rule_menu.entryconfigure(3, label=language_manager.get_text("delete"))
        
        # 更新状态子菜单
        self._update_status_menu()
        
        # 更新树状视图列标题
        self.tree.heading("rule_id", text=language_manager.get_text("rule_id"))
        self.tree.heading("condition", text=language_manager.get_text("edit_rule_condition"))
        self.tree.heading("effect", text=language_manager.get_text("edit_rule_effect"))
        self.tree.heading("status", text=language_manager.get_text("edit_rule_status"))
        
        # 更新所有规则的状态显示
        for item in self.tree.get_children():
            values = list(self.tree.item(item)["values"])
            if values and len(values) > 3:
                # 查找对应的状态并更新显示文本
                for status in RuleStatus:
                    if status.value == values[3]:
                        values[3] = language_manager.get_text(status.value)
                        self.tree.item(item, values=values)
                        break
        
    def _get_next_rule_id(self) -> int:
        """获取下一个可用的规则ID编号"""
        # 从1开始查找第一个未使用的ID
        rule_id = 1
        while rule_id in self.used_rule_ids:
            rule_id += 1
        return rule_id 

    def _load_existing_rules(self):
        """加载现有规则到树状视图"""
        try:
            # 检查是否是程序启动时的加载
            main_window = None
            # 尝试从不同路径获取main_window实例
            if hasattr(self.master, 'main_window'):
                main_window = self.master.main_window
            elif hasattr(self.winfo_toplevel(), 'main_window'):
                main_window = self.winfo_toplevel().main_window
                
            if main_window is None:
                self.logger.error("无法获取main_window实例")
                return
                
            if not main_window.rules_loaded:
                self.logger.info("规则未加载状态，等待用户确认后再加载规则")
                # 清空现有数据和已使用的ID集合
                for item in self.tree.get_children():
                    self.tree.delete(item)
                self.used_rule_ids.clear()
                return
                
            self.logger.info("开始加载规则到已保存规则框架")
            
            # 清空现有数据和已使用的ID集合
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.used_rule_ids.clear()
            
            # 加载所有规则
            rules = self.logic_builder.get_rules()
            self.logger.debug(f"从LogicBuilder获取到 {len(rules)} 条规则")
            
            if not rules:
                self.logger.info("没有规则需要加载")
                return
                
            for rule in rules:
                try:
                    # 构建显示文本
                    effect_text = f"→ {rule.action}"
                    status_text = language_manager.get_text(rule.status.value)
                    
                    # 插入到树形视图（只显示必要的列）
                    self.tree.insert(
                        "",
                        "end",
                        iid=rule.rule_id,
                        values=(
                            rule.rule_id,
                            rule.condition,
                            effect_text,
                            status_text
                        )
                    )
                    
                    # 更新已使用的规则ID
                    try:
                        if rule.rule_id.startswith('BL'):
                            rule_number = int(rule.rule_id[2:])
                            self.used_rule_ids.add(rule_number)
                            self.logger.debug(f"添加规则ID: {rule_number} 到已使用集合")
                    except (ValueError, IndexError) as e:
                        self.logger.error(f"无法解析规则ID: {rule.rule_id}, 错误: {str(e)}")
                        
                except Exception as e:
                    self.logger.error(f"插入规则到树状视图失败: {str(e)}, 规则ID: {rule.rule_id}")
                    continue
                    
            self.logger.info(f"成功加载 {len(self.tree.get_children())} 条规则到已保存规则框架")
            
        except Exception as e:
            self.logger.error(f"加载现有规则失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                str(e)
            )

    def _on_rule_change(self, change_type, rule_id=None, rule=None):
        """处理规则变更事件
        
        Args:
            change_type: 变更类型（'imported', 'added', 'modified', 'deleted', 'cleared'）
            rule_id: 规则ID
            rule: 规则对象
        """
        try:
            self.logger.info(f"收到规则变更事件: type={change_type}, rule_id={rule_id}")
            
            # 获取main_window实例
            main_window = None
            if hasattr(self.master, 'main_window'):
                main_window = self.master.main_window
            elif hasattr(self.winfo_toplevel(), 'main_window'):
                main_window = self.winfo_toplevel().main_window
            
            if change_type == "imported":
                # 检查是否有规则
                rules = self.logic_builder.get_rules()
                if rules:
                    # 检查是否已经设置了rules_loaded标志
                    if main_window is not None and main_window.rules_loaded:
                        self.logger.info("规则已加载状态，开始更新已保存规则框架")
                        # 重新加载所有规则
                        self._load_existing_rules()
                    else:
                        self.logger.info("规则未加载状态，等待用户确认")
            elif change_type == "deleted":
                # 删除规则
                if rule_id and rule_id in self.tree.get_children():
                    self.tree.delete(rule_id)
                    # 从已使用ID集合中移除
                    try:
                        rule_number = int(rule_id[2:])
                        self.used_rule_ids.remove(rule_number)
                        self.logger.info(f"已删除规则: {rule_id}")
                    except (ValueError, IndexError):
                        self.logger.error(f"无法解析规则ID: {rule_id}")
            elif change_type == "cleared":
                # 清空所有规则
                for item in self.tree.get_children():
                    self.tree.delete(item)
                self.used_rule_ids.clear()
                # 重置规则已加载标志
                if main_window is not None:
                    main_window.rules_loaded = False
                    self.logger.info("已清空所有规则，重置规则已加载标志")
                else:
                    self.logger.info("已清空所有规则")
            elif change_type in ["added", "modified"]:
                # 更新或添加规则
                if rule:
                    effect_text = f"→ {rule.action}"
                    try:
                        if rule.rule_id in self.tree.get_children():
                            # 更新现有规则
                            self.tree.item(
                                rule.rule_id,
                                values=(
                                    rule.rule_id,
                                    rule.condition,
                                    effect_text,
                                    language_manager.get_text(rule.status.value)
                                )
                            )
                            self.logger.info(f"已更新规则: {rule.rule_id}")
                        else:
                            # 添加新规则
                            self.tree.insert(
                                "",
                                "end",
                                iid=rule.rule_id,
                                values=(
                                    rule.rule_id,
                                    rule.condition,
                                    effect_text,
                                    language_manager.get_text(rule.status.value)
                                )
                            )
                            # 更新已使用的规则ID
                            try:
                                rule_number = int(rule.rule_id[2:])
                                self.used_rule_ids.add(rule_number)
                                self.logger.info(f"已添加新规则: {rule.rule_id}")
                            except (ValueError, IndexError):
                                self.logger.error(f"无法解析规则ID: {rule.rule_id}")
                    except Exception as e:
                        self.logger.error(f"更新/添加规则到树状视图失败: {str(e)}, 规则ID: {rule.rule_id}")
                            
        except Exception as e:
            self.logger.error(f"处理规则变更事件失败: {str(e)}", exc_info=True) 