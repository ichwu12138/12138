# ZK_LogicBom_Builder

ZK_LogicBom_Builder 是一个专业的BOM逻辑规则构建工具，用于创建和管理ZK系统中BOM与配置选项之间的逻辑关系。该工具提供了直观的图形界面，支持多语言，并具有完整的逻辑验证功能。

## 主要功能

### 1. 三栏式界面布局
- **配置选项面板（左侧）**
  - 导入配置选项Excel文件
  - 树形结构展示特征码(F码)和特征值(K码)
  - 支持搜索和快速导航
  
- **逻辑编辑面板（中间）**
  - 逻辑规则编辑器
  - 实时语法验证
  - 支持AND、OR、NOT等逻辑操作符
  - 支持关系操作符(→)
  
- **BOM管理面板（右侧）**
  - 导入BOM Excel文件
  - 树形结构展示BOM层级
  - 支持占位符和BOM码关联

### 2. 逻辑规则管理
- **规则库功能**
  - 规则创建和编辑
  - 规则状态管理（启用/禁用/测试）
  - 规则标签管理
  - 技术文档关联
  
- **数据导入导出**
  - 支持JSON格式规则导出
  - 规则文件导入功能
  - 临时规则自动保存

### 3. 系统功能
- **多语言支持**
  - 中文（简体）
  - 英文
  - 德文
  
- **主题支持**
  - 浅色主题
  - 深色主题
  
- **日志系统**
  - 详细的操作日志
  - 错误追踪
  - 自动日志清理

## 技术规格

### 系统要求
- Python 3.6+
- Windows 10/11
- 最小分辨率：1024x768（推荐1920x1080）

### 主要依赖
```
pandas>=2.1.4
openpyxl>=3.1.2
ttkbootstrap>=1.10.0
PyQt6>=6.6.1
Pillow>=10.1.0
```

## 项目结构
```
ZK_LogicBom_Builder/
├── core/                   # 核心功能模块
│   ├── bom_processor.py    # BOM数据处理
│   ├── config_processor.py # 配置选项处理
│   └── logic_builder.py    # 逻辑规则构建
├── gui/                    # 图形界面模块
│   ├── bom_panel.py       # BOM管理面板
│   ├── config_panel.py    # 配置选项面板
│   ├── logic_panel.py     # 逻辑编辑面板
│   ├── logic_library_window.py  # 逻辑规则库窗口
│   ├── logic_rule_editor.py     # 规则编辑器
│   ├── language_dialog_tk.py    # 语言选择对话框
│   ├── theme_dialog_tk.py       # 主题选择对话框
│   └── main_window_tk.py        # 主窗口
├── models/                 # 数据模型
│   ├── feature.py         # 特征模型
│   ├── logic_rule.py      # 逻辑规则模型
│   └── option.py          # 选项模型
├── utils/                  # 工具模块
│   ├── config_manager.py   # 配置管理
│   ├── language_manager.py # 语言管理
│   ├── logger.py          # 日志管理
│   ├── message_utils_tk.py # 消息工具
│   ├── observer.py        # 观察者模式
│   └── validator.py       # 表达式验证
├── data/                   # 数据目录
│   ├── app_config.json    # 应用配置
│   └── temp_rules_latest.json  # 临时规则
├── logs/                   # 日志目录
├── app_tk.py              # 应用程序入口
└── README.md              # 项目说明文档

## 使用说明

### 1. 启动程序
```bash
python app_tk.py
```

### 2. 基本操作流程
1. 启动时选择界面语言和主题
2. 导入配置选项Excel文件（左侧面板）
3. 导入BOM文件（右侧面板）
4. 在中间面板创建逻辑规则
5. 使用逻辑规则库管理规则

### 3. 逻辑规则格式
- **基本格式**：`条件表达式 → 结果表达式`
- **条件表达式**：使用K码组合的逻辑表达式
- **结果表达式**：BOM码
- **支持的操作符**：
  - 逻辑：AND、OR、NOT
  - 关系：→（蕴含）
  - 括号：()用于分组

### 4. 数据文件要求
- **配置选项Excel**：
  - 工作表名必须包含数字编号
  - 必需列：特征值/Merkmalwert、特征/Merkmale等
  
- **BOM Excel**：
  - 必须包含Max-Gruppe工作表
  - 必需列：Auflösungsstufe、Placeholder等

## 注意事项

1. **数据安全**
   - 定期导出规则数据
   - 程序会自动保存临时规则
   - 重要操作有确认提示

2. **性能考虑**
   - Excel文件导入可能需要一定时间
   - 规则验证实时进行
   - 日志文件会自动清理

3. **已知限制**
   - 仅支持Windows平台
   - 规则编辑器一次只能编辑一条规则
   - 技术文档仅支持本地文件

## 错误处理

如果遇到问题：
1. 检查日志文件（logs目录）
2. 确认Excel文件格式正确
3. 验证输入的逻辑表达式
4. 确保所有必需的列都存在

## 技术支持

如需帮助，请：
1. 查看日志文件获取详细错误信息
2. 确认使用的Python版本和依赖包版本
3. 验证数据文件格式是否正确
4. 检查系统环境是否满足要求