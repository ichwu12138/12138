"""
逻辑关系库窗口模块

该模块提供了一个独立窗口来展示所有保存的 BOM 逻辑关系规则。
"""
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from utils.language_manager import language_manager
from utils.logger import Logger
from core.logic_builder import LogicBuilder
from models.logic_rule import RuleStatus
from gui.logic_rule_editor import LogicRuleEditor

class LogicLibraryWindow(tk.Toplevel):
    """逻辑关系库窗口类"""
    
    def __init__(self, parent, logic_builder: LogicBuilder):
        """初始化逻辑关系库窗口"""
        super().__init__(parent)
        
        # 保存参数
        self.logic_builder = logic_builder
        self.parent = parent
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 设置窗口属性
        self.title(language_manager.get_text("logic_library"))
        self.minsize(1024, 768)
        
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
        
        # 加载规则数据
        self._load_rules()
        
        # 确保窗口显示在前台
        self.lift()
        self.focus_force()
        
        # 添加最大化按钮
        if hasattr(self, 'attributes'):
            try:
                self.attributes('-toolwindow', 0)
                self.state('normal')
            except:
                pass
                
        # 注册规则变更观察者
        self.logic_builder.add_rule_observer(self._on_rule_change)
        
    def destroy(self):
        """销毁窗口时移除观察者"""
        self.logic_builder.remove_rule_observer(self._on_rule_change)
        super().destroy()
        
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
            padding=5,
            style="Large.TLabelframe"
        )
        frame.pack(fill=X, pady=(0, 10))
        
        # 创建搜索输入框
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            frame,
            textvariable=self.search_var,
            font=("Microsoft YaHei", 18)
        )
        search_entry.pack(side=LEFT, fill=X, expand=YES, padx=5)
        
        # 创建清除按钮
        clear_btn = ttk.Button(
            frame,
            text=language_manager.get_text("clear"),
            command=self._clear_search,
            width=10,
            style="Large.TButton"
        )
        clear_btn.pack(side=LEFT, padx=5)
        
        # 绑定搜索事件
        self.search_var.trace_add("write", self._on_search_changed)
        
    def _create_rules_frame(self, parent):
        """创建规则列表框架"""
        frame = ttk.LabelFrame(
            parent,
            text=language_manager.get_text("rules"),
            padding=5,
            style="Large.TLabelframe"
        )
        frame.pack(fill=BOTH, expand=YES)
        
        # 创建树状视图
        columns = ("rule_id", "condition", "effect", "status")
        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Large.Treeview"
        )
        
        # 设置列标题
        self.tree.heading("rule_id", text=language_manager.get_text("rule_id"), anchor=CENTER)
        self.tree.heading("condition", text=language_manager.get_text("edit_rule_condition"), anchor=CENTER)
        self.tree.heading("effect", text=language_manager.get_text("edit_rule_effect"), anchor=CENTER)
        self.tree.heading("status", text=language_manager.get_text("edit_rule_status"), anchor=CENTER)
        
        # 设置列宽
        self.tree.column("rule_id", width=100, anchor=CENTER)
        self.tree.column("condition", width=400, anchor=CENTER)
        self.tree.column("effect", width=400, anchor=CENTER)
        self.tree.column("status", width=100, anchor=CENTER)
        
        # 配置大字体样式
        style = ttk.Style()
        style.configure(
            "Large.Treeview",
            font=("Microsoft YaHei", 18),
            rowheight=36
        )
        style.configure(
            "Large.Treeview.Heading",
            font=("Microsoft YaHei", 18, "bold"),
            rowheight=36
        )
        
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
        self.context_menu = tk.Menu(self, tearoff=0, font=("Microsoft YaHei", 18))
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
        self.status_menu = tk.Menu(self.context_menu, tearoff=0, font=("Microsoft YaHei", 18))
        self._update_status_menu()
        
        self.context_menu.add_cascade(
            label=language_manager.get_text("status"),
            menu=self.status_menu
        )
        
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
        
    def _show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
            
    def _edit_selected_rule(self):
        """编辑选中的规则"""
        try:
            selection = self.tree.selection()
            if not selection:
                return
                
            item = selection[0]
            rule = self.logic_builder.get_rule_by_id(item)
            if not rule:
                return
                
            # 创建编辑对话框
            dialog = LogicRuleEditor(self, rule, self.logic_builder)
            result = dialog.show()
            
            if result:
                # 更新树形视图中的显示
                effect_text = f"→ {result['effect']}"
                self.tree.item(
                    item,
                    values=(
                        rule.rule_id,
                        result["condition"],
                        effect_text,
                        language_manager.get_text(result["status"].value)
                    )
                )
                self.logger.info(f"已编辑规则: {rule.rule_id}")
                
        except Exception as e:
            self.logger.error(f"编辑规则失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                str(e)
            )
            
    def _delete_selected_rule(self):
        """删除选中的规则"""
        try:
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
                
            # 从逻辑构建器中删除规则
            self.logic_builder.delete_rule(item)
            
            # 从树形视图中删除
            self.tree.delete(item)
            
            self.logger.info(f"已删除规则: {item}")
            
        except Exception as e:
            self.logger.error(f"删除规则失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                str(e)
            )
            
    def _change_rule_status(self, new_status: RuleStatus):
        """更改规则状态"""
        try:
            selection = self.tree.selection()
            if not selection:
                return
                
            item = selection[0]
            rule = self.logic_builder.get_rule_by_id(item)
            if not rule:
                return
                
            # 更新规则状态
            rule.status = new_status
            
            # 更新树形视图显示
            values = list(self.tree.item(item)["values"])
            values[3] = language_manager.get_text(new_status.value)
            self.tree.item(item, values=values)
            
            # 保存更改
            self.logic_builder._save_rules()
            
            self.logger.info(f"已更改规则状态: {item} -> {new_status.value}")
            
        except Exception as e:
            self.logger.error(f"更改规则状态失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                str(e)
            )
        
    def _clear_search(self):
        """清空搜索"""
        self.search_var.set("")
        
    def _on_search_changed(self, *args):
        """搜索内容变化事件处理"""
        search_text = self.search_var.get().lower()
        
        # 遍历所有规则
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            # 检查规则ID、条件和影响是否包含搜索文本
            if (search_text in str(values[0]).lower() or
                search_text in str(values[1]).lower() or
                search_text in str(values[2]).lower()):
                self.tree.reattach(item, "", "end")  # 显示匹配的项
            else:
                self.tree.detach(item)  # 隐藏不匹配的项
        
    def _on_double_click(self, event):
        """双击事件处理"""
        self._edit_selected_rule()
        
    def _load_rules(self):
        """加载规则数据"""
        try:
            # 清空现有数据
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # 加载所有规则
            for rule in self.logic_builder.get_rules():
                effect_text = f"→ {rule.action}"
                try:
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
                except Exception as e:
                    self.logger.error(f"插入规则到树状视图失败: {str(e)}, 规则ID: {rule.rule_id}")
                    continue
                
            self.logger.info(f"已加载 {len(self.tree.get_children())} 条 BOM 逻辑关系规则")
                
        except Exception as e:
            self.logger.error(f"加载规则数据失败: {str(e)}", exc_info=True)
            
    def _on_rule_change(self, change_type, rule_id=None, rule=None):
        """规则变更事件处理"""
        try:
            if change_type == "imported":
                # 重新加载所有规则
                self._load_rules()
                self.logger.info("已重新加载所有规则")
            elif change_type == "deleted":
                # 删除规则
                if rule_id and rule_id in self.tree.get_children():
                    self.tree.delete(rule_id)
                    self.logger.info(f"已删除规则: {rule_id}")
            elif change_type == "added" or change_type == "modified":
                # 更新或添加规则
                if rule:
                    effect_text = f"→ {rule.action}"
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
                        self.logger.info(f"已添加新规则: {rule.rule_id}")
                        
        except Exception as e:
            self.logger.error(f"处理规则变更事件失败: {str(e)}", exc_info=True)
            
    def refresh_texts(self):
        """刷新所有文本"""
        # 更新窗口标题
        self.title(language_manager.get_text("logic_library"))
        
        # 更新列标题
        self.tree.heading("rule_id", text=language_manager.get_text("rule_id"))
        self.tree.heading("condition", text=language_manager.get_text("edit_rule_condition"))
        self.tree.heading("effect", text=language_manager.get_text("edit_rule_effect"))
        self.tree.heading("status", text=language_manager.get_text("edit_rule_status"))
        
        # 更新框架标题
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if "search" in str(child.cget("text")).lower():
                    child.configure(text=language_manager.get_text("search"))
                elif "rules" in str(child.cget("text")).lower():
                    child.configure(text=language_manager.get_text("rules"))
        
        # 更新菜单文本
        self.context_menu.entryconfigure(0, label=language_manager.get_text("edit"))
        self.context_menu.entryconfigure(1, label=language_manager.get_text("delete"))
        self.context_menu.entryconfigure(3, label=language_manager.get_text("status"))
        
        # 更新状态子菜单
        self._update_status_menu()
        
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