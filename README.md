# ZKBom逻辑编辑器

ZKBom逻辑编辑器是一个专业的配置管理工具，用于构建和管理ZK系统的BOM逻辑规则。它提供了三栏式的图形界面，支持配置选项和BOM文件的关联管理，以及逻辑规则的创建和维护。

## 核心功能

### 1. 三栏式界面
- **左侧配置面板**
  - 加载配置选项Excel文件
  - 树形结构展示配置数据
  - F码和K码关联显示
  
- **中央逻辑编辑区**
  - 静态逻辑规则编辑
  - 支持关系操作符（→, :）
  - 支持 AND、OR、NOT、XOR 逻辑操作符
  - F码和K码关联验证
  
- **右侧BOM面板**
  - 加载BOM文件
  - 树形结构展示BOM数据
  - 与配置选项联动

### 2. 逻辑关系库
- **独立窗口展示**
  - 通过菜单栏访问
  - 查看所有保存的逻辑规则
  - 规则状态管理
  - 规则导入导出

### 3. 数据处理
- **双重Excel处理**
  - 配置选项文件处理
  - BOM文件处理
  - 自动解析F码和K码
  
- **规则数据管理**
  - 规则保存和加载
  - 规则验证
  - 规则导出

### 4. 系统功能
- **多语言支持**
  - 中文（简体）
  - 英文
  - 德文
  
- **日志系统**
  - 详细的操作日志
  - 错误追踪和诊断
  - 日志文件管理

## 技术规格

### 系统要求
- Python 3.8+
- Windows 10/11（主要支持平台）
- 显示器：建议1920x1080或更高分辨率

### 依赖项
```bash
pandas>=1.3.0         # 数据处理
ttkbootstrap>=1.10.0  # UI框架
openpyxl==3.1.2      # Excel处理
Pillow>=9.0.0        # 图像处理
python-dateutil>=2.8.2  # 日期时间处理
pytz>=2021.1         # 时区支持
typing-extensions>=4.0.0  # 类型提示扩展
pathlib>=1.0.1       # 路径处理
```

## 项目结构

```
ZKBom_LogicEditor/
├── app_tk.py              # 应用程序入口
├── core/                  # 核心功能模块
│   ├── excel_processor.py # Excel数据处理
│   ├── bom_processor.py   # BOM文件处理
│   └── logic_builder.py   # 逻辑规则构建
├── gui/                   # 图形界面模块
│   ├── main_window_tk.py  # 主窗口
│   ├── config_panel.py    # 配置选项面板
│   ├── logic_panel.py     # 逻辑编辑面板
│   ├── bom_panel.py       # BOM文件面板
│   ├── logic_library.py   # 逻辑关系库窗口
│   ├── edit_rule_dialog_tk.py  # 规则编辑对话框
│   ├── language_dialog_tk.py   # 语言选择对话框
│   └── theme_dialog_tk.py      # 主题选择对话框
├── utils/                 # 工具模块
│   ├── check_data_dir.py  # 数据目录检查
│   ├── config_manager.py  # 配置管理
│   ├── language_manager.py # 语言管理
│   ├── logger.py         # 日志管理
│   ├── message_utils_tk.py # 消息工具
│   ├── observer.py       # 观察者模式
│   ├── rule_exporter.py  # 规则导出
│   ├── theme_manager_tk.py # 主题管理
│   └── validator.py      # 表达式验证
├── data/                  # 数据目录
│   ├── app_config.json   # 应用配置
│   └── temp_rules_latest.json # 临时规则数据
└── tech_docs/            # 技术文档目录

## 使用说明

### 启动程序
```bash
python app_tk.py
```

### 基本操作流程
1. 选择界面语言（中/英/德）
2. 加载配置选项Excel文件（左侧面板）
3. 加载BOM文件（右侧面板）
4. 创建/编辑逻辑规则（中间面板）
5. 通过菜单栏访问逻辑关系库

### 数据文件格式
1. **配置选项Excel文件**
   - 选项ID/OptionsID(K-nummer)
   - 特征/Merkmale (F-nummer)
   - 默认值/Standardwert
   - 多选/Mehrfachauswahl
   - 可选项/wählbare Option
   - 说明/Anmerkung

2. **BOM文件格式**
   - [具体格式待定]

### 逻辑规则创建
- 使用静态逻辑规则格式
- 支持关系操作符（→/:）
- 支持逻辑操作符（AND/OR/NOT/XOR）
- 支持F码和K码验证

## 注意事项

1. **数据备份**
   - 定期导出规则数据
   - 保存重要的Excel配置
   - 备份BOM文件

2. **性能考虑**
   - 大型Excel文件导入可能较慢
   - 规则验证在实时编辑时进行
   - 日志文件会定期清理

3. **已知限制**
   - 主要支持Windows平台
   - 需要1920x1080以上分辨率获得最佳体验
   - 单个规则文件大小限制为10MB

## 技术支持

如遇到问题，请检查：
1. Python版本是否符合要求
2. 依赖包是否完整安装
3. 日志文件中的错误信息
4. 数据文件格式是否正确

## 项目结构

```
ZKBom_LogicEditor/
├── app_tk.py              # 应用程序入口
├── core/                  # 核心功能模块
│   ├── excel_processor.py # Excel数据处理
│   ├── bom_processor.py   # BOM文件处理
│   └── logic_builder.py   # 逻辑规则构建
├── gui/                   # 图形界面模块
│   ├── main_window_tk.py  # 主窗口
│   ├── config_panel.py    # 配置选项面板
│   ├── logic_panel.py     # 逻辑编辑面板
│   ├── bom_panel.py       # BOM文件面板
│   ├── logic_library.py   # 逻辑关系库窗口
│   ├── edit_rule_dialog_tk.py  # 规则编辑对话框
│   ├── language_dialog_tk.py   # 语言选择对话框
│   └── theme_dialog_tk.py      # 主题选择对话框
├── utils/                 # 工具模块
│   ├── check_data_dir.py  # 数据目录检查
│   ├── config_manager.py  # 配置管理
│   ├── language_manager.py # 语言管理
│   ├── logger.py         # 日志管理
│   ├── message_utils_tk.py # 消息工具
│   ├── observer.py       # 观察者模式
│   ├── rule_exporter.py  # 规则导出
│   ├── theme_manager_tk.py # 主题管理
│   └── validator.py      # 表达式验证
├── data/                  # 数据目录
│   ├── app_config.json   # 应用配置
│   └── temp_rules_latest.json # 临时规则数据
└── tech_docs/            # 技术文档目录
```