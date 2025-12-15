#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import threading
import time
from typing import Dict, List, Optional, Tuple

from .config import Config
from .utils import logger, get_current_timestamp, save_json_file, load_json_file

class BehaviorBaseline:
    """设备行为基线类"""
    
    def __init__(self, device_mac: str):
        """初始化行为基线
        
        Args:
            device_mac: 设备MAC地址
        """
        self.device_mac = device_mac
        self.created_at = get_current_timestamp()
        self.updated_at = get_current_timestamp()
        self.features = {
            "daily_traffic": {},  # 按天统计的流量
            "hourly_activity": {},  # 按小时统计的活动情况
            "connection_patterns": {},  # 连接模式
            "domain_visits": {},  # 访问的域名统计
            "port_usage": {},  # 端口使用情况
            "protocol_distribution": {}  # 协议分布
        }
        
    def update(self, behavior_data: Dict) -> None:
        """更新行为基线
        
        Args:
            behavior_data: 行为数据
        """
        # 更新流量统计
        if "traffic" in behavior_data:
            self._update_traffic_stats(behavior_data["traffic"])
        
        # 更新连接模式
        if "connections" in behavior_data:
            self._update_connection_patterns(behavior_data["connections"])
        
        # 更新域名访问
        if "domains" in behavior_data:
            self._update_domain_visits(behavior_data["domains"])
        
        # 更新端口使用
        if "ports" in behavior_data:
            self._update_port_usage(behavior_data["ports"])
        
        # 更新协议分布
        if "protocols" in behavior_data:
            self._update_protocol_distribution(behavior_data["protocols"])
        
        self.updated_at = get_current_timestamp()
    
    def _update_traffic_stats(self, traffic_data: Dict) -> None:
        """更新流量统计
        
        Args:
            traffic_data: 流量数据
        """
        # 简化实现，实际应该按天和小时统计
        pass
    
    def _update_connection_patterns(self, connection_data: Dict) -> None:
        """更新连接模式
        
        Args:
            connection_data: 连接数据
        """
        pass
    
    def _update_domain_visits(self, domain_data: Dict) -> None:
        """更新域名访问
        
        Args:
            domain_data: 域名数据
        """
        pass
    
    def _update_port_usage(self, port_data: Dict) -> None:
        """更新端口使用
        
        Args:
            port_data: 端口数据
        """
        pass
    
    def _update_protocol_distribution(self, protocol_data: Dict) -> None:
        """更新协议分布
        
        Args:
            protocol_data: 协议数据
        """
        pass
    
    def detect_anomaly(self, current_behavior: Dict) -> Tuple[bool, float]:
        """检测异常行为
        
        Args:
            current_behavior: 当前行为数据
            
        Returns:
            (是否异常, 异常分数)
        """
        # 简化的异常检测算法，实际应该使用机器学习模型
        anomaly_score = 0.0
        
        # 示例：检查流量是否超过基线的200%
        if "traffic" in current_behavior:
            current_bytes = current_behavior["traffic"].get("bytes_out", 0)
            # 这里应该与基线比较，计算异常分数
            # 简化实现，返回固定分数
            anomaly_score = 0.5
        
        # 示例：检查是否访问了新的域名
        if "domains" in current_behavior:
            new_domains = current_behavior["domains"].get("new", [])
            if new_domains:
                anomaly_score += 0.3
        
        # 如果异常分数超过阈值，认为是异常
        is_anomaly = anomaly_score > 0.7
        return is_anomaly, anomaly_score
    
    def to_dict(self) -> Dict:
        """转换为字典
        
        Returns:
            行为基线字典
        """
        return {
            "device_mac": self.device_mac,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "features": self.features
        }

class AnomalyDetector:
    """异常行为检测器"""
    
    def __init__(self, config: Config, device_manager):
        """初始化异常行为检测器
        
        Args:
            config: 配置对象
            device_manager: 设备管理器对象
        """
        self.config = config
        self.device_manager = device_manager
        self.enabled = config.get("anomaly_detection.enabled", True)
        self.baseline_update_interval = config.get("anomaly_detection.baseline_update_interval_hours", 24) * 3600
        self.detection_threshold = config.get("anomaly_detection.detection_threshold", 0.95)
        self.features = config.get("anomaly_detection.features", [])
        
        self.baselines: Dict[str, BehaviorBaseline] = {}  # MAC地址 -> 行为基线
        self.models_dir = "../../data/models"
        self.is_running = False
        self.update_thread = None
        
        # 确保模型目录存在
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
        
        # 加载现有基线
        self.load_baselines()
    
    def load_baselines(self) -> None:
        """加载行为基线"""
        logger.info("Loading behavior baselines")
        
        try:
            for file in os.listdir(self.models_dir):
                if file.endswith(".baseline.json"):
                    file_path = os.path.join(self.models_dir, file)
                    baseline_data = load_json_file(file_path)
                    if "device_mac" in baseline_data:
                        baseline = BehaviorBaseline(baseline_data["device_mac"])
                        baseline.created_at = baseline_data.get("created_at", get_current_timestamp())
                        baseline.updated_at = baseline_data.get("updated_at", get_current_timestamp())
                        baseline.features = baseline_data.get("features", baseline.features)
                        self.baselines[baseline.device_mac] = baseline
            
            logger.info(f"Loaded {len(self.baselines)} behavior baselines")
        except Exception as e:
            logger.error(f"Error loading baselines: {e}")
    
    def save_baseline(self, baseline: BehaviorBaseline) -> None:
        """保存行为基线
        
        Args:
            baseline: 行为基线对象
        """
        try:
            # Replace colons with hyphens in MAC address for Windows compatibility
            safe_mac = baseline.device_mac.replace(':', '-')
            file_path = os.path.join(self.models_dir, f"{safe_mac}.baseline.json")
            save_json_file(baseline.to_dict(), file_path)
        except Exception as e:
            logger.error(f"Error saving baseline for {baseline.device_mac}: {e}")
    
    def start(self) -> None:
        """启动异常行为检测器"""
        if not self.enabled:
            logger.info("Anomaly detector is disabled by configuration")
            return
        
        if self.is_running:
            logger.warning("Anomaly detector is already running")
            return
        
        logger.info("Starting anomaly detector...")
        
        # 启动基线更新线程
        self.update_thread = threading.Thread(target=self._update_baselines_loop, daemon=True)
        self.update_thread.start()
        
        self.is_running = True
        logger.info("Anomaly detector started successfully")
    
    def stop(self) -> None:
        """停止异常行为检测器"""
        if not self.is_running:
            return
        
        logger.info("Stopping anomaly detector...")
        
        self.is_running = False
        
        # 等待更新线程结束
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
        
        logger.info("Anomaly detector stopped")
    
    def _update_baselines_loop(self) -> None:
        """基线更新循环"""
        logger.info("Starting baselines update loop")
        
        while self.is_running:
            # 更新所有基线
            for mac, device in self.device_manager.devices.items():
                self.update_device_baseline(mac)
            
            # 每小时检查一次
            time.sleep(3600)
        
        logger.info("Stopped baselines update loop")
    
    def update_device_baseline(self, device_mac: str) -> None:
        """更新设备行为基线
        
        Args:
            device_mac: 设备MAC地址
        """
        device = self.device_manager.get_device(device_mac)
        if not device:
            return
        
        # 获取设备当前行为数据
        behavior_data = self._get_device_behavior(device)
        
        # 获取或创建基线
        baseline = self.baselines.get(device_mac)
        if not baseline:
            baseline = BehaviorBaseline(device_mac)
            self.baselines[device_mac] = baseline
        
        # 更新基线
        baseline.update(behavior_data)
        
        # 保存基线
        self.save_baseline(baseline)
    
    def _get_device_behavior(self, device) -> Dict:
        """获取设备当前行为数据
        
        Args:
            device: 设备对象
            
        Returns:
            设备行为数据字典
        """
        # 从设备对象获取行为数据
        return {
            "traffic": device.traffic_stats,
            "connections": {},
            "domains": {},
            "ports": {},
            "protocols": {}
        }
    
    def detect_anomaly(self, device_mac: str, current_behavior: Dict) -> Dict:
        """检测设备异常行为
        
        Args:
            device_mac: 设备MAC地址
            current_behavior: 当前行为数据
            
        Returns:
            异常检测结果
        """
        # 如果没有基线，先创建基线
        if device_mac not in self.baselines:
            baseline = BehaviorBaseline(device_mac)
            baseline.update(current_behavior)
            self.baselines[device_mac] = baseline
            self.save_baseline(baseline)
            return {
                "is_anomaly": False,
                "score": 0.0,
                "reason": "No baseline available yet",
                "timestamp": get_current_timestamp()
            }
        
        # 使用基线检测异常
        baseline = self.baselines[device_mac]
        is_anomaly, score = baseline.detect_anomaly(current_behavior)
        
        # 更新基线
        baseline.update(current_behavior)
        self.save_baseline(baseline)
        
        result = {
            "is_anomaly": is_anomaly,
            "score": score,
            "reason": "",
            "timestamp": get_current_timestamp()
        }
        
        # 如果是异常，添加原因
        if is_anomaly:
            result["reason"] = self._get_anomaly_reason(current_behavior, baseline)
        
        return result
    
    def _get_anomaly_reason(self, current_behavior: Dict, baseline: BehaviorBaseline) -> str:
        """获取异常原因
        
        Args:
            current_behavior: 当前行为数据
            baseline: 行为基线
            
        Returns:
            异常原因
        """
        reasons = []
        
        # 简化实现，实际应该基于具体的异常特征
        if "traffic" in current_behavior:
            reasons.append("流量异常")
        
        if "domains" in current_behavior and "new" in current_behavior["domains"]:
            reasons.append("访问了新的域名")
        
        if "ports" in current_behavior and "unusual" in current_behavior["ports"]:
            reasons.append("使用了不常见的端口")
        
        return ", ".join(reasons) if reasons else "行为偏离正常模式"
    
    def get_baseline_stats(self) -> Dict:
        """获取基线统计信息
        
        Returns:
            基线统计字典
        """
        return {
            "total_baselines": len(self.baselines),
            "feature_count": len(self.features),
            "detection_threshold": self.detection_threshold,
            "last_updated": max(b.updated_at for b in self.baselines.values()) if self.baselines else 0
        }
    
    def get_device_baseline(self, device_mac: str) -> Optional[Dict]:
        """获取设备行为基线
        
        Args:
            device_mac: 设备MAC地址
            
        Returns:
            设备行为基线字典，不存在则返回None
        """
        baseline = self.baselines.get(device_mac)
        if baseline:
            return baseline.to_dict()
        return None
