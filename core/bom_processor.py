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
            
            # 读取Excel文件
            xl = pd.ExcelFile(file_path)
            self.logger.info(f"找到工作表: {xl.sheet_names}")
            
            # 检查是否存在 MAX-gruppe 工作表
            if "MAX-gruppe" not in xl.sheet_names:
                raise ValueError("未找到 MAX-gruppe 工作表")
            
            # 读取 MAX-gruppe 工作表
            df = pd.read_excel(file_path, sheet_name="MAX-gruppe")
            
            # 检查必需的列是否存在
            required_columns = ["层级", "占位符", "Baugruppe", "Beschreibung", "Langtext / long text"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"缺少必需的列: {', '.join(missing_columns)}")
            
            # 处理数据
            self._process_max_gruppe(df)
            
            self.logger.info("BOM文件导入成功")
            
        except Exception as e:
            self.logger.error(f"导入BOM文件失败: {str(e)}", exc_info=True)
            raise ImportError(f"导入BOM文件失败: {str(e)}")
    
    def _process_max_gruppe(self, df: pd.DataFrame) -> None:
        """处理 MAX-gruppe 工作表数据
        
        Args:
            df: MAX-gruppe 工作表的数据帧
        """
        try:
            # 按行处理数据
            current_level_items = {}  # 记录每个层级的当前项
            current_parent = None     # 当前父项
            last_level = 1           # 上一个处理的层级
            
            # 先过滤掉层级为空的行
            df = df.dropna(subset=["层级"])
            
            for _, row in df.iterrows():
                try:
                    # 获取行数据，将层级转换为整数
                    try:
                        level = int(float(row["层级"]))  # 处理可能的浮点数格式
                    except (ValueError, TypeError):
                        continue  # 跳过无效的层级值
                        
                    baugruppe = str(row["Baugruppe"]).strip()
                    placeholder = str(row["占位符"]).strip() if not pd.isna(row["占位符"]) else ""
                    description = str(row["Beschreibung"]).strip()
                    long_text = str(row["Langtext / long text"]).strip() if not pd.isna(row["Langtext / long text"]) else ""
                    
                    # 跳过空行
                    if pd.isna(baugruppe):
                        continue
                    
                    # 构建BOM码 - 使用占位符和Baugruppe的组合
                    bom_code = f"{placeholder}-{baugruppe}" if placeholder else baugruppe
                    
                    # 创建节点数据
                    item_data = {
                        "name": description,
                        "level": level,
                        "placeholder": placeholder,
                        "long_text": long_text,
                        "sub_items": {},
                        "bom_code": bom_code  # 保存构建的BOM码
                    }
                    
                    # 处理层级关系
                    if level == 1:
                        # 一级节点直接添加到根
                        self.bom_data[baugruppe] = item_data
                        current_level_items = {1: baugruppe}  # 重置层级记录
                        current_parent = baugruppe
                        last_level = 1
                    else:
                        # 找到正确的父节点
                        if level > last_level:
                            # 层级增加，使用上一个处理的项作为父节点
                            if current_parent:
                                parent_data = self._find_item_by_id(current_parent)
                                if parent_data:
                                    parent_data["sub_items"][baugruppe] = item_data
                        else:
                            # 层级相同或减小，使用对应上级层级的项作为父节点
                            parent_level = level - 1
                            parent_id = current_level_items.get(parent_level)
                            if parent_id:
                                parent_data = self._find_item_by_id(parent_id)
                                if parent_data:
                                    parent_data["sub_items"][baugruppe] = item_data
                    
                    # 更新当前层级的项
                    current_level_items[level] = baugruppe
                    current_parent = baugruppe
                    last_level = level
                    
                except Exception as e:
                    self.logger.error(f"处理行数据时出错: {str(e)}", exc_info=True)
                    continue
                    
        except Exception as e:
            self.logger.error(f"处理 MAX-gruppe 工作表错误: {str(e)}", exc_info=True)
            raise
    
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