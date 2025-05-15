"""
逻辑关系库窗口模块

该模块提供了一个独立窗口来展示所有保存的 BOM 逻辑关系规则。
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import re
from typing import Optional

from utils.language_manager import language_manager
from utils.logger import Logger
from core.logic_builder import LogicBuilder
from models.logic_rule import RuleStatus
from gui.logic_rule_editor import LogicRuleEditor
from utils.validator import ExpressionValidator

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
        
        # 添加规则缓存
        self.cached_rules = []
        
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
        
        # 创建筛选和搜索框架
        self._create_filter_and_search_frame(main_frame)
        
        # 创建规则列表框架
        self._create_rules_frame(main_frame)
        
    def _create_filter_and_search_frame(self, parent):
        """创建筛选和搜索框架"""
        # 最外层的框架
        outer_frame = ttk.LabelFrame(
            parent,
            text=language_manager.get_text("search_and_filter"),
            padding=10,
            style="Large.TLabelframe"
        )
        outer_frame.pack(fill=X, pady=(0, 10))

        # 第一行：逻辑类型筛选 和 逻辑状态筛选
        filter_row_frame = ttk.Frame(outer_frame)
        filter_row_frame.pack(fill=X, pady=5)

        # 逻辑关系类型筛选框架
        type_filter_frame = ttk.LabelFrame(
            filter_row_frame,
            text=language_manager.get_text("logic_type_filter"),
            padding=5,
            style="Large.TLabelframe"
        )
        type_filter_frame.pack(side=LEFT, padx=(0, 10), fill=X, expand=True)

        self.rule_type_var = tk.StringVar(value="all")
        ttk.Radiobutton(type_filter_frame, text=language_manager.get_text("all_logics"), variable=self.rule_type_var, value="all", command=self._apply_filters_and_search, style="Large.TRadiobutton").pack(side=LEFT, padx=5)
        ttk.Radiobutton(type_filter_frame, text=language_manager.get_text("bom_logic"), variable=self.rule_type_var, value="BL", command=self._apply_filters_and_search, style="Large.TRadiobutton").pack(side=LEFT, padx=5)
        ttk.Radiobutton(type_filter_frame, text=language_manager.get_text("tuning_logic"), variable=self.rule_type_var, value="TL", command=self._apply_filters_and_search, style="Large.TRadiobutton").pack(side=LEFT, padx=5)

        # 逻辑状态筛选框架
        status_filter_frame = ttk.LabelFrame(
            filter_row_frame,
            text=language_manager.get_text("logic_status_filter"),
            padding=5,
            style="Large.TLabelframe"
        )
        status_filter_frame.pack(side=LEFT, fill=X, expand=True)

        self.rule_status_var = tk.StringVar(value="all")
        ttk.Radiobutton(status_filter_frame, text=language_manager.get_text("all_statuses"), variable=self.rule_status_var, value="all", command=self._apply_filters_and_search, style="Large.TRadiobutton").pack(side=LEFT, padx=5)
        ttk.Radiobutton(status_filter_frame, text=language_manager.get_text("enabled"), variable=self.rule_status_var, value=RuleStatus.ENABLED.value, command=self._apply_filters_and_search, style="Large.TRadiobutton").pack(side=LEFT, padx=5)
        ttk.Radiobutton(status_filter_frame, text=language_manager.get_text("disabled"), variable=self.rule_status_var, value=RuleStatus.DISABLED.value, command=self._apply_filters_and_search, style="Large.TRadiobutton").pack(side=LEFT, padx=5)
        ttk.Radiobutton(status_filter_frame, text=language_manager.get_text("testing"), variable=self.rule_status_var, value=RuleStatus.TESTING.value, command=self._apply_filters_and_search, style="Large.TRadiobutton").pack(side=LEFT, padx=5)

        # 第二行：内容搜索框
        search_inputs_frame = ttk.Frame(outer_frame)
        search_inputs_frame.pack(fill=X, pady=5)

        # 选择项表达式搜索
        condition_search_frame = ttk.Frame(search_inputs_frame)
        condition_search_frame.pack(fill=X, pady=2)
        ttk.Label(condition_search_frame, text=language_manager.get_text("search_condition") + ":", style="Large.TLabel").pack(side=LEFT, padx=(0,5))
        self.condition_search_var = tk.StringVar()
        condition_entry = ttk.Entry(condition_search_frame, textvariable=self.condition_search_var, font=("Microsoft YaHei", 11), width=40)
        condition_entry.pack(side=LEFT, fill=X, expand=True)
        self.condition_search_var.trace_add("write", lambda *args: self._delayed_search())

        # 影响项表达式搜索
        effect_search_frame = ttk.Frame(search_inputs_frame)
        effect_search_frame.pack(fill=X, pady=2)
        ttk.Label(effect_search_frame, text=language_manager.get_text("search_effect") + ":", style="Large.TLabel").pack(side=LEFT, padx=(0,5))
        self.effect_search_var = tk.StringVar()
        effect_entry = ttk.Entry(effect_search_frame, textvariable=self.effect_search_var, font=("Microsoft YaHei", 11), width=40)
        effect_entry.pack(side=LEFT, fill=X, expand=True)
        self.effect_search_var.trace_add("write", lambda *args: self._delayed_search())

        # 标签搜索
        tags_search_frame = ttk.Frame(search_inputs_frame)
        tags_search_frame.pack(fill=X, pady=2)
        ttk.Label(tags_search_frame, text=language_manager.get_text("search_tags") + ":", style="Large.TLabel").pack(side=LEFT, padx=(0,5))
        self.tags_search_var = tk.StringVar()
        tags_entry = ttk.Entry(tags_search_frame, textvariable=self.tags_search_var, font=("Microsoft YaHei", 11), width=40)
        tags_entry.pack(side=LEFT, fill=X, expand=True)
        self.tags_search_var.trace_add("write", lambda *args: self._delayed_search())
        
        # 清除所有筛选和搜索按钮
        clear_all_filters_button = ttk.Button(
            outer_frame, 
            text=language_manager.get_text("clear_all_filters"),
            command=self._clear_all_filters_and_search,
            style="Large.TButton"
        )
        clear_all_filters_button.pack(pady=5)

    def _delayed_search(self):
        """延迟搜索以避免过于频繁的更新"""
        if hasattr(self, '_search_after_id'):
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self._apply_filters_and_search) # 300ms延迟

    def _clear_all_filters_and_search(self):
        """清除所有筛选条件和搜索框内容"""
        self.rule_type_var.set("all")
        self.rule_status_var.set("all")
        self.condition_search_var.set("")
        self.effect_search_var.set("")
        self.tags_search_var.set("")
        # _apply_filters_and_search 会被Radiobutton的command自动触发，或者手动调用一次
        self._apply_filters_and_search()

    def _apply_filters_and_search(self):
        """应用所有筛选和搜索条件来更新规则列表的显示 - 非层级化描述行"""
        self.logger.debug("LogicLibrary _apply_filters_and_search: 开始应用筛选和搜索。清空现有Treeview项。")
        for item in self.tree.get_children():
            self.tree.delete(item)

        selected_type = self.rule_type_var.get()
        selected_status_val = self.rule_status_var.get()
        search_condition_term = self.condition_search_var.get().strip().upper()
        search_effect_term = self.effect_search_var.get().strip().upper()
        search_tags_input = self.tags_search_var.get().strip().upper()
        search_tags_list = [tag.strip() for tag in search_tags_input.split(',') if tag.strip()] if search_tags_input else []

        matched_rules_count = 0
        self.logger.debug(f"LogicLibrary _apply_filters_and_search: 从self.cached_rules (共 {len(self.cached_rules)} 条) 开始迭代。")
        for rule in self.cached_rules:
            if selected_type != "all" and not rule.rule_id.startswith(selected_type):
                continue
            if selected_status_val != "all" and rule.status.value != selected_status_val:
                continue
            
            if search_condition_term:
                condition_parts = rule.condition.upper().split()
                found_condition_match = any(part.strip("()").startswith(search_condition_term) for part in condition_parts)
                if not found_condition_match and search_condition_term not in rule.condition.upper():
                    continue
            
            if search_effect_term:
                action_upper = rule.action.upper()
                found_effect_match = False
                if search_effect_term.isdigit():
                    if not ExpressionValidator.is_tuning_logic(rule.action):
                        last_sep_index = max(rule.action.rfind(':'), rule.action.rfind('-'))
                        if last_sep_index != -1:
                            target_bom_part = rule.action[last_sep_index + 1:]
                            if target_bom_part.isdigit() and target_bom_part.startswith(search_effect_term):
                                found_effect_match = True
                    else:
                        action_numbers = re.findall(r'\d+', rule.action)
                        if any(num_seq.startswith(search_effect_term) for num_seq in action_numbers):
                            found_effect_match = True
                elif search_effect_term in action_upper:
                    found_effect_match = True
                if not found_effect_match:
                    continue

            if search_tags_list:
                rule_tags_upper = str(rule.tags).upper() if hasattr(rule, 'tags') and rule.tags else ""
                if not any(search_tag_item in rule_tags_upper for search_tag_item in search_tags_list):
                    continue
            
            # 插入规则行
            status_display_text = language_manager.get_text(rule.status.value)
            self.logger.debug(f"LogicLibrary _apply_filters_and_search: 准备插入规则ID '{rule.rule_id}'，状态 '{rule.status.value}' (显示为 '{status_display_text}').")
            rule_values = (
                rule.rule_id,
                rule.condition,
                f"→ {rule.action}",
                status_display_text,
                rule.tags if hasattr(rule, 'tags') else "",
                os.path.basename(rule.tech_doc_path) if hasattr(rule, 'tech_doc_path') and rule.tech_doc_path else ""
            )
            self.tree.insert("", "end", iid=rule.rule_id, values=rule_values, tags=('rule_row',))

            # 插入描述行 (如果存在)
            if rule.description:
                parts = rule.description.split('→', 1)
                cond_desc = parts[0].strip() if parts else ""
                eff_desc = parts[1].strip() if len(parts) > 1 else ""
                desc_item_id = f"{rule.rule_id}_desc_sep"
                desc_values = ("", f"  └─ {cond_desc}", eff_desc, "", "", "") 
                self.tree.insert("", "end", iid=desc_item_id, values=desc_values, tags=('description_row_sep',))
            
            matched_rules_count += 1
        
        self.tree.tag_configure('description_row_sep', foreground='gray50')
        self.tree.tag_configure('rule_row', background='white')
        self.logger.info(f"LogicLibrary _apply_filters_and_search: 筛选和搜索完成：显示 {matched_rules_count}/{len(self.cached_rules)} 条规则。")

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
        columns = ("rule_id", "condition", "effect", "status", "tags", "tech_doc")
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
        self.tree.heading("tags", text=language_manager.get_text("rule_tags"), anchor=CENTER)
        self.tree.heading("tech_doc", text=language_manager.get_text("tech_doc"), anchor=CENTER)
        
        # 设置列宽 (调整后)
        self.tree.column("rule_id", width=60, anchor=CENTER, stretch=tk.NO)
        self.tree.column("condition", width=310, anchor=W)
        self.tree.column("effect", width=310, anchor=W)
        self.tree.column("status", width=60, anchor=CENTER, stretch=tk.NO)
        self.tree.column("tags", width=80, anchor=CENTER, stretch=tk.NO)
        self.tree.column("tech_doc", width=80, anchor=CENTER, stretch=tk.NO)
        
        # 配置大字体样式
        style = ttk.Style()
        style.configure(
            "Large.Treeview",
            font=("Microsoft YaHei", 11),
            rowheight=30
        )
        style.configure(
            "Large.Treeview.Heading",
            font=("Microsoft YaHei", 11, "bold"),
            rowheight=30
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
            label=language_manager.get_text("import_tech_doc"),
            command=self._import_tech_doc
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
            
    def _get_actual_rule_id_from_item(self, item_id: str) -> Optional[str]:
        """从给定的Treeview item ID (可能是规则行或描述行) 获取实际的规则ID。"""
        if not item_id or not self.tree.exists(item_id):
            return None
        
        if self.tree.tag_has('description_row_sep', item_id):
            current_index = self.tree.index(item_id)
            if current_index > 0:
                all_items = self.tree.get_children("")
                if current_index < len(all_items) and current_index > 0 :
                    potential_rule_item_id = all_items[current_index-1]
                    if (self.tree.tag_has('rule_row', potential_rule_item_id) and
                       potential_rule_item_id == item_id.replace("_desc_sep", "")):
                        return potential_rule_item_id
            base_id = item_id.rsplit('_desc_sep', 1)[0]
            if self.tree.exists(base_id) and self.tree.tag_has('rule_row', base_id):
                return base_id
            return None
        elif self.tree.tag_has('rule_row', item_id):
            return item_id
        return None

    def _edit_selected_rule(self):
        """编辑选中的规则 - 支持非层级化描述行"""
        try:
            selected_item_id = self.tree.focus()
            if not selected_item_id:
                selection = self.tree.selection()
                if not selection: return
                selected_item_id = selection[0]

            rule_id = self._get_actual_rule_id_from_item(selected_item_id)
            if not rule_id:
                self.logger.warning(f"LogicLibrary: 无法从选中项 {selected_item_id} 推断规则ID进行编辑。")
                return

            rule_obj = self.logic_builder.get_rule_by_id(rule_id)
            if not rule_obj:
                self.logger.error(f"LogicLibrary: 找不到规则 {rule_id}。")
                messagebox.showerror(language_manager.get_text("error"), f"找不到规则 {rule_id}", parent=self)
                return
            
            # 直接将从logic_builder获取的rule_obj传递给编辑器
            dialog = LogicRuleEditor(self, rule_obj, self.logic_builder) 
            result = dialog.show() 
            
            if result: 
                # LogicRuleEditor 的 _on_confirm 应该已经修改了传入的 rule_obj 的属性
                # (condition, action, status)
                # 为了保险，可以像LogicPanel那样显式地从result中设置，
                # 但如果LogicRuleEditor正确地修改了传入的rule_obj，则这些是多余的。
                if 'condition' in result:
                    rule_obj.condition = result["condition"]
                if 'effect' in result:
                    rule_obj.action = result["effect"]
                if 'status' in result:
                    new_status_val = result["status"]
                    if isinstance(new_status_val, str):
                        try:
                            rule_obj.status = RuleStatus(new_status_val)
                        except ValueError:
                            self.logger.error(f"LogicLibrary: 从编辑器接收到无效的状态字符串 '{new_status_val}' for {rule_id}.")
                    elif isinstance(new_status_val, RuleStatus):
                        rule_obj.status = new_status_val
                    else:
                        self.logger.error(f"LogicLibrary: 从编辑器接收到未知类型的状态 '{type(new_status_val)}' for {rule_id}.")
                
                # 调用 update_rule_description 会保存整个 rule_obj (包括修改后的status)
                updated_rule_obj = self.logic_builder.update_rule_description(rule_obj.rule_id)

                if updated_rule_obj:
                    self.logger.info(f"LogicLibrary: 规则 {rule_obj.rule_id} 编辑完成并通过LogicBuilder更新。")
                    # _on_rule_change 会被调用以刷新列表
                else:
                    self.logger.error(f"LogicLibrary: LogicBuilder 未能更新规则 {rule_obj.rule_id}。")
        except Exception as e:
            self.logger.error(f"编辑规则失败: {str(e)}", exc_info=True)
            messagebox.showerror(language_manager.get_text("error"), str(e), parent=self)
            
    def _delete_selected_rule(self):
        """删除选中的规则 - 支持非层级化描述行"""
        try:
            selected_item_id = self.tree.focus()
            if not selected_item_id:
                selection = self.tree.selection()
                if not selection: return
                selected_item_id = selection[0]

            rule_id_to_delete = self._get_actual_rule_id_from_item(selected_item_id)
            if not rule_id_to_delete:
                self.logger.warning(f"LogicLibrary: 无法从选中项 {selected_item_id} 推断规则ID进行删除。")
                messagebox.showwarning(language_manager.get_text("warning"), "请选择一个有效的规则进行删除。", parent=self)
                return
                
            if not messagebox.askyesno(
                language_manager.get_text("confirm"),
                language_manager.get_text("confirm_delete_rule"),
                parent=self
            ):
                return
                
            if self.logic_builder.delete_rule(rule_id_to_delete):
                self.logger.info(f"LogicLibrary: 请求删除规则 {rule_id_to_delete}")
            else:
                self.logger.error(f"LogicLibrary: LogicBuilder 未能删除规则 {rule_id_to_delete}")
                messagebox.showerror(language_manager.get_text("error"), f"删除规则 {rule_id_to_delete} 失败。", parent=self)
                
        except Exception as e:
            self.logger.error(f"删除规则失败: {str(e)}", exc_info=True)
            messagebox.showerror(language_manager.get_text("error"), str(e), parent=self)
            
    def _change_rule_status(self, new_status: RuleStatus):
        """更改规则状态 - 支持非层级化描述行"""
        try:
            selected_item_id = self.tree.focus()
            if not selected_item_id:
                selection = self.tree.selection()
                if not selection: return
                selected_item_id = selection[0]

            rule_id = self._get_actual_rule_id_from_item(selected_item_id)
            if not rule_id:
                self.logger.warning(f"LogicLibrary: 无法从选中项 {selected_item_id} 推断规则ID以更改状态。")
                return
                
            rule = self.logic_builder.get_rule_by_id(rule_id)
            if not rule:
                self.logger.error(f"LogicLibrary: _change_rule_status 找不到规则 {rule_id}")
                return
                
            rule.status = new_status
            self.logic_builder._save_rules()
            self.logic_builder.notify_rule_change("modified", rule.rule_id, rule)
            self.logger.info(f"LogicLibrary: 已更改规则状态: {rule_id} -> {new_status.value}")
            
        except Exception as e:
            self.logger.error(f"更改规则状态失败: {str(e)}", exc_info=True)
            messagebox.showerror(language_manager.get_text("error"), str(e), parent=self)
        
    def _clear_search(self):
        """清空搜索"""
        self.condition_search_var.set("")
        self.effect_search_var.set("")
        self.tags_search_var.set("")
        self._apply_filters_and_search()
        
    def _on_search_changed(self, *args):
        """搜索内容变化事件处理"""
        self._delayed_search()
        
    def _show_cached_rules(self):
        """显示所有缓存的规则"""
        try:
            self.rule_type_var.set("all")
            self.rule_status_var.set("all")
            self.condition_search_var.set("")
            self.effect_search_var.set("")
            self.tags_search_var.set("")
            self._apply_filters_and_search()
            
        except Exception as e:
            self.logger.error(f"显示缓存规则失败: {str(e)}")
            # 如果显示缓存失败，尝试重新加载
            self._load_rules()
        
    def _on_double_click(self, event):
        """双击事件处理"""
        try:
            # 获取点击的列
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            
            if not item:
                return
                
            # 获取规则
            rule = self.logic_builder.get_rule_by_id(item)
            if not rule:
                return
            
            # 根据列执行不同的操作
            if column == "#5":  # 标签列
                self._edit_tags(item, rule)
            elif column == "#6":  # 技术文档列
                self._edit_tech_doc(item, rule)
            else:  # 其他列
                self._edit_selected_rule()
                
        except Exception as e:
            self.logger.error(f"处理双击事件失败: {str(e)}", exc_info=True)

    def _edit_tags(self, item, rule):
        """编辑标签"""
        try:
            # 创建对话框
            dialog = tk.Toplevel(self)
            dialog.title(language_manager.get_text("edit_tags"))
            dialog.geometry("400x200")
            dialog.transient(self)  # 设置为主窗口的临时窗口
            dialog.grab_set()  # 设置为模态对话框
            
            # 居中显示
            dialog.geometry("+%d+%d" % (
                self.winfo_rootx() + self.winfo_width()//2 - 200,
                self.winfo_rooty() + self.winfo_height()//2 - 100
            ))
            
            # 创建标签输入框
            ttk.Label(
                dialog,
                text=language_manager.get_text("input_tags"),
                font=("Microsoft YaHei", 12)
            ).pack(pady=10)
            
            # 获取当前标签值（确保是字符串）
            current_tags = str(rule.tags) if hasattr(rule, 'tags') and rule.tags is not None else ""
            tags_var = tk.StringVar(value=current_tags)
            
            entry = ttk.Entry(
                dialog,
                textvariable=tags_var,
                font=("Microsoft YaHei", 12),
                width=40
            )
            entry.pack(pady=10, padx=20)
            
            # 创建按钮框架
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(pady=20)
            
            # 确认按钮
            ttk.Button(
                btn_frame,
                text=language_manager.get_text("confirm"),
                command=lambda: self._save_tags(dialog, item, rule, tags_var.get()),
                style="Large.TButton"
            ).pack(side=LEFT, padx=10)
            
            # 取消按钮
            ttk.Button(
                btn_frame,
                text=language_manager.get_text("cancel"),
                command=dialog.destroy,
                style="Large.TButton"
            ).pack(side=LEFT, padx=10)
            
            # 设置焦点到输入框
            entry.focus_set()
            
        except Exception as e:
            self.logger.error(f"创建标签编辑对话框失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                str(e)
            )

    def _save_tags(self, dialog, item, rule, tags):
        """保存标签"""
        try:
            # 直接使用用户输入的标签值，不做任何处理
            rule.tags = tags
            
            # 更新树状视图显示
            values = list(self.tree.item(item)["values"])
            values[4] = tags
            self.tree.item(item, values=values)
            
            # 强制保存到临时文件
            self.logic_builder._save_rules()
            self.logger.info(f"已保存标签到临时文件: {rule.rule_id} -> {tags}")
            
            # 更新缓存中的规则
            for cached_rule in self.cached_rules:
                if cached_rule.rule_id == rule.rule_id:
                    cached_rule.tags = tags
                    break
            
            # 通知规则变更
            self.logic_builder.notify_rule_change("modified", item, rule)
            
            # 关闭对话框
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"保存标签失败: {str(e)}")
            messagebox.showerror(
                language_manager.get_text("error"),
                str(e)
            )

    def _edit_tech_doc(self, item, rule):
        """编辑技术文档"""
        try:
            # 如果已经有技术文档，则打开它
            if rule.tech_doc_path and os.path.exists(rule.tech_doc_path):
                try:
                    os.startfile(rule.tech_doc_path)  # Windows系统
                except Exception as e:
                    self.logger.error(f"打开技术文档失败: {str(e)}", exc_info=True)
                    messagebox.showerror(
                        language_manager.get_text("error"),
                        language_manager.get_text("open_tech_doc_error"),
                        parent=self
                    )
            else:
                # 如果没有技术文档，则添加新文档
                self._import_tech_doc(item, rule)
        except Exception as e:
            self.logger.error(f"编辑技术文档失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                str(e),
                parent=self
            )

    def _import_tech_doc(self, item=None, rule=None):
        """导入技术文档"""
        try:
            # 如果没有提供item和rule，则获取当前选中项
            if item is None or rule is None:
                selection = self.tree.selection()
                if not selection:
                    return
                item = selection[0]
                rule = self.logic_builder.get_rule_by_id(item)
                if not rule:
                    return

            # 保存当前窗口状态
            current_state = self.state()
            if current_state == 'zoomed':
                self.state('normal')
            
            # 打开文件选择对话框
            file_path = filedialog.askopenfilename(
                title=language_manager.get_text("select_tech_doc"),
                filetypes=[
                    (language_manager.get_text("word_files"), "*.doc *.docx"),
                    (language_manager.get_text("all_files"), "*.*")
                ],
                parent=self
            )
            
            # 恢复窗口状态
            if current_state == 'zoomed':
                self.state('zoomed')
            
            if file_path:
                try:
                    # 更新规则的技术文档路径
                    rule.tech_doc_path = file_path
                    
                    # 更新树状视图显示
                    values = list(self.tree.item(item)["values"])
                    values[5] = os.path.basename(file_path)
                    self.tree.item(item, values=values)
                    
                    # 强制保存到临时文件
                    self.logic_builder._save_rules()
                    self.logger.info(f"已保存技术文档到临时文件: {rule.rule_id} -> {file_path}")
                    
                    # 更新缓存中的规则
                    for cached_rule in self.cached_rules:
                        if cached_rule.rule_id == rule.rule_id:
                            cached_rule.tech_doc_path = file_path
                            break
                    
                    # 通知规则变更
                    self.logic_builder.notify_rule_change("modified", item, rule)
                    
                    # 显示成功消息
                    messagebox.showinfo(
                        language_manager.get_text("success"),
                        language_manager.get_text("tech_doc_added_success"),
                        parent=self
                    )
                    
                except Exception as e:
                    self.logger.error(f"保存技术文档路径失败: {str(e)}")
                    messagebox.showerror(
                        language_manager.get_text("error"),
                        str(e),
                        parent=self
                    )
                
        except Exception as e:
            self.logger.error(f"导入技术文档失败: {str(e)}")
            messagebox.showerror(
                language_manager.get_text("error"),
                str(e),
                parent=self
            )

    def _load_rules(self):
        """加载规则数据 - 非层级化描述行"""
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # self.logic_builder.load_from_temp_file() # 确保 LogicBuilder 有最新的规则，这通常在窗口打开前完成
            self.cached_rules = list(self.logic_builder.get_rules()) 
            
            rules_loaded_count = 0
            for rule in self.cached_rules:
                rule_values = (
                    rule.rule_id,
                    rule.condition,
                    f"→ {rule.action}",
                    language_manager.get_text(rule.status.value),
                    rule.tags if hasattr(rule, 'tags') else "",
                    os.path.basename(rule.tech_doc_path) if hasattr(rule, 'tech_doc_path') and rule.tech_doc_path else ""
                )
                self.tree.insert("", "end", iid=rule.rule_id, values=rule_values, tags=('rule_row',))
                
                if rule.description:
                    parts = rule.description.split('→', 1)
                    cond_desc = parts[0].strip() if parts else ""
                    eff_desc = parts[1].strip() if len(parts) > 1 else ""
                    desc_item_id = f"{rule.rule_id}_desc_sep"
                    desc_values = ("", f"  └─ {cond_desc}", eff_desc, "", "", "")
                    self.tree.insert("", "end", iid=desc_item_id, values=desc_values, tags=('description_row_sep',))
                rules_loaded_count += 1
            
            self.tree.tag_configure('description_row_sep', foreground='gray50')
            self.tree.tag_configure('rule_row', background='white')
            self.logger.info(f"LogicLibrary: 已加载 {rules_loaded_count} 条规则 (非层级)。")
            
            self._apply_filters_and_search() # 应用筛选和搜索

        except Exception as e:
            self.logger.error(f"加载规则数据失败: {str(e)}", exc_info=True)

    def _on_rule_change(self, change_type, rule_id=None, rule=None):
        """规则变更事件处理 - 非层级化描述行"""
        try:
            self.logger.info(f"LogicLibrary _on_rule_change: 收到通知: 类型='{change_type}', RuleID='{rule_id}'")
            if rule:
                self.logger.debug(f"LogicLibrary _on_rule_change: 附带的Rule对象: ID='{rule.rule_id}', Status='{rule.status.value if rule.status else 'N/A'}', Desc='{rule.description[:30]}...'")
            elif rule_id:
                self.logger.debug(f"LogicLibrary _on_rule_change: 仅有RuleID: {rule_id}")

            self.logger.debug(f"LogicLibrary _on_rule_change: 更新self.cached_rules前，包含 {len(self.cached_rules)} 条规则。")
            self.cached_rules = list(self.logic_builder.get_rules())
            self.logger.debug(f"LogicLibrary _on_rule_change: 更新self.cached_rules后，包含 {len(self.cached_rules)} 条规则。调用 _apply_filters_and_search。")
            
            self._apply_filters_and_search()
            
            self.logger.info(f"LogicLibrary _on_rule_change: 因 '{change_type}' (非层级)，规则列表已通过重新筛选和加载进行刷新。")

            self.tree.tag_configure('description_row_sep', foreground='gray50')
            self.tree.update_idletasks()
            self.logger.debug(f"LogicLibrary _on_rule_change: Treeview update_idletasks() 已调用。")

        except Exception as e:
            self.logger.error(f"LogicLibrary: 处理规则变更事件 (非层级) 失败: {str(e)}", exc_info=True)
            
    def refresh_texts(self):
        """刷新所有文本"""
        # 更新窗口标题
        self.title(language_manager.get_text("logic_library"))
        
        # 更新列标题
        self.tree.heading("rule_id", text=language_manager.get_text("rule_id"))
        self.tree.heading("condition", text=language_manager.get_text("edit_rule_condition"))
        self.tree.heading("effect", text=language_manager.get_text("edit_rule_effect"))
        self.tree.heading("status", text=language_manager.get_text("edit_rule_status"))
        self.tree.heading("tags", text=language_manager.get_text("rule_tags"))
        self.tree.heading("tech_doc", text=language_manager.get_text("tech_doc"))
        
        # 更新框架标题
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if "search" in str(child.cget("text")).lower():
                    child.configure(text=language_manager.get_text("search"))
                elif "rules" in str(child.cget("text")).lower():
                    child.configure(text=language_manager.get_text("rules"))
        
        # 更新菜单文本
        self.context_menu.entryconfigure(0, label=language_manager.get_text("edit"))
        self.context_menu.entryconfigure(1, label=language_manager.get_text("import_tech_doc"))
        self.context_menu.entryconfigure(2, label=language_manager.get_text("delete"))
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