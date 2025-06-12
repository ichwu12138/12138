# ZK_LogicBom_Builder

ZK_LogicBom_Builder 是一个专业的BOM逻辑规则构建工具，用于创建和管理ZK系统中BOM与配置选项之间的逻辑关系。该工具提供了直观的图形界面，支持多语言（中文、英文、德文）和主题（亮色、暗色）切换，并具有完整的逻辑验证功能。

## 主要功能

### 1. 三栏式界面布局
- **配置选项面板（左侧）**
  - 导入配置选项Excel文件（例如 `Kabinemekrmal(Test).xlsx`）。
  - 树形结构展示模块、特征码(F码/Merkmale)和特征值(K码/Merkmalwert)。
  - 双击特征值(K码)可将其插入到逻辑编辑区的表达式中。
  - 支持通过模块ID（如 `1.模块名称`）组织特征。

- **逻辑编辑面板（中间）**
  - **表达式构建区**：
    - 通过按钮添加逻辑操作符（AND, OR, NOT）、蕴含符号（→）和括号。
    - 支持从左侧配置面板和右侧BOM面板双击插入特征值 (K码) 和BOM码。
    - **微调逻辑 (Tuning Logic) 构建**：
      - `ON <BOM码> ADD <BOM码>`
      - `FROM <BOM码> DELETE <BOM码>`
      - `CHANGE QUANTITY OF <BOM码> TO <数量>`
      - `CHANGE PRICE <价格变动>` (如 `+100` 或 `-50`)
    - 实时（或尝试保存时）进行语法和语义验证。
  - **规则状态设置**：可将规则设置为启用 (enabled)、测试 (testing) 或禁用 (disabled)。
  - **已保存规则列表**：展示当前会话中已保存的规则，支持编辑和删除。

- **BOM管理面板（右侧）**
  - 导入BOM Excel文件（例如 `Bom.xlsx`）。
  - 树形结构按层级 (Auflösungsstufe) 和占位符 (Placeholder) 展示BOM结构。
  - 显示Baugruppe、Objektkurztext（名称）和Langtext（长文本描述）。
  - 双击BOM物料可将其BOM码 (格式通常为 `占位符-Baugruppe` 或仅 `Baugruppe`) 插入到逻辑编辑区的表达式中。

### 2. 逻辑规则管理
- **逻辑规则库功能 (通过菜单 "视图" -> "逻辑关系库" 访问)**
  - 独立窗口展示所有已保存的BOM逻辑和微调逻辑规则。
  - 支持对规则进行搜索（按规则ID, K码, 影响项, 标签等）。
  - **规则编辑**：修改条件表达式、影响表达式、状态。
  - **规则状态管理**：快速更改规则的启用/禁用/测试状态。
  - **规则标签管理**：为规则添加或修改逗号分隔的标签字符串。
  - **技术文档关联**：为每条规则关联一个本地技术文档（如Word文件），双击可尝试打开或重新关联。
  - 规则ID自动生成，BOM逻辑以 "BL" 开头 (如 BL01)，微调逻辑以 "TL" 开头 (如 TL01)。

- **数据导入导出**
  - **导出逻辑规则**：将当前所有规则以JSON格式导出到用户指定文件。导出后，程序内部的临时规则列表会清空。
  - **导入逻辑规则**：从用户指定的JSON文件导入规则。导入时会进行格式和内容校验。
  - **临时规则自动保存**：规则在创建或修改后会保存在 `data/temp_rules_latest.json` 文件中，程序下次启动时会提示是否加载。

### 3. 系统功能
- **多语言支持**
  - 中文（简体）
  - 英文
  - 德文
  - 启动时和运行时均可切换。

- **主题支持**
  - 浅色主题 (litera)
  - 暗色主题 (darkly)
  - 启动时选择。

- **日志系统**
  - 记录详细的操作日志和错误信息到 `logs/` 目录。
  - 日志级别可在 `data/app_config.json` 中配置。
  - 支持通过菜单 "帮助" -> "查看日志" 打开当前日志文件。

- **配置持久化**
  - 应用程序配置（如语言、主题、上次打开的文件路径）保存在 `data/app_config.json`。
  - 程序启动时会询问是否加载上次使用的配置文件、BOM文件及未导出的临时规则。

## 技术规格

### 系统要求
- Python 3.6+ (推荐3.8或更高版本以获得ttkbootstrap的最佳兼容性)
- Windows 10/11
- 最小分辨率：1024x768（推荐1920x1080或更高，以获得最佳显示效果）

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