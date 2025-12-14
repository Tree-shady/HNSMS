#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import time
import json
import hashlib
from typing import Any, Dict, List

# 全局日志对象
logger = logging.getLogger("warefire")

def setup_logging(log_level: str = "INFO", log_path: str = None) -> None:
    """设置日志配置
    
    Args:
        log_level: 日志级别，如 "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        log_path: 日志文件路径，None表示只输出到控制台
    """
    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 设置日志级别
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 创建格式器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_path:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

def get_current_timestamp() -> int:
    """获取当前时间戳（秒）
    
    Returns:
        当前时间戳
    """
    return int(time.time())

def get_current_datetime() -> str:
    """获取当前日期时间字符串
    
    Returns:
        日期时间字符串，格式：YYYY-MM-DD HH:MM:SS
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法，如 "md5", "sha1", "sha256"
        
    Returns:
        文件哈希值
    """
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash for {file_path}: {e}")
        return ""

def load_json_file(file_path: str) -> Dict[str, Any]:
    """加载JSON文件
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        JSON数据字典
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return {}

def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """保存数据到JSON文件
    
    Args:
        data: 要保存的数据
        file_path: JSON文件路径
        
    Returns:
        是否保存成功
    """
    try:
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file {file_path}: {e}")
        return False

def format_bytes(size: int) -> str:
    """格式化字节大小为可读字符串
    
    Args:
        size: 字节大小
        
    Returns:
        格式化后的字符串，如 "1.2 GB"
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def is_ip_address(ip: str) -> bool:
    """判断是否为有效的IP地址
    
    Args:
        ip: 待检查的字符串
        
    Returns:
        是否为有效IP地址
    """
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    
    for part in parts:
        if not part.isdigit():
            return False
        num = int(part)
        if num < 0 or num > 255:
            return False
    
    return True

def is_domain_name(domain: str) -> bool:
    """判断是否为有效的域名
    
    Args:
        domain: 待检查的字符串
        
    Returns:
        是否为有效域名
    """
    import re
    pattern = r'^(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))
