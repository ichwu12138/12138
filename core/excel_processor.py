import pandas as pd
from typing import Dict, Optional
from models.feature import Feature
from models.option import Option
import re
from utils.logger import Logger

class ExcelProcessor:
    """Excel数据处理器"""
    
    def __init__(self):
        # 获取当前类的日志记录器
        self.logger = Logger.get_logger(__name__)
        
        self.modules: Dict[str, list] = {}  # 模块名到特征列表的映射
        self.features: Dict[str, Feature] = {}  # F码到特征的映射
        self.options: Dict[str, Option] = {}    # K码到选项的映射
    
    def import_excel(self, file_path: str) -> None:
        """导入Excel文件"""
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
                    self.modules[module_id] = []  # 初始化模块的特征列表
                    self._process_sheet(module_id, df)
                    
                except Exception as e:
                    self.logger.error(f"处理工作表 {sheet_name} 时出错: {str(e)}", exc_info=True)
                    continue
                
        except Exception as e:
            self.logger.error(f"导入错误: {str(e)}", exc_info=True)
            raise ImportError(f"导入Excel失败: {str(e)}")
    
    def _process_sheet(self, module_name: str, df: pd.DataFrame) -> None:
        """处理单个工作表"""
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
                "选项ID/OptionsID(K-nummer)": "选项ID",
                "特征/Merkmale (F-nummer)": "特征",
                "默认值/Standardwert": "默认值",
                "多选/Mehrfachauswahl": "多选",
                "可选项/wählbare Option": "可选项",
                "说明/Anmerkung": "说明"
            }
            df = df.rename(columns=column_mapping)
            
            self.logger.debug(f"处理数据:\n{df.head()}")
            
            # 初始化模块的特征列表（如果不存在）
            if module_name not in self.modules:
                self.modules[module_name] = []
            
            for idx, row in df.iterrows():
                try:
                    if pd.isna(row['选项ID']) or pd.isna(row['特征']) or pd.isna(row['可选项']):
                        self.logger.debug(f"跳过行 {idx}: 关键字段为空")
                        continue
                    
                    # 处理特征 (格式: Fxx xxx)
                    feature_text = str(row['特征']).strip()
                    # 使用空格分割F码和特征名
                    parts = feature_text.split(' ', 1)
                    if len(parts) == 2 and parts[0].startswith('F'):
                        f_code = parts[0]  # F码是F开头到空格之前的所有内容
                        f_name = parts[1]  # 特征名是空格后的所有内容
                        self.logger.debug(f"处理特征: {f_code} - {f_name}")
                        
                        # 创建或获取特征
                        if f_code not in self.features:
                            self.features[f_code] = Feature(
                                f_code=f_code,
                                name=f_name,
                                multiple=pd.notna(row['多选']) and str(row['多选']).upper() == 'Y'
                            )
                            # 将特征添加到对应模块（如果还没有添加）
                            if f_code not in self.modules[module_name]:
                                self.modules[module_name].append(f_code)
                        
                        # 处理选项ID (格式: Kxx_xx_xx xxx)
                        k_text = str(row['选项ID']).strip()
                        # 使用空格分割K码和选项名
                        k_parts = k_text.split(' ', 1)
                        if len(k_parts) >= 1 and k_parts[0].startswith('K'):
                            k_code = k_parts[0]  # K码是K开头到空格之前的所有内容
                            
                            # 创建选项
                            option = Option(
                                k_code=k_code,
                                name=str(row['可选项']).strip(),
                                value=str(row['可选项']).strip(),
                                description=str(row['说明']).strip() if pd.notna(row['说明']) else "",
                                default=pd.notna(row['默认值']) and str(row['默认值']).strip() == str(row['可选项']).strip()
                            )
                            
                            # 建立关联
                            self.features[f_code].add_option(option)
                            self.options[k_code] = option
                            self.logger.debug(f"添加选项: {k_code} - {option.name}")
                        else:
                            self.logger.warning(f"跳过行 {idx}: K码格式错误 '{k_text}'")
                    else:
                        self.logger.warning(f"跳过行 {idx}: 特征格式错误 '{feature_text}'")
                
                except Exception as e:
                    self.logger.error(f"处理行 {idx} 时出错: {str(e)}", exc_info=True)
                    continue  # 继续处理下一行
            
        except Exception as e:
            self.logger.error(f"处理工作表错误: {str(e)}", exc_info=True)
            raise
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "features": {},
            "options": {}
        }
        
        # 添加特征
        for f_code, feature in self.features.items():
            result["features"][f_code] = {
                "name": feature.name,
                "multiple": feature.multiple,
                "options": [opt.k_code for opt in feature.options]
            }
        
        # 添加选项
        for k_code, option in self.options.items():
            result["options"][k_code] = {
                "value": option.value,
                "description": option.description,
                "default": option.default,
                "feature": option.feature.f_code if option.feature else None
            }
        
        return result
    
    def get_feature(self, f_code: str) -> Optional[Feature]:
        """获取特征"""
        return self.features.get(f_code)
    
    def get_option(self, k_code: str) -> Optional[Option]:
        """获取选项"""
        return self.options.get(k_code)
    
    def clear(self) -> None:
        """清空数据"""
        self.modules.clear()
        self.features.clear()
        self.options.clear()

    def is_valid_k_code_for_f_code(self, f_code: str, k_code: str) -> bool:
        """验证K码是否属于F码
        
        Args:
            f_code: F码
            k_code: K码
            
        Returns:
            bool: 是否有效
        """
        # 获取特征
        feature = self.get_feature(f_code)
        if not feature:
            return False
            
        # 获取特征的所有K码
        valid_k_codes = [opt.k_code for opt in feature.options]
        
        return k_code in valid_k_codes 