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
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        
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
                    "https://rules.emergingthreats.net/open/suricata/rules/emerging-all.rules.tar.gz"
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
                "unknown_device_alert": True
            },
            
            # 告警引擎配置
            "alert_engine": {
                "enabled": True,
                "alert_levels": ["info", "warning", "critical"],
                "notification_methods": ["web", "mobile"],
                "alert_db_path": "../../data/alerts.db",
                "max_alerts_per_hour": 100
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
    
    def _merge_config(self, base: Dict[str, Any], custom: Dict[str, Any]) -> None:
        """合并配置字典"""
        for key, value in custom.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
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
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点分隔符
        
        Args:
            key: 配置键，如 "system.mode"
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
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
