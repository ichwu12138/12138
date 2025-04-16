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
            
            # TODO: 根据具体的BOM文件格式实现导入逻辑
            # 这里是示例代码，需要根据实际的BOM文件格式进行修改
            xl = pd.ExcelFile(file_path)
            self.logger.info(f"找到工作表: {xl.sheet_names}")
            
            # 处理每个工作表
            for sheet_name in xl.sheet_names:
                try:
                    self.logger.info(f"处理工作表: {sheet_name}")
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    self._process_sheet(sheet_name, df)
                    
                except Exception as e:
                    self.logger.error(f"处理工作表 {sheet_name} 时出错: {str(e)}", exc_info=True)
                    continue
                    
        except Exception as e:
            self.logger.error(f"导入BOM文件失败: {str(e)}", exc_info=True)
            raise ImportError(f"导入BOM文件失败: {str(e)}")
            
    def _process_sheet(self, sheet_name: str, df: pd.DataFrame) -> None:
        """处理单个工作表
        
        Args:
            sheet_name: 工作表名称
            df: 数据帧
        """
        try:
            # TODO: 根据具体的BOM文件格式实现处理逻辑
            # 这里是示例代码，需要根据实际的BOM文件格式进行修改
            
            # 检查必需的列是否存在
            required_columns = [
                "项目ID",
                "项目名称",
                "子项ID",
                "子项名称"
            ]
            
            # 确保所有必需的列都存在
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.warning(f"缺少列: {', '.join(missing_columns)}")
                return
                
            # 处理每一行数据
            for _, row in df.iterrows():
                try:
                    item_id = str(row["项目ID"]).strip()
                    item_name = str(row["项目名称"]).strip()
                    sub_id = str(row["子项ID"]).strip()
                    sub_name = str(row["子项名称"]).strip()
                    
                    # 跳过空行
                    if pd.isna(item_id) or pd.isna(item_name):
                        continue
                        
                    # 创建或获取主项数据
                    if item_id not in self.bom_data:
                        self.bom_data[item_id] = {
                            "name": item_name,
                            "sub_items": {}
                        }
                        
                    # 添加子项数据
                    if not pd.isna(sub_id):
                        if sub_id not in self.bom_data[item_id]["sub_items"]:
                            self.bom_data[item_id]["sub_items"][sub_id] = {
                                "name": sub_name,
                                "attributes": {}
                            }
                            
                        # 处理其他属性列
                        for col in df.columns:
                            if col not in required_columns and not pd.isna(row[col]):
                                self.bom_data[item_id]["sub_items"][sub_id]["attributes"][col] = str(row[col])
                                
                except Exception as e:
                    self.logger.error(f"处理行数据时出错: {str(e)}", exc_info=True)
                    continue
                    
        except Exception as e:
            self.logger.error(f"处理工作表错误: {str(e)}", exc_info=True)
            raise
            
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
        return self.bom_data.get(item_id)
        
    def get_sub_items(self, item_id: str) -> Dict[str, Dict[str, Any]]:
        """获取指定项目的所有子项
        
        Args:
            item_id: 项目ID
            
        Returns:
            Dict[str, Dict[str, Any]]: 子项字典，如果项目不存在则返回空字典
        """
        item_data = self.bom_data.get(item_id)
        return item_data.get("sub_items", {}) if item_data else {}
        
    def get_item_name(self, item_id: str) -> str:
        """获取项目名称
        
        Args:
            item_id: 项目ID
            
        Returns:
            str: 项目名称，如果不存在则返回项目ID
        """
        item_data = self.bom_data.get(item_id)
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