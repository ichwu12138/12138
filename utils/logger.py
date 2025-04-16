"""
日志管理模块

该模块提供了一个集中的日志管理器，用于记录不同级别的日志信息，
支持输出到控制台和文件，便于调试和问题排查。
"""
import os
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union
import inspect
import traceback
import glob
import time

from utils.config_manager import config_manager, BASE_DIR

# 创建日志目录
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件最大保留数量
MAX_LOG_FILES = 10

# 日志级别映射
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# 默认日志格式
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
DETAILED_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s"

# 配置根日志记录器，避免重复日志
root_logger = logging.getLogger()
root_logger.handlers = []  # 清除所有处理器
root_logger.setLevel(logging.INFO)

# 当前日志文件路径
current_log_file = None

def cleanup_old_logs():
    """清理旧的日志文件，只保留最新的MAX_LOG_FILES个文件"""
    try:
        # 获取所有日志文件
        log_files = glob.glob(os.path.join(LOG_DIR, "*.log"))
        
        # 如果文件数量超过最大值，删除最旧的文件
        if len(log_files) > MAX_LOG_FILES:
            # 按修改时间排序
            log_files.sort(key=os.path.getmtime)
            
            # 删除最旧的文件，直到剩下MAX_LOG_FILES个
            for i in range(len(log_files) - MAX_LOG_FILES):
                try:
                    os.remove(log_files[i])
                    print(f"已删除旧日志文件: {log_files[i]}")
                except Exception as e:
                    print(f"删除日志文件时出错: {log_files[i]}, 错误: {e}")
    except Exception as e:
        print(f"清理旧日志文件时出错: {e}")

def get_new_log_filename():
    """生成新的日志文件名，基于当前时间"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"log_{timestamp}.log"

class Logger:
    """日志管理器类"""
    
    _instances: Dict[str, 'Logger'] = {}
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """初始化日志系统"""
        if cls._initialized:
            return
            
        # 配置根日志记录器
        log_level = config_manager.get_app_config("log_level", "info")
        root_logger.setLevel(LOG_LEVELS.get(log_level, logging.INFO))
        
        # 创建格式化器
        log_config = config_manager.get_app_config("logging", {})
        detailed_format = log_config.get("detailed_format", False)
        log_format = DETAILED_LOG_FORMAT if detailed_format else DEFAULT_LOG_FORMAT
        formatter = logging.Formatter(log_format)
        
        # 添加控制台处理器
        if log_config.get("console_enabled", True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        if log_config.get("file_enabled", True):
            # 清理旧日志文件
            cleanup_old_logs()
            
            # 创建新的日志文件，使用时间戳命名
            global current_log_file
            current_log_file = os.path.join(LOG_DIR, get_new_log_filename())
            
            file_handler = logging.FileHandler(current_log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # 记录首条日志，包含程序启动信息
            root_logger.info(f"程序启动，日志文件: {current_log_file}")
            
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str = None) -> 'Logger':
        """获取日志记录器实例
        
        Args:
            name: 日志记录器名称，默认为调用者的模块名
            
        Returns:
            Logger: 日志记录器实例
        """
        # 确保日志系统已初始化
        if not cls._initialized:
            cls.initialize()
            
        if name is None:
            # 获取调用者的模块名
            frame = inspect.currentframe().f_back
            module = inspect.getmodule(frame)
            name = module.__name__ if module else "root"
        
        # 如果实例已存在，则返回已有实例
        if name in cls._instances:
            return cls._instances[name]
        
        # 创建新实例
        instance = cls(name)
        cls._instances[name] = instance
        return instance
    
    @classmethod
    def get_current_log_file(cls) -> str:
        """获取当前日志文件路径
        
        Returns:
            str: 当前日志文件的路径
        """
        if not cls._initialized:
            cls.initialize()
        return current_log_file
    
    def __init__(self, name: str):
        """初始化日志记录器
        
        Args:
            name: 日志记录器名称
        """
        self.name = name
        self.logger = logging.getLogger(name)
        
        # 禁用向上传播到根日志记录器
        self.logger.propagate = False
        
        # 设置日志级别
        log_level = config_manager.get_app_config("log_level", "info")
        self.logger.setLevel(LOG_LEVELS.get(log_level, logging.INFO))
        
        # 检查是否已经添加了处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 先移除所有现有的处理器，避免重复添加
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        # 获取日志配置
        log_config = config_manager.get_app_config("logging", {})
        console_enabled = log_config.get("console_enabled", True)
        file_enabled = log_config.get("file_enabled", True)
        detailed_format = log_config.get("detailed_format", False)
        
        # 创建格式化器
        log_format = DETAILED_LOG_FORMAT if detailed_format else DEFAULT_LOG_FORMAT
        formatter = logging.Formatter(log_format)
        
        # 添加控制台处理器
        if console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 添加文件处理器
        if file_enabled and current_log_file:
            file_handler = logging.FileHandler(current_log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """记录调试级别日志
        
        Args:
            message: 日志消息
            *args: 格式化参数
            **kwargs: 关键字参数
        """
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """记录信息级别日志
        
        Args:
            message: 日志消息
            *args: 格式化参数
            **kwargs: 关键字参数
        """
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """记录警告级别日志
        
        Args:
            message: 日志消息
            *args: 格式化参数
            **kwargs: 关键字参数
        """
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, exc_info: Union[bool, Exception] = False, **kwargs):
        """记录错误级别日志
        
        Args:
            message: 日志消息
            *args: 格式化参数
            exc_info: 是否包含异常信息
            **kwargs: 关键字参数
        """
        self.logger.error(message, *args, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, *args, exc_info: Union[bool, Exception] = True, **kwargs):
        """记录严重错误级别日志
        
        Args:
            message: 日志消息
            *args: 格式化参数
            exc_info: 是否包含异常信息
            **kwargs: 关键字参数
        """
        self.logger.critical(message, *args, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """记录异常信息
        
        Args:
            message: 日志消息
            *args: 格式化参数
            **kwargs: 关键字参数
        """
        self.logger.exception(message, *args, **kwargs)

# 初始化日志系统
Logger.initialize()

# 创建全局日志记录器实例
logger = Logger.get_logger("root")