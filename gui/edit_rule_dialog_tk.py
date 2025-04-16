"""
编辑规则对话框模块 (Tkinter + ttkbootstrap版本)

该模块提供了编辑逻辑规则的对话框界面。
"""
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from models.logic_rule import RuleStatus, RuleType
from utils.language_manager import language_manager

class EditRuleDialog(tk.Toplevel):
    """编辑规则对话框"""
    
    def __init__(self, parent, rule, logic_builder=None):
        """初始化编辑规则对话框"""
        super().__init__(parent)
        
        # 保存参数
        self.rule = rule
        self.logic_builder = logic_builder
        self.result = None
        self.modified = False
        
        # 设置对话框属性
        self.title(language_manager.get_text("edit_rule"))
        self.minsize(800, 600)  # 增加最小窗口大小
        
        # 居中显示
        self.geometry("+%d+%d" % (
            parent.winfo_screenwidth() // 2 - 400,  # 调整窗口位置
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
            "Large.TLabelframe.Label",
            font=("Microsoft YaHei", 18)
        )
        
        # 创建大字体单选按钮样式
        style.configure(
            "Large.TRadiobutton",
            font=("Microsoft YaHei", 18)
        )
        
        # 创建大字体按钮样式
        style.configure(
            "Large.TButton",
            font=("Microsoft YaHei", 18)
        )
        
        # 创建大字体成功按钮样式
        style.configure(
            "Large.success.TButton",
            font=("Microsoft YaHei", 18)
        )
    
    def _create_widgets(self):
        """创建对话框组件"""
        # 创建主布局框架
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # 条件表达式
        condition_frame = ttk.LabelFrame(
            main_frame, 
            text=language_manager.get_text("condition"),
            padding=5,
            style="Large.TLabelframe"  # 使用大字体样式
        )
        condition_frame.pack(fill=BOTH, expand=YES, pady=5)
        
        self.condition_text = tk.Text(
            condition_frame,
            height=6,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 18)  # 设置文本框字体
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
        
        # 影响表达式
        effect_frame = ttk.LabelFrame(
            main_frame, 
            text=language_manager.get_text("effect"),
            padding=5,
            style="Large.TLabelframe"  # 使用大字体样式
        )
        effect_frame.pack(fill=BOTH, expand=YES, pady=5)
        
        self.effect_text = tk.Text(
            effect_frame,
            height=6,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 18)  # 设置文本框字体
        )
        if self.rule.rule_type == RuleType.DYNAMIC:
            self.effect_text.insert(tk.END, self.rule.action)
        else:
            self.effect_text.insert(tk.END, self.rule.effect_expr)
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
            text=language_manager.get_text("status"),
            padding=5,
            style="Large.TLabelframe"  # 使用大字体样式
        )
        status_frame.pack(fill=X, pady=5)
        
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
                style="Large.TRadiobutton"  # 使用大字体样式
            )
            self.status_buttons[status.value] = radio
            radio.pack(side=LEFT, padx=10)
        
        # 标签
        tags_frame = ttk.LabelFrame(
            main_frame, 
            text=language_manager.get_text("tags"),
            padding=5,
            style="Large.TLabelframe"  # 使用大字体样式
        )
        tags_frame.pack(fill=X, pady=5)
        
        self.tags_entry = ttk.Entry(
            tags_frame,
            font=("Microsoft YaHei", 18)  # 设置输入框字体
        )
        self.tags_entry.insert(0, ", ".join(self.rule.tags) if self.rule.tags else "")
        self.tags_entry.pack(fill=X, padx=5, pady=5)
        
        # 按钮区
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=10)
        
        self.cancel_btn = ttk.Button(
            btn_frame,
            text=language_manager.get_text("cancel"),
            command=self.destroy,
            width=15,
            style="Large.TButton"  # 使用大字体样式
        )
        self.cancel_btn.pack(side=RIGHT, padx=5)
        
        self.confirm_btn = ttk.Button(
            btn_frame,
            text=language_manager.get_text("confirm"),
            command=self._on_confirm,
            width=15,
            style="Large.success.TButton"  # 使用大字体成功按钮样式
        )
        self.confirm_btn.pack(side=RIGHT, padx=5)
    
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
            
            # 解析标签
            tags = [t.strip() for t in self.tags_entry.get().split(",") if t.strip()]
            
            # 验证输入
            if not condition:
                raise ValueError(language_manager.get_text("condition_required"))
            if not effect:
                raise ValueError(language_manager.get_text("effect_required"))
            
            # 更新规则
            self.rule.condition = condition
            if self.rule.rule_type == RuleType.DYNAMIC:
                self.rule.action = effect
            else:
                # 处理静态规则的影响表达式
                has_relation_operator = False
                if ":" in effect or "→" in effect:
                    has_relation_operator = True
                    parts = effect.split(":", 1) if ":" in effect else effect.split("→", 1)
                    if len(parts) == 2:
                        self.rule.relation = ":" if ":" in effect else "→"
                        self.rule.action = parts[1].strip()
                else:
                    self.rule.action = effect
                    # 如果没有关系操作符，但规则原来有关系，保留原来的关系
                    if self.rule.relation in [":", "→"]:
                        has_relation_operator = True
                
                # 如果是通过logic_builder更新，处理带有关系操作符的情况
                if self.logic_builder:
                    if has_relation_operator:
                        # 使用logic_builder验证完整表达式
                        full_expr = f"{condition} {self.rule.relation} {self.rule.action}"
                        valid, message = self.logic_builder._validate_static_expression(full_expr)
                        if not valid:
                            raise ValueError(f"{language_manager.get_text('expression_error')}: {message}")
                        
                        # 单独验证右侧表达式
                        valid, message = self.logic_builder._validate_static_expression(self.rule.action, is_relation_right_side=True)
                        if not valid:
                            raise ValueError(f"{language_manager.get_text('expression_error')}(右侧): {message}")
                    else:
                        # 对于没有关系操作符的静态表达式，验证整个字符串而不是验证为列表
                        valid, message = self.logic_builder._validate_static_expression(condition)
                        if not valid:
                            raise ValueError(f"{language_manager.get_text('expression_error')}: {message}")
            
            self.rule.status = status
            self.rule.tags = tags
            
            # 保存结果
            self.result = {
                "condition": condition,
                "effect": effect,
                "status": status,
                "tags": tags
            }
            
            # 标记为已修改
            self.modified = True
            
            # 关闭对话框
            self.destroy()
            
        except Exception as e:
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