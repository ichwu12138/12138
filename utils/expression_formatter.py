"""
表达式格式化工具模块

该模块提供了逻辑表达式的横竖式转换功能，支持：
1. 横式表达式转换为竖式表达式
2. 保持括号分组的竖式格式
3. 完全展开的竖式格式
4. 支持添加K码和BOM码的描述注释
"""
import re
from typing import List, Tuple, Optional, Dict, Union
from utils.logger import Logger

class ExpressionFormatter:
    """表达式格式化器类"""
    
    def __init__(self, config_processor=None, bom_processor=None):
        """初始化格式化器
        
        Args:
            config_processor: 配置处理器实例，用于获取K码描述
            bom_processor: BOM处理器实例，用于获取BOM码描述
        """
        self.config_processor = config_processor
        self.bom_processor = bom_processor
        self.logger = Logger.get_logger(__name__)
        
    def horizontal_to_vertical(self, 
                             horizontal_expr: str, 
                             format_style: str = "grouped",
                             include_comments: bool = True) -> str:
        """将横式表达式转换为竖式表达式
        
        Args:
            horizontal_expr: 横式逻辑表达式
            format_style: 格式化样式 ("grouped" 保持分组, "expanded" 完全展开)
            include_comments: 是否包含代码描述注释
            
        Returns:
            str: 转换后的竖式表达式
            
        Examples:
            输入: "(K-200-000017 and K-200-000246) or (K-200-000250 and K-000-000020) → 1139101"
            输出（grouped）:
            K-200-000017  # Sitzplatz 2a Z-Rack Einflaschengerit
            and 
            K-200-000246  # Airbag
            or 
            K-200-000250  # Airbag
            and 
            K-000-000020  # MAN
            → 
            1139101
        """
        try:
            if not horizontal_expr or not horizontal_expr.strip():
                return ""
                
            # 分割条件和结果部分
            if "→" not in horizontal_expr:
                self.logger.warning("表达式中未找到蕴含符号 (→)")
                return horizontal_expr
                
            parts = horizontal_expr.split("→", 1)
            condition_part = parts[0].strip()
            result_part = parts[1].strip()
            
            # 转换条件部分
            vertical_condition = self._convert_condition_to_vertical(
                condition_part, format_style, include_comments
            )
            
            # 转换结果部分
            vertical_result = self._convert_result_to_vertical(
                result_part, include_comments
            )
            
            # 组合最终结果
            vertical_expr = f"{vertical_condition}\n→\n{vertical_result}"
            
            self.logger.info(f"成功转换表达式为竖式格式 ({format_style})")
            return vertical_expr
            
        except Exception as e:
            self.logger.error(f"转换表达式时出错: {str(e)}", exc_info=True)
            return horizontal_expr
            
    def _convert_condition_to_vertical(self, 
                                     condition: str, 
                                     format_style: str,
                                     include_comments: bool) -> str:
        """转换条件表达式为竖式
        
        Args:
            condition: 条件表达式
            format_style: 格式化样式
            include_comments: 是否包含注释
            
        Returns:
            str: 竖式条件表达式
        """
        if format_style == "grouped":
            return self._convert_grouped_vertical(condition, include_comments)
        elif format_style == "expanded":
            return self._convert_expanded_vertical(condition, include_comments)
        else:
            self.logger.warning(f"不支持的格式化样式: {format_style}，使用默认样式")
            return self._convert_grouped_vertical(condition, include_comments)
            
    def _convert_grouped_vertical(self, expression: str, include_comments: bool) -> str:
        """转换为保持分组的竖式格式
        
        Args:
            expression: 表达式
            include_comments: 是否包含注释
            
        Returns:
            str: 分组竖式表达式
        """
        # 解析表达式的括号分组
        groups = self._parse_parentheses_groups(expression)
        vertical_lines = []
        
        for i, group in enumerate(groups):
            if i > 0:
                vertical_lines.append("or")
                
            # 处理组内的内容
            group_lines = self._format_group_content(group, include_comments)
            vertical_lines.extend(group_lines)
            
        return "\n".join(vertical_lines)
        
    def _convert_expanded_vertical(self, expression: str, include_comments: bool) -> str:
        """转换为完全展开的竖式格式
        
        Args:
            expression: 表达式
            include_comments: 是否包含注释
            
        Returns:
            str: 完全展开的竖式表达式
        """
        # 移除所有括号，展开为最简形式
        tokens = self._tokenize_expression(expression)
        vertical_lines = []
        
        for token in tokens:
            if self._is_k_code(token):
                comment = self._get_comment(token) if include_comments else ""
                line = f"{token}{comment}"
                vertical_lines.append(line)
            elif token.upper() in ["AND", "OR", "NOT"]:
                vertical_lines.append(token.lower())
                
        return "\n".join(vertical_lines)
        
    def _parse_parentheses_groups(self, expression: str) -> List[str]:
        """解析括号分组
        
        Args:
            expression: 表达式
            
        Returns:
            List[str]: 分组列表
        """
        groups = []
        current_group = ""
        paren_count = 0
        i = 0
        
        # 移除外层空格
        expression = expression.strip()
        
        while i < len(expression):
            char = expression[i]
            
            if char == '(':
                paren_count += 1
                if paren_count == 1:
                    # 开始新分组，跳过左括号
                    i += 1
                    continue
                else:
                    # 嵌套括号，保留
                    current_group += char
                    
            elif char == ')':
                paren_count -= 1
                if paren_count == 0:
                    # 结束当前分组，保存并重置
                    if current_group.strip():
                        groups.append(current_group.strip())
                        current_group = ""
                    i += 1
                    # 跳过可能的OR连接符
                    while i < len(expression) and expression[i].isspace():
                        i += 1
                    if i < len(expression) - 1 and expression[i:i+2].upper() == "OR":
                        i += 2
                    continue
                else:
                    # 嵌套括号，保留
                    current_group += char
                    
            elif paren_count == 0:
                # 在括号外，检查是否遇到OR分隔符
                if i < len(expression) - 1 and expression[i:i+2].upper() == "OR":
                    # 如果当前有内容，保存为一个组
                    if current_group.strip():
                        groups.append(current_group.strip())
                        current_group = ""
                    i += 2
                    continue
                else:
                    current_group += char
            else:
                current_group += char
                
            i += 1
            
        # 处理没有括号的表达式或剩余内容
        if current_group.strip():
            groups.append(current_group.strip())
            
        return groups
        
    def _format_group_content(self, group_content: str, include_comments: bool) -> List[str]:
        """格式化组内容
        
        Args:
            group_content: 组内容
            include_comments: 是否包含注释
            
        Returns:
            List[str]: 格式化后的行列表
        """
        lines = []
        tokens = self._tokenize_expression(group_content)
        
        for token in tokens:
            if self._is_k_code(token):
                comment = self._get_comment(token) if include_comments else ""
                line = f"{token}{comment}"
                lines.append(line)
            elif token.upper() in ["AND", "OR", "NOT"]:
                lines.append(token.lower())
                
        return lines
        
    def _convert_result_to_vertical(self, result: str, include_comments: bool) -> str:
        """转换结果部分为竖式
        
        Args:
            result: 结果表达式
            include_comments: 是否包含注释
            
        Returns:
            str: 竖式结果表达式
        """
        result = result.strip()
        
        # 检查是否是BOM码
        if self._is_bom_code(result):
            comment = self._get_comment(result) if include_comments else ""
            return f"{result}{comment}"
        # 检查是否是微调逻辑
        elif self._is_tuning_logic(result):
            return self._format_tuning_logic(result)
        else:
            return result
            
    def _tokenize_expression(self, expression: str) -> List[str]:
        """将表达式分解为token
        
        Args:
            expression: 表达式
            
        Returns:
            List[str]: token列表
        """
        # 移除括号并分割
        expression = re.sub(r'[()]', '', expression)
        tokens = expression.split()
        return [token for token in tokens if token]
        
    def _is_k_code(self, token: str) -> bool:
        """检查是否为K码
        
        Args:
            token: 待检查的token
            
        Returns:
            bool: 是否为K码
        """
        return bool(re.match(r'^K-\d{3}-\d{6}$', token))
        
    def _is_bom_code(self, token: str) -> bool:
        """检查是否为BOM码
        
        Args:
            token: 待检查的token
            
        Returns:
            bool: 是否为BOM码
        """
        return bool(re.match(r'^\d+$', token)) or token.startswith('PL-')
        
    def _is_tuning_logic(self, text: str) -> bool:
        """检查是否为微调逻辑
        
        Args:
            text: 待检查的文本
            
        Returns:
            bool: 是否为微调逻辑
        """
        tuning_keywords = ["ON", "ADD", "FROM", "DELETE", "CHANGE QUANTITY", "CHANGE PRICE"]
        upper_text = text.upper()
        return any(keyword in upper_text for keyword in tuning_keywords)
        
    def _format_tuning_logic(self, tuning_logic: str) -> str:
        """格式化微调逻辑为竖式
        
        Args:
            tuning_logic: 微调逻辑表达式
            
        Returns:
            str: 格式化后的微调逻辑
        """
        # 微调逻辑保持原格式，但可以添加换行增强可读性
        return tuning_logic
        
    def _get_comment(self, code: str) -> str:
        """获取代码的描述注释
        
        Args:
            code: 代码
            
        Returns:
            str: 注释字符串
        """
        try:
            if self._is_k_code(code) and self.config_processor:
                description = self.config_processor.get_name(code)
                if description and description != code:
                    return f"  # {description}"
            elif self._is_bom_code(code) and self.bom_processor:
                description = self.bom_processor.get_bom_description(code)
                if description and description != code:
                    return f"  # {description}"
        except Exception as e:
            self.logger.warning(f"获取代码 {code} 的描述时出错: {str(e)}")
            
        return ""
        
    def vertical_to_horizontal(self, vertical_expr: str) -> str:
        """将竖式表达式转换为横式表达式
        
        Args:
            vertical_expr: 竖式表达式
            
        Returns:
            str: 横式表达式
        """
        try:
            lines = [line.strip() for line in vertical_expr.split('\n') if line.strip()]
            if not lines:
                return ""
                
            # 找到箭头分隔符的位置
            arrow_index = -1
            for i, line in enumerate(lines):
                if line == "→":
                    arrow_index = i
                    break
                    
            if arrow_index == -1:
                self.logger.warning("竖式表达式中未找到 → 分隔符")
                return vertical_expr
                
            # 分别处理条件部分和结果部分
            condition_lines = lines[:arrow_index]
            result_lines = lines[arrow_index + 1:]
            
            # 转换条件部分
            horizontal_condition = self._convert_vertical_condition_to_horizontal(condition_lines)
            
            # 转换结果部分
            horizontal_result = self._convert_vertical_result_to_horizontal(result_lines)
            
            return f"{horizontal_condition} → {horizontal_result}"
            
        except Exception as e:
            self.logger.error(f"转换竖式表达式时出错: {str(e)}", exc_info=True)
            return vertical_expr
            
    def _convert_vertical_condition_to_horizontal(self, condition_lines: List[str]) -> str:
        """将竖式条件转换为横式
        
        Args:
            condition_lines: 条件行列表
            
        Returns:
            str: 横式条件表达式
        """
        tokens = []
        current_group = []
        
        for line in condition_lines:
            # 移除注释
            code_part = line.split('#')[0].strip()
            
            if code_part.lower() == "or":
                # 遇到OR，结束当前组
                if current_group:
                    if len(current_group) > 1:
                        tokens.append(f"({' '.join(current_group)})")
                    else:
                        tokens.extend(current_group)
                    current_group = []
                tokens.append("or")
            elif code_part.lower() in ["and", "not"]:
                current_group.append(code_part.upper())
            elif self._is_k_code(code_part):
                current_group.append(code_part)
                
        # 处理最后一个组
        if current_group:
            if len(current_group) > 1:
                tokens.append(f"({' '.join(current_group)})")
            else:
                tokens.extend(current_group)
                
        return " ".join(tokens)
        
    def _convert_vertical_result_to_horizontal(self, result_lines: List[str]) -> str:
        """将竖式结果转换为横式
        
        Args:
            result_lines: 结果行列表
            
        Returns:
            str: 横式结果表达式
        """
        if not result_lines:
            return ""
            
        # 结果通常只有一行，或者是微调逻辑的多行
        result_parts = []
        for line in result_lines:
            # 移除注释
            code_part = line.split('#')[0].strip()
            if code_part:
                result_parts.append(code_part)
                
        return " ".join(result_parts)
        
    def format_with_descriptions(self, expression: str, format_type: str = "inline") -> str:
        """为表达式添加描述信息
        
        Args:
            expression: 原始表达式
            format_type: 格式类型 ("inline" 行内注释, "block" 块注释)
            
        Returns:
            str: 带描述的表达式
        """
        try:
            if format_type == "inline":
                return self._add_inline_descriptions(expression)
            elif format_type == "block":
                return self._add_block_descriptions(expression)
            else:
                self.logger.warning(f"不支持的格式类型: {format_type}")
                return expression
                
        except Exception as e:
            self.logger.error(f"添加描述时出错: {str(e)}", exc_info=True)
            return expression
            
    def _add_inline_descriptions(self, expression: str) -> str:
        """添加行内描述
        
        Args:
            expression: 表达式
            
        Returns:
            str: 带行内描述的表达式
        """
        # 使用正则表达式找到所有的K码和BOM码，并添加注释
        def replace_code(match):
            code = match.group(0)
            comment = self._get_comment(code)
            return f"{code}{comment}" if comment else code
            
        # 匹配K码
        pattern_k = r'K-\d{3}-\d{6}'
        expression = re.sub(pattern_k, replace_code, expression)
        
        # 匹配BOM码（数字或PL-开头）
        pattern_bom = r'\b\d+\b|PL-[A-Za-z0-9-]+'
        expression = re.sub(pattern_bom, replace_code, expression)
        
        return expression
        
    def _add_block_descriptions(self, expression: str) -> str:
        """添加块描述
        
        Args:
            expression: 表达式
            
        Returns:
            str: 带块描述的表达式
        """
        # 提取所有代码及其描述，在表达式后添加说明块
        codes_descriptions = {}
        
        # 查找K码
        k_codes = re.findall(r'K-\d{3}-\d{6}', expression)
        for code in k_codes:
            comment = self._get_comment(code)
            if comment:
                codes_descriptions[code] = comment.replace('  # ', '')
                
        # 查找BOM码
        bom_codes = re.findall(r'\b\d+\b|PL-[A-Za-z0-9-]+', expression)
        for code in bom_codes:
            comment = self._get_comment(code)
            if comment:
                codes_descriptions[code] = comment.replace('  # ', '')
                
        if codes_descriptions:
            description_block = "\n\n代码说明：\n"
            for code, desc in codes_descriptions.items():
                description_block += f"{code}: {desc}\n"
            return expression + description_block
        else:
            return expression 