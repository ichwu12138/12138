from typing import Dict, Any
from utils.observer import Observable
from utils.config_manager import config_manager

class LanguageManager(Observable):
    """语言管理器类"""
    
    def __init__(self):
        """初始化语言管理器"""
        super().__init__()
        
        # 默认语言
        self.current_language = "zh"
        
        # 加载翻译
        self._load_translations()
        
    def _load_translations(self):
        """加载翻译数据"""
        self.translations = {
            # 通用
            "app_title": {
                "zh": "ZK逻辑编辑器",
                "en": "ZK Logic Editor",
                "de": "ZK Logik-Editor"
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
            "error": {
                "zh": "错误",
                "en": "Error",
                "de": "Fehler"
            },
            "warning": {
                "zh": "警告",
                "en": "Warning",
                "de": "Warnung"
            },
            "info": {
                "zh": "信息",
                "en": "Information",
                "de": "Information"
            },
            
            # 菜单
            "menu_file": {
                "zh": "文件",
                "en": "File",
                "de": "Datei"
            },
            "menu_view": {
                "zh": "视图",
                "en": "View",
                "de": "Ansicht"
            },
            "menu_help": {
                "zh": "帮助",
                "en": "Help",
                "de": "Hilfe"
            },
            "import_config": {
                "zh": "导入配置",
                "en": "Import Config",
                "de": "Konfiguration importieren"
            },
            "import_bom": {
                "zh": "导入BOM",
                "en": "Import BOM",
                "de": "BOM importieren"
            },
            "logic_library": {
                "zh": "逻辑关系库",
                "en": "Logic Library",
                "de": "Logik-Bibliothek"
            },
            "language": {
                "zh": "语言",
                "en": "Language",
                "de": "Sprache"
            },
            "theme": {
                "zh": "主题",
                "en": "Theme",
                "de": "Thema"
            },
            "view_log": {
                "zh": "查看日志",
                "en": "View Log",
                "de": "Log anzeigen"
            },
            "about": {
                "zh": "关于",
                "en": "About",
                "de": "Über"
            },
            "exit": {
                "zh": "退出",
                "en": "Exit",
                "de": "Beenden"
            },
            
            # 面板标题
            "panels_title": {
                "zh": "ZK逻辑编辑器",
                "en": "ZK Logic Editor",
                "de": "ZK Logik-Editor"
            },
            "config_panel_title": {
                "zh": "配置选项",
                "en": "Configuration",
                "de": "Konfiguration"
            },
            "logic_panel_title": {
                "zh": "逻辑编辑",
                "en": "Logic Editor",
                "de": "Logik-Editor"
            },
            "bom_panel_title": {
                "zh": "BOM管理",
                "en": "BOM Management",
                "de": "BOM-Verwaltung"
            },
            
            # 工具栏
            "tools": {
                "zh": "工具",
                "en": "Tools",
                "de": "Werkzeuge"
            },
            "refresh": {
                "zh": "刷新",
                "en": "Refresh",
                "de": "Aktualisieren"
            },
            "clear": {
                "zh": "清除",
                "en": "Clear",
                "de": "Löschen"
            },
            "save": {
                "zh": "保存",
                "en": "Save",
                "de": "Speichern"
            },
            
            # 逻辑编辑
            "logic_operators": {
                "zh": "逻辑操作符",
                "en": "Logic Operators",
                "de": "Logische Operatoren"
            },
            "brackets": {
                "zh": "括号",
                "en": "Brackets",
                "de": "Klammern"
            },
            "rule_status": {
                "zh": "规则状态",
                "en": "Rule Status",
                "de": "Regel-Status"
            },
            "enabled": {
                "zh": "启用",
                "en": "Enabled",
                "de": "Aktiviert"
            },
            "disabled": {
                "zh": "禁用",
                "en": "Disabled",
                "de": "Deaktiviert"
            },
            "testing": {
                "zh": "测试",
                "en": "Testing",
                "de": "Test"
            },
            "expression": {
                "zh": "表达式",
                "en": "Expression",
                "de": "Ausdruck"
            },
            "saved_rules": {
                "zh": "已保存规则",
                "en": "Saved Rules",
                "de": "Gespeicherte Regeln"
            },
            
            # 树状视图
            "config_tree": {
                "zh": "配置树",
                "en": "Config Tree",
                "de": "Konfigurations-Baum"
            },
            "bom_tree": {
                "zh": "BOM树",
                "en": "BOM Tree",
                "de": "BOM-Baum"
            },
            
            # 逻辑关系库
            "search": {
                "zh": "搜索",
                "en": "Search",
                "de": "Suche"
            },
            "rules": {
                "zh": "规则",
                "en": "Rules",
                "de": "Regeln"
            },
            "rule_id": {
                "zh": "规则ID",
                "en": "Rule ID",
                "de": "Regel-ID"
            },
            "rule_type": {
                "zh": "规则类型",
                "en": "Rule Type",
                "de": "Regel-Typ"
            },
            "condition": {
                "zh": "条件",
                "en": "Condition",
                "de": "Bedingung"
            },
            "action": {
                "zh": "动作",
                "en": "Action",
                "de": "Aktion"
            },
            "status": {
                "zh": "状态",
                "en": "Status",
                "de": "Status"
            },
            
            # 主题
            "light_theme": {
                "zh": "浅色主题",
                "en": "Light Theme",
                "de": "Helles Thema"
            },
            "dark_theme": {
                "zh": "深色主题",
                "en": "Dark Theme",
                "de": "Dunkles Thema"
            },
            
            # 状态栏
            "ready": {
                "zh": "就绪",
                "en": "Ready",
                "de": "Bereit"
            },
            
            # 操作提示
            "copy_code": {
                "zh": "复制代码",
                "en": "Copy Code",
                "de": "Code kopieren"
            },
            "copy_item": {
                "zh": "复制项目",
                "en": "Copy Item",
                "de": "Element kopieren"
            },
            "edit": {
                "zh": "编辑",
                "en": "Edit",
                "de": "Bearbeiten"
            },
            "delete": {
                "zh": "删除",
                "en": "Delete",
                "de": "Löschen"
            },
            
            # 文件选择
            "select_excel_file": {
                "zh": "选择Excel文件",
                "en": "Select Excel File",
                "de": "Excel-Datei auswählen"
            },
            "select_bom_file": {
                "zh": "选择BOM文件",
                "en": "Select BOM File",
                "de": "BOM-Datei auswählen"
            },
            "excel_files": {
                "zh": "Excel文件",
                "en": "Excel Files",
                "de": "Excel-Dateien"
            },
            "all_files": {
                "zh": "所有文件",
                "en": "All Files",
                "de": "Alle Dateien"
            },
            
            # 消息
            "confirm_exit": {
                "zh": "确认退出",
                "en": "Confirm Exit",
                "de": "Beenden bestätigen"
            },
            "confirm_exit_message": {
                "zh": "确定要退出程序吗？",
                "en": "Are you sure you want to exit?",
                "de": "Möchten Sie das Programm wirklich beenden?"
            },
            "excel_imported_successfully": {
                "zh": "Excel文件导入成功",
                "en": "Excel file imported successfully",
                "de": "Excel-Datei erfolgreich importiert"
            },
            "bom_imported_successfully": {
                "zh": "BOM文件导入成功",
                "en": "BOM file imported successfully",
                "de": "BOM-Datei erfolgreich importiert"
            },
            "excel_import_error": {
                "zh": "导入Excel文件失败",
                "en": "Failed to import Excel file",
                "de": "Fehler beim Importieren der Excel-Datei"
            },
            "bom_import_error": {
                "zh": "导入BOM文件失败",
                "en": "Failed to import BOM file",
                "de": "Fehler beim Importieren der BOM-Datei"
            },
            "refresh_tree_error": {
                "zh": "刷新树状图失败",
                "en": "Failed to refresh tree",
                "de": "Fehler beim Aktualisieren des Baums"
            },
            "open_log_error": {
                "zh": "打开日志文件失败",
                "en": "Failed to open log file",
                "de": "Fehler beim Öffnen der Log-Datei"
            },
            
            # 主题对话框
            "theme_dialog_title": {
                "zh": "选择主题",
                "en": "Select Theme",
                "de": "Thema auswählen"
            },
            "theme_dialog_header": {
                "zh": "请选择主题",
                "en": "Please select a theme",
                "de": "Bitte wählen Sie ein Thema"
            },
            "light_theme": {
                "zh": "浅色主题",
                "en": "Light Theme",
                "de": "Helles Thema"
            },
            "dark_theme": {
                "zh": "深色主题",
                "en": "Dark Theme",
                "de": "Dunkles Thema"
            },
        }
    
    def set_language(self, lang_code: str) -> None:
        """设置当前语言
        
        Args:
            lang_code: 语言代码
        """
        if lang_code in ["zh", "en", "de"]:
            self.current_language = lang_code
            config_manager.set_app_config("language", lang_code)
            self.notify_observers(lang_code)
    
    def get_text(self, key: str) -> str:
        """获取指定键的翻译文本
        
        Args:
            key: 翻译键
            
        Returns:
            str: 翻译文本
        """
        if key in self.translations:
            return self.translations[key].get(self.current_language, key)
        return key
    
    def get_current_language(self) -> str:
        """获取当前语言代码
        
        Returns:
            str: 当前语言代码
        """
        return self.current_language

# 创建全局语言管理器实例
language_manager = LanguageManager()