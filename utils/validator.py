"""
表达式验证器模块

该模块提供了验证 BOM 逻辑关系表达式的功能。
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
    
    def __init__(self, config_processor=None, bom_processor=None):
        """初始化验证器
        
        Args:
            config_processor: 配置处理器实例，用于验证K码
            bom_processor: BOM处理器实例，用于验证BOM码
        """
        self.config_processor = config_processor
        self.bom_processor = bom_processor
    
    def is_k_code(self, token: str) -> bool:
        """检查是否为K码"""
        if self.config_processor:
            return self.config_processor.is_valid_k_code(token)
        return bool(re.match(r'^K\d+(?:_\d+)*$', token))
    
    def is_bom_code(self, token: str) -> bool:
        """检查是否为BOM码"""
        if self.bom_processor:
            return self.bom_processor.is_valid_bom_code(token)
        return bool(re.match(r'^(PL-[A-Za-z0-9-]+)$', token))
    
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
            
        valid, message = ExpressionValidator.validate_logic_expression(
            effect_expr,
            config_processor,
            is_effect_side=True
        )
        if not valid:
            return False, f"影响项表达式错误: {message}"
            
        return True, ""
    
    def validate_next_token(self, current_expr: str, next_token: str) -> Tuple[bool, str]:
        """验证下一个要插入的token是否合法
        
        Args:
            current_expr: 当前表达式
            next_token: 下一个要插入的token
            
        Returns:
            Tuple[bool, str]: (是否可以插入, 错误消息)
        """
        # 如果是第一个token
        if not current_expr:
            # 第一个token必须是左括号、NOT或K码
            if next_token == "(" or next_token == "NOT" or self.is_k_code(next_token):
                return True, ""
            return False, "表达式必须以左括号、NOT或K码开始"
            
        # 分割当前表达式
        current_tokens = [t for t in current_expr.split() if t]
        if not current_tokens:
            return self.validate_next_token("", next_token)
            
        last_token = current_tokens[-1]
        has_relation = "→" in current_tokens
        
        # 根据上一个token判断下一个token是否合法
        if last_token in ["AND", "OR"]:
            # 操作符后面只能跟左括号、NOT或变量
            if next_token in ["(", "NOT"] or (has_relation and self.is_bom_code(next_token)) or (not has_relation and self.is_k_code(next_token)):
                return True, ""
            return False, "操作符后面只能跟左括号、NOT或变量"
            
        elif last_token == "NOT":
            # NOT后面只能跟左括号或变量
            if next_token == "(" or (has_relation and self.is_bom_code(next_token)) or (not has_relation and self.is_k_code(next_token)):
                return True, ""
            return False, "NOT后面只能跟左括号或变量"
            
        elif last_token == "(":
            # 左括号后面只能跟左括号、NOT或变量
            if next_token in ["(", "NOT"] or (has_relation and self.is_bom_code(next_token)) or (not has_relation and self.is_k_code(next_token)):
                return True, ""
            return False, "左括号后面只能跟左括号、NOT或变量"
            
        elif last_token == ")":
            # 右括号后面只能跟右括号、AND、OR或→
            if next_token in [")", "AND", "OR"] or (not has_relation and next_token == "→"):
                return True, ""
            return False, "右括号后面只能跟右括号、AND、OR或→"
            
        elif self.is_k_code(last_token):
            # K码后面只能跟右括号、AND、OR或→
            if next_token in [")", "AND", "OR"] or (not has_relation and next_token == "→"):
                return True, ""
            return False, "K码后面只能跟右括号、AND、OR或→"
            
        elif last_token == "→":
            # →后面只能跟左括号、NOT或BOM码
            if next_token in ["(", "NOT"] or self.is_bom_code(next_token):
                return True, ""
            return False, "→后面只能跟左括号、NOT或BOM码"
            
        elif self.is_bom_code(last_token):
            # BOM码后面只能跟右括号、AND或OR
            if next_token in [")", "AND", "OR"]:
                return True, ""
            return False, "BOM码后面只能跟右括号、AND或OR"
            
        return False, "无效的表达式状态"