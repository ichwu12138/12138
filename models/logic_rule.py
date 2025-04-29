from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from utils.config_manager import RULE_STATUS_CONFIG

class RuleStatus(Enum):
    """规则状态"""
    ENABLED = RULE_STATUS_CONFIG["enabled"]
    DISABLED = RULE_STATUS_CONFIG["disabled"]
    TESTING = RULE_STATUS_CONFIG["testing"]

@dataclass
class LogicRule:
    """逻辑规则模型类"""
    rule_id: str                      # 逻辑ID Lxx
    condition: str                   # 选择项表达式
    action: str                      # 影响项表达式
    relation: str                    # 逻辑关系
    status: RuleStatus = RuleStatus.ENABLED
    tags: str = ""                   # 标签字符串
    tech_doc_path: str = ""          # 技术文档路径
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    is_editable: bool = True

    def __post_init__(self):
        """初始化后的处理"""
        # 确保 tags 是字符串类型
        if self.tags is None:
            self.tags = ""
        elif not isinstance(self.tags, str):
            self.tags = str(self.tags)
    
    @property
    def condition_expr(self) -> str:
        """选择项表达式属性"""
        return self.condition
    
    @property
    def effect_expr(self) -> str:
        """影响项表达式属性"""
        if self.relation in ["→", ":"]:
            return f"{self.relation} {self.action}"
        return self.action
    
    def update_status(self, new_status: RuleStatus) -> None:
        """更新规则状态"""
        self.status = new_status
        self.modified_at = datetime.now()
    
    def update_tags(self, new_tags: str):
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
            "tags": self.tags,  # 直接使用标签字符串
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
            # 处理tags字段 - 保持原始字符串格式
            tags = data.get('tags', '')
            if not isinstance(tags, str):
                tags = str(tags) if tags is not None else ""
            
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
                condition=condition,
                action=action,
                relation=relation,
                status=RuleStatus.ENABLED,  # 默认为启用状态
                tags=tags,
                tech_doc_path=tech_doc_path
            )
            
        except Exception as e:
            raise ValueError(f"创建规则实例失败: {str(e)}, 数据: {data}") 