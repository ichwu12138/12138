"""
配置管理模块

该模块用于集中管理应用程序的所有配置项，包括：
- 常量定义
- 应用程序设置
- UI配置
- 等等
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple

# 获取应用程序根目录
BASE_DIR = Path(__file__).resolve().parent.parent
# 数据目录
DATA_DIR = os.path.join(BASE_DIR, "data")
# 配置文件路径
CONFIG_FILE = os.path.join(DATA_DIR, "app_config.json")

# 创建数据目录（如果不存在）
os.makedirs(DATA_DIR, exist_ok=True)

# 规则状态配置
RULE_STATUS_CONFIG = {
    "enabled": "enabled",
    "disabled": "disabled",
    "testing": "testing"
}

# 逻辑操作符配置
LOGIC_OPERATOR_CONFIG = {
    "and": "AND",
    "or": "OR",
    "not": "NOT"
}

# 关系符号配置
RELATION_SYMBOL_CONFIG = {
    "implication": "→"
}

# 括号配置 
BRACKET_CONFIG = {
    "left": "(",
    "right": ")"
}

# 条件类型配置
CONDITION_TYPE_CONFIG = {
    "if": "if",
    "before": "before"
}

# 动作类型配置
ACTION_TYPE_CONFIG = {
    "display": "display",
    "disable": "disable",
    "choose": "choose", 
    "info": "info"
}

# 操作符配置
OPERATOR_CONFIG = {
    "equals": "==",
    "not_equals": "!=",
    "empty": "empty",
    "not_empty": "not empty"
}

# 条件类型规则配置
CONDITION_RULES = {
    "if": {
        "allowed_actions": ["display", "disable", "choose", "info"],
        "requires_brackets": True,  # 需要方括号
        "modes": {
            "logic_expression": {
                "active": True,  # 在影响类型出现前激活
                "rules": {
                    "require_logic_operators": True,  # 需要逻辑操作符连接
                    "allowed_operators": ["AND", "OR", "NOT"],  # 允许的逻辑操作符
                    "f_code_validation": True,  # F码需要验证（==, !=, empty, not empty）
                    "k_code_validation": True,  # K码验证规则
                    "require_spaces": True  # 要求代码之间有空格
                }
            },
            "list": {
                "active": True,  # 在影响类型出现后激活
                "rules": {
                    "allow_f_codes": True,  # 列表中允许F码
                    "allow_k_codes": True,  # 列表中允许K码
                    "f_code_validation": False,  # 在列表中不验证F码
                    "k_code_validation": False,  # 在列表中不验证K码
                    "require_spaces": True,  # 要求代码之间有空格
                    "skip_logic_validation": True  # 在列表中完全跳过逻辑验证
                }
            }
        }
    },
    "before": {
        "allowed_actions": ["choose"],  # 只允许choose
        "requires_brackets": False,  # 不需要方括号
        "modes": {
            "logic_expression": {
                "active": True,  # 始终激活
                "rules": {
                    "require_logic_operators": True,  # 需要逻辑操作符连接
                    "allowed_operators": ["AND", "OR", "NOT"],  # 允许的逻辑操作符
                    "f_code_validation": True,  # F码需要验证
                    "k_code_validation": True,  # K码验证规则
                    "require_spaces": True  # 要求代码之间有空格
                }
            },
            "list": {
                "active": False  # 不使用列表模式
            }
        }
    }
}

# 默认配置
DEFAULT_APP_CONFIG = {
    "app_name": "ZK配置器",
    "version": "1.0.0",
    "language": "zh",
    "supported_languages": ["zh", "en", "de"],
    "theme": {
        "current_theme": "light",
        "light": {
            "name": "亮色主题",
            "background": "#ffffff",
            "foreground": "#000000",
            "accent": "#007bff",
            "error": "#dc3545",
            "warning": "#ffc107",
            "success": "#28a745",
            "info": "#17a2b8"
        },
        "dark": {
            "name": "暗色主题",
            "background": "#343a40",
            "foreground": "#f8f9fa",
            "accent": "#007bff",
            "error": "#dc3545",
            "warning": "#ffc107",
            "success": "#28a745",
            "info": "#17a2b8"
        }
    },
    "ui": {
        "main_window": {
            "width": 1024,
            "height": 768,
            "title": "ZK配置器"
        },
        "font": {
            "family": "Microsoft YaHei",
            "size": 10
        },
        "toolbar": {
            "icon_size": 24,
            "style": "both"
        },
        "tree_view": {
            "row_height": 24,
            "show_lines": True
        }
    },
    "log_level": "debug",
    "logging": {
        "console_enabled": True,
        "file_enabled": True,
        "detailed_format": False
    }
}

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.app_config = self._load_app_config()
        self.condition_rules = CONDITION_RULES
    
    def get_app_config(self, key: str, default: Any = None) -> Any:
        """获取应用程序配置
        
        Args:
            key: 配置键
            default: 默认值，如果配置不存在则返回默认值
            
        Returns:
            Any: 配置值
        """
        keys = key.split(".")
        value = self.app_config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def get_ui_config(self, section: str, key: str, default: Any = None) -> Any:
        """获取UI配置
        
        Args:
            section: 配置部分
            key: 配置键
            default: 默认值，如果配置不存在则返回默认值
            
        Returns:
            Any: 配置值
        """
        ui_config = self.app_config.get("ui", {})
        if section in ui_config and key in ui_config[section]:
            return ui_config[section][key]
        return default
    
    def get_rule_status(self, key: str) -> str:
        """获取规则状态
        
        Args:
            key: 规则状态键
            
        Returns:
            str: 规则状态值
        """
        return RULE_STATUS_CONFIG.get(key, key)
    
    def get_logic_operator(self, key: str) -> str:
        """获取逻辑操作符
        
        Args:
            key: 逻辑操作符键
            
        Returns:
            str: 逻辑操作符值
        """
        return LOGIC_OPERATOR_CONFIG.get(key, key)
    
    def get_condition_type(self, key: str) -> str:
        """获取条件类型
        
        Args:
            key: 条件类型键
            
        Returns:
            str: 条件类型值
        """
        return CONDITION_TYPE_CONFIG.get(key, key)
    
    def get_action_type(self, key: str) -> str:
        """获取动作类型
        
        Args:
            key: 动作类型键
            
        Returns:
            str: 动作类型值
        """
        return ACTION_TYPE_CONFIG.get(key, key)
    
    def get_relation_symbol(self, key: str) -> str:
        """获取关系符号
        
        Args:
            key: 关系符号键
            
        Returns:
            str: 关系符号值
        """
        return RELATION_SYMBOL_CONFIG.get(key, key)
    
    def get_operator(self, key: str) -> str:
        """获取操作符
        
        Args:
            key: 操作符键
            
        Returns:
            str: 操作符值
        """
        return OPERATOR_CONFIG.get(key, key)
    
    def get_bracket(self, key: str) -> str:
        """获取括号
        
        Args:
            key: 括号键
            
        Returns:
            str: 括号值
        """
        return BRACKET_CONFIG.get(key, key)
    
    def get_theme_config(self, theme_id: str = None) -> Dict[str, Any]:
        """获取主题配置
        
        Args:
            theme_id: 主题ID，如果为None则返回当前主题配置
            
        Returns:
            Dict[str, Any]: 主题配置
        """
        theme_config = self.app_config.get("theme", {})
        if theme_id is None:
            theme_id = theme_config.get("current_theme", "light")
        return theme_config.get(theme_id, {})
    
    def _load_app_config(self) -> Dict[str, Any]:
        """加载应用程序配置
        
        Returns:
            Dict[str, Any]: 配置数据
        """
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # 确保所有必需的配置项都存在
                    for key, value in DEFAULT_APP_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                # 如果配置文件不存在，使用默认配置
                self._save_app_config(DEFAULT_APP_CONFIG)
                return DEFAULT_APP_CONFIG.copy()
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            return DEFAULT_APP_CONFIG.copy()
    
    def _save_app_config(self, config: Dict[str, Any]) -> None:
        """保存应用程序配置
        
        Args:
            config: 配置数据
        """
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
    
    def set_ui_config(self, section: str, key: str, value: Any) -> None:
        """设置UI配置
        
        Args:
            section: 配置部分
            key: 配置键
            value: 配置值
        """
        if "ui" not in self.app_config:
            self.app_config["ui"] = {}
        if section not in self.app_config["ui"]:
            self.app_config["ui"][section] = {}
        self.app_config["ui"][section][key] = value
        self._save_app_config(self.app_config)
    
    def set_app_config(self, key: str, value: Any) -> None:
        """设置应用程序配置
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split(".")
        config = self.app_config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_app_config(self.app_config)

# 创建全局配置管理器实例
config_manager = ConfigManager()