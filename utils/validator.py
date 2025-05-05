"""
表达式验证器模块

该模块提供了验证 BOM 逻辑关系表达式和微调逻辑关系表达式的功能。
"""
import re
from typing import List, Tuple, Optional
from utils.language_manager import language_manager
import logging

logger = logging.getLogger(__name__)

class ExpressionValidator:
    """BOM 逻辑关系表达式验证器"""
    
    # 定义常量
    OPERATORS = {"AND", "OR", "NOT"}  # 逻辑操作符
    RELATION_OPERATOR = "→"  # 关系操作符
    TUNING_KEYWORDS = {  # 微调逻辑关键字
        "ON", "ADD", "FROM", "DELETE", 
        "CHANGE QUANTITY OF", "TO", "CHANGE PRICE"
    }
    
    def __init__(self, config_processor=None, bom_processor=None):
        """初始化验证器
        
        Args:
            config_processor: 配置处理器实例，用于验证特征值
            bom_processor: BOM处理器实例，用于验证BOM码
        """
        self.config_processor = config_processor
        self.bom_processor = bom_processor
    
    def is_k_code(self, token: str) -> bool:
        """检查是否为特征值（K码）"""
        if self.config_processor:
            return self.config_processor.is_valid_k_code(token)
        return bool(re.match(r'^K-\d{3}-\d{6}$', token))
    
    def is_bom_code(self, token: str) -> bool:
        """检查是否为BOM码"""
        if self.bom_processor:
            return self.bom_processor.is_valid_bom_code(token)
        return bool(re.match(r'^(PL-[A-Za-z0-9-]+)$', token))

    @staticmethod
    def is_tuning_logic(text: str) -> bool:
        """检查是否包含微调逻辑关键字"""
        upper_text = text.upper()
        return any(keyword in upper_text for keyword in ExpressionValidator.TUNING_KEYWORDS)

    @staticmethod
    def validate_tuning_logic(expr: str) -> Tuple[bool, str]:
        """验证微调逻辑表达式
        
        Args:
            expr: 要验证的表达式
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        # 分割表达式为token
        tokens = expr.split()
        
        # 检查ON ADD格式
        if "ON" in tokens and "ADD" in tokens:
            on_idx = tokens.index("ON")
            add_idx = tokens.index("ADD")
            if add_idx <= on_idx or add_idx - on_idx != 2:
                return False, "ON ADD格式错误"
            if not tokens[on_idx + 1].isdigit() or not tokens[add_idx + 1].isdigit():
                return False, "ON ADD后必须是数字"
                
        # 检查FROM DELETE格式
        elif "FROM" in tokens and "DELETE" in tokens:
            from_idx = tokens.index("FROM")
            delete_idx = tokens.index("DELETE")
            if delete_idx <= from_idx or delete_idx - from_idx != 2:
                return False, "FROM DELETE格式错误"
            if not tokens[from_idx + 1].isdigit() or not tokens[delete_idx + 1].isdigit():
                return False, "FROM DELETE后必须是数字"
                
        # 检查CHANGE QUANTITY OF格式
        elif "CHANGE" in tokens and "QUANTITY" in tokens and "OF" in tokens and "TO" in tokens:
            try:
                of_idx = tokens.index("OF")
                to_idx = tokens.index("TO")
                if to_idx <= of_idx or to_idx - of_idx != 2:
                    return False, "CHANGE QUANTITY OF TO格式错误"
                if not tokens[of_idx + 1].isdigit() or not tokens[to_idx + 1].isdigit():
                    return False, "CHANGE QUANTITY OF和TO后必须是数字"
            except ValueError:
                return False, "CHANGE QUANTITY OF TO格式错误"
                
        # 检查CHANGE PRICE格式
        elif "CHANGE" in tokens and "PRICE" in tokens:
            price_idx = tokens.index("PRICE")
            if price_idx >= len(tokens) - 1:
                return False, "CHANGE PRICE后必须有值"
            price_value = tokens[price_idx + 1]
            if not re.match(r'^[+-]\d+$', price_value):
                return False, "CHANGE PRICE后必须是+或-开头的数字"
                
        else:
            return False, "不支持的微调逻辑格式"
            
        return True, ""
    
    @staticmethod
    def validate_logic_expression(expr: str, config_processor=None, is_effect_side: bool = False) -> Tuple[bool, str]:
        """验证BOM逻辑关系表达式
        
        Args:
            expr: 要验证的表达式
            config_processor: 配置处理器实例
            is_effect_side: 是否是影响项表达式（→右侧）
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        if not expr:
            return False, "表达式不能为空"
            
        # 分割表达式为token
        tokens = expr.split()
        
        # 检查括号匹配
        if tokens.count("(") != tokens.count(")"):
            return False, "括号不匹配"
            
        # 检查操作符
        operators = ["AND", "OR", "NOT"]
        last_token = None
        parentheses_count = 0
        
        for token in tokens:
            # 处理括号
            if token == "(":
                parentheses_count += 1
            elif token == ")":
                parentheses_count -= 1
                if parentheses_count < 0:
                    return False, "括号顺序错误"
            
            # 检查是否是有效的代码或操作符
            if token not in operators and token not in ["(", ")"]:
                if is_effect_side:
                    # 影响项表达式只允许BOM码
                    if not token.startswith("PL-"):
                        return False, f"影响项表达式只能使用BOM码: {token}"
                else:
                    # 选择项表达式只允许K码
                    if not token.startswith("K"):
                        return False, f"选择项表达式只能使用K码: {token}"
                        
                # 如果有配置处理器，验证代码是否存在
                if config_processor:
                    if token.startswith("K") and not config_processor.is_valid_k_code(token):
                        return False, f"未知的K码: {token}"
            
            # 检查操作符序列
            if token in operators:
                if not last_token and token != "NOT":
                    return False, "表达式不能以AND/OR开始"
                if last_token in operators and token != "NOT":
                    return False, "操作符不能连续使用"
                if token == "NOT" and last_token == ")":
                    return False, "NOT不能跟在右括号后面"
            elif token not in ["(", ")"]:
                if last_token and last_token not in operators and last_token not in ["(", ")"]:
                    return False, "代码之间必须有操作符"
            
            last_token = token
            
        # 检查最终的括号计数
        if parentheses_count != 0:
            return False, "括号不匹配"
            
        # 检查表达式结尾
        if last_token in operators:
            return False, "表达式不能以操作符结尾"
            
        return True, ""
    
    @staticmethod
    def validate_relation_expression(expr: str, config_processor=None) -> Tuple[bool, str]:
        """验证完整的BOM逻辑关系表达式（包含→）
        
        Args:
            expr: 要验证的表达式
            config_processor: 配置处理器实例
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        if not expr:
            return False, "表达式不能为空"
            
        # 分割表达式
        parts = expr.split("→")
        
        # 检查是否只有一个关系操作符
        if len(parts) != 2:
            return False, "表达式必须且只能包含一个→"
            
        # 验证选择项表达式（左侧）
        selection_expr = parts[0].strip()
        if not selection_expr:
            return False, "选择项表达式不能为空"
            
        valid, message = ExpressionValidator.validate_logic_expression(
            selection_expr,
            config_processor,
            is_effect_side=False
        )
        if not valid:
            return False, f"选择项表达式错误: {message}"
            
        # 验证影响项表达式（右侧）
        effect_expr = parts[1].strip()
        if not effect_expr:
            return False, "影响项表达式不能为空"
            
        # 检查是否包含微调逻辑关键字
        if ExpressionValidator.is_tuning_logic(effect_expr):
            # 验证微调逻辑表达式
            valid, message = ExpressionValidator.validate_tuning_logic(effect_expr)
            if not valid:
                return False, f"微调逻辑表达式错误: {message}"
        else:
            # 验证BOM逻辑表达式
            valid, message = ExpressionValidator.validate_logic_expression(
                effect_expr,
                config_processor,
                is_effect_side=True
            )
            if not valid:
                return False, f"影响项表达式错误: {message}"
            
        return True, ""