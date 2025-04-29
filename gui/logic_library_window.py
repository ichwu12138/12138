"""
逻辑关系库窗口模块

该模块提供了一个独立窗口来展示所有保存的 BOM 逻辑关系规则。
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os

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
        
        # 设置列宽
        self.tree.column("rule_id", width=100, anchor=CENTER)
        self.tree.column("condition", width=300, anchor=CENTER)
        self.tree.column("effect", width=300, anchor=CENTER)
        self.tree.column("status", width=100, anchor=CENTER)
        self.tree.column("tags", width=150, anchor=CENTER)
        self.tree.column("tech_doc", width=150, anchor=CENTER)
        
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
                
            # 保存当前的标签和技术文档值
            current_values = self.tree.item(item)["values"]
            current_tags = current_values[4] if len(current_values) > 4 else ""
            current_tech_doc = current_values[5] if len(current_values) > 5 else ""
                
            # 创建编辑对话框
            dialog = LogicRuleEditor(self, rule, self.logic_builder)
            result = dialog.show()
            
            if result:
                # 更新树形视图中的显示，保留标签和技术文档
                effect_text = f"→ {result['effect']}"
                self.tree.item(
                    item,
                    values=(
                        rule.rule_id,
                        result["condition"],
                        effect_text,
                        language_manager.get_text(result["status"].value),
                        current_tags,  # 保持原有标签
                        current_tech_doc  # 保持原有技术文档
                    )
                )
                
                # 更新逻辑构建器中的规则，但不更改标签和技术文档
                rule.condition = result["condition"]
                rule.action = result["effect"]
                rule.status = result["status"]
                # 不更新 rule.tags 和 rule.tech_doc_path
                self.logic_builder._save_rules()  # 保存更改
                
                # 通知规则变更
                self.logic_builder.notify_rule_change("modified", rule.rule_id, rule)
                
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
            
            # 通知规则变更
            self.logic_builder.notify_rule_change("deleted", item)
            
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
            
            # 通知规则变更
            self.logic_builder.notify_rule_change("modified", rule.rule_id, rule)
            
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
        search_text = self.search_var.get().strip()
        
        try:
            # 清空当前显示
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 如果搜索框为空，显示缓存的所有规则
            if not search_text:
                self._show_cached_rules()
                return
            
            # 使用缓存的规则进行搜索，避免重复加载
            matched_rules = 0
            search_upper = search_text.upper()
            
            for rule in self.cached_rules:
                show_rule = False
                
                # 1. K码搜索（严格顺序匹配）
                if search_upper == 'K' or search_upper.startswith('K-'):
                    if rule.condition.upper().startswith(search_upper):
                        show_rule = True
                
                # 2. 数字搜索
                elif search_text.isdigit():
                    # 2.1 影响项表达式（严格顺序匹配最后一个-后的数字）
                    impact_parts = rule.action.split('-')
                    if impact_parts and impact_parts[-1].startswith(search_text):
                        show_rule = True
                    # 2.2 标签中的数字（如果标签包含数字，也进行搜索）
                    elif hasattr(rule, 'tags') and rule.tags:
                        if any(tag.strip().startswith(search_text) for tag in str(rule.tags).split(',')):
                            show_rule = True
                
                # 3. 标签搜索（严格顺序匹配）
                elif hasattr(rule, 'tags') and rule.tags:
                    if any(tag.strip().startswith(search_text) for tag in str(rule.tags).split(',')):
                        show_rule = True
                
                # 4. 通用搜索（严格顺序匹配）
                else:
                    if (rule.rule_id.upper().startswith(search_upper) or
                        rule.condition.upper().startswith(search_upper) or
                        rule.action.startswith(search_text) or
                        (hasattr(rule, 'tags') and rule.tags and 
                         any(tag.strip().startswith(search_text) for tag in str(rule.tags).split(',')))):
                        show_rule = True
                
                # 如果规则匹配，显示它
                if show_rule:
                    effect_text = f"→ {rule.action}"
                    self.tree.insert(
                        "",
                        "end",
                        iid=rule.rule_id,
                        values=(
                            rule.rule_id,
                            rule.condition,
                            effect_text,
                            language_manager.get_text(rule.status.value),
                            rule.tags if hasattr(rule, 'tags') else "",
                            os.path.basename(rule.tech_doc_path) if hasattr(rule, 'tech_doc_path') and rule.tech_doc_path else ""
                        )
                    )
                    matched_rules += 1
            
            self.logger.info(f"搜索 '{search_text}' 完成：显示 {matched_rules}/{len(self.cached_rules)} 条规则")
            
        except Exception as e:
            self.logger.error(f"搜索失败: {str(e)}")
            # 发生错误时显示所有缓存的规则
            self._show_cached_rules()
            
    def _show_cached_rules(self):
        """显示所有缓存的规则"""
        try:
            # 清空当前显示
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # 显示所有缓存的规则
            for rule in self.cached_rules:
                effect_text = f"→ {rule.action}"
                self.tree.insert(
                    "",
                    "end",
                    iid=rule.rule_id,
                    values=(
                        rule.rule_id,
                        rule.condition,
                        effect_text,
                        language_manager.get_text(rule.status.value),
                        rule.tags if hasattr(rule, 'tags') else "",
                        os.path.basename(rule.tech_doc_path) if hasattr(rule, 'tech_doc_path') and rule.tech_doc_path else ""
                    )
                )
                
            self.logger.info(f"已显示所有规则（共 {len(self.cached_rules)} 条）")
            
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
        """加载规则数据"""
        try:
            # 清空现有数据
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 强制从文件重新加载规则到 LogicBuilder
            self.logic_builder.load_from_temp_file()
            
            # 更新规则缓存
            self.cached_rules = list(self.logic_builder.get_rules())
            
            # 加载所有规则
            rules_loaded = 0
            for rule in self.cached_rules:
                effect_text = f"→ {rule.action}"
                
                self.tree.insert(
                    "",
                    "end",
                    iid=rule.rule_id,
                    values=(
                        rule.rule_id,
                        rule.condition,
                        effect_text,
                        language_manager.get_text(rule.status.value),
                        rule.tags if hasattr(rule, 'tags') else "",
                        os.path.basename(rule.tech_doc_path) if hasattr(rule, 'tech_doc_path') and rule.tech_doc_path else ""
                    )
                )
                rules_loaded += 1
            
            self.logger.info(f"已加载 {rules_loaded} 条规则")
            
        except Exception as e:
            self.logger.error(f"加载规则数据失败: {str(e)}")

    def _on_rule_change(self, change_type, rule_id=None, rule=None):
        """规则变更事件处理"""
        try:
            self.logger.info(f"收到规则变更事件: type={change_type}, rule_id={rule_id}")
            
            if change_type == "imported":
                # 重新加载所有规则
                self._load_rules()
                self.logger.info("已重新加载所有规则")
            elif change_type == "deleted":
                # 删除规则
                if rule_id and rule_id in self.tree.get_children():
                    self.tree.delete(rule_id)
                    self.logger.info(f"已删除规则: {rule_id}")
            elif change_type == "cleared":
                # 清空所有规则
                for item in self.tree.get_children():
                    self.tree.delete(item)
                self.logger.info("已清空所有规则")
            elif change_type in ["added", "modified"]:
                # 更新或添加规则
                if rule:
                    effect_text = f"→ {rule.action}"
                    try:
                        if rule.rule_id in self.tree.get_children():
                            # 获取当前的标签和技术文档值
                            current_values = self.tree.item(rule.rule_id)["values"]
                            current_tags = current_values[4] if len(current_values) > 4 else ""
                            current_tech_doc = current_values[5] if len(current_values) > 5 else ""
                            
                            # 如果规则对象中有标签和技术文档，则使用规则对象中的值
                            tags = rule.tags if hasattr(rule, 'tags') and rule.tags else current_tags
                            tech_doc = os.path.basename(rule.tech_doc_path) if hasattr(rule, 'tech_doc_path') and rule.tech_doc_path else current_tech_doc
                            
                            # 更新现有规则，保留标签和技术文档
                            self.tree.item(
                                rule.rule_id,
                                values=(
                                    rule.rule_id,
                                    rule.condition,
                                    effect_text,
                                    language_manager.get_text(rule.status.value),
                                    tags,
                                    tech_doc
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
                                    language_manager.get_text(rule.status.value),
                                    ",".join(rule.tags) if rule.tags else "",
                                    os.path.basename(rule.tech_doc_path) if rule.tech_doc_path else ""
                                )
                            )
                            self.logger.info(f"已添加新规则: {rule.rule_id}")
                    except Exception as e:
                        self.logger.error(f"更新/添加规则到树状视图失败: {str(e)}, 规则ID: {rule.rule_id}")
                        
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