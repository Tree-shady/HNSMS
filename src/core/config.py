#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from typing import Dict, Any

class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = None):
        """初始化配置
        
        Args:
            config_path: 配置文件路径，默认使用默认配置
        """
        self.config: Dict[str, Any] = self._load_default_config()
        self._observers = []  # 配置变更观察者列表
        
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        
        # 初始验证配置
        self.validate_config()
    
    def add_observer(self, observer: callable) -> None:
        """添加配置变更观察者
        
        Args:
            observer: 观察者函数，接收参数(key, old_value, new_value)
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: callable) -> None:
        """移除配置变更观察者
        
        Args:
            observer: 要移除的观察者函数
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, key: str, old_value: Any, new_value: Any) -> None:
        """通知所有观察者配置已变更
        
        Args:
            key: 变更的配置键
            old_value: 旧值
            new_value: 新值
        """
        for observer in self._observers:
            try:
                observer(key, old_value, new_value)
            except Exception as e:
                print(f"通知观察者时出错: {e}")
        
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            # 系统配置
            "system": {
                "mode": "learning",  # learning: 学习模式, detection: 检测模式
                "learning_period_days": 14,  # 学习期天数
                "log_level": "INFO",
                "log_path": "../../data/logs/system.log"
            },
            
            # 网络配置
            "network": {
                "proxy": {
                    "enabled": False,
                    "type": "http",
                    "host": "",
                    "port": 8080,
                    "username": "",
                    "password": ""
                },
                "dns": {
                    "enabled": False,
                    "servers": ["8.8.8.8", "8.8.4.4"],
                    "search_domains": [],
                    "timeout_seconds": 5
                },
                "connection_timeout": 30,  # 连接超时时间（秒）
                "max_retries": 3  # 最大重试次数
            },
            
            # 存储配置
            "storage": {
                "database": {
                    "type": "sqlite",  # sqlite, mysql, postgresql
                    "host": "localhost",
                    "port": 3306,
                    "username": "",
                    "password": "",
                    "name": "hnsms.db",
                    "sqlite_path": "../../data/hnsms.db",
                    "max_connections": 10,
                    "connection_timeout": 30
                },
                "file_storage": {
                    "type": "local",  # local, s3
                    "local_path": "../../data",
                    "max_file_size": 1024 * 1024 * 100,  # 100MB
                    "file_retention_days": 30,
                    "backup_enabled": True,
                    "backup_path": "../../data/backups"
                }
            },
            
            # 流量分析配置
            "traffic_analyzer": {
                "enabled": True,
                "interfaces": ["eth0", "wlan0"],
                "capture_filter": "",  # BPF过滤规则
                "max_packet_size": 1518,
                "buffer_size": 1024 * 1024 * 100  # 100MB
            },
            
            # 签名检测配置
            "signature_detection": {
                "enabled": True,
                "suricata_rules_path": "../../data/signatures/suricata.rules",
                "rule_update_interval_hours": 24,
                "rule_sources": [
                    "https://www.openinfosecfoundation.org/rules/emerging-all.rules.tar.gz"
                ]
            },
            
            # 异常检测配置
            "anomaly_detection": {
                "enabled": True,
                "baseline_update_interval_hours": 24,
                "detection_threshold": 0.95,
                "features": [
                    "bytes_in",
                    "bytes_out",
                    "packets_in",
                    "packets_out",
                    "connection_count",
                    "unique_domains",
                    "active_hours"
                ]
            },
            
            # 威胁情报配置
            "threat_intelligence": {
                "enabled": True,
                "update_interval_hours": 12,
                "sources": [
                    {
                        "name": "OTX",
                        "type": "otx",
                        "api_key": "",
                        "url": "https://otx.alienvault.com/api/v1"
                    },
                    {
                        "name": "MISP",
                        "type": "misp",
                        "url": "",
                        "api_key": ""
                    }
                ],
                "local_cache_path": "../../data/threat_intel.cache"
            },
            
            # 设备管理配置
            "device_manager": {
                "enabled": True,
                "scan_interval_seconds": 300,  # 5分钟扫描一次
                "device_db_path": "../../data/devices.db",
                "unknown_device_alert": True,
                "main_router_ip": "",  # 主路由器IP地址
                "include_local_machine": False  # 是否将本机加入设备管理
            },
            
            # 告警引擎配置
            "alert_engine": {
                "enabled": True,
                "alert_levels": ["info", "warning", "critical"],
                "notification_methods": ["web", "mobile"],
                "alert_db_path": "../../data/alerts.db",
                "max_alerts_per_hour": 100
            },
            
            # 性能配置
            "performance": {
                "threads": {
                    "traffic_analyzer": 4,
                    "signature_detection": 2,
                    "anomaly_detection": 2,
                    "threat_intelligence": 1,
                    "device_manager": 1,
                    "alert_engine": 2
                },
                "memory": {
                    "max_usage_mb": 2048,  # 最大内存使用量（MB）
                    "buffer_size_mb": 100,  # 缓冲区大小（MB）
                    "cache_size_mb": 500  # 缓存大小（MB）
                },
                "cpu": {
                    "max_usage_percent": 80,  # 最大CPU使用率（%）
                    "affinity": []  # CPU亲和性，空列表表示使用所有CPU
                },
                "queue_size": 10000  # 队列大小
            },
            
            # 安全配置
            "security": {
                "encryption": {
                    "enabled": True,
                    "algorithm": "aes-256-cbc",
                    "key_path": "../../data/keys/encryption.key",
                    "cert_path": "../../data/keys/certificate.pem",
                    "key_size": 256,
                    "rotation_days": 90  # 密钥轮换周期（天）
                },
                "authentication": {
                    "enabled": True,
                    "method": "password",  # password, oauth2, ldap
                    "session_timeout_minutes": 30,
                    "max_login_attempts": 5,
                    "lockout_duration_minutes": 15,
                    "password_policy": {
                        "min_length": 8,
                        "require_uppercase": True,
                        "require_lowercase": True,
                        "require_digit": True,
                        "require_special": True
                    }
                },
                "access_control": {
                    "enabled": True,
                    "default_role": "viewer",
                    "roles": ["admin", "editor", "viewer"]
                },
                "audit_logging": {
                    "enabled": True,
                    "path": "../../data/logs/audit.log",
                    "retention_days": 90
                }
            },
            
            # 备份配置
            "backup": {
                "enabled": True,
                "type": "full",  # full, incremental, differential
                "schedule": {
                    "frequency": "daily",  # daily, weekly, monthly
                    "time": "02:00",  # 备份时间，格式：HH:MM
                    "day_of_week": 0,  # 每周备份日（0-6，0表示周日），仅当frequency为weekly时生效
                    "day_of_month": 1  # 每月备份日（1-31），仅当frequency为monthly时生效
                },
                "storage": {
                    "local_path": "../../data/backups",
                    "remote_enabled": False,
                    "remote_type": "s3",  # s3, ftp, scp
                    "remote_config": {
                        "bucket": "",
                        "endpoint": "",
                        "access_key": "",
                        "secret_key": "",
                        "region": ""
                    }
                },
                "retention": {
                    "days": 30,  # 保留天数
                    "max_backups": 30,  # 最大备份数量
                    "compression": "gzip"  # gzip, bzip2, none
                },
                "components": {
                    "database": True,
                    "configurations": True,
                    "logs": True,
                    "signatures": False,
                    "threat_intelligence": False
                }
            },
            
            # UI配置
            "ui": {
                "theme": "dark",  # light, dark, auto
                "language": "zh_CN",  # zh_CN, en_US, ja_JP
                "refresh_interval": 30,  # 自动刷新间隔（秒）
                "date_format": "YYYY-MM-DD HH:mm:ss",
                "timezone": "Asia/Shanghai",
                "dashboard": {
                    "show_traffic_summary": True,
                    "show_device_count": True,
                    "show_alert_count": True,
                    "show_threat_level": True
                },
                "tables": {
                    "page_size": 25,  # 默认每页显示行数
                    "max_page_size": 100,  # 最大每页显示行数
                    "sort_by": "timestamp",
                    "sort_order": "desc"  # asc, desc
                }
            }
        }
    
    def _load_config(self, config_path: str) -> None:
        """从文件加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                custom_config = json.load(f)
                # 合并配置
                self._merge_config(self.config, custom_config)
        except Exception as e:
            print(f"Error loading config file: {e}")
    
    def _merge_config(self, base: Dict[str, Any], custom: Dict[str, Any], parent_key: str = "") -> None:
        """合并配置字典，支持观察者通知
        
        Args:
            base: 基础配置字典
            custom: 自定义配置字典
            parent_key: 父配置键，用于构建完整的配置路径
        """
        for key, value in custom.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # 递归合并字典
                self._merge_config(base[key], value, full_key)
            else:
                # 保存旧值用于通知
                old_value = base[key] if key in base else None
                base[key] = value
                # 通知观察者配置变更
                self._notify_observers(full_key, old_value, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点分隔符
        
        Args:
            key: 配置键，如 "system.mode"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def validate_config(self) -> bool:
        """验证配置的有效性
        
        Returns:
            bool: 配置是否有效
        """
        valid = True
        
        # 验证系统模式
        system_mode = self.get("system.mode")
        if system_mode not in ["learning", "detection"]:
            print(f"警告: 无效的系统模式: {system_mode}，默认使用 learning")
            self.set("system.mode", "learning")
            valid = False
        
        # 验证日志级别
        log_level = self.get("system.log_level")
        if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            print(f"警告: 无效的日志级别: {log_level}，默认使用 INFO")
            self.set("system.log_level", "INFO")
            valid = False
        
        # 验证检测阈值
        detection_threshold = self.get("anomaly_detection.detection_threshold")
        if not (0 <= detection_threshold <= 1):
            print(f"警告: 无效的检测阈值: {detection_threshold}，默认使用 0.95")
            self.set("anomaly_detection.detection_threshold", 0.95)
            valid = False
        
        # 验证线程数
        for component, threads in self.get("performance.threads").items():
            if threads < 1:
                print(f"警告: {component} 线程数无效: {threads}，默认使用 1")
                self.set(f"performance.threads.{component}", 1)
                valid = False
        
        # 验证备份频率
        backup_frequency = self.get("backup.schedule.frequency")
        if backup_frequency not in ["daily", "weekly", "monthly"]:
            print(f"警告: 无效的备份频率: {backup_frequency}，默认使用 daily")
            self.set("backup.schedule.frequency", "daily")
            valid = False
        
        # 验证主题设置
        theme = self.get("ui.theme")
        if theme not in ["light", "dark", "auto"]:
            print(f"警告: 无效的主题设置: {theme}，默认使用 dark")
            self.set("ui.theme", "dark")
            valid = False
        
        return valid
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点分隔符
        
        Args:
            key: 配置键，如 "system.mode"
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        # 获取旧值
        old_value = self.get(key)
        
        # 遍历创建嵌套结构
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置新值
        config[keys[-1]] = value
        
        # 通知观察者
        self._notify_observers(key, old_value, value)
        
        # 设置后验证配置
        self.validate_config()
    
    def save(self, config_path: str) -> None:
        """保存配置到文件
        
        Args:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config file: {e}")
