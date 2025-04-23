"""
配置选项处理器模块

该模块专门用于处理配置选项Excel文件的导入和数据管理。
"""
import pandas as pd
from typing import Dict, List, Optional
import re
from utils.logger import Logger

class ConfigProcessor:
    """配置选项处理器类"""
    
    def __init__(self):
        """初始化配置选项处理器"""
        # 获取当前类的日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 存储模块数据
        self.modules: Dict[str, List[str]] = {}  # 模块名到F码列表的映射
        self.f_k_mapping: Dict[str, List[str]] = {}  # F码到K码列表的映射
        self.code_names: Dict[str, str] = {}  # 代码到名称的映射
        
    def import_excel(self, file_path: str) -> None:
        """导入Excel文件
        
        Args:
            file_path: Excel文件路径
        """
        try:
            xl = pd.ExcelFile(file_path)
            self.logger.info(f"找到工作表: {xl.sheet_names}")
            
            # 清空现有数据
            self.clear()
            
            for sheet_name in xl.sheet_names:
                # 跳过模板页和不是数字开头的工作表
                if sheet_name == "0.模板&Vorlage" or sheet_name == "TD" or not any(c.isdigit() for c in sheet_name[0]):
                    self.logger.debug(f"跳过工作表: {sheet_name}")
                    continue
                
                # 提取模块编号和名称
                try:
                    # 分割工作表名称，获取编号和名称
                    parts = sheet_name.split('.')
                    if len(parts) >= 2:
                        module_number = parts[0].strip()
                        module_name = '.'.join(parts[1:]).strip()
                        # 组合模块标识符
                        module_id = f"{module_number}.{module_name}"
                    else:
                        module_id = sheet_name
                    
                    self.logger.info(f"处理工作表: {sheet_name} -> 模块: {module_id}")
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    self._process_sheet(module_id, df)
                    
                except Exception as e:
                    self.logger.error(f"处理工作表 {sheet_name} 时出错: {str(e)}", exc_info=True)
                    continue
                
        except Exception as e:
            self.logger.error(f"导入错误: {str(e)}", exc_info=True)
            raise ImportError(f"导入Excel失败: {str(e)}")
    
    def _process_sheet(self, module_id: str, df: pd.DataFrame) -> None:
        """处理单个工作表
        
        Args:
            module_id: 模块ID
            df: 数据帧
        """
        try:
            # 检查并重命名列
            expected_columns = [
                "选项ID/OptionsID(K-nummer)", 
                "特征/Merkmale (F-nummer)", 
                "默认值/Standardwert", 
                "多选/Mehrfachauswahl", 
                "可选项/wählbare Option",
                "说明/Anmerkung"
            ]
            
            # 确保所有必需的列都存在
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                self.logger.warning(f"缺少列: {', '.join(missing_columns)}")
                return
            
            # 重命名列
            column_mapping = {
                "选项ID/OptionsID(K-nummer)": "k_code",
                "特征/Merkmale (F-nummer)": "f_code",
                "可选项/wählbare Option": "name"
            }
            df = df.rename(columns=column_mapping)
            
            # 初始化模块的F码列表
            self.modules[module_id] = []
            
            # 处理每一行数据
            for _, row in df.iterrows():
                if pd.isna(row['k_code']) or pd.isna(row['f_code']) or pd.isna(row['name']):
                    continue
                
                # 提取F码和K码
                f_code_match = re.search(r'F\d+', str(row['f_code']))
                k_code = str(row['k_code']).strip()  # 直接使用选项ID列的值作为K码
                
                if f_code_match and k_code:
                    f_code = f_code_match.group()
                    
                    # 添加到模块的F码列表
                    if f_code not in self.modules[module_id]:
                        self.modules[module_id].append(f_code)
                    
                    # 添加F码和K码的映射关系
                    if f_code not in self.f_k_mapping:
                        self.f_k_mapping[f_code] = []
                    if k_code not in self.f_k_mapping[f_code]:
                        self.f_k_mapping[f_code].append(k_code)
                    
                    # 保存代码名称
                    if f_code not in self.code_names:
                        f_name = str(row['f_code']).replace(f_code, '').strip()
                        self.code_names[f_code] = f_name
                    self.code_names[k_code] = str(row['name']).strip()
            
        except Exception as e:
            self.logger.error(f"处理工作表错误: {str(e)}", exc_info=True)
            raise
    
    def get_modules(self) -> Dict[str, List[str]]:
        """获取所有模块数据
        
        Returns:
            Dict[str, List[str]]: 模块名到F码列表的映射
        """
        return self.modules
    
    def get_k_codes(self, f_code: str) -> List[str]:
        """获取F码对应的K码列表
        
        Args:
            f_code: F码
            
        Returns:
            List[str]: K码列表
        """
        return self.f_k_mapping.get(f_code, [])
    
    def get_name(self, code: str) -> str:
        """获取代码对应的名称
        
        Args:
            code: F码或K码
            
        Returns:
            str: 代码名称
        """
        return self.code_names.get(code, code)
    
    def is_valid_k_code_for_f_code(self, f_code: str, k_code: str) -> bool:
        """验证K码是否属于F码
        
        Args:
            f_code: F码
            k_code: K码
            
        Returns:
            bool: 是否有效
        """
        return k_code in self.get_k_codes(f_code)
    
    def clear(self) -> None:
        """清空数据"""
        self.modules.clear()
        self.f_k_mapping.clear()
        self.code_names.clear()
    
    def get_all_k_codes(self) -> List[str]:
        """获取所有有效的K码
        
        Returns:
            List[str]: K码列表
        """
        k_codes = []
        for f_codes in self.f_k_mapping.values():
            k_codes.extend(f_codes)
        return list(set(k_codes))  # 去重
    
    def is_valid_k_code(self, code: str) -> bool:
        """检查是否为有效的K码
        
        Args:
            code: 要检查的代码
            
        Returns:
            bool: 是否为有效的K码
        """
        return code in self.get_all_k_codes() 