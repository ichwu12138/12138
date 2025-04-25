"""
BOM处理器模块

该模块专门用于处理BOM Excel文件的导入和数据管理。
"""
import pandas as pd
from typing import Dict, List, Optional, Any
import re
from utils.logger import Logger

class BomProcessor:
    """BOM处理器类"""
    
    def __init__(self):
        """初始化BOM处理器"""
        # 获取当前类的日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 存储BOM数据
        self.bom_data: Dict[str, Dict[str, Any]] = {}  # 主项ID到数据的映射
        
    def import_bom(self, file_path: str) -> None:
        """导入BOM Excel文件
        
        Args:
            file_path: Excel文件路径
        """
        try:
            self.logger.info(f"开始导入BOM文件: {file_path}")
            
            # 清空现有数据
            self.clear()
            self.logger.info("已清空现有数据")
            
            # 读取Excel文件
            self.logger.info("正在读取Excel文件...")
            xl = pd.ExcelFile(file_path)
            self.logger.info(f"成功打开Excel文件，包含以下工作表: {xl.sheet_names}")
            
            # 检查是否存在 MAX-gruppe 工作表
            if "MAX-gruppe" not in xl.sheet_names:
                self.logger.error("错误：未找到 MAX-gruppe 工作表")
                raise ValueError("未找到 MAX-gruppe 工作表")
            
            # 读取 MAX-gruppe 工作表
            self.logger.info("正在读取 MAX-gruppe 工作表...")
            df = pd.read_excel(file_path, sheet_name="MAX-gruppe")
            self.logger.info(f"成功读取工作表，共 {len(df)} 行数据")
            
            # 检查必需的列是否存在
            required_columns = ["层级", "占位符", "Baugruppe", "Beschreibung", "Langtext / long text"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"错误：缺少必需的列: {', '.join(missing_columns)}")
                raise ValueError(f"缺少必需的列: {', '.join(missing_columns)}")
            
            self.logger.info("所有必需列均存在，开始处理数据...")
            
            # 处理数据
            self._process_max_gruppe(df)
            
            self.logger.info(f"BOM文件导入成功，共处理 {len(self.bom_data)} 个一级节点")
            
        except Exception as e:
            self.logger.error(f"导入BOM文件失败: {str(e)}", exc_info=True)
            raise ImportError(f"导入BOM文件失败: {str(e)}")
    
    def _process_max_gruppe(self, df: pd.DataFrame) -> None:
        """处理 MAX-gruppe 工作表数据
        
        Args:
            df: MAX-gruppe 工作表的数据帧
        """
        try:
            # 先过滤掉层级为空的行
            df = df.dropna(subset=["层级"])
            self.logger.info(f"过滤空层级后剩余 {len(df)} 行数据")
            
            # 将层级转换为整数
            df["层级"] = df["层级"].astype(float).astype(int)
            
            # 按原始顺序处理数据
            self.logger.info("\n开始处理数据...")
            processed_count = 0
            
            # 用于跟踪当前处理状态
            current_level = None
            current_placeholder = None
            current_parent = None
            parent_stack = []  # [(level, baugruppe, placeholder), ...]
            
            # 直接按DataFrame的顺序处理每一行
            for idx, row in df.iterrows():
                try:
                    level = int(row["层级"])
                    baugruppe = str(row["Baugruppe"]).strip()
                    placeholder = str(row["占位符"]).strip() if not pd.isna(row["占位符"]) else ""
                    description = str(row["Beschreibung"]).strip()
                    long_text = str(row["Langtext / long text"]).strip() if not pd.isna(row["Langtext / long text"]) else ""
                    
                    # 跳过空的Baugruppe
                    if pd.isna(baugruppe):
                        self.logger.warning(f"跳过第 {idx+1} 行：Baugruppe为空")
                        continue
                    
                    # 构建BOM码
                    bom_code = f"{placeholder}-{baugruppe}" if placeholder else baugruppe
                    
                    # 创建节点数据
                    item_data = {
                        "name": description,
                        "level": level,
                        "placeholder": placeholder,
                        "long_text": long_text,
                        "sub_items": {},
                        "bom_code": bom_code,
                        "baugruppe": baugruppe,
                        "original_index": idx
                    }
                    
                    # 处理层级关系
                    if level == 1:
                        # 一级节点直接添加到根
                        self.bom_data[baugruppe] = item_data
                        current_level = level
                        current_placeholder = placeholder
                        current_parent = baugruppe
                        parent_stack = [(level, baugruppe, placeholder)]
                    else:
                        # 如果层级发生变化或在同一层级占位符发生变化
                        if level != current_level or placeholder != current_placeholder:
                            # 调整父节点栈
                            while parent_stack and parent_stack[-1][0] >= level:
                                parent_stack.pop()
                        
                        # 获取父节点
                        if parent_stack:
                            parent_id = parent_stack[-1][1]
                            parent_placeholder = parent_stack[-1][2]
                            parent_data = self._find_item_by_id(parent_id)
                            if parent_data:
                                # 确保子节点继承父节点的placeholder（如果子节点没有自己的placeholder）
                                if not placeholder and parent_placeholder:
                                    placeholder = parent_placeholder
                                    item_data["placeholder"] = placeholder
                                parent_data["sub_items"][baugruppe] = item_data
                            else:
                                # 创建为根节点
                                self.bom_data[baugruppe] = item_data
                        else:
                            # 如果没有合适的父节点，创建为根节点
                            self.bom_data[baugruppe] = item_data
                        
                        # 更新当前状态
                        current_level = level
                        current_placeholder = placeholder
                        current_parent = baugruppe
                        parent_stack.append((level, baugruppe, placeholder))
                    
                    processed_count += 1
                    
                except Exception as e:
                    self.logger.error(f"处理第 {idx+1} 行数据时出错: {str(e)}", exc_info=True)
                    continue
            
            # 记录最终的数据统计
            self.logger.info(f"\n数据处理完成，成功处理 {processed_count} 行数据")
            self.logger.info(f"最终数据包含 {len(self.bom_data)} 个一级节点")
            
        except Exception as e:
            self.logger.error(f"处理 MAX-gruppe 工作表错误: {str(e)}", exc_info=True)
            raise
            
    def _verify_data_integrity(self):
        """验证数据完整性"""
        try:
            self.logger.info("\n开始验证数据完整性...")
            
            # 收集所有节点的信息
            all_nodes = {}
            all_placeholders = set()
            
            def collect_nodes(items, level=1):
                for item_id, item_data in items.items():
                    all_nodes[item_id] = item_data
                    if item_data.get("placeholder"):
                        all_placeholders.add(item_data["placeholder"])
                    if item_data.get("sub_items"):
                        collect_nodes(item_data["sub_items"], level + 1)
            
            collect_nodes(self.bom_data)
            
            self.logger.info(f"总节点数: {len(all_nodes)}")
            self.logger.info(f"发现的所有占位符: {sorted(all_placeholders)}")
            
            # 检查每个占位符的节点
            for placeholder in sorted(all_placeholders):
                nodes_with_placeholder = [
                    node_id for node_id, data in all_nodes.items()
                    if data.get("placeholder") == placeholder
                ]
                self.logger.info(f"占位符 {placeholder} 的节点: {len(nodes_with_placeholder)} 个")
                for node_id in nodes_with_placeholder:
                    self.logger.debug(f"  节点 {node_id}: {all_nodes[node_id].get('name', '')}")
            
        except Exception as e:
            self.logger.error(f"验证数据完整性时出错: {str(e)}", exc_info=True)
    
    def _find_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找项目数据
        
        Args:
            item_id: 项目ID
            
        Returns:
            Optional[Dict[str, Any]]: 项目数据，如果不存在则返回None
        """
        # 先在一级节点中查找
        if item_id in self.bom_data:
            return self.bom_data[item_id]
        
        # 递归查找子节点
        for main_item in self.bom_data.values():
            result = self._find_item_in_subitems(item_id, main_item["sub_items"])
            if result:
                return result
        
        return None
    
    def _find_item_in_subitems(self, item_id: str, sub_items: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """在子项中递归查找项目数据
        
        Args:
            item_id: 项目ID
            sub_items: 子项字典
            
        Returns:
            Optional[Dict[str, Any]]: 项目数据，如果不存在则返回None
        """
        # 直接在当前层级查找
        if item_id in sub_items:
            return sub_items[item_id]
        
        # 递归查找下一层级
        for sub_item in sub_items.values():
            result = self._find_item_in_subitems(item_id, sub_item["sub_items"])
            if result:
                return result
        
        return None
    
    def get_bom_data(self) -> Dict[str, Dict[str, Any]]:
        """获取BOM数据
        
        Returns:
            Dict[str, Dict[str, Any]]: BOM数据字典
        """
        return self.bom_data
    
    def get_item_data(self, item_id: str) -> Optional[Dict[str, Any]]:
        """获取指定项目的数据
        
        Args:
            item_id: 项目ID
            
        Returns:
            Optional[Dict[str, Any]]: 项目数据，如果不存在则返回None
        """
        return self._find_item_by_id(item_id)
    
    def get_sub_items(self, item_id: str) -> Dict[str, Dict[str, Any]]:
        """获取指定项目的所有子项
        
        Args:
            item_id: 项目ID
            
        Returns:
            Dict[str, Dict[str, Any]]: 子项字典，如果项目不存在则返回空字典
        """
        item_data = self._find_item_by_id(item_id)
        return item_data.get("sub_items", {}) if item_data else {}
    
    def get_item_name(self, item_id: str) -> str:
        """获取项目名称
        
        Args:
            item_id: 项目ID
            
        Returns:
            str: 项目名称，如果不存在则返回项目ID
        """
        item_data = self._find_item_by_id(item_id)
        return item_data.get("name", item_id) if item_data else item_id
    
    def get_sub_item_name(self, item_id: str, sub_id: str) -> str:
        """获取子项名称
        
        Args:
            item_id: 项目ID
            sub_id: 子项ID
            
        Returns:
            str: 子项名称，如果不存在则返回子项ID
        """
        sub_items = self.get_sub_items(item_id)
        sub_data = sub_items.get(sub_id)
        return sub_data.get("name", sub_id) if sub_data else sub_id
        
    def get_sub_item_attributes(self, item_id: str, sub_id: str) -> Dict[str, str]:
        """获取子项的属性
        
        Args:
            item_id: 项目ID
            sub_id: 子项ID
            
        Returns:
            Dict[str, str]: 属性字典，如果不存在则返回空字典
        """
        sub_items = self.get_sub_items(item_id)
        sub_data = sub_items.get(sub_id)
        return sub_data.get("attributes", {}) if sub_data else {}
        
    def clear(self) -> None:
        """清空数据"""
        self.bom_data.clear()
    
    def get_all_bom_codes(self) -> List[str]:
        """获取所有有效的BOM码
        
        Returns:
            List[str]: BOM码列表，格式为 "占位符-Baugruppe"
        """
        bom_codes = []
        
        def collect_bom_codes(items: Dict[str, Dict[str, Any]]):
            for item_data in items.values():
                # 使用保存的BOM码
                if "bom_code" in item_data:
                    bom_codes.append(item_data["bom_code"])
                
                # 递归处理子项
                if "sub_items" in item_data:
                    collect_bom_codes(item_data["sub_items"])
        
        # 从根节点开始收集
        collect_bom_codes(self.bom_data)
        return bom_codes
        
    def is_valid_bom_code(self, code: str) -> bool:
        """检查是否为有效的BOM码
        
        Args:
            code: 要检查的代码
            
        Returns:
            bool: 是否为有效的BOM码
        """
        return code in self.get_all_bom_codes() 