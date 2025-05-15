"""
BOM面板模块

该模块提供了BOM文件的加载和展示功能。
"""
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import os
import re

from utils.language_manager import language_manager
from utils.logger import Logger
from core.bom_processor import BomProcessor
from utils.config_manager import config_manager

class BomPanel(ttk.Frame):
    """BOM面板类"""
    
    def __init__(self, parent, bom_processor: BomProcessor):
        """初始化BOM面板
        
        Args:
            parent: 父窗口
            bom_processor: BOM处理器实例
        """
        super().__init__(parent, style="Panel.TFrame")
        
        # 保存参数
        self.bom_processor = bom_processor
        
        # 获取日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 注册语言变化的回调函数
        language_manager.add_callback(self.refresh_texts)
        
        # 创建界面
        self._create_widgets()
        
    def destroy(self):
        """销毁面板时移除回调函数"""
        language_manager.remove_callback(self.refresh_texts)
        super().destroy()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 创建标题标签
        self.title_label = ttk.Label(
            self,
            text=language_manager.get_text("bom_panel_title"),
            style="Title.TLabel"
        )
        self.title_label.pack(fill=X, pady=(0, 10))
        
        # 创建搜索框架
        self._create_search_frame()
        
        # 创建树状视图框架
        self.tree_frame = ttk.LabelFrame(
            self,
            text=language_manager.get_text("bom_tree"),
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
            text=language_manager.get_text("search_bom_code"),
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
        search_entry.bind("<Return>", lambda event: self._apply_search()) # 绑定回车键

        # 添加清除按钮
        self.clear_button = ttk.Button(
            search_input_frame,
            text=language_manager.get_text("clear"),
            command=self._clear_search,
            style="Main.TButton",
            width=10
        )
        self.clear_button.pack(side=RIGHT, padx=5)
        
    def _clear_search(self):
        """清空搜索并重置树状图"""
        self.search_var.set("")
        self._refresh_tree() # 清除后刷新树

    def _normalize_bom_code(self, code: str) -> str:
        """标准化BOM码格式，提取最后分隔符后的数字部分
        
        Args:
            code: 原始BOM码
            
        Returns:
            str: 标准化后的BOM码数字部分
        """
        # 移除所有空白字符
        code = code.strip()
        
        # 查找最后一个分隔符的位置
        last_sep_index = -1
        if ':' in code:
            last_sep_index = code.rfind(':')
        if '-' in code:
            last_sep_index = max(last_sep_index, code.rfind('-'))
            
        # 如果找到分隔符，提取其后的数字部分
        if last_sep_index != -1:
            number_part = code[last_sep_index + 1:]
            # 如果是纯数字，返回该部分
            if number_part.isdigit():
                return number_part
        
        # 如果没有找到分隔符或分隔符后不是数字，返回原始代码
        return code.upper()

    def _code_matches(self, search_term: str, code: str) -> bool:
        """检查BOM码是否匹配搜索条件
        
        Args:
            search_term: 搜索词
            code: 要匹配的BOM码
            
        Returns:
            bool: 是否匹配
        """
        if not search_term:
            return True
            
        # 标准化搜索词和代码
        normalized_search = self._normalize_bom_code(search_term)
        normalized_code = self._normalize_bom_code(code)
        
        # 如果搜索词是纯数字，则只匹配最后分隔符后的数字部分
        if normalized_search.isdigit():
            return normalized_code.startswith(normalized_search)
        
        # 如果搜索词不是纯数字，则进行普通的包含匹配
        return normalized_search in code.upper()

    def _apply_search(self):
        """应用搜索条件"""
        try:
            search_term = self.search_var.get().strip()
            
            # 如果搜索词为空，直接返回
            if not search_term:
                return
                
            # 获取BOM数据
            bom_data = self.bom_processor.get_bom_data()
            found_match = False
            
            # 遍历所有项目
            for item in bom_data["items"]:
                level = item["level"]
                placeholder = item["placeholder"]
                baugruppe = item["baugruppe"]
                name = item["name"]
                long_text = item["long_text"]
                
                # 检查是否匹配
                if self._code_matches(search_term, baugruppe):
                    found_match = True
                    
                    # 在树状图中查找或创建节点
                    parent = ""
                    parent_node = None
                    
                    # 查找或创建所有父级节点
                    for parent_level in range(1, level):
                        # 查找当前层级的父节点
                        parent_items = self.tree.get_children(parent_node)
                        level_node = None
                        
                        # 在当前层级中查找对应的节点
                        for p_item in parent_items:
                            if self.tree.item(p_item)["text"].startswith(f"[{parent_level}]"):
                                level_node = p_item
                                break
                        
                        # 如果没有找到，创建新的层级节点
                        if not level_node:
                            # 获取该层级的占位符
                            level_placeholder = None
                            for bom_item in bom_data["items"]:
                                if bom_item["level"] == parent_level:
                                    level_placeholder = bom_item["placeholder"]
                                    break
                            
                            if level_placeholder:
                                level_node = self.tree.insert(
                                    parent_node,
                                    "end",
                                    text=f"[{parent_level}] {level_placeholder}",
                                    tags=("level_node",)
                                )
                        
                        parent_node = level_node
                    
                    # 查找或创建当前层级节点
                    current_level_items = self.tree.get_children(parent_node)
                    current_level_node = None
                    
                    for c_item in current_level_items:
                        if self.tree.item(c_item)["text"] == f"[{level}] {placeholder}":
                            current_level_node = c_item
                            break
                    
                    if not current_level_node:
                        current_level_node = self.tree.insert(
                            parent_node,
                            "end",
                            text=f"[{level}] {placeholder}",
                            tags=("level_node",)
                        )
                    
                    # 查找或创建物料节点
                    material_items = self.tree.get_children(current_level_node)
                    material_node = None
                    display_text = f"{baugruppe}\n{name}\n{long_text if long_text else ''}"
                    
                    for m_item in material_items:
                        if self.tree.item(m_item)["text"] == display_text:
                            material_node = m_item
                            break
                    
                    if not material_node:
                        material_node = self.tree.insert(
                            current_level_node,
                            "end",
                            text=display_text,
                            tags=("material",)
                        )
                    
                    # 展开所有父节点
                    parent = current_level_node
                    while parent:
                        self.tree.item(parent, open=True)
                        parent = self.tree.parent(parent)
                    
                    # 选中并滚动到匹配项
                    self.tree.selection_set(material_node)
                    self.tree.see(material_node)
                    break  #  跳出 bom_data["items"] 循环，只处理第一个匹配项
            
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
        tree_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # 创建树状视图
        self.tree = ttk.Treeview(
            tree_frame,
            selectmode="browse",
            style="Main.Treeview",
            show="tree"  # 只显示树形结构，不显示列头
        )
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # 配置样式
        style = ttk.Style()
        style.configure(
            "Main.Treeview",
            font=("Microsoft YaHei", 11),  # 调整字体大小
            rowheight=60  # 增加行高以适应三行显示
        )
        
        # 添加垂直滚动条
        vsb = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview
        )
        vsb.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=vsb.set)
        
        # 添加水平滚动条
        hsb = ttk.Scrollbar(
            parent,
            orient="horizontal",
            command=self.tree.xview
        )
        hsb.pack(fill=X, pady=(0, 5))
        self.tree.configure(xscrollcommand=hsb.set)
        
        # 绑定事件
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-1>", self._on_single_click)
        
        # 配置标签样式 - 层级节点加粗，物料节点不加粗
        self.tree.tag_configure("level_1", font=("Microsoft YaHei", 12, "bold"))
        self.tree.tag_configure("level_node", font=("Microsoft YaHei", 11, "bold"))
        self.tree.tag_configure("material", font=("Microsoft YaHei", 11))
        
    def _refresh_tree(self):
        """刷新树状视图"""
        try:
            # 清空树状视图
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # 获取BOM数据
            bom_data = self.bom_processor.get_bom_data()
            
            # 按Excel顺序处理所有项目
            self.logger.info("开始刷新树状图")
            
            # 用于跟踪每个层级的最后一个节点
            level_last_nodes = {}  # {level: node_id}
            # 用于跟踪已创建的层级+占位符节点
            level_placeholder_nodes = {}  # {(parent_id, level, placeholder): node_id}
            
            # 遍历所有项目（已按Excel顺序排列）
            for item in bom_data["items"]:
                level = item["level"]
                placeholder = item["placeholder"]
                baugruppe = item["baugruppe"]
                name = item["name"]
                long_text = item["long_text"]
                
                # 确定父节点
                parent = ""  # 默认为根节点
                for parent_level in range(level - 1, 0, -1):
                    if parent_level in level_last_nodes:
                        parent = level_last_nodes[parent_level]
                        break
                
                # 检查是否需要创建层级+占位符节点
                level_key = (parent, level, placeholder)
                if level_key not in level_placeholder_nodes:
                    # 创建新的层级+占位符节点
                    level_node = self.tree.insert(
                        parent,
                        "end",
                        text=f"[{level}] {placeholder}",
                        tags=("level_node",)
                    )
                    level_placeholder_nodes[level_key] = level_node
                
                # 在层级+占位符节点下创建物料节点
                display_text = f"{baugruppe}\n{name}\n{long_text if long_text else ''}"
                node = self.tree.insert(
                    level_placeholder_nodes[level_key],
                    "end",
                    text=display_text,
                    tags=("material",)
                )
                
                # 更新层级跟踪
                level_last_nodes[level] = level_placeholder_nodes[level_key]
                
                # 清除所有更高层级的最后节点记录
                higher_levels = [l for l in level_last_nodes.keys() if l > level]
                for l in higher_levels:
                    level_last_nodes.pop(l)
            
            self.logger.info("树状图刷新完成")
            
        except Exception as e:
            self.logger.error(f"刷新树状图失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error"),
                language_manager.get_text("refresh_tree_error")
            )
            
    def _on_single_click(self, event):
        """处理单击事件"""
        # 获取点击的项目
        item = self.tree.identify("item", event.x, event.y)
        if item:
            # 选中项目
            self.tree.selection_set(item)
            # 如果项是关闭的，则打开它
            if not self.tree.item(item, "open"):
                self.tree.item(item, open=True)
            # 如果项是打开的，则关闭它
            else:
                self.tree.item(item, open=False)
            
    def _on_double_click(self, event):
        """处理双击事件"""
        try:
            # 获取选中的项
            item = self.tree.identify("item", event.x, event.y)
            if not item:
                return
                
            # 获取项的文本
            text = self.tree.item(item, "text")
            self.logger.debug(f"BomPanel: 选中项文本: {text}")
            
            # 如果是层级节点（以[开头），不处理
            if text.startswith("["):
                return
                
            # 提取Baugruppe码 - 从第一行获取
            baugruppe = text.split("\n")[0].strip()
            self.logger.debug(f"BomPanel: 提取到Baugruppe: {baugruppe}")
            
            # 获取层级节点的文本
            level_node = self.tree.parent(item)
            if level_node:
                level_text = self.tree.item(level_node, "text")
                if level_text.startswith("["):  # 是层级节点
                    # 提取占位符 - 格式为 "[层级] 占位符"
                    placeholder = level_text.split(" ", 1)[1].strip()
                    self.logger.debug(f"BomPanel: 提取到占位符: {placeholder}")
                    # 构建完整的BOM码
                    bom_code = f"{placeholder}-{baugruppe}"
                    self.logger.debug(f"BomPanel: 构建的BOM码: {bom_code}")
                    # 插入BOM码
                    self.insert_code(bom_code)
                    self.logger.info(f"BomPanel: 成功插入BOM码: {bom_code}")
                    return
            
            # 如果没有找到层级节点，直接使用Baugruppe
            self.insert_code(baugruppe)
            self.logger.info(f"BomPanel: 成功插入Baugruppe: {baugruppe}")
                
        except Exception as e:
            self.logger.error(f"BomPanel: 双击处理出错: {str(e)}", exc_info=True)

    def _import_bom(self, file_path=None):
        """导入BOM文件
        
        Args:
            file_path: 文件路径,如果为None则弹出文件选择对话框
        """
        try:
            if file_path is None:
                # 显示文件选择对话框
                file_path = filedialog.askopenfilename(
                    title=language_manager.get_text("select_bom_file"),
                    filetypes=[
                        (language_manager.get_text("excel_files"), "*.xlsx *.xlsm"),
                        (language_manager.get_text("all_files"), "*.*")
                    ]
                )
                if file_path:
                    self.logger.info(f"用户选择了新的BOM文件: {file_path}")
                
            if file_path:
                # 导入BOM文件
                self.bom_processor.import_bom(file_path)
                self.logger.info(f"成功导入BOM文件: {file_path}")
                
                # 刷新树状视图
                self._refresh_tree()
                
                # 保存文件路径到app_config.json
                if hasattr(self.master, 'main_window'):
                    self.master.main_window._save_bom_path(file_path)
                    self.logger.info(f"已保存BOM文件路径到app_config.json: {file_path}")
                else:
                    # 尝试从根窗口获取MainWindow实例
                    root = self.winfo_toplevel()
                    if hasattr(root, 'main_window'):
                        root.main_window._save_bom_path(file_path)
                        self.logger.info(f"已保存BOM文件路径到app_config.json: {file_path}")
                    else:
                        self.logger.warning("无法保存BOM文件路径：未找到MainWindow实例")
                
                # 显示成功消息
                messagebox.showinfo(
                    language_manager.get_text("success_title"),
                    language_manager.get_text("import_bom_success")
                )
                
        except Exception as e:
            self.logger.error(f"导入BOM文件失败: {str(e)}", exc_info=True)
            messagebox.showerror(
                language_manager.get_text("error_title"),
                language_manager.get_text("bom_import_error")
            )
            
    def refresh_texts(self):
        """刷新界面文本"""
        # 更新标题
        self.title_label.configure(
            text=language_manager.get_text("bom_panel_title")
        )
        
        # 更新搜索框架标题
        self.search_frame.configure(
            text=language_manager.get_text("search_bom_code")
        )
        
        # 更新清除按钮文本
        self.clear_button.configure(
            text=language_manager.get_text("clear")
        )
        
        # 更新树状视图框架标题
        self.tree_frame.configure(
            text=language_manager.get_text("bom_tree")
        )
        
    def insert_code(self, code: str):
        """插入代码到逻辑编辑区
        
        Args:
            code: 要插入的代码
        """
        try:
            # 获取主窗口
            root = self.winfo_toplevel()
            self.logger.debug("BomPanel: 获取根窗口成功")
            
            # 获取MainWindow实例
            if hasattr(root, 'main_window'):
                main_window = root.main_window
                self.logger.debug("BomPanel: 获取MainWindow实例成功")
                
                # 获取逻辑面板
                logic_panel = main_window.get_logic_panel()
                if logic_panel:
                    self.logger.debug("BomPanel: 找到逻辑面板")
                    logic_panel.insert_code(code)
                    self.logger.info(f"BomPanel: 成功发送代码到逻辑面板: {code}")
                else:
                    self.logger.warning("BomPanel: 未找到逻辑面板")
            else:
                self.logger.warning("BomPanel: 未找到MainWindow实例")
                
        except Exception as e:
            self.logger.error(f"BomPanel: 插入代码时出错: {str(e)}", exc_info=True) 