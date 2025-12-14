#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import threading
import tarfile
import requests
from typing import Dict, List, Optional

from .config import Config
from .utils import logger, get_current_timestamp, calculate_file_hash

class SignatureRule:
    """签名规则类，代表一条检测规则"""
    
    def __init__(self, rule_text: str):
        """初始化签名规则
        
        Args:
            rule_text: 规则文本
        """
        self.rule_text = rule_text
        self.enabled = True
        self.last_updated = get_current_timestamp()
        self.match_count = 0
        
        # 解析规则基本信息
        self.id = ""
        self.description = ""
        self.severity = "medium"  # low, medium, high, critical
        self.protocols = []
        self.source_ports = []
        self.dest_ports = []
        self.parse_rule()
    
    def parse_rule(self) -> None:
        """解析规则内容"""
        try:
            # 提取规则ID
            id_match = re.search(r"sid:(\d+);", self.rule_text)
            if id_match:
                self.id = id_match.group(1)
            
            # 提取描述
            desc_match = re.search(r"msg:\"([^\"]+)\";", self.rule_text)
            if desc_match:
                self.description = desc_match.group(1)
            
            # 提取严重程度
            severity_match = re.search(r"severity:(\w+);", self.rule_text)
            if severity_match:
                self.severity = severity_match.group(1).lower()
            
            # 提取协议
            proto_match = re.search(r"^(\w+)\s+", self.rule_text)
            if proto_match:
                self.protocols.append(proto_match.group(1).lower())
        except Exception as e:
            logger.debug(f"Error parsing rule: {e}")
    
    def match(self, packet) -> bool:
        """匹配数据包
        
        Args:
            packet: 数据包对象
            
        Returns:
            是否匹配规则
        """
        # 这里只是一个简化的实现，实际应该使用更高效的匹配算法
        # 在生产环境中，应该使用Suricata或其他专业的IDS引擎
        if not self.enabled:
            return False
        
        try:
            # 检查协议匹配
            if self.protocols and packet.protocol.lower() not in self.protocols:
                return False
            
            # TODO: 实现更复杂的规则匹配逻辑
            # 如内容匹配、端口匹配、流量特征匹配等
            
            return False
        except Exception as e:
            logger.debug(f"Error matching rule {self.id}: {e}")
            return False
    
    def to_dict(self) -> Dict:
        """转换为字典
        
        Returns:
            规则信息字典
        """
        return {
            "id": self.id,
            "description": self.description,
            "severity": self.severity,
            "protocols": self.protocols,
            "source_ports": self.source_ports,
            "dest_ports": self.dest_ports,
            "enabled": self.enabled,
            "last_updated": self.last_updated,
            "match_count": self.match_count,
            "rule_text": self.rule_text
        }

class SignatureDetector:
    """签名检测类，负责基于规则的威胁检测"""
    
    def __init__(self, config: Config):
        """初始化签名检测器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.enabled = config.get("signature_detection.enabled", True)
        self.rules_path = config.get("signature_detection.suricata_rules_path", "../../data/signatures/suricata.rules")
        self.rule_update_interval = config.get("signature_detection.rule_update_interval_hours", 24) * 3600
        self.rule_sources = config.get("signature_detection.rule_sources", [])
        
        self.rules: Dict[str, SignatureRule] = {}  # 规则ID -> 规则对象
        self.rules_last_updated = 0
        self.update_thread = None
        self.is_running = False
        
        # 确保规则目录存在
        self._ensure_rules_directory()
        
        # 加载初始规则
        self.load_rules()
    
    def _ensure_rules_directory(self) -> None:
        """确保规则目录存在"""
        rules_dir = os.path.dirname(self.rules_path)
        if not os.path.exists(rules_dir):
            os.makedirs(rules_dir)
    
    def load_rules(self) -> None:
        """加载规则库"""
        logger.info(f"Loading rules from {self.rules_path}")
        
        try:
            if not os.path.exists(self.rules_path):
                logger.warning(f"Rules file not found at {self.rules_path}, will download default rules")
                self._download_default_rules()
            
            with open(self.rules_path, "r") as f:
                rule_lines = []
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    rule_lines.append(line)
                    if line.rstrip().endswith(';\\'):
                        # 多行规则，继续读取
                        continue
                    
                    # 完整规则
                    rule_text = "\n".join(rule_lines)
                    rule = SignatureRule(rule_text)
                    if rule.id:
                        self.rules[rule.id] = rule
                    rule_lines.clear()
            
            self.rules_last_updated = get_current_timestamp()
            logger.info(f"Loaded {len(self.rules)} rules successfully")
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
    
    def _download_default_rules(self) -> None:
        """下载默认规则集"""
        if not self.rule_sources:
            logger.error("No rule sources configured, cannot download rules")
            return
        
        logger.info(f"Downloading rules from {self.rule_sources[0]}")
        
        try:
            response = requests.get(self.rule_sources[0], timeout=30)
            if response.status_code == 200:
                # 保存到临时文件
                temp_file = "/tmp/rules.tar.gz"
                with open(temp_file, "wb") as f:
                    f.write(response.content)
                
                # 解压并合并规则
                with tarfile.open(temp_file, "r:gz") as tar:
                    # 遍历所有文件
                    for member in tar.getmembers():
                        if member.isfile() and member.name.endswith(".rules"):
                            # 读取规则文件
                            with tar.extractfile(member) as f:
                                content = f.read().decode("utf-8")
                                # 追加到主规则文件
                                with open(self.rules_path, "a") as rules_file:
                                    rules_file.write(content)
                
                # 删除临时文件
                os.remove(temp_file)
                logger.info(f"Downloaded and extracted rules to {self.rules_path}")
            else:
                logger.error(f"Failed to download rules: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading rules: {e}")
    
    def start(self) -> None:
        """启动签名检测器"""
        if not self.enabled:
            logger.info("Signature detection is disabled by configuration")
            return
        
        if self.is_running:
            logger.warning("Signature detector is already running")
            return
        
        logger.info("Starting signature detector...")
        
        # 启动规则更新线程
        self.update_thread = threading.Thread(target=self._update_rules_loop, daemon=True)
        self.update_thread.start()
        
        self.is_running = True
        logger.info("Signature detector started successfully")
    
    def stop(self) -> None:
        """停止签名检测器"""
        if not self.is_running:
            return
        
        logger.info("Stopping signature detector...")
        
        self.is_running = False
        
        # 等待更新线程结束
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
        
        logger.info("Signature detector stopped")
    
    def _update_rules_loop(self) -> None:
        """规则更新循环"""
        logger.info("Starting rules update loop")
        
        while self.is_running:
            current_time = get_current_timestamp()
            if current_time - self.rules_last_updated > self.rule_update_interval:
                logger.info("Updating rules...")
                self.update_rules()
            
            # 每小时检查一次
            time.sleep(3600)
        
        logger.info("Stopped rules update loop")
    
    def update_rules(self) -> None:
        """更新规则库"""
        # 备份旧规则
        backup_path = f"{self.rules_path}.bak.{get_current_timestamp()}"
        if os.path.exists(self.rules_path):
            os.rename(self.rules_path, backup_path)
        
        # 下载新规则
        self._download_default_rules()
        
        # 重新加载规则
        self.load_rules()
        
        # 清理旧备份（保留最近5个）
        self._cleanup_old_backups()
    
    def _cleanup_old_backups(self) -> None:
        """清理旧的规则备份文件"""
        try:
            rules_dir = os.path.dirname(self.rules_path)
            base_name = os.path.basename(self.rules_path)
            backup_pattern = f"{base_name}.bak."
            
            # 获取所有备份文件
            backups = []
            for file in os.listdir(rules_dir):
                if file.startswith(backup_pattern):
                    file_path = os.path.join(rules_dir, file)
                    backups.append((os.path.getmtime(file_path), file_path))
            
            # 按时间排序，保留最近5个
            backups.sort(reverse=True)
            for _, file_path in backups[5:]:
                os.remove(file_path)
                logger.debug(f"Removed old backup: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def detect_threat(self, packet) -> List[Dict]:
        """检测威胁
        
        Args:
            packet: 数据包对象
            
        Returns:
            匹配的规则列表
        """
        matches = []
        
        for rule_id, rule in self.rules.items():
            if rule.match(packet):
                rule.match_count += 1
                matches.append({
                    "rule_id": rule.id,
                    "description": rule.description,
                    "severity": rule.severity,
                    "timestamp": get_current_timestamp(),
                    "packet_info": packet.to_dict()
                })
        
        return matches
    
    def get_rule_stats(self) -> Dict:
        """获取规则统计信息
        
        Returns:
            规则统计字典
        """
        severity_counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0
        }
        
        for rule in self.rules.values():
            if rule.severity in severity_counts:
                severity_counts[rule.severity] += 1
        
        return {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for rule in self.rules.values() if rule.enabled),
            "severity_counts": severity_counts,
            "last_updated": self.rules_last_updated
        }
    
    def enable_rule(self, rule_id: str) -> bool:
        """启用规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否成功启用
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否成功禁用
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[SignatureRule]:
        """获取规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            规则对象，不存在则返回None
        """
        return self.rules.get(rule_id)
    
    def get_rules_by_severity(self, severity: str) -> List[SignatureRule]:
        """根据严重程度获取规则
        
        Args:
            severity: 严重程度
            
        Returns:
            规则列表
        """
        return [rule for rule in self.rules.values() if rule.severity == severity]
