#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import threading
import requests
from typing import Dict, List, Optional

from .config import Config
from .utils import logger, get_current_timestamp, save_json_file, load_json_file

class ThreatIntelligence:
    """威胁情报集成类"""
    
    def __init__(self, config: Config):
        """初始化威胁情报模块
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.enabled = config.get("threat_intelligence.enabled", True)
        self.update_interval = config.get("threat_intelligence.update_interval_hours", 12) * 3600
        self.sources = config.get("threat_intelligence.sources", [])
        self.cache_path = config.get("threat_intelligence.local_cache_path", "../../data/threat_intel.cache")
        
        self.threat_data = {
            "malicious_ips": set(),
            "malicious_domains": set(),
            "malicious_urls": set(),
            "updated_at": 0
        }
        
        # 加载本地缓存
        self._load_cache()
        
        # 启动更新线程
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def _load_cache(self) -> None:
        """加载本地威胁情报缓存"""
        if os.path.exists(self.cache_path):
            logger.info(f"Loading threat intelligence from cache: {self.cache_path}")
            cache_data = load_json_file(self.cache_path)
            if cache_data:
                self.threat_data = {
                    "malicious_ips": set(cache_data.get("malicious_ips", [])),
                    "malicious_domains": set(cache_data.get("malicious_domains", [])),
                    "malicious_urls": set(cache_data.get("malicious_urls", [])),
                    "updated_at": cache_data.get("updated_at", 0)
                }
                logger.info(f"Loaded {len(self.threat_data['malicious_ips'])} malicious IPs, {len(self.threat_data['malicious_domains'])} malicious domains, {len(self.threat_data['malicious_urls'])} malicious URLs")
    
    def _save_cache(self) -> None:
        """保存威胁情报到本地缓存"""
        cache_data = {
            "malicious_ips": list(self.threat_data["malicious_ips"]),
            "malicious_domains": list(self.threat_data["malicious_domains"]),
            "malicious_urls": list(self.threat_data["malicious_urls"]),
            "updated_at": self.threat_data["updated_at"]
        }
        save_json_file(cache_data, self.cache_path)
        logger.info(f"Saved threat intelligence to cache: {self.cache_path}")
    
    def _update_loop(self) -> None:
        """威胁情报更新循环"""
        logger.info("Starting threat intelligence update loop")
        
        while True:
            current_time = get_current_timestamp()
            if current_time - self.threat_data["updated_at"] > self.update_interval:
                logger.info("Updating threat intelligence...")
                self.update_threat_intelligence()
            
            # 每小时检查一次
            time.sleep(3600)
    
    def update_threat_intelligence(self) -> None:
        """更新威胁情报"""
        if not self.sources:
            logger.error("No threat intelligence sources configured")
            return
        
        for source in self.sources:
            try:
                source_type = source.get("type", "")
                if source_type == "otx":
                    self._update_from_otx(source)
                elif source_type == "misp":
                    self._update_from_misp(source)
                else:
                    logger.warning(f"Unknown threat intelligence source type: {source_type}")
            except Exception as e:
                logger.error(f"Error updating threat intelligence from {source.get('name', 'unknown')}: {e}")
        
        # 更新时间戳并保存缓存
        self.threat_data["updated_at"] = get_current_timestamp()
        self._save_cache()
    
    def _update_from_otx(self, source_config: Dict) -> None:
        """从AlienVault OTX更新威胁情报
        
        Args:
            source_config: OTX源配置
        """
        api_key = source_config.get("api_key")
        url = source_config.get("url", "https://otx.alienvault.com/api/v1")
        
        if not api_key:
            logger.error("No API key provided for OTX")
            return
        
        try:
            # 获取最近的威胁情报
            # 这里只获取恶意IP，实际可以获取更多类型的威胁情报
            headers = {
                "X-OTX-API-KEY": api_key
            }
            
            # 获取恶意IP列表
            response = requests.get(f"{url}/indicators/export", headers=headers, timeout=30)
            if response.status_code == 200:
                # 解析OTX导出数据
                data = response.json()
                if "indicators" in data:
                    for indicator in data["indicators"]:
                        if indicator["type"] == "IPv4":
                            self.threat_data["malicious_ips"].add(indicator["indicator"])
                        elif indicator["type"] == "domain":
                            self.threat_data["malicious_domains"].add(indicator["indicator"])
                        elif indicator["type"] == "URL":
                            self.threat_data["malicious_urls"].add(indicator["indicator"])
        except Exception as e:
            logger.error(f"Error updating from OTX: {e}")
    
    def _update_from_misp(self, source_config: Dict) -> None:
        """从MISP更新威胁情报
        
        Args:
            source_config: MISP源配置
        """
        # MISP集成实现
        # 这里只是一个占位符，实际需要实现MISP API调用
        logger.info("MISP threat intelligence update not implemented yet")
    
    def check_ip(self, ip_address: str) -> bool:
        """检查IP地址是否在恶意IP列表中
        
        Args:
            ip_address: IP地址
            
        Returns:
            是否为恶意IP
        """
        return ip_address in self.threat_data["malicious_ips"]
    
    def check_domain(self, domain: str) -> bool:
        """检查域名是否在恶意域名列表中
        
        Args:
            domain: 域名
            
        Returns:
            是否为恶意域名
        """
        return domain in self.threat_data["malicious_domains"]
    
    def check_url(self, url: str) -> bool:
        """检查URL是否在恶意URL列表中
        
        Args:
            url: URL
            
        Returns:
            是否为恶意URL
        """
        return url in self.threat_data["malicious_urls"]
    
    def add_malicious_ip(self, ip_address: str) -> None:
        """添加恶意IP到本地列表
        
        Args:
            ip_address: IP地址
        """
        self.threat_data["malicious_ips"].add(ip_address)
        self._save_cache()
    
    def add_malicious_domain(self, domain: str) -> None:
        """添加恶意域名到本地列表
        
        Args:
            domain: 域名
        """
        self.threat_data["malicious_domains"].add(domain)
        self._save_cache()
    
    def add_malicious_url(self, url: str) -> None:
        """添加恶意URL到本地列表
        
        Args:
            url: URL
        """
        self.threat_data["malicious_urls"].add(url)
        self._save_cache()
    
    def remove_malicious_ip(self, ip_address: str) -> None:
        """从本地列表移除恶意IP
        
        Args:
            ip_address: IP地址
        """
        if ip_address in self.threat_data["malicious_ips"]:
            self.threat_data["malicious_ips"].remove(ip_address)
            self._save_cache()
    
    def remove_malicious_domain(self, domain: str) -> None:
        """从本地列表移除恶意域名
        
        Args:
            domain: 域名
        """
        if domain in self.threat_data["malicious_domains"]:
            self.threat_data["malicious_domains"].remove(domain)
            self._save_cache()
    
    def remove_malicious_url(self, url: str) -> None:
        """从本地列表移除恶意URL
        
        Args:
            url: URL
        """
        if url in self.threat_data["malicious_urls"]:
            self.threat_data["malicious_urls"].remove(url)
            self._save_cache()
    
    def get_stats(self) -> Dict:
        """获取威胁情报统计信息
        
        Returns:
            威胁情报统计字典
        """
        return {
            "malicious_ips_count": len(self.threat_data["malicious_ips"]),
            "malicious_domains_count": len(self.threat_data["malicious_domains"]),
            "malicious_urls_count": len(self.threat_data["malicious_urls"]),
            "last_updated": self.threat_data["updated_at"],
            "next_update": self.threat_data["updated_at"] + self.update_interval
        }
    
    def get_malicious_ips(self, limit: int = 100) -> List[str]:
        """获取恶意IP列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            恶意IP列表
        """
        return list(self.threat_data["malicious_ips"])[:limit]
    
    def get_malicious_domains(self, limit: int = 100) -> List[str]:
        """获取恶意域名列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            恶意域名列表
        """
        return list(self.threat_data["malicious_domains"])[:limit]
    
    def get_malicious_urls(self, limit: int = 100) -> List[str]:
        """获取恶意URL列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            恶意URL列表
        """
        return list(self.threat_data["malicious_urls"])[:limit]
