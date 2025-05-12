"""
配置面板模块

该模块提供了配置选项的导入、编辑和管理功能。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import os

from utils.language_manager import language_manager
from utils.logger import Logger
from core.config_processor import ConfigProcessor
from utils.config_manager import config_manager

class ConfigPanel(ttk.Frame):
    """配置面板类"""
    
    def __init__(self, master, config_processor: ConfigProcessor):
        """初始化配置面板
        
        Args:
            master: 父窗口
            config_processor: 配置处理器实例
        """
        super().__init__(master)
        
        # 保存参数
        self.config_processor = config_processor
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 创建界面
        self._create_widgets()
        
    def _import_excel(self, file_path=None):
        """导入Excel文件
        
        Args:
            file_path: 文件路径,如果为None则弹出文件选择对话框
        """
        try:
            if file_path is None:
                # 显示文件选择对话框
                file_path = filedialog.askopenfilename(
                    title=language_manager.get_text("select_config_file"),
                    filetypes=[
                        (language_manager.get_text("excel_files"), "*.xlsx *.xlsm"),
                        (language_manager.get_text("all_files"), "*.*")
                    ]
                )
                if file_path:
                    self.logger.info(f"用户选择了新的配置文件: {file_path}")
                
            if file_path:
                # 导入Excel文件
                self.config_processor.import_excel(file_path)
                self.logger.info(f"成功导入配置文件: {file_path}")
                
                # 更新显示
                self._update_display()
                
                # 保存文件路径到app_config.json
                if hasattr(self.master, 'main_window'):
                    self.master.main_window._save_config_path(file_path)
                    self.logger.info(f"已保存配置文件路径到app_config.json: {file_path}")
                else:
                    # 尝试从根窗口获取MainWindow实例
                    root = self.winfo_toplevel()
                    if hasattr(root, 'main_window'):
                        root.main_window._save_config_path(file_path)
                        self.logger.info(f"已保存配置文件路径到app_config.json: {file_path}")
                    else:
                        self.logger.warning("无法保存配置文件路径：未找到MainWindow实例")
                
                # 显示成功消息
                messagebox.showinfo(
                    language_manager.get_text("success_title"),
                    language_manager.get_text("import_config_success")
                )
                
        except Exception as e:
            self.logger.error(f"导入配置文件失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error_title"),
                language_manager.get_text("import_config_error")
            )

    def _update_display(self):
        """更新显示"""
        try:
            # 刷新树状视图
            self._refresh_tree()
        except Exception as e:
            self.logger.error(f"更新显示失败: {str(e)}")
            messagebox.showerror(
                language_manager.get_text("error"),
                language_manager.get_text("update_display_error")
            )

    def _create_widgets(self):
        """创建界面组件"""
        # 创建标题标签
        self.title_label = ttk.Label(
            self,
            text=language_manager.get_text("config_panel_title"),
            style="Title.TLabel"
        )
        self.title_label.pack(fill=X, pady=(0, 10))
        
        # 创建搜索框架
        self._create_search_frame()
        
        # 创建树状视图框架
        self.tree_frame = ttk.LabelFrame(
            self,
            text=language_manager.get_text("config_tree"),
            style="Main.TLabelframe"
        )
        self.tree_frame.pack(fill=BOTH, expand=YES, padx=5)
        
        # 创建树状视图
        self._create_tree(self.tree_frame)
        
    def _create_search_frame(self):
        """创建搜索框架"""
        # 创建搜索框架
        self.search_frame = ttk.LabelFrame(
            self,
            text=language_manager.get_text("search_feature_or_k"),
            padding=5,
            style="Main.TLabelframe"
        )
        self.search_frame.pack(fill=X, pady=(0, 10), padx=5)

        # 创建搜索输入框
        search_input_frame = ttk.Frame(self.search_frame)
        search_input_frame.pack(fill=X, pady=2)
        
        # 搜索输入框
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            search_input_frame,
            textvariable=self.search_var,
            font=("Microsoft YaHei", 11),
            width=40
        )
        search_entry.pack(side=LEFT, fill=X, expand=True)
        
        # 添加清除按钮
        clear_button = ttk.Button(
            search_input_frame,
            text=language_manager.get_text("clear"),
            command=self._clear_search,
            style="Main.TButton",
            width=10
        )
        clear_button.pack(side=RIGHT, padx=5)
        
        # 绑定搜索事件
        self.search_var.trace_add("write", self._on_search_changed)

    def _delayed_search(self):
        """延迟搜索以避免过于频繁的更新"""
        if hasattr(self, '_search_after_id'):
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self._apply_search)

    def _on_search_changed(self, *args):
        """搜索内容变化事件处理"""
        self._delayed_search()

    def _clear_search(self):
        """清空搜索"""
        self.search_var.set("")

    def _normalize_code(self, code: str) -> str:
        """标准化代码格式，移除分隔符
        
        Args:
            code: 原始代码
            
        Returns:
            str: 标准化后的代码
        """
        # 移除所有的分隔符（- 和 _）
        normalized = code.replace("-", "").replace("_", "").upper()
        return normalized

    def _code_matches(self, search_term: str, code: str, name: str) -> bool:
        """检查代码是否匹配搜索条件
        
        Args:
            search_term: 搜索词
            code: 要匹配的代码
            name: 代码的名称
            
        Returns:
            bool: 是否匹配
        """
        if not search_term:
            return True
            
        # 标准化搜索词和代码
        normalized_search = self._normalize_code(search_term)
        normalized_code = self._normalize_code(code)
        
        # 如果搜索词以K开头（不区分大小写），则按K码格式处理
        if normalized_search.startswith('K'):
            # 如果代码是K码，则进行标准化比较
            if code.startswith('K-'):
                return normalized_code.startswith(normalized_search)
            return False
            
        # 如果搜索词以H或HBG开头（不区分大小写），则按HBG码格式处理
        if normalized_search.startswith('H') or normalized_search.startswith('HBG'):
            # 如果代码是HBG码，则进行标准化比较
            if code.startswith('HBG_'):
                return normalized_code.startswith(normalized_search)
            return False
            
        # 其他情况：搜索词可以匹配代码的任何部分或名称
        return (normalized_search in normalized_code or 
                normalized_search in name.upper())

    def _apply_search(self):
        """应用搜索条件"""
        try:
            search_term = self.search_var.get().strip()
            
            # 如果搜索词为空，直接返回
            if not search_term:
                return
                
            # 获取所有模块
            modules = self.config_processor.get_modules()
            found_match = False
            
            # 遍历所有节点
            for module_id, f_codes in modules.items():
                module_node = None
                
                # 检查每个特征码
                for f_code in f_codes:
                    f_node = None
                    f_code_name = self.config_processor.get_name(f_code)
                    
                    # 检查特征码是否匹配
                    f_code_matches = self._code_matches(search_term, f_code, f_code_name)
                    
                    # 获取特征值
                    k_codes = self.config_processor.get_k_codes(f_code)
                    k_code_matches = []
                    
                    # 检查特征值是否匹配
                    for k_code in k_codes:
                        k_code_name = self.config_processor.get_name(k_code)
                        if self._code_matches(search_term, k_code, k_code_name):
                            k_code_matches.append(k_code)
                    
                    # 如果找到匹配项
                    if f_code_matches or k_code_matches:
                        found_match = True
                        
                        # 在树状图中查找或创建节点
                        module_items = self.tree.get_children()
                        module_node = None
                        
                        # 查找模块节点
                        for item in module_items:
                            if self.tree.item(item)["text"] == module_id:
                                module_node = item
                                break
                        
                        # 如果模块节点不存在，创建它
                        if not module_node:
                            module_node = self.tree.insert(
                                "",
                                "end",
                                text=module_id,
                                tags=("module",)
                            )
                        
                        # 查找特征码节点
                        f_node = None
                        f_items = self.tree.get_children(module_node)
                        for item in f_items:
                            if self.tree.item(item)["text"] == f"{f_code} {f_code_name}":
                                f_node = item
                                break
                        
                        # 如果特征码节点不存在，创建它
                        if not f_node:
                            f_node = self.tree.insert(
                                module_node,
                                "end",
                                text=f"{f_code} {f_code_name}",
                                tags=("f_code",)
                            )
                        
                        # 展开找到的节点
                        self.tree.item(module_node, open=True)
                        self.tree.item(f_node, open=True)
                        
                        # 如果是特征码匹配，选中特征码节点
                        if f_code_matches:
                            self.tree.selection_set(f_node)
                            self.tree.see(f_node)
                        
                        # 如果是特征值匹配，选中对应的特征值节点
                        for k_code in k_code_matches:
                            k_code_name = self.config_processor.get_name(k_code)
                            # 查找或创建特征值节点
                            k_node = None
                            k_items = self.tree.get_children(f_node)
                            for item in k_items:
                                if self.tree.item(item)["text"] == f"{k_code} {k_code_name}":
                                    k_node = item
                                    break
                            
                            if not k_node:
                                k_node = self.tree.insert(
                                    f_node,
                                    "end",
                                    text=f"{k_code} {k_code_name}",
                                    tags=("k_code",)
                                )
                            
                            # 选中并滚动到特征值节点
                            self.tree.selection_set(k_node)
                            self.tree.see(k_node)
            
            # 如果没有找到匹配项，显示提示信息
            if not found_match:
                messagebox.showinfo(
                    language_manager.get_text("info"),
                    language_manager.get_text("code_not_found")
                )
                
        except Exception as e:
            self.logger.error(f"应用搜索失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                language_manager.get_text("search_error")
            )

    def _create_tree(self, parent):
        """创建树状视图"""
        # 创建树状视图框架
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=YES, padx=4, pady=4)
        
        # 配置样式
        style = ttk.Style()
        style.configure(
            "Main.Treeview",
            font=("Microsoft YaHei", 11),  # 调整字体大小
            rowheight=60  # 调整行高以适应三行显示
        )
        
        # 创建树状视图
        self.tree = ttk.Treeview(
            tree_frame,
            selectmode="browse",
            style="Main.Treeview",
            show="tree"  # 只显示树形结构，不显示列头
        )
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # 配置标签样式
        self.tree.tag_configure("module", font=("Microsoft YaHei", 11, "bold"))
        self.tree.tag_configure("f_code", font=("Microsoft YaHei", 11))
        self.tree.tag_configure("k_code", font=("Microsoft YaHei", 11))
        
        # 添加垂直滚动条
        vsb = ttk.Scrollbar(
            tree_frame,
            orient=VERTICAL,
            command=self.tree.yview
        )
        vsb.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=vsb.set)
        
        # 添加水平滚动条
        hsb = ttk.Scrollbar(
            parent,
            orient=HORIZONTAL,
            command=self.tree.xview
        )
        hsb.pack(fill=X, pady=(0, 5))
        self.tree.configure(xscrollcommand=hsb.set)
        
        # 绑定事件 - 只保留必要的点击事件
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-1>", self._on_single_click)
        
    def _refresh_tree(self):
        """刷新树状视图"""
        try:
            # 清空树状视图
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # 获取所有模块
            modules = self.config_processor.get_modules()
            
            # 添加模块节点
            for module_id, f_codes in modules.items():
                module_node = self.tree.insert(
                    "",
                    "end",
                    text=module_id,
                    tags=("module",)
                )
                
                # 添加特征码节点
                for f_code in f_codes:
                    f_node = self.tree.insert(
                        module_node,
                        "end",
                        text=f"{f_code} {self.config_processor.get_name(f_code)}",
                        tags=("f_code",)
                    )
                    
                    # 添加特征值节点
                    for k_code in self.config_processor.get_k_codes(f_code):
                        self.tree.insert(
                            f_node,
                            "end",
                            text=f"{k_code} {self.config_processor.get_name(k_code)}",
                            tags=("k_code",)
                        )
            
            # 配置标签样式
            self.tree.tag_configure("module", font=("Microsoft YaHei", 11, "bold"))  # 调整字体大小
            self.tree.tag_configure("f_code", font=("Microsoft YaHei", 11))  # 调整字体大小
            self.tree.tag_configure("k_code", font=("Microsoft YaHei", 11))  # 调整字体大小
                        
        except Exception as e:
            from utils.message_utils_tk import show_error
            show_error("refresh_tree_error", error=str(e))
            
    def _on_right_click(self, event):
        """右键事件处理"""
        # 获取点击位置的项
        item = self.tree.identify_row(event.y)
        if item:
            # 选中该项
            self.tree.selection_set(item)
            
            # 创建右键菜单
            menu = tk.Menu(self, tearoff=0)
            menu.configure(font=("Microsoft YaHei", 16))  # 使用统一的菜单字体大小
            
            # 获取项的文本
            text = self.tree.item(item, "text")
            code = text.split()[0]
            
            # 如果是特征码或特征值，添加复制选项
            if code.startswith("HBG_") or code.startswith("K-"):
                menu.add_command(
                    label=language_manager.get_text("copy_code"),
                    command=lambda: self.insert_code(code)
                )
                
            # 显示菜单
            menu.post(event.x_root, event.y_root)
            
    def _on_single_click(self, event):
        """单击事件处理"""
        # 获取点击位置的项
        item = self.tree.identify_row(event.y)
        if item:
            # 如果项是关闭的，则打开它
            if not self.tree.item(item, "open"):
                self.tree.item(item, open=True)
            # 如果项是打开的，则关闭它
            else:
                self.tree.item(item, open=False)
            
    def _on_double_click(self, event):
        """双击事件处理"""
        try:
            # 获取选中的项
            item = self.tree.selection()[0]
            self.logger.debug(f"ConfigPanel: 双击选中项 ID: {item}")
            
            # 获取项的文本
            text = self.tree.item(item, "text")
            self.logger.debug(f"ConfigPanel: 选中项文本: {text}")
            
            # 提取特征值
            code = text.split()[0]
            self.logger.debug(f"ConfigPanel: 提取的代码: {code}")
            
            # 如果是特征值，发送到逻辑编辑区
            if code.startswith("K-"):
                self.logger.info(f"ConfigPanel: 准备插入特征值: {code}")
                self.insert_code(code)
            else:
                self.logger.debug(f"ConfigPanel: 忽略非特征值: {code}")
                
        except Exception as e:
            self.logger.error(f"ConfigPanel: 双击处理出错: {str(e)}", exc_info=True)

    def insert_code(self, code: str):
        """插入代码到逻辑编辑区
        
        Args:
            code: 要插入的代码
        """
        try:
            # 获取主窗口
            root = self.winfo_toplevel()
            self.logger.debug("ConfigPanel: 获取根窗口成功")
            
            # 获取MainWindow实例
            if hasattr(root, 'main_window'):
                main_window = root.main_window
                self.logger.debug("ConfigPanel: 获取MainWindow实例成功")
                
                # 获取逻辑面板
                logic_panel = main_window.get_logic_panel()
                if logic_panel:
                    self.logger.debug("ConfigPanel: 找到逻辑面板")
                    logic_panel.insert_code(code)
                    self.logger.info(f"ConfigPanel: 成功发送代码到逻辑面板: {code}")
                else:
                    self.logger.warning("ConfigPanel: 未找到逻辑面板")
            else:
                self.logger.warning("ConfigPanel: 未找到MainWindow实例")
                
        except Exception as e:
            self.logger.error(f"ConfigPanel: 插入代码时出错: {str(e)}", exc_info=True)
            
    def refresh_texts(self):
        """刷新所有文本"""
        try:
            # 更新标题
            self.title_label.configure(text=language_manager.get_text("config_panel_title"))
            
            # 更新搜索框架标题
            self.search_frame.configure(text=language_manager.get_text("search_feature_or_k"))
            
            # 更新配置树标题
            self.tree_frame.configure(text=language_manager.get_text("config_tree"))
                
        except Exception as e:
            self.logger.error(f"刷新文本失败: {str(e)}", exc_info=True) 