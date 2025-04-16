from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .option import Option  # 只在类型检查时导入

@dataclass
class Feature:
    """特征模型类"""
    f_code: str                # 特征码 Fxx
    name: str                  # 特征名称
    options: List['Option'] = field(default_factory=list)  # 使用字符串引用
    default: Optional['Option'] = None  # 使用字符串引用
    multiple: bool = False     # 是否多选
    
    def add_option(self, option: 'Option') -> None:  # 使用字符串引用
        """添加选项到特征"""
        self.options.append(option)
        option.feature = self  # 建立双向关联
    
    def get_k_codes(self) -> List[str]:
        """获取所有关联的K码列表"""
        return [opt.k_code for opt in self.options]
    
    def __str__(self) -> str:
        return f"{self.f_code} {self.name}" 