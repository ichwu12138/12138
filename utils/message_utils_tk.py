"""
消息工具模块 (Tkinter版本)

该模块提供了显示错误、警告和信息消息的工具函数。
"""
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
import logging

from utils.language_manager import language_manager
from utils.logger import Logger

logger = Logger.get_logger(__name__)

def show_error(message_key: str, **kwargs):
    """显示错误消息
    Args:
        message_key: 消息的语言管理器键
        **kwargs: 格式化参数
            detail: 可选的详细错误信息
            error: 可选的错误信息
    """
    try:
        title = language_manager.get_text("error_title")
        # 获取翻译文本
        message = language_manager.get_text(message_key)
        
        # 如果没有找到翻译，尝试从translations中获取
        if not message or message == message_key:
            translations = {
                "missing_logic_operator": {
                    "zh": "F码或K码之间必须有逻辑操作符连接",
                    "en": "F-codes or K-codes must be connected by logical operators",
                    "de": "F-Codes oder K-Codes müssen durch logische Operatoren verbunden sein"
                },
                "k_code_operator_error": {
                    "zh": "K码后面不能使用==、!=、empty或not empty",
                    "en": "K-code cannot be followed by ==, !=, empty or not empty",
                    "de": "K-Code kann nicht von ==, !=, empty oder not empty gefolgt werden"
                },
                "invalid_k_code_for_f": {
                    "zh": "K码不属于该F码，请选择正确的K码",
                    "en": "K-code does not belong to this F-code, please select the correct K-code",
                    "de": "K-Code gehört nicht zu diesem F-Code, bitte wählen Sie den richtigen K-Code"
                },
                "parentheses_validation_save": {
                    "zh": "保存时括号必须成对出现",
                    "en": "Parentheses must be paired when saving",
                    "de": "Beim Speichern müssen Klammern paarweise auftreten"
                },
                "info_input_title": {
                    "zh": "输入信息文本",
                    "en": "Enter information text",
                    "de": "Informationstext eingeben"
                },
                "info_input_prompt": {
                    "zh": "请输入要显示的信息文本:",
                    "en": "Please enter the information text to display:",
                    "de": "Bitte geben Sie den anzuzeigenden Informationstext ein:"
                },
                "info_no_more_content": {
                    "zh": "info操作符后不能添加更多内容",
                    "en": "No more content can be added after the info operator",
                    "de": "Nach dem Info-Operator können keine weiteren Inhalte hinzugefügt werden"
                },
                "confirm": {
                    "zh": "确认",
                    "en": "Confirm",
                    "de": "Bestätigen"
                },
                "cancel": {
                    "zh": "取消",
                    "en": "Cancel",
                    "de": "Abbrechen"
                },
                "missing_brackets": {
                    "zh": "缺少方括号",
                    "en": "Missing brackets",
                    "de": "Fehlende Klammern"
                },
                "list_content_error": {
                    "zh": "方括号内容错误",
                    "en": "Invalid list content",
                    "de": "Ungültiger Listeninhalt"
                },
                "unclosed_list": {
                    "zh": "方括号未闭合",
                    "en": "Unclosed list brackets",
                    "de": "Ungeschlossene Listenklammern"
                },
                "parentheses_mismatch": {
                    "zh": "圆括号不匹配",
                    "en": "Parentheses mismatch",
                    "de": "Klammern stimmen nicht überein"
                },
                "choose_only_k_codes": {
                    "zh": "choose类型只能使用K码",
                    "en": "Choose type can only use K-codes",
                    "de": "Choose-Typ kann nur K-Codes verwenden"
                },
                "missing_info_text": {
                    "zh": "缺少信息文本",
                    "en": "Missing information text",
                    "de": "Fehlender Informationstext"
                },
                "condition_type_start_only": {
                    "zh": "条件类型只能在表达式开头使用",
                    "en": "Condition type can only be used at the beginning of expression",
                    "de": "Bedingungstyp kann nur am Anfang des Ausdrucks verwendet werden"
                },
                "missing_choose_expression": {
                    "zh": "缺少选择表达式",
                    "en": "Missing choice expression",
                    "de": "Fehlender Auswahlausdruck"
                },
                "invalid_effect_type_for_condition": {
                    "zh": "该条件类型不支持此影响类型",
                    "en": "This condition type does not support this effect type",
                    "de": "Dieser Bedingungstyp unterstützt diesen Effekttyp nicht"
                },
                "info_no_brackets": {
                    "zh": "info类型不需要方括号",
                    "en": "Info type does not need brackets",
                    "de": "Info-Typ benötigt keine Klammern"
                },
                "condition_type_invalid_next": {
                    "zh": "条件类型后面必须是逻辑表达式",
                    "en": "Condition type must be followed by logical expression",
                    "de": "Auf den Bedingungstyp muss ein logischer Ausdruck folgen"
                },
                "dynamic_logic_invalid_start": {
                    "zh": "动态逻辑必须以if或before开头",
                    "en": "Dynamic logic must start with if or before",
                    "de": "Dynamische Logik muss mit if oder before beginnen"
                },
                "before_requires_choose": {
                    "zh": "before条件必须跟choose影响类型",
                    "en": "before condition must be followed by choose effect type",
                    "de": "after Bedingung muss von choose Effekttyp gefolgt werden"
                },
                "empty_expression": {
                    "zh": "表达式不能为空",
                    "en": "Expression cannot be empty",
                    "de": "Ausdruck darf nicht leer sein"
                },
                "expression_validation_warning": {
                    "zh": "表达式验证警告",
                    "en": "Expression validation warning",
                    "de": "Ausdrucksvalidierungswarnung"
                },
                "expression_error": {
                    "zh": "表达式错误",
                    "en": "Expression error",
                    "de": "Ausdrucksfehler"
                },
                "rule_status_updated": {
                    "zh": "规则状态已更新",
                    "en": "Rule status updated",
                    "de": "Regelstatus aktualisiert"
                },
                "rule_updated_successfully": {
                    "zh": "规则更新成功",
                    "en": "Rule updated successfully",
                    "de": "Regel erfolgreich aktualisiert"
                },
                "rule_deleted_successfully": {
                    "zh": "规则删除成功",
                    "en": "Rule deleted successfully",
                    "de": "Regel erfolgreich gelöscht"
                },
                "confirm_delete_rule": {
                    "zh": "确认删除规则吗？",
                    "en": "Confirm delete rule?",
                    "de": "Regel löschen bestätigen?"
                },
                "delete_rule_error": {
                    "zh": "删除规则时出错",
                    "en": "Error deleting rule",
                    "de": "Fehler beim Löschen der Regel"
                },
                "save_rule_error": {
                    "zh": "保存规则时出错：{error}",
                    "en": "Error saving rule: {error}",
                    "de": "Fehler beim Speichern der Regel: {error}"
                },
                "log_saved_successfully": {
                    "zh": "日志保存成功",
                    "en": "Log saved successfully",
                    "de": "Protokoll erfolgreich gespeichert"
                },
                "log_save_error": {
                    "zh": "保存日志出错：{error}",
                    "en": "Error saving log: {error}",
                    "de": "Fehler beim Speichern des Protokolls: {error}"
                },
                "invalid_not_usage": {
                    "zh": "NOT只能跟在AND/OR后面",
                    "en": "NOT can only follow AND/OR",
                    "de": "NOT kann nur nach AND/OR folgen"
                },
                "static_expression_must_start_with": {
                    "zh": "静态逻辑表达式必须以F码、K码或左括号开头",
                    "en": "Static logic expression must start with F-code, K-code or left parenthesis",
                    "de": "Statischer logischer Ausdruck muss mit F-Code, K-Code oder linker Klammer beginnen"
                },
                "expression_validation_error": {
                    "zh": "表达式验证错误",
                    "en": "Expression validation error",
                    "de": "Fehler bei der Ausdrucksvalidierung"
                },
                "static_relation_needs_expression": {
                    "zh": "静态逻辑关系符号(→或:)前必须有完整的逻辑表达式",
                    "en": "Static logic relation symbols (→ or :) must be preceded by a complete logic expression",
                    "de": "Statische Logikrelationssymbole (→ oder :) müssen einem vollständigen logischen Ausdruck vorangestellt werden"
                },
                "f_code_operator_required": {
                    "zh": "F码后面必须接==、!=、empty或not empty，或使用AND/OR/XOR连接其他表达式",
                    "en": "F-code must be followed by ==, !=, empty or not empty, or connected to other expressions with AND/OR/XOR", 
                    "de": "F-Code muss von ==, !=, empty oder not empty gefolgt werden, oder mit AND/OR/XOR mit anderen Ausdrücken verbunden sein"
                },
                "f_code_empty_operator": {
                    "zh": "F码 empty和F码 not empty表达式之间必须通过AND/OR/XOR操作符连接",
                    "en": "F-code empty and F-code not empty expressions must be connected with AND/OR/XOR operators",
                    "de": "F-Code empty und F-Code not empty Ausdrücke müssen mit AND/OR/XOR Operatoren verbunden werden"
                },
                "k_code_after_operator_required": {
                    "zh": "==或!=操作符后面必须跟K码",
                    "en": "== or != operator must be followed by K-code",
                    "de": "== oder != Operator muss von K-Code gefolgt werden"
                },
                "relation_operator_position_error": {
                    "zh": "静态逻辑关系符号(→或:)不能出现在表达式开头或结尾",
                    "en": "Static logic relation symbol (→ or :) cannot appear at the beginning or end of the expression",
                    "de": "Statisches Logikrelationssymbol (→ oder :) darf nicht am Anfang oder Ende des Ausdrucks erscheinen"
                },
                "invalid_logic_operator_usage": {
                    "zh": "逻辑操作符(AND、OR、XOR)前面必须有有效的完整表达式",
                    "en": "Logic operators (AND, OR, XOR) must be preceded by a valid complete expression",
                    "de": "Logischen Operatoren (AND, OR, XOR) muss ein gültiger vollständiger Ausdruck vorangehen"
                },
                "invalid_not_usage": {
                    "zh": "NOT只能跟在AND、OR或XOR后面",
                    "en": "NOT can only follow AND, OR or XOR",
                    "de": "NOT kann nur nach AND, OR oder XOR folgen"
                },
                "invalid_k_code_for_f": {
                    "zh": "该K码不属于这个F码，请选择正确的K码",
                    "en": "This K-code does not belong to this F-code, please select the correct K-code",
                    "de": "Dieser K-Code gehört nicht zu diesem F-Code, bitte wählen Sie den richtigen K-Code"
                },
                "code_needs_operator": {
                    "zh": "F码或K码之间必须有逻辑操作符连接",
                    "en": "F-codes or K-codes must be connected by logical operators",
                    "de": "F-Codes oder K-Codes müssen durch logische Operatoren verbunden sein"
                },
                "operator_conflict_error": {
                    "zh": "==、!=、empty和not empty不能连用",
                    "en": "==, !=, empty and not empty cannot be used together",
                    "de": "==, !=, empty und not empty können nicht zusammen verwendet werden"
                },
                "static_relation_operator_duplicate": {
                    "zh": "静态逻辑关系符号(→或:)只能使用一个",
                    "en": "Only one static logic relation symbol (→ or :) can be used",
                    "de": "Nur ein statisches Logikrelationssymbol (→ oder :) kann verwendet werden"
                },
                "load_rules_success": {
                    "zh": "成功加载逻辑规则数据",
                    "en": "Logic rules data loaded successfully",
                    "de": "Logikregeldaten erfolgreich geladen"
                },
                "invalid_static_logic_format": {
                    "zh": "无效的静态逻辑格式，必须包含关系操作符(→或:)、XOR或F码的empty/not empty判断",
                    "en": "Invalid static logic format, must contain relation operator (→ or :), XOR or F-code empty/not empty check",
                    "de": "Ungültiges statisches Logikformat, muss Relationsoperator (→ oder :), XOR oder F-Code-empty/not empty-Prüfung enthalten"
                },
                "static_relation_operators_exclusive": {
                    "zh": "静态逻辑关系符号(→和:)不能同时使用",
                    "en": "Static logic relation symbols (→ and :) cannot be used together",
                    "de": "Statische Logikrelationssymbole (→ und :) können nicht zusammen verwendet werden"
                },
                "multiple_static_relation_operators": {
                    "zh": "静态逻辑关系符号(→或:)只能使用一次",
                    "en": "Static logic relation symbol (→ or :) can only be used once",
                    "de": "Statisches Logikrelationssymbol (→ oder :) kann nur einmal verwendet werden"
                },
                "relation_operator_position_error": {
                    "zh": "关系操作符不能位于表达式的开头或结尾",
                    "en": "Relation operator cannot be at the beginning or end of the expression",
                    "de": "Relationsoperator kann nicht am Anfang oder Ende des Ausdrucks stehen"
                },
                "load_temp_rules_error": {
                    "zh": "加载临时规则文件失败",
                    "en": "Failed to load temporary rules file",
                    "de": "Fehler beim Laden der temporären Regeldatei"
                },
                "load_rules_error": {
                    "zh": "加载规则数据出错：{error}",
                    "en": "Error loading rules data: {error}",
                    "de": "Fehler beim Laden der Regeldaten: {error}"
                },
                "relation_right_invalid_token": {
                    "zh": "关系操作符右侧只能包含F码、K码或逗号，发现无效的token: {token}",
                    "en": "Relation operator right side can only contain F-codes, K-codes or commas, found invalid token: {token}",
                    "de": "Die rechte Seite des Relationsoperators kann nur F-Codes, K-Codes oder Kommas enthalten, gefunden ungültiges Token: {token}"
                },
                "relation_right_empty": {
                    "zh": "关系操作符右侧必须至少包含一个F码或K码",
                    "en": "Relation operator right side must contain at least one F-code or K-code",
                    "de": "Die rechte Seite des Relationsoperators muss mindestens einen F-Code oder K-Code enthalten"
                },
                "relation_operator_invalid_next": {
                    "zh": "关系操作符后面只能跟F码、K码、逻辑操作符(AND/OR/XOR/NOT)或左括号",
                    "en": "Relation operator can only be followed by F-code, K-code, logic operators(AND/OR/XOR/NOT) or left parenthesis",
                    "de": "Auf einen Relationsoperator können nur F-Code, K-Code, logische Operatoren(AND/OR/XOR/NOT) oder eine linke Klammer folgen"
                },
                "static_relation_needs_complete_var": {
                    "zh": "关系操作符前面必须是完整的变量或右括号",
                    "en": "Relation operator must be preceded by a complete variable or right parenthesis",
                    "de": "Dem Relationsoperator muss eine vollständige Variable oder eine rechte Klammer vorangehen"
                },
                "static_relation_invalid_after_logic": {
                    "zh": "逻辑操作符(AND/OR/XOR/NOT)后面不能直接跟关系操作符",
                    "en": "Logic operator (AND/OR/XOR/NOT) cannot be directly followed by a relation operator",
                    "de": "Auf einen logischen Operator (AND/OR/XOR/NOT) kann nicht direkt ein Relationsoperator folgen"
                },
                "consecutive_codes": {
                    "zh": "F码或K码之间必须使用逻辑操作符(AND/OR/XOR)连接",
                    "en": "F-codes or K-codes must be connected with logical operators (AND/OR/XOR)",
                    "de": "F-Codes oder K-Codes müssen mit logischen Operatoren (AND/OR/XOR) verbunden werden"
                },
                "search_no_results": {
                    "zh": "未找到匹配项",
                    "en": "No matches found",
                    "de": "Keine Übereinstimmungen gefunden"
                },
                "conversion_error": {
                    "zh": "转换时出错",
                    "en": "Error during conversion",
                    "de": "Fehler bei der Konvertierung"
                },
                "not_vertical_format": {
                    "zh": "当前表达式不是竖式格式",
                    "en": "Current expression is not in vertical format",
                    "de": "Aktueller Ausdruck ist nicht im vertikalen Format"
                },
                "empty_expression": {
                    "zh": "表达式不能为空",
                    "en": "Expression cannot be empty",
                    "de": "Ausdruck darf nicht leer sein"
                }
            }
            
            # 获取当前语言
            current_lang = language_manager.get_current_language()
            
            # 尝试从备用翻译中获取
            if message_key in translations and current_lang in translations[message_key]:
                message = translations[message_key][current_lang]
            else:
                # 如果仍然没有找到，使用消息键
                message = message_key
        
        # 如果消息中包含格式化占位符，使用kwargs进行格式化
        if kwargs:
            # 检查是否有detail参数
            detail = kwargs.pop("detail", "")
            error = kwargs.pop("error", "")
            
            try:
                message = message.format(**kwargs)
                
                # 如果有detail参数，附加到消息中
                if detail:
                    message = f"{message}\n\n{detail}"
                
                # 如果有error参数，附加到消息中
                if error:
                    message = f"{message}\n\n{error}"
                    
            except (KeyError, ValueError) as e:
                logger.warning(f"格式化错误消息时出错: {message_key}, {str(e)}")
                message = message_key  # 如果格式化失败，显示消息键
        
        # 显示错误消息对话框
        messagebox.showerror(title, message)
        
    except Exception as e:
        logger.error(f"显示错误消息时出错: {str(e)}")
        # 如果出错，尝试直接显示消息键
        messagebox.showerror("Error", message_key)

def show_warning(message_key: str, **kwargs):
    """显示警告消息
    Args:
        message_key: 消息的语言管理器键
        **kwargs: 格式化参数
    """
    try:
        title = language_manager.get_text("warning_title")
        message = language_manager.get_text(message_key)
        
        # 如果没有找到翻译，尝试从translations中获取
        if not message or message == message_key:
            translations = {
                "missing_logic_operator": {
                    "zh": "F码或K码之间必须有逻辑操作符连接",
                    "en": "F-codes or K-codes must be connected by logical operators",
                    "de": "F-Codes oder K-Codes müssen durch logische Operatoren verbunden sein"
                },
                "k_code_operator_error": {
                    "zh": "K码后面不能使用==、!=、empty或not empty",
                    "en": "K-code cannot be followed by ==, !=, empty or not empty",
                    "de": "K-Code kann nicht von ==, !=, empty oder not empty gefolgt werden"
                },
                "invalid_k_code_for_f": {
                    "zh": "K码不属于该F码，请选择正确的K码",
                    "en": "K-code does not belong to this F-code, please select the correct K-code",
                    "de": "K-Code gehört nicht zu diesem F-Code, bitte wählen Sie den richtigen K-Code"
                },
                "parentheses_validation_save": {
                    "zh": "保存时括号必须成对出现",
                    "en": "Parentheses must be paired when saving",
                    "de": "Beim Speichern müssen Klammern paarweise auftreten"
                },
                "info_input_title": {
                    "zh": "输入信息文本",
                    "en": "Enter information text",
                    "de": "Informationstext eingeben"
                },
                "info_input_prompt": {
                    "zh": "请输入要显示的信息文本:",
                    "en": "Please enter the information text to display:",
                    "de": "Bitte geben Sie den anzuzeigenden Informationstext ein:"
                },
                "info_no_more_content": {
                    "zh": "info操作符后不能添加更多内容",
                    "en": "No more content can be added after the info operator",
                    "de": "Nach dem Info-Operator können keine weiteren Inhalte hinzugefügt werden"
                },
                "confirm": {
                    "zh": "确认",
                    "en": "Confirm",
                    "de": "Bestätigen"
                },
                "cancel": {
                    "zh": "取消",
                    "en": "Cancel",
                    "de": "Abbrechen"
                },
                "expression_validation_warning": {
                    "zh": "表达式验证警告",
                    "en": "Expression validation warning",
                    "de": "Ausdrucksvalidierungswarnung"
                },
                "expression_error": {
                    "zh": "表达式错误",
                    "en": "Expression error",
                    "de": "Ausdrucksfehler"
                },
                "rule_status_updated": {
                    "zh": "规则状态已更新",
                    "en": "Rule status updated",
                    "de": "Regelstatus aktualisiert"
                },
                "rule_updated_successfully": {
                    "zh": "规则更新成功",
                    "en": "Rule updated successfully",
                    "de": "Regel erfolgreich aktualisiert"
                },
                "rule_deleted_successfully": {
                    "zh": "规则删除成功",
                    "en": "Rule deleted successfully",
                    "de": "Regel erfolgreich gelöscht"
                },
                "confirm_delete_rule": {
                    "zh": "确认删除规则吗？",
                    "en": "Confirm delete rule?",
                    "de": "Regel löschen bestätigen?"
                },
                "delete_rule_error": {
                    "zh": "删除规则时出错",
                    "en": "Error deleting rule",
                    "de": "Fehler beim Löschen der Regel"
                },
                "save_rule_error": {
                    "zh": "保存规则时出错",
                    "en": "Error saving rule",
                    "de": "Fehler beim Speichern der Regel"
                }
            }
            
            # 获取当前语言
            current_lang = language_manager.get_current_language()
            
            # 尝试从备用翻译中获取
            if message_key in translations and current_lang in translations[message_key]:
                message = translations[message_key][current_lang]
            else:
                # 如果仍然没有找到，使用消息键
                message = message_key
        
        if kwargs:
            try:
                # 如果有error_message参数，使用它作为消息键
                if "error_message" in kwargs:
                    error_message = language_manager.get_text(kwargs["error_message"])
                    # 如果没有找到翻译，尝试从translations中获取
                    if not error_message or error_message == kwargs["error_message"]:
                        # 获取当前语言
                        current_lang = language_manager.get_current_language()
                        
                        # 尝试从备用翻译中获取
                        if kwargs["error_message"] in translations and current_lang in translations[kwargs["error_message"]]:
                            error_message = translations[kwargs["error_message"]][current_lang]
                        else:
                            # 如果仍然没有找到，使用消息键
                            error_message = kwargs["error_message"]
                    message = error_message
                else:
                    message = message.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"格式化警告消息时出错: {message_key}, {str(e)}")
                message = message_key  # 如果格式化失败，显示消息键
        
        # 显示警告消息对话框
        messagebox.showwarning(title, message)
        
    except Exception as e:
        logger.error(f"显示警告消息时出错: {str(e)}")
        # 如果出错，尝试直接显示消息键
        messagebox.showwarning("Warning", message_key)

def show_info(message_key: str, **kwargs):
    """显示信息消息
    Args:
        message_key: 消息的语言管理器键
        **kwargs: 格式化参数
    """
    try:
        title = language_manager.get_text("success_title")
        message = language_manager.get_text(message_key)
        
        # 如果没有找到翻译，尝试从translations中获取
        if not message or message == message_key:
            translations = {
                "rule_saved_successfully": {
                    "zh": "规则保存成功",
                    "en": "Rule saved successfully",
                    "de": "Regel erfolgreich gespeichert"
                },
                "rule_status_updated": {
                    "zh": "规则状态已更新",
                    "en": "Rule status updated",
                    "de": "Regelstatus aktualisiert"
                },
                "rule_updated_successfully": {
                    "zh": "规则更新成功",
                    "en": "Rule updated successfully",
                    "de": "Regel erfolgreich aktualisiert"
                },
                "rule_deleted_successfully": {
                    "zh": "规则删除成功",
                    "en": "Rule deleted successfully",
                    "de": "Regel erfolgreich gelöscht"
                },
                "info_input_title": {
                    "zh": "输入信息文本",
                    "en": "Enter information text",
                    "de": "Informationstext eingeben"
                },
                "info_input_prompt": {
                    "zh": "请输入要显示的信息文本:",
                    "en": "Please enter the information text to display:",
                    "de": "Bitte geben Sie den anzuzeigenden Informationstext ein:"
                },
                "info_no_more_content": {
                    "zh": "info操作符后不能添加更多内容",
                    "en": "No more content can be added after the info operator",
                    "de": "Nach dem Info-Operator können keine weiteren Inhalte hinzugefügt werden"
                },
                "confirm": {
                    "zh": "确认",
                    "en": "Confirm",
                    "de": "Bestätigen"
                },
                "cancel": {
                    "zh": "取消",
                    "en": "Cancel",
                    "de": "Abbrechen"
                }
            }
            
            # 获取当前语言
            current_lang = language_manager.get_current_language()
            
            # 尝试从备用翻译中获取
            if message_key in translations and current_lang in translations[message_key]:
                message = translations[message_key][current_lang]
            else:
                # 如果仍然没有找到，使用消息键
                message = message_key
        
        if kwargs:
            try:
                message = message.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"格式化信息消息时出错: {message_key}, {str(e)}")
                message = message_key  # 如果格式化失败，显示消息键
        
        # 显示信息消息对话框
        messagebox.showinfo(title, message)
        
    except Exception as e:
        logger.error(f"显示信息消息时出错: {str(e)}")
        # 如果出错，尝试直接显示消息键
        messagebox.showinfo("Information", message_key)

def show_confirm(message_key: str, **kwargs) -> bool:
    """显示确认对话框
    Args:
        message_key: 消息的语言管理器键
        **kwargs: 格式化参数
    Returns:
        bool: 用户是否确认
    """
    try:
        title = language_manager.get_text("confirm_title")
        message = language_manager.get_text(message_key)
        
        # 如果没有找到翻译，尝试从translations中获取
        if not message or message == message_key:
            translations = {
                "confirm_delete_rule": {
                    "zh": "确认删除规则吗？",
                    "en": "Confirm delete rule?",
                    "de": "Regel löschen bestätigen?"
                },
                "confirm": {
                    "zh": "确认",
                    "en": "Confirm",
                    "de": "Bestätigen"
                },
                "cancel": {
                    "zh": "取消",
                    "en": "Cancel",
                    "de": "Abbrechen"
                }
            }
            
            # 获取当前语言
            current_lang = language_manager.get_current_language()
            
            # 尝试从备用翻译中获取
            if message_key in translations and current_lang in translations[message_key]:
                message = translations[message_key][current_lang]
            else:
                # 如果仍然没有找到，使用消息键
                message = message_key
        
        if kwargs:
            try:
                message = message.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"格式化确认消息时出错: {message_key}, {str(e)}")
                message = message_key  # 如果格式化失败，显示消息键
        
        # 显示确认对话框
        result = messagebox.askyesno(title, message)
        
        return result
        
    except Exception as e:
        logger.error(f"显示确认消息时出错: {str(e)}")
        # 如果出错，尝试直接显示消息键
        return messagebox.askyesno("Confirm", message_key) 