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

from models.logic_rule import LogicRule, RuleType, RuleStatus
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
                    
                # 解析数据并创建规则
                for rule_data in data.get('rules', []):
                    try:
                        # 使用LogicRule.from_dict方法统一创建规则
                        rule = LogicRule.from_dict(rule_data)
                        
                        # 添加到规则字典
                        self.rules[rule.rule_id] = rule
                        
                    except Exception as e:
                        self.logger.error(f"加载规则失败: {str(e)}", exc_info=True)
                        continue
                        
                self.logger.info(f"已加载 {len(self.rules)} 条规则")
            else:
                self.logger.info("规则数据文件不存在，使用空规则集")
                
        except Exception as e:
            self.logger.error(f"加载规则数据失败: {str(e)}", exc_info=True)
    
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
            rules_data = []
            
            for rule in self.rules.values():
                rule_dict = rule.to_dict()
                rules_data.append(rule_dict)
                self.logger.debug(f"已导出规则: ID={rule.rule_id}")
            
            # 标记规则已导出
            self.rules_exported = True
            
            # 保存导出状态
            self._save_rules()
            
            export_data = {
                'rules': rules_data,
                'exported_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"规则导出完成，共导出 {len(rules_data)} 条规则")
            
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
            
            # 解析数据并创建规则
            imported_count = 0
            max_rule_number = 0
            
            for rule_data in data.get('rules', []):
                try:
                    # 获取规则ID
                    rule_id = rule_data.get('logic_id', '')
                    if not rule_id.startswith('BL'):
                        # 如果不是BL开头，生成新的BL规则ID
                        rule_id = self._generate_rule_id()
                    else:
                        try:
                            rule_number = int(rule_id[2:])
                            max_rule_number = max(max_rule_number, rule_number)
                        except (ValueError, IndexError):
                            self.logger.warning(f"无法解析规则ID: {rule_id}")
                    
                    # 创建规则对象
                    rule = LogicRule(
                        rule_id=rule_id,
                        rule_type=RuleType.STATIC,  # 保留但不使用
                        condition=rule_data.get('selection_expression', ''),
                        action=rule_data.get('impact_expression', ''),
                        relation=rule_data.get('logic_relation', '→'),
                        status=RuleStatus(rule_data.get('status', 'enabled'))
                    )
                    
                    # 添加到规则字典
                    self.rules[rule_id] = rule
                    imported_count += 1
                    
                    self.logger.debug(f"成功导入规则: ID={rule_id}")
                    
                except Exception as e:
                    self.logger.error(f"导入规则失败: {str(e)}", exc_info=True)
                    continue
            
            # 更新规则计数器
            self.rule_counter = max_rule_number + 1
            
            # 设置导出状态为False
            self.rules_exported = False
            
            # 保存到临时文件
            self._save_rules()
            
            # 通知观察者
            self.notify_observers()
            self.notify_rule_change("imported")
            
            self.logger.info(f"规则导入完成，成功导入 {imported_count} 条规则")
            
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
            # 确保目录存在
            os.makedirs(os.path.dirname(RULES_DATA_FILE), exist_ok=True)
            
            # 准备数据
            data = {
                'rules': [rule.to_dict() for rule in self.rules.values()],
                'exported': self.rules_exported  # 保存导出状态
            }
            
            # 保存到文件
            with open(RULES_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.debug("规则数据已保存到临时文件")
            
        except Exception as e:
            self.logger.error(f"保存规则数据失败: {str(e)}", exc_info=True)
            raise
    
    def clear_rules(self):
        """清空规则数据"""
        try:
            # 清空内存中的规则
            self.rules.clear()
            
            # 创建空的规则数据
            data = {
                'rules': [],
                'saved_at': datetime.now().isoformat(),
                'exported': True,  # 设置为已导出状态
                'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
            }
            
            # 确保数据目录存在
            os.makedirs(DATA_DIR, exist_ok=True)
            
            # 保存空规则到文件
            with open(RULES_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.info("规则数据已成功清空")
            
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
            # 使用固定名称的文件或指定的文件路径
            if not file_path:
                file_path = RULES_DATA_FILE
                self.logger.info(f"准备从临时文件加载规则: {file_path}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.logger.error(f"规则文件不存在: {file_path}")
                return False
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 清空现有规则
            self.rules.clear()
            
            # 获取导出状态
            self.rules_exported = data.get('exported', True)
            
            # 解析数据并创建规则
            for rule_data in data.get('rules', []):
                try:
                    # 使用LogicRule.from_dict方法创建规则
                    rule = LogicRule.from_dict(rule_data)
                    
                    # 添加到规则字典
                    self.rules[rule.rule_id] = rule
                    
                except Exception as e:
                    self.logger.error(f"加载规则失败: {str(e)}", exc_info=True)
                    continue
            
            # 通知规则变更
            self.notify_rule_change("imported")
            
            self.logger.info("从临时文件加载规则完成")
            return True
            
        except Exception as e:
            self.logger.error(f"从临时文件加载规则失败: {str(e)}", exc_info=True)
            return False 