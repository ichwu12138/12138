"""
逻辑构建器模块

该模块提供了创建和管理逻辑规则的功能。
"""
import json
import os
import re
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
import uuid

from models.logic_rule import LogicRule, RuleStatus
from core.config_processor import ConfigProcessor
from core.bom_processor import BomProcessor
from utils.config_manager import config_manager, DATA_DIR
from utils.observer import Observable
from utils.logger import Logger
from utils.validator import ExpressionValidator

# 规则数据文件路径
RULES_DATA_FILE = os.path.join(DATA_DIR, "temp_rules_latest.json")
# 备份目录路径
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

class LogicBuilder(Observable):
    """逻辑规则构建器"""
    
    def __init__(self, config_processor: ConfigProcessor, bom_processor: BomProcessor):
        """初始化逻辑规则构建器"""
        super().__init__()
        
        # 获取当前类的日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 保存处理器
        self.config_processor = config_processor
        self.bom_processor = bom_processor
        
        # 初始化规则字典
        self.rules: Dict[str, LogicRule] = {}
        
        # 创建专门用于规则创建和删除的观察者列表
        self._rule_created_observers = []
        self._rule_deleted_observers = []
        self._rule_observers = []  # 添加规则观察者列表
        
        # 添加导出状态跟踪
        self.rules_exported = False
        
        # Instantiate Validator FIRST
        self.validator = ExpressionValidator(config_processor, bom_processor)
        
        # 加载规则
        self._load_rules()
    
    def _generate_rule_description(self, rule: LogicRule) -> str:
        """为规则生成单一字符串的文本描述。"""
        if not rule:
            self.logger.debug("Attempted to generate description for a None rule.")
            return ""
        
        condition_str_desc = ""
        if rule.condition:
            condition_tokens = self._tokenize_for_description(rule.condition)
            translated_cond_tokens = self._translate_tokens_for_description(condition_tokens)
            condition_str_desc = " ".join(translated_cond_tokens)
            self.logger.debug(f"Generated condition part for rule {rule.rule_id}: '{condition_str_desc}'")

        action_str_desc = ""
        if rule.action:
            action_tokens = self._tokenize_for_description(rule.action)
            translated_action_tokens = self._translate_tokens_for_description(action_tokens)
            action_str_desc = " ".join(translated_action_tokens)
            self.logger.debug(f"Generated action part for rule {rule.rule_id}: '{action_str_desc}'")

        if condition_str_desc and action_str_desc:
            return f"{condition_str_desc} → {action_str_desc}"
        elif condition_str_desc:
            return condition_str_desc
        elif action_str_desc:
            return f"→ {action_str_desc}" 
        else:
            self.logger.debug(f"Rule {rule.rule_id} has no condition or action content for description.")
            return ""

    def _tokenize_for_description(self, expression_part: str) -> List[str]:
        """Helper to tokenize a part of an expression for description generation."""
        # Simplified tokenization focusing on known codes and operators
        # This regex might need to be the same or similar to the one previously used for the full expression
        raw_tokens = re.split(r'(\s+|\b(AND|OR|NOT|→)\b|\(|\))\s*', expression_part)
        final_tokens = [t.strip() for t in raw_tokens if t and t.strip()]
        return final_tokens

    def _translate_tokens_for_description(self, tokens: List[str]) -> List[str]:
        """Helper to translate a list of tokens to their descriptive strings."""
        described_tokens = []
        for token in tokens:
            token_upper = token.upper()
            if self.validator.is_k_code(token): 
                described_tokens.append(self.config_processor.get_name(token))
            elif token.startswith("HBG_"):
                described_tokens.append(self.config_processor.get_name(token))
            elif token_upper in ["AND", "OR", "NOT", "(", ")", "→"]:
                described_tokens.append(token) 
            elif self.bom_processor.is_valid_bom_code(token): 
                described_tokens.append(self.bom_processor.get_bom_description(token))
            else:
                described_tokens.append(token)
        return described_tokens

    def _load_rules(self):
        """加载规则数据"""
        try:
            if os.path.exists(RULES_DATA_FILE):
                with open(RULES_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.rules_exported = data.get('exported', False)
                self.rules.clear()
                loaded_rules_count = 0
                
                # Determine rule data source (new vs old format)
                bl_rules_data = data.get('BL_rules', data.get('bl_rules', [] if "TL_rules" in data or "tl_rules" in data else None))
                tl_rules_data = data.get('TL_rules', data.get('tl_rules', []))

                if bl_rules_data is None and "rules" in data: # Original old format
                    combined_rules_data = data.get('rules', [])
                    self.logger.info(f"从 {RULES_DATA_FILE} 加载时检测到旧版规则文件格式 (rules列表)。")
                elif bl_rules_data is not None :
                    combined_rules_data = bl_rules_data + tl_rules_data
                    if "BL_rules" in data or "TL_rules" in data:
                         self.logger.info(f"从 {RULES_DATA_FILE} 加载时检测到新版大写键名规则文件格式 (BL_rules/TL_rules)。")
                    elif "bl_rules" in data or "tl_rules" in data:
                         self.logger.info(f"从 {RULES_DATA_FILE} 加载时检测到新版小写键名规则文件格式 (bl_rules/tl_rules)。")
                else: # No recognizable rule keys
                    combined_rules_data = []
                    self.logger.warning(f"加载的文件 {RULES_DATA_FILE} 不包含可识别的规则数据键。")


                for rule_data in combined_rules_data:
                    try:
                        rule = LogicRule.from_dict(rule_data)
                        # ALWAYS regenerate description on load to ensure it uses current processor data
                        # This overwrites any description loaded from the file.
                        self.logger.debug(f"Rule {rule.rule_id} loaded from file. Original file description: '{rule.description}'. Regenerating description.")
                        rule.description = self._generate_rule_description(rule)
                        self.logger.info(f"Newly generated description for {rule.rule_id} (on _load_rules): '{rule.description}'")
                        
                        self.rules[rule.rule_id] = rule
                        loaded_rules_count += 1
                    except Exception as e:
                        self.logger.error(f"加载单条规则失败: {str(e)}，规则数据: {rule_data}", exc_info=True)
                        continue
                        
                self.logger.info(f"已加载 {loaded_rules_count} 条规则从 {RULES_DATA_FILE}")
            else:
                self.logger.info(f"规则数据文件 {RULES_DATA_FILE} 不存在，使用空规则集")
                
        except Exception as e:
            self.logger.error(f"加载规则数据 ({RULES_DATA_FILE}) 失败: {str(e)}", exc_info=True)
    
    def _generate_rule_id(self) -> str:
        """生成规则ID
        
        Returns:
            str: 规则ID
        """
        # 获取现有BL规则的数量
        count = len([r for r in self.rules.values()]) + 1
        
        # 生成ID (BLxx)
        rule_id = f"BL{count:02d}"
        
        # 确保ID唯一
        while rule_id in self.rules:
            count += 1
            rule_id = f"BL{count:02d}"
            
        return rule_id
    
    def get_rule(self, rule_id: str) -> Optional[LogicRule]:
        """获取规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Optional[LogicRule]: 规则对象，如果不存在则为None
        """
        return self.rules.get(rule_id)
    
    def get_rule_by_id(self, rule_id: str):
        """获取规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Optional[LogicRule]: 规则对象，如果不存在则为None
        """
        return self.rules.get(rule_id)
    
    def delete_rule(self, rule_id: str) -> bool:
        """删除规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 是否成功删除
        """
        self.logger.debug(f"LogicBuilder delete_rule: 尝试删除规则 ID: '{rule_id}'. 规则是否存在于 self.rules: {rule_id in self.rules}")
        if rule_id in self.rules:
            deleted_rule = self.rules.pop(rule_id)
            if not self.rules:  # 规则列表变空
                self.rules_exported = True
            else:  # 仍有规则
                self.rules_exported = False
            self._save_rules() # 这会保存不包含已删除规则的列表
            self.notify_rule_change("deleted", rule_id, deleted_rule) 
            self.logger.info(f"LogicBuilder delete_rule: 规则 '{rule_id}' 已成功从 self.rules 移除, 保存并发送删除通知。")
            return True
        self.logger.warning(f"LogicBuilder delete_rule: 尝试删除规则 '{rule_id}' 失败，因为它不在 self.rules 中。")
        return False
    
    def export_rules(self) -> Dict[str, Any]:
        """导出规则
        
        Returns:
            Dict[str, Any]: 规则数据
        """
        try:
            self.logger.info("开始导出规则数据")
            BL_rules_data = []
            TL_rules_data = []
            
            for rule in self.rules.values():
                # Ensure description is up-to-date before exporting, though it should be
                if not rule.description and (rule.condition or rule.action): # Defensive check
                    self.logger.debug(f"Rule {rule.rule_id} has empty description during export, regenerating.")
                    rule.description = self._generate_rule_description(rule)
                rule_dict = rule.to_dict() 
                if rule.rule_id.startswith("BL"):
                    BL_rules_data.append(rule_dict)
                elif rule.rule_id.startswith("TL"):
                    TL_rules_data.append(rule_dict)
                else:
                    self.logger.warning(f"规则 {rule.rule_id} 不符合BL或TL前缀，导出时归类到BL_rules。")
                    BL_rules_data.append(rule_dict) 

                self.logger.debug(f"已准备导出规则: ID={rule.rule_id}, Desc='{rule.description[:50]}...'")
            
            self.rules_exported = True 
            
            export_data = {
                'BL_rules': BL_rules_data,
                'TL_rules': TL_rules_data,
                'exported_at': datetime.now().isoformat(),
                'exported': True 
            }
            
            # Clear rules in memory and the temp file after successful export packaging
            # This behavior is kept as per the original logic, but consider if this is always desired.
            self.clear_rules() 
            
            self.logger.info(f"规则导出完成，共导出 {len(BL_rules_data) + len(TL_rules_data)} 条规则")
            return export_data
            
        except Exception as e:
            self.logger.error(f"导出规则数据失败: {str(e)}", exc_info=True)
            raise
    
    def import_rules(self, file_path: str):
        """导入规则
        
        Args:
            file_path: 规则文件路径
        """
        try:
            self.logger.info(f"开始导入规则文件: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.rules.clear()
            self.logger.info("已清空现有规则")
            
            max_bl_number = 0
            max_tl_number = 0
            imported_count = 0
            
            # Determine rule data source (new vs old format) - similar logic to _load_rules
            bl_rules_data_imp = data.get('BL_rules', data.get('bl_rules', [] if "TL_rules" in data or "tl_rules" in data else None))
            tl_rules_data_imp = data.get('TL_rules', data.get('tl_rules', []))

            if bl_rules_data_imp is None and "rules" in data: # Original old format
                rules_to_process = data.get('rules', [])
                self.logger.info("导入时检测到旧版规则文件格式 (rules列表)。")
            elif bl_rules_data_imp is not None:
                rules_to_process = bl_rules_data_imp + tl_rules_data_imp
                if "BL_rules" in data or "TL_rules" in data:
                    self.logger.info("导入时检测到新版大写键名规则文件格式 (BL_rules/TL_rules)。")
                elif "bl_rules" in data or "tl_rules" in data:
                    self.logger.info("导入时检测到新版小写键名规则文件格式 (bl_rules/tl_rules)。")
            else: # No recognizable rule keys
                rules_to_process = []
                self.logger.warning(f"导入的文件 {file_path} 不包含可识别的规则数据键。")


            for rule_data in rules_to_process:
                try:
                    rule = LogicRule.from_dict(rule_data)
                    
                    # ALWAYS regenerate description on import to ensure it uses current processor data
                    self.logger.debug(f"Rule {rule.rule_id} imported from file. Original file description: '{rule.description}'. Regenerating description.")
                    rule.description = self._generate_rule_description(rule) 
                    self.logger.info(f"Newly generated description for imported rule {rule.rule_id}: '{rule.description}'")

                    # Handle Rule ID generation/validation (copied from original, may need review for description context)
                    rule_id = rule.rule_id 
                    impact_expression = rule.action
                    is_tuning = self.validator.is_tuning_logic(impact_expression)
                    # ... (ID generation/validation logic from original import_rules)
                    current_rule_id_prefix = "TL" if is_tuning else "BL"
                    current_max_number = max_tl_number if is_tuning else max_bl_number

                    if rule_id and rule_id.startswith(current_rule_id_prefix) and rule_id[2:].isdigit():
                        num = int(rule_id[2:])
                        if is_tuning: max_tl_number = max(max_tl_number, num)
                        else: max_bl_number = max(max_bl_number, num)
                    else: # ID is missing, or wrong prefix, or not ending with number
                        if is_tuning:
                            max_tl_number += 1
                            rule_id = f"TL{max_tl_number:02d}"
                        else:
                            max_bl_number += 1
                            rule_id = f"BL{max_bl_number:02d}"
                        self.logger.warning(f"原始规则ID '{rule.rule_id}' 无效或缺失，已重新生成为 '{rule_id}'")
                    rule.rule_id = rule_id


                    if rule_id in self.rules:
                        self.logger.warning(f"导入规则时发现重复的规则ID: {rule_id}。旧规则将被覆盖。")
                    self.rules[rule_id] = rule
                    imported_count += 1
                    self.logger.debug(f"成功导入规则: ID={rule.rule_id}, Desc='{rule.description[:50]}...'")
                except Exception as e:
                    self.logger.error(f"处理单条导入规则时失败: {str(e)}，规则数据: {rule_data}", exc_info=True)
                    continue
            
            self.rules_exported = False
            self._save_rules() # This will save descriptions too
            
            self.notify_observers()
            self.notify_rule_change("imported")
            
            BL_rules_count = sum(1 for r in self.rules.values() if r.rule_id.startswith('BL'))
            TL_rules_count = sum(1 for r in self.rules.values() if r.rule_id.startswith('TL'))
            self.logger.info(f"规则导入完成，成功导入 {imported_count} 条规则（BOM逻辑: {BL_rules_count}，微调逻辑: {TL_rules_count}）")
            
        except Exception as e:
            self.logger.error(f"导入规则数据失败: {str(e)}", exc_info=True)
            raise
    
    def add_rule(self, rule: LogicRule) -> None:
        """添加新规则或更新现有规则
        
        Args:
            rule: 要添加或更新的规则对象
        """
        if not rule.rule_id:
            self.logger.error("尝试添加没有ID的规则。")
            return

        is_new_rule = rule.rule_id not in self.rules
        # self.rules[rule.rule_id] = rule # 将规则加入/更新到字典中

        # 为规则生成/更新描述
        rule.description = self._generate_rule_description(rule) 
        rule.modified_at = datetime.now() # 更新修改时间
        
        self.rules[rule.rule_id] = rule # 确保字典中的对象是最新的（包含描述和新修改时间）
        
        self.rules_exported = False # 规则已更改，标记为未导出
        self._save_rules() # 保存所有规则（包括这条新规则或更新后的规则）
        
        change_type = "added" if is_new_rule else "modified"
        self.notify_rule_change(change_type, rule.rule_id, rule)

        self.logger.info(f"已{'添加' if is_new_rule else '更新'}规则: {rule.rule_id}, Desc='{rule.description[:30]}...'")
    
    def _save_rules(self):
        """保存规则数据"""
        try:
            BL_rules_data = []
            TL_rules_data = []

            for rule in self.rules.values():
                # Ensure description is current before saving, though add_rule/import should handle it
                if not rule.description and (rule.condition or rule.action): # Defensive: generate if empty but has content
                     self.logger.debug(f"Rule {rule.rule_id} has empty description during save, regenerating.")
                     rule.description = self._generate_rule_description(rule)
                
                rule_dict = rule.to_dict() # This now includes 'description'
                # rule_dict['status'] = rule.status.value # Already handled by to_dict

                if rule.rule_id.startswith("BL"):
                    BL_rules_data.append(rule_dict)
                elif rule.rule_id.startswith("TL"):
                    TL_rules_data.append(rule_dict)
                else:
                    self.logger.warning(f"规则 {rule.rule_id} 不符合BL或TL前缀，保存时归类到BL_rules。")
                    BL_rules_data.append(rule_dict)
            
            now = datetime.now()
            formatted_saved_at = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:22]

            data = {
                "BL_rules": BL_rules_data, 
                "TL_rules": TL_rules_data, 
                "exported": self.rules_exported,
                "saved_at": formatted_saved_at # 添加格式化的 saved_at
            }
            
            os.makedirs(os.path.dirname(RULES_DATA_FILE), exist_ok=True)
            with open(RULES_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"已保存 {len(BL_rules_data) + len(TL_rules_data)} 条规则到临时文件 ({RULES_DATA_FILE})")
        except Exception as e:
            self.logger.error(f"保存规则数据失败: {str(e)}", exc_info=True)
            raise
    
    def clear_rules(self):
        """清空规则数据"""
        try:
            # 清空内存中的规则
            self.rules.clear()
            
            now = datetime.now()
            formatted_saved_at = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:22]
            formatted_timestamp = now.strftime("%Y%m%d_%H%M%S")

            # 创建空的规则数据结构 (新格式，大写键名)
            data = {
                'BL_rules': [], # Uppercase key
                'TL_rules': [], # Uppercase key
                'saved_at': formatted_saved_at, # 使用格式化后的时间
                'exported': True,
                'timestamp': formatted_timestamp # 使用与 saved_at 相同 now 对象生成的时间戳
            }
            
            # 确保数据目录存在
            os.makedirs(DATA_DIR, exist_ok=True)
            
            # 保存空规则到文件
            with open(RULES_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"规则数据已成功清空，并写入空的临时文件: {RULES_DATA_FILE}")
            
            # 通知观察者
            self.notify_observers()
            
            # 通知规则变更
            self.notify_rule_change("cleared")
            
        except Exception as e:
            self.logger.error(f"清空规则数据失败: {str(e)}", exc_info=True)
            raise

    def has_unsaved_rules(self) -> bool:
        """检查是否有未导出的规则
        
        Returns:
            bool: 是否有未导出的规则
        """
        return not self.rules_exported and len(self.rules) > 0
    
    def get_rules(self) -> List[LogicRule]:
        """获取所有规则
        
        Returns:
            List[LogicRule]: 规则列表
        """
        return list(self.rules.values())
    
    def notify_observers(self, data: Any = None):
        """通知观察者"""
        super().notify_observers(data)
    
    def add_rule_created_observer(self, observer):
        """添加规则创建观察者
        
        Args:
            observer: 观察者回调函数，接收一个规则参数
        """
        if observer not in self._rule_created_observers:
            self._rule_created_observers.append(observer)
    
    def add_rule_deleted_observer(self, observer):
        """添加规则删除观察者
        
        Args:
            observer: 观察者回调函数，接收rule_id参数
        """
        if observer not in self._rule_deleted_observers:
            self._rule_deleted_observers.append(observer)
    
    def add_rule_observer(self, observer):
        """添加规则观察者
        
        Args:
            observer: 观察者回调函数，接收 change_type, rule_id, rule 参数
        """
        if observer not in self._rule_observers:
            self._rule_observers.append(observer)
            
    def remove_rule_observer(self, observer):
        """移除规则观察者
        
        Args:
            observer: 要移除的观察者回调函数
        """
        if observer in self._rule_observers:
            self._rule_observers.remove(observer)
            
    def notify_rule_change(self, change_type, rule_id=None, rule=None):
        """通知所有观察者规则变更"""
        for observer in self._rule_observers:
            try:
                observer(change_type, rule_id, rule)
            except Exception as e:
                self.logger.error(f"通知规则观察者时出错: {str(e)}", exc_info=True)
    
    def save_to_temp_file(self, file_path=None) -> str:
        """将规则保存到临时文件
        
        Args:
            file_path: 可选的文件路径，如果不提供则使用固定名称
            
        Returns:
            str: 保存的文件路径
        """
        try:
            # 使用固定的文件名或指定的文件路径
            if not file_path:
                file_path = RULES_DATA_FILE
            
            # 调用_save_rules方法保存数据
            self._save_rules()
            
            self.logger.info(f"规则数据已保存到文件: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"保存规则到文件失败: {str(e)}", exc_info=True)
            raise
    
    def load_from_temp_file(self, file_path=None):
        """从临时文件加载规则
        
        Args:
            file_path: 临时文件路径，如果不提供则使用固定名称的文件
        
        Returns:
            bool: 是否成功加载
        """
        try:
            target_file = file_path if file_path else RULES_DATA_FILE
            self.logger.info(f"准备从临时文件加载规则: {target_file}")
            
            if not os.path.exists(target_file):
                self.logger.error(f"规则文件不存在: {target_file}。将清空内存规则并标记为已导出。")
                self.rules.clear()
                self.rules_exported = True 
                self.notify_rule_change("cleared") 
                return False
            
            with open(target_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.rules.clear()
            self.rules_exported = data.get('exported', True) 
            loaded_rules_count = 0
            
            # Determine rule data source (new vs old format) - similar logic to _load_rules
            bl_rules_data_load = data.get('BL_rules', data.get('bl_rules', [] if "TL_rules" in data or "tl_rules" in data else None))
            tl_rules_data_load = data.get('TL_rules', data.get('tl_rules', []))

            if bl_rules_data_load is None and "rules" in data: # Original old format
                rules_to_process = data.get('rules', [])
            elif bl_rules_data_load is not None:
                rules_to_process = bl_rules_data_load + tl_rules_data_load
            else: # No recognizable rule keys
                rules_to_process = []


            for rule_data in rules_to_process:
                try:
                    rule = LogicRule.from_dict(rule_data)
                    # ALWAYS regenerate description on load to ensure it uses current processor data
                    self.logger.debug(f"Rule {rule.rule_id} loaded from temp file. Original file description: '{rule.description}'. Regenerating description.")
                    rule.description = self._generate_rule_description(rule)
                    self.logger.info(f"Newly generated description for {rule.rule_id} (from temp): '{rule.description}'")
                    
                    self.rules[rule.rule_id] = rule
                    loaded_rules_count +=1
                except Exception as e:
                    self.logger.error(f"加载单条规则失败: {str(e)}，规则数据: {rule_data}", exc_info=True)
                    continue
            
            self.notify_rule_change("imported") # This will trigger UI updates
            self.logger.info(f"从临时文件 ({target_file}) 加载 {loaded_rules_count} 条规则完成。导出状态: {self.rules_exported}")
            return True
            
        except Exception as e:
            self.logger.error(f"从临时文件加载规则的整个过程失败: {str(e)}", exc_info=True)
            self.rules.clear()
            self.rules_exported = True 
            self.notify_rule_change("cleared") 
            return False

    def get_rules_with_descriptions(self) -> List[Dict[str, str]]:
        """获取所有规则及其描述，用于导出。"""
        output = []
        for rule_id, rule in self.rules.items():
            # Ensure description is up-to-date, though it should be
            description = rule.description if rule.description else self._generate_rule_description(rule)
            # Ensure the description is a string, if _generate_rule_description somehow failed or was skipped.
            if not isinstance(description, str):
                self.logger.warning(f"Description for rule {rule_id} is not a string ('{description}') during get_rules_with_descriptions. Regenerating as a fallback.")
                description = self._generate_rule_description(rule)

            output.append({
                "rule_id": rule_id,
                "description": description
            })
        return output

    def update_rule_description(self, rule_id: str) -> Optional[LogicRule]:
        """更新指定规则的描述并保存。通常在规则编辑后调用。"""
        rule = self.get_rule_by_id(rule_id) # rule 是 self.rules[rule_id] 的引用
        if rule:
            self.logger.debug(f"LogicBuilder update_rule_description for '{rule_id}': 方法入口时规则状态 = '{rule.status.value if rule.status else 'None'}', 描述 = '{rule.description[:50]}...'")

            old_description = rule.description
            new_description = self._generate_rule_description(rule)
            
            description_changed = False
            if rule.description != new_description:
                rule.description = new_description
                description_changed = True
            
            rule.modified_at = datetime.now()
            
            # 记录状态和描述，在保存前
            self.logger.debug(f"LogicBuilder update_rule_description for '{rule_id}': 调用 _save_rules() 前，规则状态 = '{rule.status.value if rule.status else 'None'}', 描述是否更改 = {description_changed}, 新描述 = '{rule.description[:50]}...'")
            
            self._save_rules() # 保存包括任何状态和描述在内的所有修改
            
            self.logger.info(f"LogicBuilder update_rule_description for '{rule_id}': 规则已保存。通知UI变更 (modified)。")
            self.notify_rule_change("modified", rule.rule_id, rule)
            return rule
        
        self.logger.error(f"LogicBuilder update_rule_description: 无法找到规则 '{rule_id}' 进行更新。")
        return None

    # Ensure ExpressionValidator has is_bom_code_candidate or similar helper
    # In ExpressionValidator, we can add:
    # @staticmethod
    # def is_bom_code_candidate(token: str, all_bom_codes: List[str]) -> bool:
    #     # This is a simplistic check. A BOM code might not be in all_bom_codes
    #     # if it's part of a more complex pattern or dynamically generated.
    #     # It also depends on how specific all_bom_codes list is.
    #     # A more robust check might involve regex for BOM patterns.
    #     # For now, checking if it's in the list of known codes is a start.
    #     if token in all_bom_codes:
    #          return True
    #     # Add regex for typical BOM code patterns, e.g., placeholder-baugruppe or just baugruppe
    #     # Example: if re.fullmatch(r\"^[A-Z0-9]+-[A-Z0-9]+$\", token) or re.fullmatch(r\"^[A-Z0-9]+$\", token):
    #     # This is very generic, needs to be specific to the project's BOM code format.
    #     # Let's assume bom_processor.is_valid_bom_code is the authority or get_all_bom_codes provides enough coverage.
    #     return False 
    # This helper method might be better placed in LogicBuilder or used directly with bom_processor.is_valid_bom_code

# Placeholder for ExpressionValidator.is_bom_code_candidate
# This static method should be added to the ExpressionValidator class in utils/validator.py
# For now, the logic in _generate_rule_description will use bom_processor.is_valid_bom_code directly.


# Placeholder for ExpressionValidator.is_bom_code_candidate
# This static method should be added to the ExpressionValidator class in utils/validator.py
# For now, the logic in _generate_rule_description will use bom_processor.is_valid_bom_code directly. 