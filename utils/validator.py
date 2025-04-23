"""
表达式验证器模块

该模块提供了验证逻辑表达式的功能。
"""
import re
from typing import List, Tuple, Optional
from utils.language_manager import language_manager
import logging

logger = logging.getLogger(__name__)

class ExpressionValidator:
    """表达式验证器类"""
    
    # 定义常量
    BOOL_OPERATORS = {"AND", "OR", "NOT"}  # 布尔操作符
    IMPLICATION_OPERATOR = "→"  # 蕴含操作符
    
    @staticmethod
    def is_k_code(token: str) -> bool:
        """检查是否为K码"""
        return bool(re.match(r'^K\d+(?:_\d+)*$', token))
    
    @staticmethod
    def is_bom_code(token: str) -> bool:
        """检查是否为BOM码"""
        return bool(re.match(r'^BOM\d+(?:_\d+)*$', token))
    
    @staticmethod
    def validate_bool_expression(
        tokens: List[str], 
        start_index: int, 
        end_index: int,
        allow_k_code: bool = True,  # 是否允许K码
        allow_bom_code: bool = True,  # 是否允许BOM码
        is_saving: bool = False  # 是否是保存操作
    ) -> Tuple[bool, str, int]:
        """验证布尔表达式
        
        Args:
            tokens: token列表
            start_index: 起始索引
            end_index: 结束索引
            allow_k_code: 是否允许K码
            allow_bom_code: 是否允许BOM码
            is_saving: 是否是保存操作
            
        Returns:
            Tuple[bool, str, int]: (是否有效, 错误消息, 结束位置)
        """
        if start_index >= end_index:
            return True, "", start_index  # 允许空的布尔表达式
            
        stack = []  # 用于检查括号匹配
        i = start_index
        expect_variable = True  # 是否期望变量
        
        while i < end_index:
            token = tokens[i]
            logger.debug(f"处理token[{i}]: {token}, expect_variable={expect_variable}")
            
            # 处理NOT
            if token == "NOT":
                if not expect_variable:
                    return False, "not_operator_error", i
                i += 1
                continue
                
            # 处理左括号
            if token == "(":
                if not expect_variable:
                    if is_saving:
                        return False, "parentheses_mismatch", i
                stack.append(token)
                i += 1
                continue
                
            # 处理右括号
            if token == ")":
                if expect_variable:
                    if is_saving:
                        return False, "parentheses_mismatch", i
                if not stack and is_saving:
                    return False, "parentheses_mismatch", i
                if stack:
                    stack.pop()
                i += 1
                expect_variable = False
                continue
                
            # 处理AND/OR
            if token in ["AND", "OR"]:
                if expect_variable:
                    return False, "invalid_bool_expression", i
                i += 1
                expect_variable = True
                continue
                
            # 处理变量(K码或BOM码)
            if ((allow_k_code and ExpressionValidator.is_k_code(token)) or 
                (allow_bom_code and ExpressionValidator.is_bom_code(token))):
                if not expect_variable:
                    return False, "consecutive_codes", i
                i += 1
                expect_variable = False
                continue
                
            # 如果遇到蕴含操作符，直接返回
            if token == ExpressionValidator.IMPLICATION_OPERATOR:
                return True, "", i
                
            return False, "invalid_bool_expression", i
            
        # 只在保存时检查括号匹配
        if stack and is_saving:
            return False, "parentheses_mismatch", i
            
        # 检查表达式是否以操作符结尾
        if expect_variable and is_saving:
            return False, "expression_ends_with_operator", i
            
        return True, "", i
    
    @staticmethod
    def validate_implication_expression(expr: str, is_saving: bool = False) -> Tuple[bool, str]:
        """验证蕴含表达式（完整的逻辑规则表达式）
        
        Args:
            expr: 要验证的表达式
            is_saving: 是否是保存操作
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        if not expr:
            return False, "empty_expression"
            
        # 分割表达式
        tokens = [t for t in expr.split() if t]
        
        # 查找蕴含操作符的位置
        implication_index = -1
        for i, token in enumerate(tokens):
            if token == ExpressionValidator.IMPLICATION_OPERATOR:
                implication_index = i
                break
                
        # 检查是否存在蕴含操作符
        if implication_index == -1:
            if is_saving:  # 只在保存时要求必须有蕴含操作符
                return False, "missing_implication_operator"
            # 在编辑过程中，验证当前输入的部分是否是有效的K码布尔表达式
            is_valid, error_msg, _ = ExpressionValidator.validate_bool_expression(
                tokens, 0, len(tokens),
                allow_k_code=True,
                allow_bom_code=False,
                is_saving=is_saving
            )
            return is_valid, error_msg
            
        # 验证左侧表达式（只允许K码）
        if implication_index == 0:
            return False, "empty_left_expression"
            
        left_tokens = tokens[:implication_index]
        is_valid_left, error_msg_left, _ = ExpressionValidator.validate_bool_expression(
            left_tokens, 0, len(left_tokens),
            allow_k_code=True,
            allow_bom_code=False,
            is_saving=is_saving
        )
        
        if not is_valid_left:
            return False, f"left_expression_error: {error_msg_left}"
            
        # 验证右侧表达式（只允许BOM码）
        if implication_index == len(tokens) - 1:
            if is_saving:  # 只在保存时要求右侧必须有表达式
                return False, "empty_right_expression"
            return True, ""  # 在编辑过程中允许不完整的表达式
            
        right_tokens = tokens[implication_index + 1:]
        is_valid_right, error_msg_right, _ = ExpressionValidator.validate_bool_expression(
            right_tokens, 0, len(right_tokens),
            allow_k_code=False,
            allow_bom_code=True,
            is_saving=is_saving
        )
        
        if not is_valid_right:
            return False, f"right_expression_error: {error_msg_right}"
            
        return True, ""
    
    @staticmethod
    def validate_next_token(current_expr: str, next_token: str) -> Tuple[bool, str]:
        """验证下一个要插入的token是否合法
        
        Args:
            current_expr: 当前表达式
            next_token: 下一个要插入的token
            
        Returns:
            Tuple[bool, str]: (是否可以插入, 错误消息)
        """
        # 如果是第一个token
        if not current_expr:
            # 第一个token必须是左括号、NOT、K码
            if next_token == "(" or next_token == "NOT" or ExpressionValidator.is_k_code(next_token):
                return True, ""
            return False, "invalid_first_token"
            
        # 分割当前表达式
        current_tokens = [t for t in current_expr.split() if t]
        if not current_tokens:
            return ExpressionValidator.validate_next_token("", next_token)
            
        last_token = current_tokens[-1]
        
        # 根据上一个token判断下一个token是否合法
        if last_token in ["AND", "OR"]:
            # 操作符后面只能跟左括号、NOT或变量
            if next_token in ["(", "NOT"] or ExpressionValidator.is_k_code(next_token):
                return True, ""
            return False, "invalid_token_after_operator"
            
        elif last_token == "NOT":
            # NOT后面只能跟左括号或变量
            if next_token == "(" or ExpressionValidator.is_k_code(next_token):
                return True, ""
            return False, "invalid_token_after_not"
            
        elif last_token == "(":
            # 左括号后面只能跟左括号、NOT或变量
            if next_token in ["(", "NOT"] or ExpressionValidator.is_k_code(next_token):
                return True, ""
            return False, "invalid_token_after_left_parenthesis"
            
        elif last_token == ")":
            # 右括号后面只能跟右括号、AND、OR或→
            if next_token in [")", "AND", "OR", "→"]:
                return True, ""
            return False, "invalid_token_after_right_parenthesis"
            
        elif ExpressionValidator.is_k_code(last_token):
            # K码后面只能跟右括号、AND、OR或→
            if next_token in [")", "AND", "OR", "→"]:
                return True, ""
            return False, "invalid_token_after_k_code"
            
        elif last_token == "→":
            # →后面只能跟左括号、NOT或BOM码
            if next_token in ["(", "NOT"] or ExpressionValidator.is_bom_code(next_token):
                return True, ""
            return False, "invalid_token_after_implication"
            
        elif ExpressionValidator.is_bom_code(last_token):
            # BOM码后面只能跟右括号、AND或OR
            if next_token in [")", "AND", "OR"]:
                return True, ""
            return False, "invalid_token_after_bom_code"
            
        return False, "invalid_expression_state"