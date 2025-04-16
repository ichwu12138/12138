"""
检查数据目录
"""
import os
from pathlib import Path

# 检查基本目录
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

print(f"BASE_DIR: {BASE_DIR}")
print(f"DATA_DIR: {DATA_DIR}")
print(f"LOG_DIR: {LOG_DIR}")

# 检查数据文件
print("\n检查数据文件:")
if os.path.exists(os.path.join(DATA_DIR, "app_config.json")):
    print("app_config.json 存在")
else:
    print("app_config.json 不存在")

if os.path.exists(os.path.join(DATA_DIR, "theme_config.json")):
    print("theme_config.json 存在")
else:
    print("theme_config.json 不存在") 