"""
逻辑规则编辑器对话框模块

该模块提供了编辑逻辑规则的对话框界面，支持新的逻辑关系格式。
"""
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from models.logic_rule import RuleStatus
from utils.language_manager import language_manager
from utils.logger import Logger
from utils.validator import ExpressionValidator

class LogicRuleEditor(tk.Toplevel):
    """逻辑规则编辑器对话框"""
    
    def __init__(self, parent, rule, logic_builder=None):
        """初始化逻辑规则编辑器对话框
        
        Args:
            parent: 父窗口
            rule: 要编辑的规则对象
            logic_builder: 逻辑构建器实例
        """
        super().__init__(parent)
        
        # 保存参数
        self.rule = rule
        self.logic_builder = logic_builder
        self.result = None
        self.modified = False
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 设置对话框属性
        self.title(language_manager.get_text("edit_rule"))
        self.minsize(800, 600)
        
        # 居中显示
        self.geometry("+%d+%d" % (
            parent.winfo_screenwidth() // 2 - 400,
            parent.winfo_screenheight() // 2 - 300
        ))
        
        # 创建自定义样式
        self._create_custom_styles()
        
        # 创建界面
        self._create_widgets()
        
        # 使对话框模态
        self.transient(parent)
        self.grab_set()
        
    def _create_custom_styles(self):
        """创建自定义样式"""
        style = ttk.Style()
        
        # 创建大字体标签框架样式
        style.configure(
            "Large.TLabelframe",
            font=("Microsoft YaHei", 12)
        )
        style.configure(
            "Large.TLabelframe.Label",
            font=("Microsoft YaHei", 12)
        )
        
        # 创建大字体单选按钮样式
        style.configure(
            "Large.TRadiobutton",
            font=("Microsoft YaHei", 11)
        )
        
        # 创建大字体按钮样式
        style.configure(
            "Large.TButton",
            font=("Microsoft YaHei", 11)
        )
        
        # 创建大字体成功按钮样式
        style.configure(
            "Large.success.TButton",
            font=("Microsoft YaHei", 11)
        )
        
    def _create_widgets(self):
        """创建对话框组件"""
        # 创建主布局框架
        main_frame = ttk.Frame(self, padding=8)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # 选择项表达式
        condition_frame = ttk.LabelFrame(
            main_frame, 
            text=language_manager.get_text("edit_rule_condition"),
            padding=4,
            style="Large.TLabelframe"
        )
        condition_frame.pack(fill=BOTH, expand=YES, pady=4)
        
        self.condition_text = tk.Text(
            condition_frame,
            height=5,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 11)
        )
        self.condition_text.insert(tk.END, self.rule.condition)
        self.condition_text.pack(fill=BOTH, expand=YES)
        
        # 滚动条
        condition_scrollbar = ttk.Scrollbar(
            condition_frame, 
            orient=VERTICAL, 
            command=self.condition_text.yview
        )
        condition_scrollbar.pack(side=RIGHT, fill=Y)
        self.condition_text.config(yscrollcommand=condition_scrollbar.set)
        
        # 影响项表达式
        effect_frame = ttk.LabelFrame(
            main_frame, 
            text=language_manager.get_text("edit_rule_effect"),
            padding=4,
            style="Large.TLabelframe"
        )
        effect_frame.pack(fill=BOTH, expand=YES, pady=4)
        
        self.effect_text = tk.Text(
            effect_frame,
            height=5,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 11)
        )
        
        # 显示规则的action
        self.effect_text.insert(tk.END, self.rule.action)
        self.effect_text.pack(fill=BOTH, expand=YES)
        
        # 滚动条
        effect_scrollbar = ttk.Scrollbar(
            effect_frame, 
            orient=VERTICAL, 
            command=self.effect_text.yview
        )
        effect_scrollbar.pack(side=RIGHT, fill=Y)
        self.effect_text.config(yscrollcommand=effect_scrollbar.set)
        
        # 状态选择
        status_frame = ttk.LabelFrame(
            main_frame, 
            text=language_manager.get_text("edit_rule_status"),
            padding=4,
            style="Large.TLabelframe"
        )
        status_frame.pack(fill=X, pady=4)
        
        # 创建状态变量
        self.status_var = tk.StringVar(value=self.rule.status.value)
        
        # 创建状态单选按钮
        status_inner_frame = ttk.Frame(status_frame)
        status_inner_frame.pack(fill=X)
        
        self.status_buttons = {}
        for status in RuleStatus:
            radio = ttk.Radiobutton(
                status_inner_frame,
                text=language_manager.get_text(status.value),
                variable=self.status_var,
                value=status.value,
                style="Large.TRadiobutton"
            )
            self.status_buttons[status.value] = radio
            radio.pack(side=LEFT, padx=10)
        
        # 按钮区
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=8)
        
        self.cancel_btn = ttk.Button(
            btn_frame,
            text=language_manager.get_text("cancel"),
            command=self.destroy,
            width=12,
            style="Large.TButton"
        )
        self.cancel_btn.pack(side=RIGHT, padx=4)
        
        self.confirm_btn = ttk.Button(
            btn_frame,
            text=language_manager.get_text("confirm"),
            command=self._on_confirm,
            width=12,
            style="Large.success.TButton"
        )
        self.confirm_btn.pack(side=RIGHT, padx=4)
        
    def _on_confirm(self):
        """确认按钮点击事件"""
        try:
            # 获取输入的值
            condition = self.condition_text.get("1.0", tk.END).strip()
            effect = self.effect_text.get("1.0", tk.END).strip()
            
            # 获取选中的状态
            status_value = self.status_var.get()
            status = None
            for s in RuleStatus:
                if s.value == status_value:
                    status = s
                    break
            
            # 验证输入
            if not condition:
                raise ValueError(language_manager.get_text("condition_required"))
            if not effect:
                raise ValueError(language_manager.get_text("effect_required"))
            
            # 验证选择项表达式
            valid, message = ExpressionValidator.validate_logic_expression(
                condition,
                self.logic_builder.config_processor if self.logic_builder else None,
                is_effect_side=False
            )
            if not valid:
                raise ValueError(f"{language_manager.get_text('condition_error')}: {message}")
            
            # 检查是否包含微调逻辑
            if ExpressionValidator.is_tuning_logic(effect):
                # 验证微调逻辑表达式
                valid, message = ExpressionValidator.validate_tuning_logic(effect)
                if not valid:
                    raise ValueError(f"{language_manager.get_text('effect_error')}: {message}")
            else:
                # 验证BOM逻辑表达式
                valid, message = ExpressionValidator.validate_logic_expression(
                    effect,
                    self.logic_builder.config_processor if self.logic_builder else None,
                    is_effect_side=True
                )
                if not valid:
                    raise ValueError(f"{language_manager.get_text('effect_error')}: {message}")
            
            # 更新规则
            self.rule.condition = condition
            self.rule.action = effect
            self.rule.status = status
            
            # 保存结果
            self.result = {
                "condition": condition,
                "effect": effect,
                "status": status
            }
            
            # 标记为已修改
            self.modified = True
            
            # 关闭对话框
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"保存规则时出错: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                str(e)
            )
    
    def show(self):
        """显示对话框并等待结果
        
        Returns:
            Dict: 修改结果，如果取消则为None
        """
        # 等待窗口关闭
        self.wait_window()
        
        # 返回结果
        return self.result if self.modified else None 