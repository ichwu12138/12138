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
    
    def build_dynamic_rule(self, condition: str, action: str, status: RuleStatus = RuleStatus.ENABLED, relation: str = "") -> LogicRule:
        """构建动态逻辑规则
        
        Args:
            condition: 条件表达式
            action: 影响表达式
            status: 规则状态
            relation: 逻辑关系
            
        Returns:
            LogicRule: 创建的逻辑规则
        """
        # 验证条件表达式
        valid, message = self._validate_dynamic_expression(condition)
        if not valid:
            raise ValueError(f"条件表达式无效: {message}")
        
        # 特殊情况处理
        # 检查是否是before...choose情况
        tokens = condition.split()
        condition_type = tokens[0].lower() if tokens else None
        is_before_choose = False
        
        tokens_action = action.split()
        effect_type = tokens_action[0].lower() if tokens_action else None
        
        # 检查before情况，before只能跟choose
        if condition_type == "before" and effect_type != "choose":
            raise ValueError(f"before条件只能使用choose影响类型")
        
        # 检查是否是before...choose组合
        if condition_type == "before" and effect_type == "choose":
            is_before_choose = True
            # before...choose组合不需要验证括号内容
            valid = True
        # 检查是否是info类型
        elif effect_type == "info":
            # info类型不需要方括号，但需要检查是否有引号文本
            has_quoted_text = False
            for token in tokens_action[1:]:
                if token.startswith('"') and token.endswith('"'):
                    has_quoted_text = True
                    break
            
            if not has_quoted_text:
                raise ValueError("info类型需要引号包裹的文本")
            
            # info类型+引号文本是有效的，不检查方括号
            valid = True
        else:
            # 其他情况，验证影响表达式
            # 从action中提取方括号内容进行验证
            bracket_content = ""
            if "[" in action and "]" in action:
                bracket_start = action.find("[")
                bracket_end = action.rfind("]")
                if bracket_start < bracket_end:
                    bracket_content = action[bracket_start+1:bracket_end].strip()
            
            # 只有当存在方括号内容时才验证
            if bracket_content:
                valid, message = self._validate_code_expression(bracket_content)
                if not valid:
                    raise ValueError(f"影响表达式无效: {message}")
            elif not is_before_choose:  # 非before...choose情况必须有方括号，但info除外
                if effect_type != "info":  # 确保info类型不需要方括号
                    raise ValueError("影响表达式缺少方括号")
        
        # 创建规则ID
        rule_id = self._generate_rule_id(RuleType.DYNAMIC)
        
        # 创建规则
        rule = LogicRule(
            rule_id=rule_id,
            rule_type=RuleType.DYNAMIC,
            condition=condition,
            action=action,
            relation=relation,
            status=status
        )
        
        # 添加到规则字典
        self.rules[rule_id] = rule
        
        # 保存规则
        self._save_rules()
        
        # 通知规则创建观察者
        for observer in self._rule_created_observers:
            observer(rule)
        
        return rule
    
    def build_static_rule(self, condition: str, effect_expr: str, status: RuleStatus = RuleStatus.ENABLED, is_special_case: bool = False, skip_condition_validation: bool = False, force_has_relation: bool = False) -> LogicRule:
        """构建静态逻辑规则
        
        Args:
            condition: 条件表达式
            effect_expr: 影响表达式
            status: 规则状态
            is_special_case: 是否是特殊情况（XOR或F码 empty/not empty）
            skip_condition_validation: 是否跳过对condition部分的验证
            force_has_relation: 是否强制标记为包含关系操作符
            
        Returns:
            LogicRule: 创建的逻辑规则
        """
        # 检查condition和effect_expr表达式中是否包含关系操作符
        has_relation_operator = "→" in condition or ":" in condition or "→" in effect_expr or ":" in effect_expr or force_has_relation
        
        # 记录日志
        self.logger.debug(f"构建静态规则 - condition: {condition}, effect_expr: {effect_expr}")
        self.logger.debug(f"是否包含关系操作符: {has_relation_operator}, force_has_relation: {force_has_relation}")
        
        # 检查完整表达式是否需要拆分
        # 如果condition中没有关系操作符，但效果表达式为空，检查完整表达式是否包含关系操作符
        if not ("→" in condition or ":" in condition) and not effect_expr and not force_has_relation:
            tokens = condition.split()
            
            # 查找关系操作符位置
            relation_index = -1
            for i, token in enumerate(tokens):
                if token in ["→", ":"]:
                    relation_index = i
                    break
                    
            # 如果找到关系操作符，拆分表达式
            if relation_index != -1 and relation_index < len(tokens) - 1:
                relation = tokens[relation_index]
                left_part = " ".join(tokens[:relation_index])
                right_part = " ".join(tokens[relation_index+1:])
                
                # 重置condition和effect_expr
                condition = left_part
                effect_expr = right_part
                is_special_case = False
                skip_condition_validation = True  # 跳过对左侧部分的单独验证
                has_relation_operator = True  # 设置关系操作符标志
                
                # 记录日志
                self.logger.info(f"检测到完整表达式中的关系操作符，已拆分为：condition={condition}, relation={relation}, effect_expr={effect_expr}")
        
        # 如果包含关系操作符，则不是特殊情况
        if has_relation_operator:
            is_special_case = False
            
        # 验证条件表达式（除非明确指示跳过验证）
        if not skip_condition_validation:
            valid, message = self._validate_static_expression(condition)
            if not valid:
                raise ValueError(f"条件表达式无效: {message}")
        
        # 解析影响表达式
        relation = ""
        action = effect_expr
        
        # 只有在非特殊情况下才解析影响表达式
        if not is_special_case:
            if effect_expr.strip():
                # 如果effect_expr不为空，检查是否包含关系操作符
                if "→" in effect_expr:
                    parts = effect_expr.split("→", 1)
                    action = parts[1].strip()
                    relation = "→"
                    has_relation_operator = True  # 确保设置关系操作符标志
                elif ":" in effect_expr:
                    parts = effect_expr.split(":", 1)
                    action = parts[1].strip()
                    relation = ":"
                    has_relation_operator = True  # 确保设置关系操作符标志
                else:
                    # 如果没有关系操作符，entire effect_expr就是action
                    action = effect_expr
                    relation = "→"  # 默认使用→
            elif has_relation_operator:
                # 如果condition包含关系操作符（通常不应该走到这里）
                self.logger.warning("在condition中检测到关系操作符，但effect_expr为空，这可能是一个错误")
                relation = "→"  # 默认使用→
            else:
                # 非特殊情况但没有effect_expr，默认使用→
                relation = "→"
        
        # 日志记录最终的action和has_relation_operator状态
        self.logger.debug(f"验证影响表达式: {action}, 包含关系操作符: {has_relation_operator}")
        
        # 验证影响表达式 - 修改此处的验证方法
        # 如果存在关系操作符，验证右侧内容为逻辑表达式而不是列表
        if has_relation_operator:
            # 对于关系操作符右侧的内容，使用静态表达式验证方法，传入is_relation_right_side=True
            valid, message = self._validate_static_expression(action, is_relation_right_side=True)
            if not valid:
                raise ValueError(f"影响表达式无效: {message}")
        else:
            # 对于不包含关系操作符的情况，使用原来的列表内容验证
            valid, message = self._validate_code_expression(action)
            if not valid:
                raise ValueError(f"影响表达式无效: {message}")
        
        # 创建规则ID
        rule_id = self._generate_rule_id(RuleType.STATIC)
        
        # 创建规则
        rule = LogicRule(
            rule_id=rule_id,
            rule_type=RuleType.STATIC,
            condition=condition,
            action=action,
            relation=relation,
            status=status
        )
        
        # 添加到规则字典
        self.rules[rule_id] = rule
        
        # 保存规则
        self._save_rules()
        
        # 通知规则创建观察者
        for observer in self._rule_created_observers:
            observer(rule)
        
        return rule
    
    def _expand_expression(self, expr: str, use_and: bool = False) -> str:
        """展开表达式，将F码替换为(K1 OR K2 OR...)
        
        Args:
            expr: 原始表达式
            use_and: 是否使用AND连接符
            
        Returns:
            str: 展开后的表达式
        """
        # 查找所有F码
        f_codes = re.findall(r'F\d+', expr)
        
        # 替换表达式
        for f_code in f_codes:
            feature = self.config_processor.get_feature(f_code)
            if feature:
                k_codes = feature.get_k_codes()
                if k_codes:
                    operator = " AND " if use_and else " OR "
                    replacement = "(" + operator.join(k_codes) + ")"
                    expr = expr.replace(f_code, replacement)
                    
        return expr
    
    def _validate_dynamic_expression(self, expr: str) -> Tuple[bool, str]:
        """验证动态表达式
        
        Args:
            expr: 动态表达式
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        return ExpressionValidator.validate_dynamic_expression(expr, self.config_processor)
    
    def _validate_static_expression(self, expr: str, is_relation_right_side: bool = False) -> Tuple[bool, str]:
        """验证静态表达式
        
        Args:
            expr: 静态表达式
            is_relation_right_side: 是否是关系操作符右侧的表达式
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        return ExpressionValidator.validate_static_expression(expr, self.config_processor, is_relation_right_side)
    
    def _validate_code_expression(self, expr: str) -> Tuple[bool, str]:
        """验证代码表达式
        
        Args:
            expr: 代码表达式
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        return ExpressionValidator.validate_list_content(expr, True)
    
    def _generate_rule_id(self, rule_type: RuleType) -> str:
        """生成规则ID
        
        Args:
            rule_type: 规则类型
            
        Returns:
            str: 规则ID
        """
        # 获取该类型的规则数
        prefix = "LS" if rule_type == RuleType.STATIC else "LD"
        count = len([r for r in self.rules.values() if r.rule_type == rule_type]) + 1
        
        # 生成ID (LSxx 或 LDxx)
        rule_id = f"{prefix}{count:02d}"
        
        # 确保ID唯一
        while rule_id in self.rules:
            count += 1
            rule_id = f"{prefix}{count:02d}"
            
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
            # 获取规则类型
            rule_type = self.rules[rule_id].rule_type.value
            
            # 删除规则
            del self.rules[rule_id]
            
            # 保存规则
            self._save_rules()
            
            # 通知规则删除观察者
            if rule_type:
                for observer in self._rule_deleted_observers:
                    observer(rule_id, rule_type)
            
            return True
        
        return False
    
    def export_rules(self) -> Dict[str, Any]:
        """导出规则
        
        Returns:
            Dict[str, Any]: 规则数据
        """
        rules_data = []
        
        for rule in self.rules.values():
            rules_data.append({
                'rule_id': rule.rule_id,
                'rule_type': rule.rule_type.value,
                'condition': rule.condition,
                'action': rule.action,
                'relation': rule.relation,
                'status': rule.status.value,
                'tags': rule.tags
            })
            
        # 标记规则已导出
        self.rules_exported = True
        
        # 保存导出状态
        self._save_rules()
        
        # 清空规则
        self.clear_rules()
        
        return {
            'rules': rules_data,
            'exported_at': datetime.now().isoformat()
        }
    
    def _extract_codes(self, expression: str) -> List[str]:
        """提取表达式中的F码和K码
        
        Args:
            expression: 表达式
            
        Returns:
            List[str]: 提取的代码列表
        """
        # 查找所有F码和K码
        codes = re.findall(r'[FK]\d+', expression)
        return codes
    
    def import_rules(self, file_path: str):
        """导入规则
        
        Args:
            file_path: 规则文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 清空现有规则
            self.rules.clear()
            
            # 解析数据并创建规则
            for rule_data in data.get('rules', []):
                try:
                    # 使用LogicRule.from_dict方法统一创建规则
                    rule = LogicRule.from_dict(rule_data)
                    
                    # 检查一下规则类型是否明确
                    if rule.rule_id.startswith('LD'):
                        rule.rule_type = RuleType.DYNAMIC
                    elif rule.rule_id.startswith('LS'):
                        rule.rule_type = RuleType.STATIC
                    
                    # 添加到规则字典
                    self.rules[rule.rule_id] = rule
                    
                    self.logger.debug(f"导入规则: ID={rule.rule_id}, 类型={rule.rule_type.value}")
                    
                except Exception as e:
                    self.logger.error(f"导入规则失败: {str(e)}", exc_info=True)
                    continue
                    
            # 保存规则
            self._save_rules()
            
            # 通知观察者
            self.notify_observers()
            
            # 通知规则变更
            for rule_id, rule in self.rules.items():
                self.notify_rule_change("imported", rule_id, rule)
            
            self.logger.info(f"已导入 {len(self.rules)} 条规则")
            
        except Exception as e:
            self.logger.error(f"导入规则数据失败: {str(e)}", exc_info=True)
            raise
    
    def add_rule(self, rule: LogicRule) -> None:
        """添加规则
        
        Args:
            rule: 规则对象
        """
        # 如果规则ID已存在，生成新的ID
        if rule.rule_id in self.rules:
            rule.rule_id = self._generate_rule_id(rule.rule_type)
            
        # 添加到规则字典
        self.rules[rule.rule_id] = rule
        
        # 保存规则
        self._save_rules()
        
        # 通知观察者
        self.notify_observers()
    
    def _save_rules(self):
        """保存规则数据"""
        try:
            # 确保数据目录存在
            os.makedirs(DATA_DIR, exist_ok=True)
            
            # 获取当前时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 准备要保存的数据
            data = {
                'rules': [rule.to_dict() for rule in self.rules.values()],
                'saved_at': datetime.now().isoformat(),
                'exported': self.rules_exported,
                'timestamp': timestamp
            }
            
            # 保存新的规则数据
            with open(RULES_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())  # 确保数据写入磁盘
                
            self.logger.info(f"规则数据已保存到文件: {RULES_DATA_FILE}")
            
            # 通知观察者
            self.notify_observers()
            
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
        return bool(self.rules) and not self.rules_exported
    
    def get_rules(self) -> List[LogicRule]:
        """获取所有规则
        
        Returns:
            List[LogicRule]: 规则列表
        """
        return list(self.rules.values())
    
    def notify_observers(self, data: Any = None):
        """通知观察者"""
        super().notify_observers(data)
    
    # 添加规则创建观察者方法
    def add_rule_created_observer(self, observer):
        """添加规则创建观察者
        
        Args:
            observer: 观察者回调函数，接收一个规则参数
        """
        if observer not in self._rule_created_observers:
            self._rule_created_observers.append(observer)
    
    # 添加规则删除观察者方法
    def add_rule_deleted_observer(self, observer):
        """添加规则删除观察者
        
        Args:
            observer: 观察者回调函数，接收rule_id和rule_type参数
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
                self.logger.info(f"使用规则文件: {file_path}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.logger.error(f"规则文件不存在: {file_path}")
                return False
            
            # 从文件导入规则
            self.import_rules(file_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"从文件加载规则失败: {str(e)}", exc_info=True)
            return False 