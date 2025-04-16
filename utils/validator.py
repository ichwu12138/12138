"""
表达式验证器模块

该模块提供了验证表达式的功能。
"""
import re
from typing import List, Set, Tuple, Dict, Any, Optional
from utils.language_manager import language_manager
from utils.config_manager import config_manager
from utils.config_manager import LOGIC_OPERATOR_CONFIG, ACTION_TYPE_CONFIG, OPERATOR_CONFIG
import logging

logger = logging.getLogger(__name__)

class ExpressionValidator:
    """表达式验证器类"""
    
    # 定义常量
    CONDITION_TYPES = {"if", "before"}  # 动态逻辑条件类型
    BOOL_OPERATORS = {"AND", "OR", "NOT"}  # 布尔操作符（动态和静态通用）
    STATIC_OPERATORS = {"AND", "OR", "NOT", "XOR"}  # 静态逻辑操作符
    COMPARISON_OPERATORS = {"==", "!="}  # 比较操作符
    EMPTY_OPERATORS = {"empty"}  # 空值操作符，只包含"empty"
    ACTION_TYPES = {"display", "disable", "choose", "info"}  # 动态逻辑动作类型
    
    @staticmethod
    def is_f_code(token: str) -> bool:
        """检查是否为F码"""
        return bool(re.match(r'^F\d+$', token))
    
    @staticmethod
    def is_k_code(token: str) -> bool:
        """检查是否为K码"""
        # 修改正则表达式以匹配包含下划线的K码格式
        return bool(re.match(r'^K\d+(?:_\d+)*$', token))
    
    @staticmethod
    def is_bool_variable(tokens: List[str], index: int, excel_processor) -> bool:
        """检查是否为布尔变量（K码或F码相关表达式）"""
        if index >= len(tokens):
            return False
            
        token = tokens[index]
        
        # K码可以作为单独变量
        if ExpressionValidator.is_k_code(token):
            return True
            
        # F码必须和操作符组合
        if ExpressionValidator.is_f_code(token):
            if index + 1 >= len(tokens):
                return False
                
            next_token = tokens[index + 1]
            
            # F码 empty 或 F码 not empty
            if next_token == "empty":
                return True
            
            # 特殊处理F码 not empty的情况
            if next_token == "not" and index + 2 < len(tokens) and tokens[index + 2] == "empty":
                return True
                
            # F码 == K码 或 F码 != K码
            if (next_token in ExpressionValidator.COMPARISON_OPERATORS and 
                index + 2 < len(tokens) and 
                ExpressionValidator.is_k_code(tokens[index + 2])):
                # 验证K码是否属于F码
                if excel_processor and not excel_processor.is_valid_k_code_for_f_code(token, tokens[index + 2]):
                    return False
                return True
                
        return False
    
    @staticmethod
    def validate_bool_expression(
        tokens: List[str], 
        start_index: int, 
        end_index: int, 
        excel_processor,
        operators: Set[str] = None,
        skip_f_code_validation: bool = False,  # 新增参数，用于控制是否跳过F码验证
        is_saving: bool = False  # 新增is_saving参数
    ) -> Tuple[bool, str, int]:
        """验证布尔表达式"""
        logger.debug(f"验证布尔表达式: {' '.join(tokens[start_index:end_index])}")
        if start_index >= end_index:
            return True, "", start_index  # 允许空的布尔表达式
            
        # 如果没有指定操作符集合，使用默认的布尔操作符
        if operators is None:
            operators = ExpressionValidator.BOOL_OPERATORS
            
        stack = []
        i = start_index
        expect_variable = True  # 是否期望变量
        last_was_f_code_special = False  # 标记上一个处理的是否是F码特殊表达式(empty/not empty)
        f_code_not_empty_seen = False  # 标记是否已见过F码not empty表达式
        
        while i < end_index:
            token = tokens[i]
            logger.debug(f"处理token[{i}]: {token}, expect_variable={expect_variable}")
            
            # 处理NOT
            if token in operators and token == "NOT":
                if not expect_variable or (i > 0 and tokens[i-1] not in ["AND", "OR", "XOR", "(", "if", "before"]):
                    return False, "not_operator_error", i
                i += 1
                continue
                
            # 处理左括号
            if token == "(":
                if not expect_variable:
                    # 只在保存时验证括号匹配
                    if is_saving:
                        return False, "parentheses_mismatch", i
                stack.append(token)
                i += 1
                continue
                
            # 处理右括号
            if token == ")":
                if expect_variable:
                    # 只在保存时验证括号匹配
                    if is_saving:
                        return False, "parentheses_mismatch", i
                if not stack and is_saving:  # 只在保存时验证括号匹配
                    return False, "parentheses_mismatch", i
                if stack:
                    stack.pop()
                i += 1
                expect_variable = False
                continue
                
            # 处理AND/OR/XOR
            if token in operators and token != "NOT":
                if expect_variable:
                    return False, "invalid_bool_expression", i
                i += 1
                expect_variable = True
                last_was_f_code_special = False  # 重置F码特殊表达式标记
                continue
                
            # 处理变量
            if ExpressionValidator.is_bool_variable(tokens, i, excel_processor):
                if not expect_variable:
                    return False, "consecutive_codes", i
                    
                # 跳过F码的操作符和K码
                if ExpressionValidator.is_f_code(token):
                    if skip_f_code_validation:  # 如果跳过F码验证，直接跳到下一个token
                        i += 1
                        expect_variable = False
                        continue
                    else:
                        if i + 1 >= end_index:
                            return False, "f_code_operator_required", i
                        next_token = tokens[i + 1]
                        if next_token in ExpressionValidator.COMPARISON_OPERATORS:
                            if i + 2 >= end_index:
                                return False, "k_code_after_f_code", i
                            k_code = tokens[i + 2]
                            if not ExpressionValidator.is_k_code(k_code):
                                return False, "k_code_after_f_code", i
                            # 验证K码是否属于F码
                            if excel_processor and not excel_processor.is_valid_k_code_for_f_code(token, k_code):
                                return False, "invalid_k_code_for_f", i + 2
                            i += 3  # 跳过 F码、操作符和K码
                            expect_variable = False
                        elif next_token == "empty":
                            # 处理F码 empty
                            i += 2  # 跳过 F码和"empty"
                            expect_variable = False
                            last_was_f_code_special = True
                            f_code_not_empty_seen = True
                            logger.debug(f"处理F码empty: {token} empty")
                        elif next_token == "not" and i + 2 < end_index and tokens[i + 2] == "empty":
                            # 处理F码 not empty
                            i += 3  # 跳过 F码、"not"和"empty"
                            expect_variable = False
                            last_was_f_code_special = True
                            f_code_not_empty_seen = True  # 标记检测到了F码 not empty表达式
                            logger.debug(f"处理F码not empty: {token} not empty")
                        else:
                            if last_was_f_code_special:
                                # 如果上一个是F码特殊表达式，且当前也是F码，可能是缺少连接符
                                logger.debug(f"F码特殊表达式后直接跟随F码，可能缺少连接符")
                            return False, "f_code_operator_required", i
                else:  # K码
                    i += 1
                    expect_variable = False
                    
                continue
                
            # 如果是F码或K码，但不是有效的布尔变量
            if ExpressionValidator.is_f_code(token) or ExpressionValidator.is_k_code(token):
                if ExpressionValidator.is_f_code(token) and not skip_f_code_validation:
                    return False, "f_code_operator_required", i
                else:
                    i += 1  # K码是有效的布尔变量，或者跳过F码验证
                    expect_variable = False
                    continue
            
            # 如果是动作类型，直接返回
            if token in ExpressionValidator.ACTION_TYPES:
                return True, "", i
            
            return False, "invalid_bool_expression", i
            
        # 只在保存时检查括号匹配
        if stack and is_saving:
            return False, "parentheses_mismatch", i
            
        # 检查是否存在至少一个F码 empty/not empty表达式或XOR（适用于静态逻辑）
        if "XOR" in tokens[start_index:end_index] or f_code_not_empty_seen:
            return True, "", i
            
        return True, "", i
    
    @staticmethod
    def validate_list_content(content: str, is_saving: bool = False) -> Tuple[bool, str]:
        """验证列表内容（方括号内）
        
        Args:
            content: 要验证的内容
            is_saving: 是否是在保存时验证
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        logger.debug(f"=== 开始验证列表内容 ===")
        logger.debug(f"列表内容: {content}")
        logger.debug(f"是否是保存操作: {is_saving}")
        
        if not content:
            logger.debug("列表内容为空，返回有效")
            return True, ""
            
        # 分割内容，支持逗号分隔
        tokens = [t.strip() for t in content.split(',') if t.strip()]
        logger.debug(f"分割后的tokens: {tokens}")
        
        # 检查每个token是否是有效的F码或K码
        for i, token in enumerate(tokens):
            logger.debug(f"验证token[{i}]: {token}")
            
            # 尝试剔除潜在的逻辑操作符
            if token in ["AND", "OR", "XOR", "NOT"]:
                logger.debug(f"发现逻辑操作符: {token}，在列表内容中不允许")
                return False, "list_content_error"
                
            # 检查是否是F码或K码
            if not (ExpressionValidator.is_f_code(token) or ExpressionValidator.is_k_code(token)):
                logger.debug(f"Token不是F码或K码: {token}")
                
                # 提供更具体的错误信息
                if " " in token:
                    logger.debug(f"Token中包含空格，可能是复合表达式，应使用_validate_static_expression验证")
                    return False, "complex_expression_in_list"
                else:
                    logger.debug(f"无效的token: {token}")
                    return False, "list_content_error"
                
        logger.debug("列表内容验证通过")
        return True, ""
    
    @staticmethod
    def is_valid_next_token_for_f_code(token: str, f_code: str) -> bool:
        """验证F码后面的token是否合法
        Args:
            token: 当前token
            f_code: F码
        Returns:
            bool: 是否合法
        """
        # F码后面只能是==、!=、empty或not empty
        valid_operators = ["==", "!=", "empty", "not empty"]
        return token in valid_operators

    @staticmethod
    def validate_dynamic_expression(expr: str, excel_processor=None, is_saving: bool = False) -> Tuple[bool, str]:
        """验证动态表达式"""
        logger.debug(f"=== 开始验证动态表达式 ===")
        logger.debug(f"表达式: {expr}")
        logger.debug(f"是否是保存操作: {is_saving}")
        
        if not expr:
            return False, "empty_expression"
        
        # 分割表达式
        tokens = [t for t in expr.split() if t]
        
        # 检查开头必须是if或before
        if not tokens or tokens[0].lower() not in ExpressionValidator.CONDITION_TYPES:
            return False, "dynamic_logic_invalid_start"
        
        # 获取条件类型和规则
        condition_type = tokens[0].lower()
        condition_rules = config_manager.condition_rules.get(condition_type)
        
        if not condition_rules:
            return False, "invalid_condition_type"
            
        logger.debug(f"条件类型: {condition_type}")
        
        # 查找影响类型的位置
        effect_index = -1
        effect_type = None
        for i, token in enumerate(tokens):
            if token in ExpressionValidator.ACTION_TYPES:
                effect_index = i
                effect_type = token
                break
                
        # 检查影响类型是否允许
        if effect_type and effect_type not in condition_rules["allowed_actions"]:
            return False, "invalid_effect_type"
        
        # 对于before类型，必须有choose
        if condition_type == "before" and (not effect_type or effect_type != "choose"):
            if is_saving:  # 只在保存时检查
                return False, "before_requires_choose"
        
        # 确定当前模式
        current_mode = None
        if condition_type == "before" or (condition_type == "if" and not effect_type):
            current_mode = "logic_expression"
        elif condition_type == "if" and effect_type:
            current_mode = "list" if condition_rules["modes"]["list"]["active"] else "logic_expression"
            
        logger.debug(f"当前模式: {current_mode}")
        
        # 获取模式规则
        mode_rules = condition_rules["modes"][current_mode]["rules"] if condition_rules["modes"][current_mode]["active"] else None
        
        if not mode_rules:
            return False, "invalid_mode"

        # 只在保存时检查括号是否匹配
        if is_saving:
            # 检查括号是否匹配
            left_parentheses = expr.count('(')
            right_parentheses = expr.count(')')
            
            if left_parentheses != right_parentheses:
                return False, "parentheses_mismatch"
        
        # 特殊处理info类型
        if effect_type == "info":
            # 检查info后面是否有引号包裹的文本
            has_quoted_text = False
            for i in range(effect_index + 1, len(tokens)):
                if tokens[i].startswith('"') and tokens[i].endswith('"'):
                    has_quoted_text = True
                    break
            
            if not has_quoted_text and is_saving:
                return False, "missing_info_text"
            
            # 检查引号文本后是否有方括号 - 如果有，也是错误的
            for i in range(effect_index + 1, len(tokens)):
                if tokens[i] == "[":
                    return False, "info_no_brackets"
            
            # info类型验证条件部分（从条件类型后到影响类型前）
            if effect_index > 1:
                condition_tokens = tokens[1:effect_index]
                is_valid, error_msg, _ = ExpressionValidator.validate_bool_expression(
                    condition_tokens, 0, len(condition_tokens), 
                    excel_processor,
                    operators=set(mode_rules["allowed_operators"]) if mode_rules.get("require_logic_operators") else None,
                    skip_f_code_validation=False,
                    is_saving=is_saving
                )
                if not is_valid:
                    return False, error_msg
            
            # info类型不需要验证方括号
            return True, ""
        
        # 特殊处理before...choose情况
        if condition_type == "before" and effect_type == "choose":
            # 验证条件部分
            if effect_index > 1:
                condition_tokens = tokens[1:effect_index]
                is_valid, error_msg, _ = ExpressionValidator.validate_bool_expression(
                    condition_tokens, 0, len(condition_tokens), 
                    excel_processor,
                    operators=set(mode_rules["allowed_operators"]) if mode_rules.get("require_logic_operators") else None,
                    skip_f_code_validation=False,
                    is_saving=is_saving
                )
                if not is_valid:
                    return False, error_msg
            
            # 验证choose后面是否有K码
            has_k_code = False
            for i in range(effect_index + 1, len(tokens)):
                if ExpressionValidator.is_k_code(tokens[i]):
                    has_k_code = True
                    break
            
            if not has_k_code and is_saving:
                return False, "missing_choose_expression"
            
            # before...choose不需要验证方括号
            return True, ""
        
        # 在列表模式下且配置了跳过逻辑验证时，只验证基本格式，不验证F码和K码
        if current_mode == "list" and mode_rules.get("skip_logic_validation", False):
            # info类型不需要方括号
            if effect_type == "info":
                return True, ""
                
            # 只检查方括号格式和内容是否有效
            list_start = -1
            for i in range(effect_index + 1, len(tokens)):
                if tokens[i] == "[":
                    list_start = i
                    break
                    
            if list_start == -1:
                # 没有方括号
                if is_saving:  # 保存时需要完整的方括号
                    return False, "missing_brackets"
                return True, ""  # 编辑中，允许不完整的表达式
                
            # 检查方括号后的内容
            list_end = -1
            for i in range(list_start + 1, len(tokens)):
                if tokens[i] == "]":
                    list_end = i
                    break
                    
            # 检查未闭合的方括号
            if is_saving and list_end == -1:
                return False, "unclosed_list"
                
            # 方括号内容有效性检查 - 只检查是否是F码和K码，不做其他验证
            # 跳过所有验证，允许在列表中自由使用F码和K码
            return True, ""
            
        # 处理列表模式
        if current_mode == "list":
            # info类型不需要方括号
            if effect_type == "info":
                return True, ""
                
            # 验证列表内容
            list_start = -1
            list_end = -1
            
            # 查找方括号位置
            for i in range(effect_index + 1, len(tokens)):
                if tokens[i] == "[":
                    list_start = i
                    break
            
            if list_start != -1:
                for i in range(list_start + 1, len(tokens)):
                    if tokens[i] == "]":
                        list_end = i
                        break
                
                # 如果是保存操作，需要完整的列表
                if is_saving and list_end == -1:
                    return False, "unclosed_list"
                
                # 验证列表内容
                list_content = tokens[list_start + 1:list_end] if list_end != -1 else tokens[list_start + 1:]
                
                # 检查列表内容
                for item in list_content:
                    if item == ",":
                        continue
                    # 检查F码
                    if ExpressionValidator.is_f_code(item):
                        if not mode_rules["allow_f_codes"]:
                            return False, "f_codes_not_allowed"
                    # 检查K码
                    elif ExpressionValidator.is_k_code(item):
                        if not mode_rules["allow_k_codes"]:
                            return False, "k_codes_not_allowed"
                    else:
                        return False, "invalid_list_item"
                    
                    # choose模式特殊处理
                    if effect_type == "choose" and ExpressionValidator.is_f_code(item):
                        return False, "choose_only_k_codes"
            
            # 验证条件部分（从条件类型后到影响类型前）
            if effect_index > 1 and is_saving:
                condition_tokens = tokens[1:effect_index]
                is_valid, error_msg, _ = ExpressionValidator.validate_bool_expression(
                    condition_tokens, 0, len(condition_tokens), 
                    excel_processor,
                    operators=set(mode_rules["allowed_operators"]) if mode_rules.get("require_logic_operators") else None,
                    skip_f_code_validation=True,  # 在列表模式中始终跳过F码验证
                    is_saving=is_saving  # 添加is_saving参数
                )
                if not is_valid:
                    return False, error_msg
        
        # 处理逻辑表达式模式
        else:
            # 验证条件表达式部分
            if len(tokens) > 1:  # 跳过条件类型token
                end_index = effect_index if effect_index != -1 else len(tokens)
                condition_tokens = tokens[1:end_index]
                
                # 检查是否需要逻辑操作符
                if mode_rules["require_logic_operators"] and is_saving:  # 只在保存时检查
                    # 检查相邻的F码或K码
                    for i in range(len(condition_tokens) - 1):
                        current_token = condition_tokens[i]
                        next_token = condition_tokens[i + 1]
                        if (ExpressionValidator.is_f_code(current_token) or ExpressionValidator.is_k_code(current_token)) and \
                           (ExpressionValidator.is_f_code(next_token) or ExpressionValidator.is_k_code(next_token)):
                            return False, "missing_logic_operator"
                
                # 验证布尔表达式 - 只在保存时进行完整验证
                is_valid, error_msg, _ = ExpressionValidator.validate_bool_expression(
                    condition_tokens, 0, len(condition_tokens), 
                    excel_processor,
                    operators=set(mode_rules["allowed_operators"]) if mode_rules.get("require_logic_operators") else None,
                    skip_f_code_validation=mode_rules.get("skip_f_code_validation", False),  # 根据模式规则决定是否跳过F码验证
                    is_saving=is_saving  # 添加is_saving参数
                )
                if not is_valid:
                    return False, error_msg
        
        return True, ""
    
    @staticmethod
    def validate_static_expression(expr: str, excel_processor=None, is_relation_right_side: bool = False) -> Tuple[bool, str]:
        """验证静态表达式
        
        Args:
            expr: 要验证的静态表达式
            excel_processor: Excel处理器，用于验证F码和K码的关系
            is_relation_right_side: 是否是关系操作符右侧的表达式，如果是，则不要求包含XOR或F码empty/not empty
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        logger.debug(f"开始验证静态表达式: {expr}, is_relation_right_side={is_relation_right_side}")
        
        if not expr:
            logger.debug("表达式为空，验证失败")
            return False, "表达式不能为空"
            
        # 分割表达式
        tokens = [t for t in re.split(r'[\s]+', expr) if t]
        logger.debug(f"分割后的tokens: {tokens}")
        
        # 检查表达式是否以F码、K码或左括号开头
        if not tokens:
            logger.debug("分割后tokens为空，验证失败")
            return False, "表达式不能为空"
        
        first_token = tokens[0]
        if not (ExpressionValidator.is_f_code(first_token) or 
                ExpressionValidator.is_k_code(first_token) or 
                first_token == "("):
            logger.debug(f"表达式首token '{first_token}'不是F码、K码或左括号，验证失败")
            return False, "静态逻辑表达式必须以F码、K码或左括号开头"
        
        # 检查是否包含关系操作符(→或:)
        relation_operators = ["→", ":"]
        relation_index = -1
        for i, token in enumerate(tokens):
            if token in relation_operators:
                relation_index = i
                logger.debug(f"在位置{i}发现关系操作符: {token}")
                break
        
        # 如果有关系操作符，分别验证两边的表达式
        if relation_index != -1:
            logger.debug(f"表达式包含关系操作符，将验证两边的表达式")
            # 验证左侧表达式(条件部分)
            if relation_index == 0:
                logger.debug("关系操作符在首位，验证失败")
                return False, "关系操作符前必须有完整的表达式"
            
            left_tokens = tokens[:relation_index]
            logger.debug(f"左侧tokens: {left_tokens}")
            is_valid_left, error_msg_left, _ = ExpressionValidator.validate_bool_expression(
                left_tokens, 0, len(left_tokens), excel_processor, 
                operators=ExpressionValidator.STATIC_OPERATORS  # 使用静态逻辑的操作符集
            )
            
            if not is_valid_left:
                logger.debug(f"左侧表达式验证失败: {error_msg_left}")
                return False, f"关系操作符左侧表达式错误: {error_msg_left}"
            
            # 验证右侧表达式(结果部分)
            if relation_index == len(tokens) - 1:
                logger.debug("关系操作符在末位，验证失败")
                return False, "关系操作符后必须有完整的表达式"
            
            right_tokens = tokens[relation_index + 1:]
            logger.debug(f"右侧tokens: {right_tokens}")
            
            # 对右侧使用与左侧相同的验证方式，允许完整的逻辑表达式
            is_valid_right, error_msg_right, _ = ExpressionValidator.validate_bool_expression(
                right_tokens, 0, len(right_tokens), excel_processor, 
                operators=ExpressionValidator.STATIC_OPERATORS  # 使用静态逻辑的操作符集
            )
            
            if not is_valid_right:
                logger.debug(f"右侧表达式验证失败: {error_msg_right}")
                return False, f"关系操作符右侧表达式错误: {error_msg_right}"
                
            # 如果有关系操作符，且两侧表达式都验证通过，则整个表达式有效
            logger.debug("表达式包含关系操作符且两侧都验证通过，表达式有效")
            return True, ""
        else:
            # 没有关系操作符的情况，检查是否是特殊情况或是关系操作符右侧
            logger.debug("表达式不包含关系操作符，检查是否是特殊情况(XOR或F码 empty/not empty)或是关系操作符右侧")
            
            # 如果是关系操作符右侧的表达式，直接验证布尔表达式语法，不要求特殊条件
            if is_relation_right_side:
                logger.debug("作为关系操作符右侧的表达式，仅验证布尔表达式语法")
                is_valid, error_msg, _ = ExpressionValidator.validate_bool_expression(
                    tokens, 0, len(tokens), excel_processor, 
                    operators=ExpressionValidator.STATIC_OPERATORS  # 使用静态逻辑的操作符集
                )
                
                if not is_valid:
                    logger.debug(f"布尔表达式验证失败: {error_msg}")
                    return False, error_msg
                
                logger.debug("作为关系操作符右侧的表达式验证通过")
                return True, ""
            
            # 检查是否包含XOR
            has_xor = "XOR" in tokens
            
            # 检查是否包含F码 empty/not empty
            has_empty_or_not_empty = False
            
            # 验证F码empty和F码not empty表达式
            i = 0
            while i < len(tokens):
                if ExpressionValidator.is_f_code(tokens[i]):
                    if i + 1 < len(tokens) and tokens[i + 1] == "empty":
                        has_empty_or_not_empty = True
                        logger.debug(f"检测到F码empty特殊情况: {tokens[i]} empty")
                        i += 2
                        continue
                    elif i + 2 < len(tokens) and tokens[i + 1] == "not" and tokens[i + 2] == "empty":
                        has_empty_or_not_empty = True
                        logger.debug(f"检测到F码not empty特殊情况: {tokens[i]} not empty")
                        i += 3
                        continue
                i += 1
            
            if has_xor:
                logger.debug("检测到XOR特殊情况")
            
            if has_empty_or_not_empty:
                logger.debug("检测到至少一个F码empty或F码not empty特殊情况")
            
            # 特殊情况检查
            if not (has_xor or has_empty_or_not_empty):
                logger.debug("没有检测到特殊情况(XOR或F码 empty/not empty)，验证失败")
                return False, "静态逻辑表达式必须包含XOR或F码 empty/not empty"
            
            # 验证布尔表达式
            logger.debug("验证布尔表达式语法")
            is_valid, error_msg, _ = ExpressionValidator.validate_bool_expression(
                tokens, 0, len(tokens), excel_processor, 
                operators=ExpressionValidator.STATIC_OPERATORS  # 使用静态逻辑的操作符集
            )
            
            if not is_valid:
                logger.debug(f"布尔表达式验证失败: {error_msg}")
                return False, error_msg
            
            logger.debug("特殊情况验证通过，表达式有效")
        
        return True, ""