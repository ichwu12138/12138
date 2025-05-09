"""
主窗口模块 (Tkinter + ttkbootstrap版本)

该模块提供了应用程序的主窗口，采用三栏式布局设计。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import json
import os

from utils.config_manager import config_manager
from utils.language_manager import language_manager
from utils.logger import Logger
from utils.validator import ExpressionValidator
from core.logic_builder import LogicBuilder, RULES_DATA_FILE
from core.config_processor import ConfigProcessor
from core.bom_processor import BomProcessor
from models.logic_rule import LogicRule, RuleStatus
from gui.logic_panel import LogicPanel
from gui.config_panel import ConfigPanel
from gui.bom_panel import BomPanel
from gui.language_dialog_tk import LanguageDialog
from gui.logic_library_window import LogicLibraryWindow

class MainWindow:
    """主窗口类"""
    
    def __init__(self, root):
        """初始化主窗口
        
        Args:
            root: 根窗口
        """
        self.root = root
        
        # 保存参数
        self.root.main_window = self  # 在根窗口中保存MainWindow实例的引用
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 创建配置选项处理器
        self.config_processor = ConfigProcessor()
        
        # 创建BOM处理器
        self.bom_processor = BomProcessor()
        
        # 创建逻辑构建器
        self.logic_builder = LogicBuilder(self.config_processor)
        
        # 标记规则是否已加载
        self.rules_loaded = False
        
        # 注册语言变化的回调函数
        language_manager.add_callback(self.refresh_all_texts)
        
        # 配置全局样式
        self._configure_global_styles()
        
        # 创建界面
        self._create_widgets()
        
        # 创建菜单
        self._create_menu()
        
        # 绑定事件
        self._bind_events()
        
        # 设置窗口标题
        self.root.title(language_manager.get_text("app_title"))
        
        # 加载上次的配置
        self.root.after(1000, self._load_last_config)  # 延迟1秒后执行
        
    def _configure_global_styles(self):
        """配置全局样式"""
        style = ttk.Style()
        
        # 定义统一的字体大小 - 调整为适应1920*1080分辨率
        FONT_SIZES = {
            "menu": 12,           # 菜单字体大小
            "title": 14,          # 标题字体大小
            "frame_title": 12,    # 框架标题字体大小
            "button": 11,         # 按钮字体大小
            "tree": 12,           # 树状图字体大小
            "tree_title": 12,     # 树状图标题字体大小
            "status": 10,         # 状态栏字体大小
            "label": 11,          # 标签字体大小
            "text": 11            # 文本字体大小
        }
        
        # 定义统一的内边距
        PADDINGS = {
            "button": (10, 6),    # 按钮内边距
            "frame": 8,           # 框架内边距
            "tree": 4             # 树状图内边距
        }
        
        # 定义统一的颜色
        COLORS = {
            "frame_bg": "#f0f0f0",      # 框架背景色
            "title_fg": "#000000",      # 标题前景色
            "button_bg": "#e1e1e1",     # 按钮背景色
            "tree_select": "#0078D7",   # 树状图选中色
            "f_code": "blue",           # F码颜色
            "k_code": "green"           # K码颜色
        }
        
        # 配置菜单样式
        self.root.option_add("*Menu.font", ("Microsoft YaHei", FONT_SIZES["menu"]))
        
        # 配置标题样式
        style.configure(
            "Title.TLabel",
            font=("Microsoft YaHei", FONT_SIZES["title"], "bold"),
            padding=8
        )
        
        # 配置框架标题样式
        style.configure(
            "FrameTitle.TLabel",
            font=("Microsoft YaHei", FONT_SIZES["frame_title"], "bold"),
            padding=4
        )
        
        # 配置按钮样式
        style.configure(
            "Main.TButton",
            font=("Microsoft YaHei", FONT_SIZES["button"]),
            padding=PADDINGS["button"]
        )
        
        # 配置成功按钮样式
        style.configure(
            "success.Main.TButton",
            font=("Microsoft YaHei", FONT_SIZES["button"]),
            padding=PADDINGS["button"]
        )
        
        # 配置树状视图样式
        style.configure(
            "Main.Treeview",
            font=("Microsoft YaHei", FONT_SIZES["tree"]),
            rowheight=30,
            padding=PADDINGS["tree"]
        )
        
        # 配置树状视图标题样式
        style.configure(
            "Main.Treeview.Heading",
            font=("Microsoft YaHei", FONT_SIZES["tree_title"], "bold"),
            padding=4
        )
        
        # 配置标签样式
        style.configure(
            "Main.TLabel",
            font=("Microsoft YaHei", FONT_SIZES["label"]),
            padding=4
        )
        
        # 配置框架样式
        style.configure(
            "Main.TFrame",
            padding=PADDINGS["frame"],
            relief="solid",
            borderwidth=1
        )
        
        # 配置LabelFrame样式
        style.configure(
            "Main.TLabelframe",
            padding=PADDINGS["frame"],
            font=("Microsoft YaHei", FONT_SIZES["frame_title"])
        )
        style.configure(
            "Main.TLabelframe.Label",
            font=("Microsoft YaHei", FONT_SIZES["frame_title"])
        )
        
        # 配置状态栏样式
        style.configure(
            "Status.TLabel",
            font=("Microsoft YaHei", FONT_SIZES["status"]),
            padding=4
        )
        
        # 配置树状图标签样式
        style.map(
            "Main.Treeview",
            background=[("selected", COLORS["tree_select"])],
            foreground=[("selected", "white")]
        )
        
        # 配置特殊代码样式
        style.configure(
            "FCode.TLabel",
            foreground=COLORS["f_code"],
            font=("Microsoft YaHei", FONT_SIZES["text"])
        )
        style.configure(
            "KCode.TLabel",
            foreground=COLORS["k_code"],
            font=("Microsoft YaHei", FONT_SIZES["text"])
        )
        
        # 配置面板样式
        style.configure(
            "Panel.TFrame",
            relief="solid",
            borderwidth=1,
            padding=PADDINGS["frame"]
        )
        
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主布局框架
        self.main_frame = ttk.Frame(self.root, padding=5, style="Main.TFrame")
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        # 创建水平布局的Panedwindow
        self.paned = ttk.PanedWindow(self.main_frame, orient=HORIZONTAL)
        self.paned.pack(fill=BOTH, expand=YES)
        
        # 创建左侧配置面板
        self.left_panel = ttk.Frame(self.paned, style="Panel.TFrame")
        self.paned.add(self.left_panel, weight=1)
        
        # 创建中间逻辑编辑面板
        self.center_panel = ttk.Frame(self.paned, style="Panel.TFrame")
        self.paned.add(self.center_panel, weight=2)
        
        # 创建右侧BOM面板
        self.right_panel = ttk.Frame(self.paned, style="Panel.TFrame")
        self.paned.add(self.right_panel, weight=1)
        
        # 创建各个面板的标题
        ttk.Label(
            self.main_frame,
            text=language_manager.get_text("panels_title"),
            style="Title.TLabel"
        ).pack(side=TOP, fill=X, pady=(0, 10))
        
        # 创建各个面板的内容
        self._create_left_panel()
        self._create_center_panel()
        self._create_right_panel()
        
    def _create_left_panel(self):
        """创建左侧配置面板内容"""
        # 创建配置面板
        self.config_panel = ConfigPanel(self.left_panel, self.config_processor)
        self.config_panel.pack(fill=BOTH, expand=YES)
        
    def _create_center_panel(self):
        """创建中间逻辑编辑面板内容"""
        # 创建逻辑编辑面板
        self.logic_panel = LogicPanel(
            self.center_panel, 
            self.logic_builder,
            config_processor=self.config_processor,
            bom_processor=self.bom_processor
        )
        self.logic_panel.pack(fill=BOTH, expand=YES)
        
    def _create_right_panel(self):
        """创建右侧BOM面板内容"""
        # 创建BOM面板
        self.bom_panel = BomPanel(self.right_panel, self.bom_processor)
        self.bom_panel.pack(fill=BOTH, expand=YES)
    
    def _create_menu(self):
        """创建菜单栏"""
        # 创建菜单栏
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # 文件菜单
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=language_manager.get_text("menu_file"), menu=self.file_menu)
        self.file_menu.add_command(label=language_manager.get_text("import_config"), 
                                 command=self._import_config)
        self.file_menu.add_command(label=language_manager.get_text("import_bom"), 
                                 command=self._import_bom)
        self.file_menu.add_command(label=language_manager.get_text("import_logic_rules"), 
                                 command=self._import_logic_rules)
        self.file_menu.add_command(label=language_manager.get_text("export_logic_rules"), 
                                 command=self._export_logic_rules)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=language_manager.get_text("exit"), 
                                 command=self._on_closing)
        
        # 视图菜单
        self.view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=language_manager.get_text("menu_view"), menu=self.view_menu)
        self.view_menu.add_command(label=language_manager.get_text("logic_library"), 
                                 command=self._show_logic_library)
        self.view_menu.add_separator()
        self.view_menu.add_command(label=language_manager.get_text("language"), 
                                 command=self._show_language_dialog)
        
        # 帮助菜单
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=language_manager.get_text("menu_help"), menu=self.help_menu)
        self.help_menu.add_command(label=language_manager.get_text("view_log"), 
                                 command=self._show_log_viewer)
        self.help_menu.add_command(label=language_manager.get_text("about"), 
                                 command=self._show_about)
    
    def _bind_events(self):
        """绑定事件"""
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _on_closing(self):
        """窗口关闭事件处理"""
        # 检查是否有未导出的规则
        if self.logic_builder.has_unsaved_rules():
            if not messagebox.askyesno(
                language_manager.get_text("confirm_exit"),
                language_manager.get_text("unsaved_rules_exit_confirm")
            ):
                return
        elif not messagebox.askyesno(
            language_manager.get_text("confirm_exit"),
            language_manager.get_text("confirm_exit_message")
        ):
            return
            
        # 移除语言变化的回调函数
        language_manager.remove_callback(self.refresh_all_texts)
        self.root.destroy()
            
    def _import_config(self):
        """导入配置文件"""
        if hasattr(self, 'config_panel'):
            self.config_panel._import_excel()
            
    def _import_bom(self):
        """导入BOM文件"""
        if hasattr(self, 'bom_panel'):
            self.bom_panel._import_bom()
            
    def _import_logic_rules(self):
        """导入BOM逻辑关系"""
        try:
            # 检查是否有未导出的规则
            if self.logic_builder.has_unsaved_rules():
                if not messagebox.askyesno(
                    language_manager.get_text("confirm"),
                    language_manager.get_text("unsaved_rules_import_confirm")
                ):
                    return
            
            # 打开文件选择对话框
            file_path = filedialog.askopenfilename(
                title=language_manager.get_text("select_import_file"),
                filetypes=[(language_manager.get_text("json_files"), "*.json")]
            )
            
            if file_path:
                try:
                    # 读取JSON文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        import_data = json.load(f)
                    
                    # 验证规则数据格式
                    # 检查是新格式还是旧格式
                    is_new_format = "BL_rules" in import_data or "TL_rules" in import_data
                    is_old_format = "rules" in import_data

                    if not is_new_format and not is_old_format:
                        raise ValueError("无效的规则文件格式，缺少 'rules' 或 'BL_rules'/'TL_rules' 字段")

                    rules_to_validate = []
                    if is_new_format:
                        bl_rules = import_data.get("BL_rules", [])
                        tl_rules = import_data.get("TL_rules", [])
                        if not isinstance(bl_rules, list) or not isinstance(tl_rules, list):
                            raise ValueError("新格式中 'BL_rules' 和 'TL_rules' 必须是列表")
                        rules_to_validate = bl_rules + tl_rules
                    elif is_old_format:
                        rules_list = import_data["rules"]
                        if not isinstance(rules_list, list):
                            raise ValueError("旧格式中 'rules' 必须是列表")
                        rules_to_validate = rules_list
                    
                    # 验证每条规则
                    for rule_data_item in rules_to_validate: # Renamed to avoid conflict
                        if not isinstance(rule_data_item, dict):
                            raise ValueError("规则必须是字典格式")
                        
                        # 检查必需字段
                        required_fields = ["logic_id", "selection_expression", "logic_relation", "impact_expression", "status"]
                        missing_fields = [field for field in required_fields if field not in rule_data_item]
                        if missing_fields:
                            raise ValueError(f"规则 {rule_data_item.get('logic_id', '')} 缺少必需字段: {', '.join(missing_fields)}")
                        
                        # 验证状态值
                        if rule_data_item["status"] not in [s.value for s in RuleStatus]: # Check against enum values
                            raise ValueError(f"规则 {rule_data_item['logic_id']} 的状态值无效: {rule_data_item['status']}")
                        
                        # 检查是否是微调逻辑
                        is_tuning = ExpressionValidator.is_tuning_logic(rule_data_item["impact_expression"])
                        
                        # 验证规则ID格式 (logic_builder.import_rules 将处理ID重新生成，此处仅作基本校验)
                        logic_id = rule_data_item["logic_id"]
                        if not logic_id: 
                            self.logger.warning("导入规则时发现空logic_id，将由LogicBuilder生成新ID。")
                        elif not (logic_id.startswith("BL") or logic_id.startswith("TL")):
                             self.logger.warning(f"规则ID '{logic_id}' 格式不规范，LogicBuilder将尝试处理。")
                        elif is_tuning and not logic_id.startswith("TL"):
                            self.logger.warning(f"微调逻辑规则 '{logic_id}' 的ID应以TL开头，LogicBuilder将尝试处理。")
                        elif not is_tuning and not logic_id.startswith("BL"):
                            self.logger.warning(f"BOM逻辑规则 '{logic_id}' 的ID应以BL开头，LogicBuilder将尝试处理。")
                        
                        # 验证条件表达式
                        valid_cond, msg_cond = ExpressionValidator.validate_logic_expression(
                            rule_data_item["selection_expression"],
                            self.config_processor,
                            is_effect_side=False
                        )
                        if not valid_cond:
                            raise ValueError(f"规则 {logic_id} 的条件表达式无效: {msg_cond}")
                        
                        # 验证影响表达式
                        if is_tuning:
                            # 验证微调逻辑
                            valid_eff, msg_eff = ExpressionValidator.validate_tuning_logic(rule_data_item["impact_expression"])
                            if not valid_eff:
                                raise ValueError(f"规则 {logic_id} 的微调逻辑无效: {msg_eff}")
                        else:
                            # 验证BOM逻辑
                            valid_eff, msg_eff = ExpressionValidator.validate_logic_expression(
                                rule_data_item["impact_expression"],
                                self.config_processor,
                                is_effect_side=True
                            )
                            if not valid_eff:
                                raise ValueError(f"规则 {logic_id} 的影响表达式无效: {msg_eff}")
                    
                    # 导入规则 (现在LogicBuilder.import_rules会处理新旧两种格式)
                    self.logic_builder.import_rules(file_path)
                    
                    # 设置规则已加载标志
                    self.rules_loaded = True
                    
                    # 统计规则信息 (从logic_builder获取最新统计)
                    final_rules = self.logic_builder.get_rules()
                    total_rules = len(final_rules)
                    tuning_rules_count = sum(1 for r in final_rules if ExpressionValidator.is_tuning_logic(r.action))
                    enabled_rules_count = sum(1 for r in final_rules if r.status == RuleStatus.ENABLED)
                    testing_rules_count = sum(1 for r in final_rules if r.status == RuleStatus.TESTING)
                    disabled_rules_count = sum(1 for r in final_rules if r.status == RuleStatus.DISABLED)
                    self.logger.info(
                        f"成功导入 {total_rules} 条规则（BOM逻辑: {total_rules - tuning_rules_count}，微调逻辑: {tuning_rules_count}）\n"
                        f"规则状态统计：启用 {enabled_rules_count}，测试 {testing_rules_count}，禁用 {disabled_rules_count}"
                    )
                    
                    # 强制刷新逻辑面板和逻辑关系库
                    if hasattr(self, 'logic_panel'):
                        self.logic_panel._load_existing_rules()
                    
                    # 显示成功消息
                    messagebox.showinfo(
                        language_manager.get_text("success"),
                        language_manager.get_text("import_rules_success")
                    )
                    
                except json.JSONDecodeError:
                    self.logger.error("JSON文件格式错误")
                    messagebox.showerror(
                        language_manager.get_text("error"),
                        language_manager.get_text("import_rules_error") + "\n\nJSON文件格式错误"
                    )
                except ValueError as e:
                    self.logger.error(f"规则验证失败: {str(e)}")
                    messagebox.showerror(
                        language_manager.get_text("error"),
                        language_manager.get_text("import_rules_error") + f"\n\n{str(e)}"
                    )
                except Exception as e:
                    self.logger.error(f"导入BOM逻辑关系失败: {str(e)}", exc_info=True)
                    messagebox.showerror(
                        language_manager.get_text("error"),
                        language_manager.get_text("import_rules_error") + f"\n\n{str(e)}"
                    )
                
        except Exception as e:
            self.logger.error(f"导入BOM逻辑关系失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                language_manager.get_text("import_rules_error")
            )

    def _show_logic_library(self):
        """显示逻辑关系库窗口"""
        window = LogicLibraryWindow(self.root, self.logic_builder)
        window.wait_window()  # 等待窗口关闭
    
    def _show_language_dialog(self):
        """显示语言选择对话框"""
        try:
            dialog = LanguageDialog(self.root)
            selected_lang = dialog.show()
            if selected_lang and selected_lang != language_manager.get_current_language():
                # 设置新的语言
                language_manager.set_language(selected_lang)
                # 强制更新所有面板
                self.refresh_all_texts()
                # 强制更新显示
                self.root.update_idletasks()
        except Exception as e:
            self.logger.error(f"切换语言时出错: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                str(e)
            )
            
    def _update_widget_texts(self, widget):
        """递归更新所有组件的文本
        
        Args:
            widget: 要更新的组件
        """
        try:
            # 更新 Label 文本
            if isinstance(widget, ttk.Label):
                if "Title.TLabel" in str(widget.cget("style")):
                    if widget.winfo_parent() == str(self.main_frame):
                        widget.configure(text=language_manager.get_text("panels_title"))
                    else:
                        # 根据父组件类型设置标题
                        parent = widget.winfo_parent()
                        if "configpanel" in parent.lower():
                            widget.configure(text=language_manager.get_text("config_panel_title"))
                        elif "logicpanel" in parent.lower():
                            widget.configure(text=language_manager.get_text("logic_panel_title"))
                        elif "bompanel" in parent.lower():
                            widget.configure(text=language_manager.get_text("bom_panel_title"))
            
            # 更新 Button 文本
            elif isinstance(widget, ttk.Button):
                current_text = str(widget.cget("text")).lower()
                if "import" in current_text:
                    if "config" in current_text:
                        widget.configure(text=language_manager.get_text("import_config"))
                    elif "bom" in current_text:
                        widget.configure(text=language_manager.get_text("import_bom"))
                elif "refresh" in current_text:
                    widget.configure(text=language_manager.get_text("refresh"))
                elif "clear" in current_text:
                    widget.configure(text=language_manager.get_text("clear"))
                elif "save" in current_text:
                    widget.configure(text=language_manager.get_text("save"))
            
            # 更新 LabelFrame 文本
            elif isinstance(widget, ttk.LabelFrame):
                current_text = str(widget.cget("text")).lower()
                if "tools" in current_text:
                    widget.configure(text=language_manager.get_text("tools"))
                elif "config" in current_text and "tree" in current_text:
                    widget.configure(text=language_manager.get_text("config_tree"))
                elif "bom" in current_text and "tree" in current_text:
                    widget.configure(text=language_manager.get_text("bom_tree"))
                elif "logic" in current_text and "operators" in current_text:
                    widget.configure(text=language_manager.get_text("logic_operators"))
                elif "brackets" in current_text:
                    widget.configure(text=language_manager.get_text("brackets"))
                elif "rule" in current_text and "status" in current_text:
                    widget.configure(text=language_manager.get_text("rule_status"))
                elif "expression" in current_text:
                    widget.configure(text=language_manager.get_text("expression"))
                elif "saved" in current_text and "rules" in current_text:
                    widget.configure(text=language_manager.get_text("saved_rules"))
            
            # 更新 Radiobutton 文本
            elif isinstance(widget, ttk.Radiobutton):
                value = str(widget.cget("value"))
                if value == "enabled":
                    widget.configure(text=language_manager.get_text("enabled"))
                elif value == "testing":
                    widget.configure(text=language_manager.get_text("testing"))
                elif value == "disabled":
                    widget.configure(text=language_manager.get_text("disabled"))
            
            # 递归处理子组件
            for child in widget.winfo_children():
                self._update_widget_texts(child)
                
        except Exception as e:
            self.logger.error(f"更新组件文本时出错: {str(e)}", exc_info=True)
            
    def _refresh_menu_texts(self):
        """刷新菜单文本"""
        # 文件菜单
        self.menubar.entryconfig(0, label=language_manager.get_text("menu_file"))
        self.menubar.entryconfig(1, label=language_manager.get_text("menu_view"))
        self.menubar.entryconfig(2, label=language_manager.get_text("menu_help"))
        
        # 文件菜单项
        self.file_menu.entryconfigure(0, label=language_manager.get_text("import_config"))
        self.file_menu.entryconfigure(1, label=language_manager.get_text("import_bom"))
        self.file_menu.entryconfigure(2, label=language_manager.get_text("import_logic_rules"))
        self.file_menu.entryconfigure(3, label=language_manager.get_text("export_logic_rules"))
        self.file_menu.entryconfigure(5, label=language_manager.get_text("exit"))
        
        # 视图菜单
        self.view_menu.entryconfigure(0, label=language_manager.get_text("logic_library"))
        self.view_menu.entryconfigure(2, label=language_manager.get_text("language"))
        
        # 帮助菜单
        self.help_menu.entryconfigure(0, label=language_manager.get_text("view_log"))
        self.help_menu.entryconfigure(1, label=language_manager.get_text("about"))
        
    def refresh_all_texts(self):
        """刷新所有文本"""
        # 刷新窗口标题
        self.root.title(language_manager.get_text("app_title"))
        
        # 刷新菜单文本
        self._refresh_menu_texts()
        
        # 刷新各个面板的文本
        if hasattr(self, 'config_panel'):
            self.config_panel.refresh_texts()
        if hasattr(self, 'logic_panel'):
            self.logic_panel.refresh_texts()
        if hasattr(self, 'bom_panel'):
            self.bom_panel.refresh_texts()
            
        # 强制更新显示
        self.root.update_idletasks()
        
    def _show_log_viewer(self):
        """显示日志查看器"""
        log_file = Logger.get_current_log_file()
        if log_file:
            try:
                import os
                os.startfile(log_file)  # 在Windows上使用默认文本编辑器打开
            except Exception as e:
                self.logger.error(f"打开日志文件失败: {str(e)}")
                messagebox.showerror(
                    language_manager.get_text("error"),
                    language_manager.get_text("open_log_error")
                )
                
    def _show_about(self):
        """显示关于对话框"""
        # TODO: 实现关于对话框显示
        pass

    def get_logic_panel(self):
        """获取逻辑面板实例
        
        Returns:
            LogicPanel: 逻辑面板实例
        """
        return self.logic_panel if hasattr(self, 'logic_panel') else None

    def _load_last_config(self):
        """加载上次的配置"""
        try:
            # 读取配置文件
            with open('data/app_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查是否有上次的配置文件路径
            config_loaded = False
            if config.get('last_config_path'):
                if messagebox.askyesno(
                    language_manager.get_text("confirm"),
                    language_manager.get_text("load_last_config_confirm")
                ):
                    try:
                        self.config_panel._import_excel(config['last_config_path'])
                        config_loaded = True
                    except Exception as e:
                        self.logger.error(f"加载上次配置文件失败: {str(e)}")
                        messagebox.showerror(
                            language_manager.get_text("error"),
                            language_manager.get_text("load_last_config_error")
                        )
                else:
                    # 用户选择不加载，删除保存的路径
                    config.pop('last_config_path', None)
            
            # 检查是否有上次的BOM文件路径
            if config.get('last_bom_path'):
                if messagebox.askyesno(
                    language_manager.get_text("confirm"),
                    language_manager.get_text("load_last_bom_confirm")
                ):
                    try:
                        self.bom_panel._import_bom(config['last_bom_path'])
                    except Exception as e:
                        self.logger.error(f"加载上次BOM文件失败: {str(e)}")
                        messagebox.showerror(
                            language_manager.get_text("error"),
                            language_manager.get_text("load_last_bom_error")
                        )
                else:
                    # 用户选择不加载，删除保存的路径
                    config.pop('last_bom_path', None)
            
            # 保存更新后的配置
            with open('data/app_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # 检查是否有未导出的逻辑关系
            if os.path.exists(RULES_DATA_FILE):
                try:
                    with open(RULES_DATA_FILE, 'r', encoding='utf-8') as f:
                        rules_data = json.load(f)
                        if not rules_data.get('exported', True) and rules_data.get('rules', []):
                            if messagebox.askyesno(
                                language_manager.get_text("confirm"),
                                language_manager.get_text("load_last_rules_confirm")
                            ):
                                # 设置规则已加载标志
                                self.rules_loaded = True
                                self.logger.info("用户确认加载规则，设置规则已加载标志为True")
                                
                                # 加载规则
                                self.logic_builder.load_from_temp_file()
                                
                                # 强制刷新逻辑面板
                                if hasattr(self, 'logic_panel'):
                                    self.logger.info("开始刷新逻辑面板显示")
                                    self.logic_panel._load_existing_rules()
                                    self.logger.info("逻辑面板显示刷新完成")
                                
                                # 显示成功消息
                                messagebox.showinfo(
                                    language_manager.get_text("success"),
                                    language_manager.get_text("temp_rules_loaded")
                                )
                            else:
                                # 删除规则
                                self.logic_builder.clear_rules()
                                # 重置规则已加载标志
                                self.rules_loaded = False
                                self.logger.info("用户取消加载规则，设置规则已加载标志为False")
                                messagebox.showinfo(
                                    language_manager.get_text("info"),
                                    language_manager.get_text("rules_deleted")
                                )
                except Exception as e:
                    self.logger.error(f"加载临时规则文件失败: {str(e)}")
                    messagebox.showerror(
                        language_manager.get_text("error"),
                        language_manager.get_text("temp_rules_load_error")
                    )
                    
        except Exception as e:
            self.logger.error(f"加载上次配置时出错: {str(e)}")
            messagebox.showerror(
                language_manager.get_text("error"),
                str(e)
            )

    def _save_config_path(self, path: str):
        """保存配置文件路径
        
        Args:
            path: 文件路径
        """
        try:
            # 确保data目录存在
            os.makedirs('data', exist_ok=True)
            
            # 读取现有配置
            config = {}
            if os.path.exists('data/app_config.json'):
                with open('data/app_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新配置
            config['last_config_path'] = path
            
            # 保存配置
            with open('data/app_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            self.logger.info(f"成功保存配置文件路径到app_config.json: {path}")
                
        except Exception as e:
            self.logger.error(f"保存配置文件路径时出错: {str(e)}", exc_info=True)
            
    def _save_bom_path(self, path: str):
        """保存BOM文件路径
        
        Args:
            path: 文件路径
        """
        try:
            # 确保data目录存在
            os.makedirs('data', exist_ok=True)
            
            # 读取现有配置
            config = {}
            if os.path.exists('data/app_config.json'):
                with open('data/app_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新配置
            config['last_bom_path'] = path
            
            # 保存配置
            with open('data/app_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            self.logger.info(f"成功保存BOM文件路径到app_config.json: {path}")
                
        except Exception as e:
            self.logger.error(f"保存BOM文件路径时出错: {str(e)}", exc_info=True)

    def _export_logic_rules(self):
        """导出BOM逻辑关系"""
        try:
            # 打开文件选择对话框
            file_path = filedialog.asksaveasfilename(
                title=language_manager.get_text("select_export_file"),
                defaultextension=".json",
                filetypes=[(language_manager.get_text("json_files"), "*.json")]
            )
            
            if file_path:
                # 获取已分组的规则数据进行导出
                export_data_dict = self.logic_builder.export_rules()
                # export_rules() 内部已经调用了 clear_rules()
                
                # 保存到文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data_dict, f, ensure_ascii=False, indent=2)
                
                # 统计规则信息 (从导出的数据中获取，因为此时内存可能已清空)
                bl_rules_count = len(export_data_dict.get('BL_rules', []))
                tl_rules_count = len(export_data_dict.get('TL_rules', []))
                total_rules = bl_rules_count + tl_rules_count
                
                # 状态统计需要从导出数据中重新计算，如果需要的话
                # enabled_rules = sum(1 for r_list in [bl_rules, tl_rules] for r in r_list if r['status'] == RuleStatus.ENABLED.value)
                # testing_rules = sum(1 for r_list in [bl_rules, tl_rules] for r in r_list if r['status'] == RuleStatus.TESTING.value)
                # disabled_rules = sum(1 for r_list in [bl_rules, tl_rules] for r in r_list if r['status'] == RuleStatus.DISABLED.value)
                # logger.info(
                #     f"成功导出 {total_rules} 条规则（BOM逻辑: {bl_rules_count}，微调逻辑: {tl_rules_count}）\n"
                #     f"规则状态统计：启用 {enabled_rules}，测试 {testing_rules}，禁用 {disabled_rules}"
                # )
                self.logger.info(f"成功导出 {total_rules} 条规则到 {file_path}。")

                # 显示成功消息
                messagebox.showinfo(
                    language_manager.get_text("success"),
                    language_manager.get_text("export_and_clear_success") # 这个消息可能需要更新，因为清空是export_rules做的
                )
                
        except Exception as e:
            self.logger.error(f"导出BOM逻辑关系失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                language_manager.get_text("export_rules_error")
            )