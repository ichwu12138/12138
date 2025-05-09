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
    
    def __init__(self, config_processor: ConfigProcessor):
        """初始化逻辑规则构建器"""
        super().__init__()
        
        # 获取当前类的日志记录器
        self.logger = Logger.get_logger(__name__)
        
        # 保存Excel处理器
        self.config_processor = config_processor
        
        # 初始化规则字典
        self.rules: Dict[str, LogicRule] = {}
        
        # 创建专门用于规则创建和删除的观察者列表
        self._rule_created_observers = []
        self._rule_deleted_observers = []
        self._rule_observers = []  # 添加规则观察者列表
        
        # 添加导出状态跟踪
        self.rules_exported = False
        
        # 加载规则
        self._load_rules()
    
    def _load_rules(self):
        """加载规则数据"""
        try:
            if os.path.exists(RULES_DATA_FILE):
                with open(RULES_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 获取导出状态
                self.rules_exported = data.get('exported', False)
                
                # 清空现有规则，因为 load_from_temp_file 会处理
                self.rules.clear()

                # 解析数据并创建规则 - 优先尝试新格式
                loaded_rules_count = 0
                if "BL_rules" in data or "TL_rules" in data: # Check for uppercase keys
                    bl_rules_data = data.get('BL_rules', []) # Use uppercase key
                    tl_rules_data = data.get('TL_rules', []) # Use uppercase key
                    combined_rules_data = bl_rules_data + tl_rules_data
                    self.logger.info(f"从 {RULES_DATA_FILE} 加载时检测到新版规则文件格式 (BL_rules/TL_rules)。")
                else: # 兼容旧格式 (bl_rules/tl_rules or rules)
                    if "bl_rules" in data or "tl_rules" in data: # Check for lowercase keys (old new format)
                         bl_rules_data = data.get('bl_rules', [])
                         tl_rules_data = data.get('tl_rules', [])
                         self.logger.info(f"从 {RULES_DATA_FILE} 加载时检测到小写键名的新版规则文件格式 (bl_rules/tl_rules)。")
                    else: # Original old format
                         bl_rules_data = [] # Ensure it's initialized
                         tl_rules_data = [] # Ensure it's initialized
                         self.logger.info(f"从 {RULES_DATA_FILE} 加载时检测到旧版规则文件格式 (rules列表)。")
                    combined_rules_data = data.get('rules', bl_rules_data + tl_rules_data)


                for rule_data in combined_rules_data:
                    try:
                        # 使用LogicRule.from_dict方法统一创建规则
                        rule = LogicRule.from_dict(rule_data)
                        
                        # 添加到规则字典
                        self.rules[rule.rule_id] = rule
                        loaded_rules_count += 1
                        
                    except Exception as e:
                        self.logger.error(f"加载单条规则失败: {str(e)}", exc_info=True)
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
        if rule_id in self.rules:
            # 删除规则
            del self.rules[rule_id]
            
            # 保存规则
            self._save_rules()
            
            # 通知规则删除观察者
            for observer in self._rule_deleted_observers:
                observer(rule_id)
            
            return True
        
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
                rule_dict = rule.to_dict() # 确保 to_dict() 返回所需的所有字段
                if rule.rule_id.startswith("BL"):
                    BL_rules_data.append(rule_dict)
                elif rule.rule_id.startswith("TL"):
                    TL_rules_data.append(rule_dict)
                else:
                    # 对于不符合命名规范的规则ID，可以考虑如何处理，例如放入一个通用列表或报错
                    self.logger.warning(f"规则 {rule.rule_id} 不符合BL或TL前缀，导出时未分类。")
                    # 暂且放入BL列表，或创建一个 'other_rules' 列表
                    BL_rules_data.append(rule_dict) 

                self.logger.debug(f"已准备导出规则: ID={rule.rule_id}")
            
            # 标记规则已导出
            self.rules_exported = True # 导出操作本身意味着规则已导出，这个状态应在保存到临时文件时重置
            
            # 创建导出数据
            export_data = {
                'BL_rules': BL_rules_data,
                'TL_rules': TL_rules_data,
                'exported_at': datetime.now().isoformat(),
                'exported': True # 明确标记此文件是导出文件
            }
            
            # 清空临时文件中的规则，因为它们现在已被导出
            # 注意：调用 clear_rules() 会删除内存中的规则并写入一个空的、标记为exported的临时文件。
            # 如果导出操作后不希望立即清空内存中的规则，则不应在此处调用 clear_rules()。
            # 根据之前的逻辑，导出后通常会清空。
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
                
            # 清空现有规则
            self.rules.clear()
            self.logger.info("已清空现有规则")
            
            # 初始化BL和TL规则的最大编号
            max_bl_number = 0
            max_tl_number = 0
            
            # 解析数据并创建规则
            imported_count = 0
            
            # 确定规则数据来源
            if "BL_rules" in data or "TL_rules" in data: # 新格式
                BL_rules_data = data.get('BL_rules', [])
                TL_rules_data = data.get('TL_rules', [])
                rules_to_process = BL_rules_data + TL_rules_data
                self.logger.info("检测到新版规则文件格式 (BL_rules/TL_rules)。")
            elif "rules" in data: # 旧格式
                rules_to_process = data.get('rules', [])
                self.logger.info("检测到旧版规则文件格式 (rules列表)。")
            else:
                self.logger.warning(f"导入的文件 {file_path} 不包含 'rules', 'BL_rules' 或 'TL_rules' 键。")
                rules_to_process = []

            for rule_data in rules_to_process:
                try:
                    # 获取规则ID和表达式
                    rule_id = rule_data.get('logic_id', '')
                    impact_expression = rule_data.get('impact_expression', '')
                    
                    # 检查是否是微调逻辑
                    is_tuning = ExpressionValidator.is_tuning_logic(impact_expression)
                    
                    # 处理规则ID
                    if rule_id:
                        # 如果已有ID，检查格式是否匹配规则类型
                        if is_tuning and not rule_id.startswith('TL'):
                            # 微调逻辑但ID不是TL开头，生成新的TL ID
                            max_tl_number += 1
                            new_rule_id = f"TL{max_tl_number:02d}"
                            self.logger.warning(f"规则 '{rule_id}' 是微调逻辑但ID不是TL开头，将重新生成ID为 '{new_rule_id}'。")
                            rule_id = new_rule_id
                        elif not is_tuning and not rule_id.startswith('BL'):
                            # BOM逻辑但ID不是BL开头，生成新的BL ID
                            max_bl_number += 1
                            new_rule_id = f"BL{max_bl_number:02d}"
                            self.logger.warning(f"规则 '{rule_id}' 是BOM逻辑但ID不是BL开头，将重新生成ID为 '{new_rule_id}'。")
                            rule_id = new_rule_id
                        else:
                            # ID格式正确，更新对应的最大编号
                            try:
                                number = int(rule_id[2:])
                                if rule_id.startswith('BL'):
                                    max_bl_number = max(max_bl_number, number)
                                else:  # TL
                                    max_tl_number = max(max_tl_number, number)
                            except (ValueError, IndexError):
                                self.logger.warning(f"无法解析规则ID数字部分: {rule_id}")
                    else:
                        # 没有ID，根据规则类型生成新ID
                        if is_tuning:
                            max_tl_number += 1
                            rule_id = f"TL{max_tl_number:02d}"
                        else:
                            max_bl_number += 1
                            rule_id = f"BL{max_bl_number:02d}"
                    
                    # 创建规则对象
                    # 使用 LogicRule.from_dict 来确保所有字段都被正确处理
                    rule = LogicRule.from_dict(rule_data)
                    rule.rule_id = rule_id # 确保使用上面处理过的rule_id

                    # 添加到规则字典
                    if rule_id in self.rules:
                        self.logger.warning(f"导入规则时发现重复的规则ID: {rule_id}。旧规则将被覆盖。")
                    self.rules[rule_id] = rule
                    imported_count += 1
                    
                    self.logger.debug(f"成功导入规则: ID={rule.rule_id}, 类型={'微调逻辑' if is_tuning else 'BOM逻辑'}")
                    
                except Exception as e:
                    self.logger.error(f"处理单条导入规则时失败: {str(e)}，规则数据: {rule_data}", exc_info=True)
                    continue
            
            # 设置导出状态为False，因为这是新导入的规则集合
            self.rules_exported = False
            
            # 保存到临时文件
            self._save_rules()
            
            # 通知观察者
            self.notify_observers()
            self.notify_rule_change("imported")
            
            # 记录导入统计信息
            BL_rules_count = sum(1 for r in self.rules.values() if r.rule_id.startswith('BL'))
            TL_rules_count = sum(1 for r in self.rules.values() if r.rule_id.startswith('TL'))
            self.logger.info(f"规则导入完成，成功导入 {imported_count} 条规则（BOM逻辑: {bl_rules_count}，微调逻辑: {tl_rules_count}）")
            
        except Exception as e:
            self.logger.error(f"导入规则数据失败: {str(e)}", exc_info=True)
            raise
    
    def add_rule(self, rule: LogicRule) -> None:
        """添加规则
        
        Args:
            rule: 规则对象
        """
        # 添加规则
        self.rules[rule.rule_id] = rule
        
        # 标记规则未导出
        self.rules_exported = False
        
        # 保存规则
        self._save_rules()
        
        # 通知规则创建观察者
        for observer in self._rule_created_observers:
            observer(rule)
            
        # 通知规则变更
        self.notify_rule_change("added", rule.rule_id, rule)
    
    def _save_rules(self):
        """保存规则数据"""
        try:
            # 创建规则数据
            BL_rules_data = [] # Using uppercase for local variable for clarity, matches user's edit
            TL_rules_data = [] # Using uppercase for local variable

            for rule in self.rules.values():
                rule_dict = rule.to_dict()
                rule_dict['status'] = rule.status.value 

                if rule.rule_id.startswith("BL"):
                    BL_rules_data.append(rule_dict)
                elif rule.rule_id.startswith("TL"):
                    TL_rules_data.append(rule_dict)
                else:
                    self.logger.warning(f"规则 {rule.rule_id} 不符合BL或TL前缀，保存时归类到BL_rules。")
                    BL_rules_data.append(rule_dict)
            
            # 创建完整的数据结构，使用大写键名
            data = {
                "BL_rules": BL_rules_data, # Uppercase key
                "TL_rules": TL_rules_data, # Uppercase key
                "exported": self.rules_exported
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(RULES_DATA_FILE), exist_ok=True)
            
            # 保存到文件
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
            
            # 创建空的规则数据结构 (新格式，大写键名)
            data = {
                'BL_rules': [], # Uppercase key
                'TL_rules': [], # Uppercase key
                'saved_at': datetime.now().isoformat(),
                'exported': True,
                'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
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
            rules_to_process = []

            if "BL_rules" in data or "TL_rules" in data: # Check for uppercase keys first
                bl_data = data.get('BL_rules', [])
                tl_data = data.get('TL_rules', [])
                rules_to_process = bl_data + tl_data
                self.logger.info(f"加载时检测到新版大写键名规则文件格式 (BL_rules/TL_rules) 从 {target_file}。")
            elif "bl_rules" in data or "tl_rules" in data: # Check for lowercase keys (old new format)
                 bl_data = data.get('bl_rules', [])
                 tl_data = data.get('tl_rules', [])
                 rules_to_process = bl_data + tl_data
                 self.logger.info(f"加载时检测到新版小写键名规则文件格式 (bl_rules/tl_rules) 从 {target_file}。")
            elif "rules" in data: # Original old format
                rules_to_process = data.get('rules', [])
                self.logger.info(f"加载时检测到旧版规则文件格式 (rules列表) 从 {target_file}。")
            else:
                self.logger.warning(f"加载的文件 {target_file} 不包含可识别的规则数据键。")

            for rule_data in rules_to_process:
                try:
                    rule = LogicRule.from_dict(rule_data)
                    self.rules[rule.rule_id] = rule
                    loaded_rules_count +=1
                except Exception as e:
                    self.logger.error(f"加载单条规则失败: {str(e)}，规则数据: {rule_data}", exc_info=True)
                    continue
            
            self.notify_rule_change("imported")
            self.logger.info(f"从临时文件 ({target_file}) 加载 {loaded_rules_count} 条规则完成。导出状态: {self.rules_exported}")
            return True
            
        except Exception as e:
            self.logger.error(f"从临时文件加载规则的整个过程失败: {str(e)}", exc_info=True)
            self.rules.clear()
            self.rules_exported = True # Or False, depending on desired state on failure
            self.notify_rule_change("cleared") # Notify that rules are now empty
            return False 