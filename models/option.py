from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .feature import Feature  # 只在类型检查时导入

@dataclass
class Option:
    """选项模型类"""
    k_code: str               # 选项码 Kxx
    name: str                 # 选项名称
    value: str               # 可选值
    description: str = ""    # 说明
    feature: Optional['Feature'] = None  # 使用字符串引用
    default: bool = False    # 是否为默认选项
    multiple: bool = False   # 是否支持多选
    
    def __str__(self) -> str:
        return f"{self.k_code} {self.name} ({self.value})" 