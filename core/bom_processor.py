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
        
        # 存储BOM数据 - 新的数据结构
        self.bom_data = {
            "items": [],  # 按Excel顺序存储所有项目
            "level_placeholders": {},  # 用于跟踪层级和占位符组合
            "hierarchy": {}  # 保持层级结构
        }
        
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
            
            # 检查是否存在 Max-Gruppe 工作表
            if "Max-Gruppe" not in xl.sheet_names:
                self.logger.error("错误：未找到 Max-Gruppe 工作表")
                raise ValueError("未找到 Max-Gruppe 工作表")
            
            # 读取 Max-Gruppe 工作表
            self.logger.info("正在读取 Max-Gruppe 工作表...")
            df = pd.read_excel(file_path, sheet_name="Max-Gruppe")
            self.logger.info(f"成功读取工作表，共 {len(df)} 行数据")
            
            # 检查必需的列是否存在
            required_columns = ["Auflösungsstufe", "Placeholder", "Baugruppe", "Objektkurztext", "Langtext"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"错误：缺少必需的列: {', '.join(missing_columns)}")
                raise ValueError(f"缺少必需的列: {', '.join(missing_columns)}")
            
            self.logger.info("所有必需列均存在，开始处理数据...")
            
            # 处理数据
            self._process_max_gruppe(df)
            
            self.logger.info(f"BOM文件导入成功，共处理 {len(self.bom_data['items'])} 个项目")
            
        except Exception as e:
            self.logger.error(f"导入BOM文件失败: {str(e)}", exc_info=True)
            raise ImportError(f"导入BOM文件失败: {str(e)}")
    
    def _process_max_gruppe(self, df: pd.DataFrame) -> None:
        """处理 Max-Gruppe 工作表数据
        
        Args:
            df: Max-Gruppe 工作表的数据帧
        """
        try:
            # 先过滤掉层级为空的行，使用 copy() 避免 SettingWithCopyWarning
            df = df.dropna(subset=["Auflösungsstufe"]).copy()
            self.logger.info(f"过滤空层级后剩余 {len(df)} 行数据")
            
            # 将层级转换为整数
            df.loc[:, "Auflösungsstufe"] = df["Auflösungsstufe"].astype(float).astype(int)
            
            # 清空现有数据
            self.bom_data = {
                "items": [],
                "level_placeholders": {},
                "hierarchy": {}
            }
            
            # 按原始顺序处理数据
            self.logger.info("\n开始处理数据...")
            processed_count = 0
            current_parent = None
            parent_stack = []  # [(level, id), ...]
            
            # 直接按DataFrame的顺序处理每一行
            for idx, row in df.iterrows():
                try:
                    level = int(row["Auflösungsstufe"])
                    baugruppe = str(row["Baugruppe"]).strip()
                    placeholder = str(row["Placeholder"]).strip() if not pd.isna(row["Placeholder"]) else ""
                    description = str(row["Objektkurztext"]).strip()
                    long_text = str(row["Langtext"]).strip() if not pd.isna(row["Langtext"]) else ""
                    
                    # 跳过空的Baugruppe
                    if pd.isna(baugruppe):
                        self.logger.warning(f"跳过第 {idx+1} 行：Baugruppe为空")
                        continue
                    
                    # 构建BOM码
                    bom_code = f"{placeholder}-{baugruppe}" if placeholder else baugruppe
                    
                    # 创建节点数据
                    item_data = {
                        "id": len(self.bom_data["items"]),  # 使用唯一ID
                        "name": description,
                        "level": level,
                        "placeholder": placeholder,
                        "long_text": long_text,
                        "bom_code": bom_code,
                        "baugruppe": baugruppe,
                        "original_index": idx,
                        "children": []  # 存储子节点的ID
                    }
                    
                    # 将项目添加到items列表
                    self.bom_data["items"].append(item_data)
                    current_item_id = item_data["id"]
                    
                    # 更新层级占位符跟踪
                    level_key = f"{level}_{placeholder}"
                    if level_key not in self.bom_data["level_placeholders"]:
                        self.bom_data["level_placeholders"][level_key] = []
                    self.bom_data["level_placeholders"][level_key].append(current_item_id)
                    
                    # 更新层级结构
                    if level == 1:
                        # 一级节点直接添加到根
                        self.bom_data["hierarchy"][current_item_id] = item_data
                        parent_stack = [(1, current_item_id)]
                    else:
                        # 调整父节点栈，移除所有大于等于当前层级的节点
                        while parent_stack and parent_stack[-1][0] >= level:
                            parent_stack.pop()
                        
                        # 如果有父节点，添加到父节点的children中
                        if parent_stack:
                            parent_id = parent_stack[-1][1]
                            self.bom_data["items"][parent_id]["children"].append(current_item_id)
                        
                        # 将当前节点加入父节点栈
                        parent_stack.append((level, current_item_id))
                    
                    processed_count += 1
                    
                except Exception as e:
                    self.logger.error(f"处理第 {idx+1} 行数据时出错: {str(e)}", exc_info=True)
                    continue
            
            # 统计各层级节点数量
            level_counts = {}
            for item in self.bom_data["items"]:
                level = item["level"]
                if level not in level_counts:
                    level_counts[level] = 0
                level_counts[level] += 1
            
            # 记录统计信息
            self.logger.info("\n数据处理完成，成功处理 {processed_count} 行数据")
            for level, count in sorted(level_counts.items()):
                self.logger.info(f"第 {level} 级节点数量: {count}")
            
        except Exception as e:
            self.logger.error(f"处理 Max-Gruppe 工作表错误: {str(e)}", exc_info=True)
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
        if item_id in self.bom_data["hierarchy"]:
            return self.bom_data["hierarchy"][item_id]
        
        # 递归查找子节点
        for main_item in self.bom_data["hierarchy"].values():
            result = self._find_item_in_subitems(item_id, main_item["children"])
            if result:
                return result
        
        return None
    
    def _find_item_in_subitems(self, item_id: str, sub_items: List[int]) -> Optional[Dict[str, Any]]:
        """在子项中递归查找项目数据
        
        Args:
            item_id: 项目ID
            sub_items: 子项列表
            
        Returns:
            Optional[Dict[str, Any]]: 项目数据，如果不存在则返回None
        """
        # 直接在当前层级查找
        if item_id in sub_items:
            return self.bom_data["items"][item_id]
        
        # 递归查找下一层级
        for sub_item_id in sub_items:
            result = self._find_item_in_subitems(item_id, self.bom_data["items"][sub_item_id]["children"])
            if result:
                return result
        
        return None
    
    def get_bom_data(self) -> Dict[str, Any]:
        """获取BOM数据
        
        Returns:
            Dict[str, Any]: BOM数据字典
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
        return item_data.get("children", []) if item_data else []
    
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
        self.bom_data = {
            "items": [],
            "level_placeholders": {},
            "hierarchy": {}
        }
    
    def get_all_bom_codes(self) -> List[str]:
        """获取所有有效的BOM码
        
        Returns:
            List[str]: BOM码列表，格式为 "占位符-Baugruppe"
        """
        bom_codes = []
        
        def collect_bom_codes(items):
            """递归收集BOM码
            
            Args:
                items: 项目列表或字典
            """
            if isinstance(items, list):
                # 如果是列表（children），遍历列表
                for item in items:
                    if isinstance(item, int):
                        # 如果是ID，获取实际的项目数据
                        item_data = self.bom_data["items"][item]
                    else:
                        # 如果已经是项目数据
                        item_data = item
                    
                    # 添加BOM码
                    if "bom_code" in item_data:
                        bom_codes.append(item_data["bom_code"])
                    
                    # 递归处理子项
                    if "children" in item_data and item_data["children"]:
                        collect_bom_codes(item_data["children"])
            elif isinstance(items, dict):
                # 如果是字典（hierarchy），遍历值
                for item_data in items.values():
                    # 添加BOM码
                    if "bom_code" in item_data:
                        bom_codes.append(item_data["bom_code"])
                    
                    # 递归处理子项
                    if "children" in item_data and item_data["children"]:
                        collect_bom_codes(item_data["children"])
        
        # 从根节点开始收集
        collect_bom_codes(self.bom_data["hierarchy"])
        # 收集所有项目的BOM码
        collect_bom_codes(self.bom_data["items"])
        
        # 去重并返回
        return list(set(bom_codes))
        
    def is_valid_bom_code(self, code: str) -> bool:
        """检查是否为有效的BOM码
        
        Args:
            code: 要检查的代码
            
        Returns:
            bool: 是否为有效的BOM码
        """
        try:
            return code in self.get_all_bom_codes()
        except Exception as e:
            self.logger.error(f"检查BOM码时出错: {str(e)}", exc_info=True)
            return False 

    def get_bom_description(self, bom_code: str) -> str:
        """根据BOM码生成描述字符串
        
        Args:
            bom_code: BOM码 (格式如 "占位符-Baugruppe" 或 "Baugruppe")
            
        Returns:
            str: 描述字符串 (格式如 "占位符-Objektkurztext-Langtext")，找不到则返回原BOM码
        """
        try:
            # 尝试匹配所有存储的BOM项目
            for item in self.bom_data.get("items", []):
                if item.get("bom_code") == bom_code:
                    placeholder = item.get("placeholder", "")
                    name = item.get("name", "") # Objektkurztext
                    long_text = item.get("long_text", "")
                    
                    desc_parts = []
                    if placeholder:
                        desc_parts.append(placeholder)
                    if name:
                        desc_parts.append(name)
                    if long_text:
                        desc_parts.append(long_text)
                    
                    return "-".join(desc_parts) if desc_parts else bom_code
            
            self.logger.warning(f"未找到BOM码 '{bom_code}' 对应的描述信息，将返回原BOM码。")
            return bom_code
        except Exception as e:
            self.logger.error(f"为BOM码 '{bom_code}' 生成描述时出错: {str(e)}", exc_info=True)
            return bom_code 