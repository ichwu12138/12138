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
    comment: Dict[str, Any] = field(
        default_factory=lambda: {'text': '', 'images': {}}
    )
    _effect_expr: str = None  # 添加 _effect_expr 参数，默认为 None

    def __post_init__(self):
        """初始化后的处理"""
        # 确保comment是正确的格式
        if not isinstance(self.comment, dict):
            self.comment = {'text': str(self.comment), 'images': {}}
        elif 'images' not in self.comment:
            self.comment['images'] = {}
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
        # 确保comment是字典格式
        if not isinstance(self.comment, dict):
            self.comment = {'text': str(self.comment), 'images': {}}
        
        # 基本字段
        result = {
            "logic_id": self.rule_id,
            "tags": ",".join(self.tags),
            "tech_doc_path": self.tech_doc_path,
            "comment": self.comment  # 包含 text 和 images
        }
        
        # 根据规则类型添加不同的字段
        if self.rule_type == RuleType.STATIC:
            result.update({
                "selection_expression": self.condition,
                "logic_relation": self.relation,
                "impact_expression": self.action
            })
        else:  # 动态规则
            result.update({
                "selection_expression": self.condition,
                "logic_relation": self.relation,
                "impact_expression": self.action
            })
        
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogicRule':
        """从字典创建实例"""
        try:
            # 处理comment数据
            comment = data.get('comment', {'text': '', 'images': {}})
            comment_text = ''
            if isinstance(comment, dict):
                comment_text = comment.get('text', '')
            else:
                comment_text = str(comment)
            
            # 处理tags数据
            tags = data.get('tags', '').split(',')
            if isinstance(tags, str):
                tags = [tags]
            elif not isinstance(tags, list):
                tags = [str(tag) for tag in tags if tag]
            
            # 处理技术文档路径
            tech_doc_path = data.get('tech_doc_path', '')
            if not isinstance(tech_doc_path, str):
                tech_doc_path = str(tech_doc_path)
            
            # 获取表达式
            selection_expr = data.get('selection_expression', '')
            
            # 更智能地确定规则类型
            # 1. 如果显式指定了rule_type，使用它
            if 'rule_type' in data:
                rule_type = RuleType.DYNAMIC if data.get('rule_type') == 'dynamic' else RuleType.STATIC
            # 2. 根据选择表达式格式判断
            elif selection_expr:
                # 动态规则通常以if、when、after、before等关键词开头
                first_word = selection_expr.split(' ')[0].lower() if selection_expr else ''
                dynamic_keywords = ['if', 'when', 'after', 'before', 'on']
                rule_type = RuleType.DYNAMIC if first_word in dynamic_keywords else RuleType.STATIC
            else:
                # 默认为静态规则
                rule_type = RuleType.STATIC
            
            logic_id = data.get('logic_id', '')
            # 根据ID前缀再次确认类型（如果ID符合LD/LS格式）
            if logic_id.startswith('LD'):
                rule_type = RuleType.DYNAMIC
            elif logic_id.startswith('LS'):
                rule_type = RuleType.STATIC
            
            # 创建实例
            return cls(
                rule_id=logic_id,
                rule_type=rule_type,
                condition=selection_expr,
                action=data.get('impact_expression', ''),
                relation=data.get('logic_relation', '→'),
                status=RuleStatus.ENABLED,
                tags=tags,
                tech_doc_path=tech_doc_path,
                comment=comment_text
            )
        except Exception as e:
            raise ValueError(f"创建规则实例失败: {str(e)}, 数据: {data}") 