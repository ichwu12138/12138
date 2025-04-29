from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from utils.config_manager import RULE_TYPE_CONFIG, RULE_STATUS_CONFIG

class RuleType(Enum):
    """规则类型"""
    STATIC = RULE_TYPE_CONFIG["static"]
    DYNAMIC = RULE_TYPE_CONFIG["dynamic"]

class RuleStatus(Enum):
    """规则状态"""
    ENABLED = RULE_STATUS_CONFIG["enabled"]
    DISABLED = RULE_STATUS_CONFIG["disabled"]
    TESTING = RULE_STATUS_CONFIG["testing"]

@dataclass
class LogicRule:
    """逻辑规则模型类"""
    rule_id: str                      # 逻辑ID Lxx
    rule_type: RuleType              # 规则类型
    condition: str                   # 选择项表达式
    action: str                      # 影响项表达式
    relation: str                    # 逻辑关系
    status: RuleStatus = RuleStatus.ENABLED
    tags: List[str] = None           # 标签列表
    tech_doc_path: str = ""          # 技术文档路径
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    is_editable: bool = True
    _effect_expr: str = None  # 添加 _effect_expr 参数，默认为 None

    def __post_init__(self):
        """初始化后的处理"""
        self.tags = self.tags or []
    
    @property
    def condition_expr(self) -> str:
        """选择项表达式属性"""
        return self.condition
    
    @property
    def effect_expr(self) -> str:
        """影响项表达式属性"""
        if self.rule_type == RuleType.STATIC and self.relation in ["→", ":"]:
            return f"{self.relation} {self.action}"
        return self.action
    
    @effect_expr.setter
    def effect_expr(self, value):
        """设置影响项表达式"""
        self._effect_expr = value
    
    def update_status(self, new_status: RuleStatus) -> None:
        """更新规则状态"""
        self.status = new_status
        self.modified_at = datetime.now()
    
    def update_tags(self, new_tags: List[str]):
        """更新标签"""
        self.tags = new_tags
    
    def update_tech_doc(self, new_path: str):
        """更新技术文档路径"""
        self.tech_doc_path = new_path
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        # 基本字段
        result = {
            "logic_id": self.rule_id,
            "tags": ",".join(self.tags) if self.tags else "",
            "tech_doc_path": self.tech_doc_path,
            "selection_expression": self.condition,
            "logic_relation": self.relation,
            "impact_expression": self.action
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogicRule':
        """从字典创建规则实例
        
        Args:
            data: 规则数据字典
            
        Returns:
            LogicRule: 规则实例
        """
        try:
            # 处理tags字段
            tags = data.get('tags', '')
            if isinstance(tags, str):
                tags = tags.split(',') if tags else []
            elif isinstance(tags, list):
                tags = tags
            else:
                tags = []
            
            # 处理技术文档路径
            tech_doc_path = data.get('tech_doc_path', '')
            
            # 处理旧格式数据
            if 'selection_expression' in data:
                condition = data.get('selection_expression', '')
                action = data.get('impact_expression', '')
                relation = data.get('logic_relation', '→')
                rule_id = data.get('logic_id', '')
            else:
                condition = data.get('condition', '')
                action = data.get('action', '')
                relation = data.get('relation', '→')
                rule_id = data.get('rule_id', '')
            
            # 创建规则实例
            return cls(
                rule_id=rule_id,
                rule_type=RuleType.STATIC,  # 默认为静态规则
                condition=condition,
                action=action,
                relation=relation,
                status=RuleStatus.ENABLED,  # 默认为启用状态
                tags=tags,
                tech_doc_path=tech_doc_path
            )
            
        except Exception as e:
            raise ValueError(f"创建规则实例失败: {str(e)}, 数据: {data}") 