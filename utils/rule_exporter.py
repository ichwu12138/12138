"""
规则导出器模块

该模块提供了导出逻辑规则的功能。
"""
import re
from typing import Dict, Any, List
from datetime import datetime
from models.logic_rule import LogicRule

class RuleExporter:
    """规则导出器类"""
    
    @staticmethod
    def parse_expression(expression: str) -> Dict[str, Any]:
        """解析表达式，提取K码和BOM码
        
        Args:
            expression: 要解析的表达式
            
        Returns:
            Dict[str, Any]: 包含K码和BOM码的字典
        """
        return {
            "k_codes": re.findall(r'K\d+(?:_\d+)*', expression),
            "bom_codes": re.findall(r'BOM\d+(?:_\d+)*', expression),
            "expression": expression
        }
    
    @staticmethod
    def create_rule_data(rule: LogicRule) -> Dict[str, Any]:
        """创建规则数据
        
        Args:
            rule: 逻辑规则对象
            
        Returns:
            Dict[str, Any]: 规则数据字典
        """
        # 分割表达式为左右两部分
        parts = rule.expression.split("→")
        left_expr = parts[0].strip() if parts else ""
        right_expr = parts[1].strip() if len(parts) > 1 else ""
        
        # 基本数据
        rule_data = {
            "id": rule.rule_id,
            "expression": rule.expression,
            "status": rule.status,
            "comment": rule.comment,
            "parsed": {
                "left": RuleExporter.parse_expression(left_expr),
                "right": RuleExporter.parse_expression(right_expr)
            }
        }
        
        return rule_data
    
    @staticmethod
    def export_rules(rules: List[LogicRule]) -> Dict[str, Any]:
        """导出规则到JSON格式
        
        Args:
            rules: 规则列表
            
        Returns:
            Dict[str, Any]: JSON格式的规则数据
        """
        # 创建基本结构
        rules_data = {
            "metadata": {
                "version": "1.0",
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "total_rules": len(rules)
            },
            "rules": [],
            "indexes": {
                # 按K码索引
                "by_k_code": {},  # K码 -> 规则列表
                # 按BOM码索引
                "by_bom_code": {}  # BOM码 -> 规则列表
            }
        }
        
        # 处理每个规则
        for rule in rules:
            # 创建规则数据
            rule_data = RuleExporter.create_rule_data(rule)
            rules_data["rules"].append(rule_data)
            
            # 更新K码索引
            for k_code in rule_data["parsed"]["left"]["k_codes"]:
                if k_code not in rules_data["indexes"]["by_k_code"]:
                    rules_data["indexes"]["by_k_code"][k_code] = []
                rules_data["indexes"]["by_k_code"][k_code].append({
                    "rule_id": rule.rule_id,
                    "expression": rule.expression,
                    "affects": rule_data["parsed"]["right"]["bom_codes"]
                })
            
            # 更新BOM码索引
            for bom_code in rule_data["parsed"]["right"]["bom_codes"]:
                if bom_code not in rules_data["indexes"]["by_bom_code"]:
                    rules_data["indexes"]["by_bom_code"][bom_code] = []
                rules_data["indexes"]["by_bom_code"][bom_code].append({
                    "rule_id": rule.rule_id,
                    "expression": rule.expression,
                    "triggered_by": rule_data["parsed"]["left"]["k_codes"]
                })
        
        return rules_data 