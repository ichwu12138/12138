import re
from typing import Dict, Any, List
from datetime import datetime
from models.logic_rule import LogicRule, RuleType, RuleStatus

class RuleExporter:
    """规则导出器类"""
    
    @staticmethod
    def parse_dynamic_condition(condition: str) -> Dict[str, Any]:
        """解析动态规则的条件部分"""
        return {
            "f_codes": re.findall(r'F\d+(?:_\d+)*', condition),
            "k_codes": re.findall(r'K\d+(?:_\d+)*', condition),
            "expression": condition
        }
    
    @staticmethod
    def parse_dynamic_action(action: str) -> Dict[str, Any]:
        """解析动态规则的动作部分"""
        # 提取动作类型
        action_type = None
        for at in ["display", "disable", "choose", "info"]:
            if at in action:
                action_type = at
                break
        
        # 提取目标代码
        if action_type == "choose" and not action.strip().startswith("choose ["):
            # before choose 特殊处理：解析逻辑表达式
            action_expr = action.replace("choose", "", 1).strip()
            return {
                "type": action_type,
                "expression": action_expr,
                "f_codes": re.findall(r'F\d+(?:_\d+)*', action_expr),
                "k_codes": re.findall(r'K\d+(?:_\d+)*', action_expr)
            }
        elif action_type in ["display", "disable", "choose"]:
            # 提取方括号中的内容
            targets = []
            start = action.find("[")
            end = action.find("]")
            if start != -1 and end != -1:
                content = action[start+1:end].strip()
                targets = [t.strip() for t in content.split(",") if t.strip()]
            return {
                "type": action_type,
                "targets": targets
            }
        else:  # info
            # 提取引号中的文本
            start = action.find('"')
            end = action.rfind('"')
            if start != -1 and end != -1:
                targets = [action[start+1:end]]
            else:
                targets = []
            return {
                "type": action_type,
                "targets": targets
            }
    
    @staticmethod
    def parse_static_condition(condition: str) -> Dict[str, Any]:
        """解析静态规则的条件部分"""
        return {
            "f_codes": re.findall(r'F\d+(?:_\d+)*', condition),
            "k_codes": re.findall(r'K\d+(?:_\d+)*', condition),
            "expression": condition
        }
    
    @staticmethod
    def parse_static_effect(effect: str) -> Dict[str, Any]:
        """解析静态规则的影响部分"""
        f_codes = re.findall(r'F\d+(?:_\d+)*', effect)
        k_codes = re.findall(r'K\d+(?:_\d+)*', effect)
        return {
            "f_code": f_codes[0] if f_codes else None,
            "k_code": k_codes[0] if k_codes else None
        }
    
    @staticmethod
    def create_rule_data(rule: LogicRule) -> Dict[str, Any]:
        """创建规则数据"""
        # 基本数据
        rule_data = {
            "id": rule.rule_id,
            "tags": rule.tags,
            "comment": rule.comment.get('text', '') if isinstance(rule.comment, dict) else str(rule.comment),
            "type": "static" if rule.rule_type == RuleType.STATIC else "dynamic",
            "status": "enabled" if rule.status == RuleStatus.ENABLED else 
                     "testing" if rule.status == RuleStatus.TESTING else "disabled"
        }
        
        if rule.rule_type == RuleType.STATIC:
            # 静态规则
            rule_data.update({
                "condition": rule.condition,
                "relation": rule.relation,
                "effect": rule.effect_expr,
                "relation_type": "implication" if rule.relation == "→" else "prerequisite",
                "parsed": {
                    "condition": RuleExporter.parse_static_condition(rule.condition),
                    "effect": RuleExporter.parse_static_effect(rule.effect_expr)
                } if rule.relation == "→" else {
                    "target_k_code": re.findall(r'K\d+(?:_\d+)*', rule.condition)[0],
                    "prerequisites": RuleExporter.parse_static_condition(rule.effect_expr)
                }
            })
        else:
            # 动态规则
            condition_type = "before" if rule.condition.strip().startswith("before") else "if"
            rule_data.update({
                "condition": rule.condition,
                "action": rule.action,
                "condition_type": condition_type,
                "action_type": next((at for at in ["display", "disable", "choose", "info"] 
                                   if at in rule.action), None),
                "parsed": {
                    "condition": RuleExporter.parse_dynamic_condition(rule.condition),
                    "action": RuleExporter.parse_dynamic_action(rule.action)
                }
            })
        
        return rule_data
    
    @staticmethod
    def export_rules(rules: List[LogicRule]) -> Dict[str, Any]:
        """导出规则到JSON格式"""
        # 创建基本结构
        rules_data = {
            "metadata": {
                "version": "1.0",
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "total_rules": len(rules)
            },
            "rules": {
                "static": {
                    "enabled": [],
                    "testing": [],
                    "disabled": []
                },
                "dynamic": {
                    "enabled": [],
                    "testing": [],
                    "disabled": []
                }
            },
            "indexes": {
                # 按触发条件索引
                "by_trigger": {
                    "k_codes": {},  # K码 -> 规则列表
                    "f_codes": {}   # F码 -> 规则列表
                },
                # 按影响项索引
                "by_impact": {
                    "k_codes": {},  # K码 -> 被哪些规则影响
                    "f_codes": {}   # F码 -> 被哪些规则影响
                },
                # 按动态规则类型索引
                "by_action_type": {
                    "if_display": [],    # if ... display [...]
                    "if_disable": [],    # if ... disable [...]
                    "if_choose": [],     # if ... choose [...]
                    "if_info": [],       # if ... info "..."
                    "before_choose": []  # before ... choose [...]
                }
            }
        }

        # 处理每个规则
        for rule in rules:
            # 确定规则类型和状态
            rule_type = "static" if rule.rule_type == RuleType.STATIC else "dynamic"
            if rule.status == RuleStatus.ENABLED:
                status = "enabled"
            elif rule.status == RuleStatus.TESTING:
                status = "testing"
            else:
                status = "disabled"

            # 创建规则数据
            if rule.rule_type == RuleType.STATIC:
                rule_data = {
                    "id": rule.rule_id,
                    "condition": rule.condition,
                    "effect": rule.action,
                    "relation": rule.relation,
                    "tags": rule.tags if hasattr(rule, 'tags') else [],
                    "comment": {"text": rule.comment.get('text', '') if isinstance(rule.comment, dict) else ''}
                }
            else:  # 动态规则
                rule_data = {
                    "id": rule.rule_id,
                    "condition": rule.condition,
                    "action": rule.action,
                    "tags": rule.tags if hasattr(rule, 'tags') else [],
                    "comment": {"text": rule.comment.get('text', '') if isinstance(rule.comment, dict) else ''}
                }

            # 添加规则到相应的分类
            rules_data["rules"][rule_type][status].append(rule_data)

            # 更新索引
            # 1. 提取条件中的代码
            condition_k_codes = re.findall(r'K\d+(?:_\d+)*', rule.condition)
            condition_f_codes = re.findall(r'F\d+(?:_\d+)*', rule.condition)

            # 2. 提取动作/影响中的代码
            action_k_codes = re.findall(r'K\d+(?:_\d+)*', rule.action)
            action_f_codes = re.findall(r'F\d+(?:_\d+)*', rule.action)

            # 3. 更新触发条件索引
            for k_code in condition_k_codes:
                if k_code not in rules_data["indexes"]["by_trigger"]["k_codes"]:
                    rules_data["indexes"]["by_trigger"]["k_codes"][k_code] = []
                rules_data["indexes"]["by_trigger"]["k_codes"][k_code].append({
                    "rule_id": rule.rule_id,
                    "type": rule_type,
                    "action_type": rule.action.split()[0] if rule_type == "dynamic" else None,
                    "full_condition": rule.condition,  # 保存完整条件表达式
                    "impacts": {
                        "k_codes": action_k_codes,
                        "f_codes": action_f_codes
                    }
                })

            for f_code in condition_f_codes:
                if f_code not in rules_data["indexes"]["by_trigger"]["f_codes"]:
                    rules_data["indexes"]["by_trigger"]["f_codes"][f_code] = []
                rules_data["indexes"]["by_trigger"]["f_codes"][f_code].append({
                    "rule_id": rule.rule_id,
                    "type": rule_type,
                    "action_type": rule.action.split()[0] if rule_type == "dynamic" else None,
                    "full_condition": rule.condition,
                    "impacts": {
                        "k_codes": action_k_codes,
                        "f_codes": action_f_codes
                    }
                })

            # 4. 更新影响项索引
            for k_code in action_k_codes:
                if k_code not in rules_data["indexes"]["by_impact"]["k_codes"]:
                    rules_data["indexes"]["by_impact"]["k_codes"][k_code] = []
                rules_data["indexes"]["by_impact"]["k_codes"][k_code].append({
                    "rule_id": rule.rule_id,
                    "type": rule_type,
                    "action_type": rule.action.split()[0] if rule_type == "dynamic" else None,
                    "triggers": {
                        "k_codes": condition_k_codes,
                        "f_codes": condition_f_codes,
                        "full_condition": rule.condition
                    }
                })

            for f_code in action_f_codes:
                if f_code not in rules_data["indexes"]["by_impact"]["f_codes"]:
                    rules_data["indexes"]["by_impact"]["f_codes"][f_code] = []
                rules_data["indexes"]["by_impact"]["f_codes"][f_code].append({
                    "rule_id": rule.rule_id,
                    "type": rule_type,
                    "action_type": rule.action.split()[0] if rule_type == "dynamic" else None,
                    "triggers": {
                        "k_codes": condition_k_codes,
                        "f_codes": condition_f_codes,
                        "full_condition": rule.condition
                    }
                })

            # 5. 更新动态规则类型索引
            if rule_type == "dynamic":
                condition_type = "if" if rule.condition.startswith("if") else "before"
                action_type = rule.action.split()[0]  # display/disable/choose/info
                index_key = f"{condition_type}_{action_type}"
                
                if index_key in rules_data["indexes"]["by_action_type"]:
                    rules_data["indexes"]["by_action_type"][index_key].append({
                        "rule_id": rule.rule_id,
                        "condition": {
                            "k_codes": condition_k_codes,
                            "f_codes": condition_f_codes,
                            "full_expression": rule.condition
                        },
                        "impacts": {
                            "k_codes": action_k_codes,
                            "f_codes": action_f_codes,
                            "full_expression": rule.action
                        }
                    })

        return rules_data 