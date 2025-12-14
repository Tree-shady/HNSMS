#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import re
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime

from .config import Config
from .utils import logger, get_current_timestamp, is_ip_address

class Device:
    """设备类，代表一个网络设备"""
    
    def __init__(self, mac_address: str, ip_address: str = ""):
        """初始化设备
        
        Args:
            mac_address: MAC地址
            ip_address: IP地址
        """
        self.mac_address = mac_address
        self.ip_address = ip_address
        self.hostname = ""
        self.device_type = "unknown"  # 设备类型：computer, mobile, iot, camera, speaker等
        self.manufacturer = "unknown"
        self.model = "unknown"
        self.os = "unknown"
        self.status = "online"  # online, offline
        self.first_seen = get_current_timestamp()
        self.last_seen = get_current_timestamp()
        self.traffic_stats = {
            "bytes_in": 0,
            "bytes_out": 0,
            "packets_in": 0,
            "packets_out": 0
        }
        self.behavior_baseline = {}  # 行为基线数据
        self.vulnerabilities = []  # 已知漏洞
        self.groups = []  # 所属分组
    
    def to_dict(self) -> Dict:
        """转换为字典
        
        Returns:
            设备信息字典
        """
        return {
            "mac_address": self.mac_address,
            "ip_address": self.ip_address,
            "hostname": self.hostname,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "os": self.os,
            "status": self.status,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "traffic_stats": self.traffic_stats,
            "behavior_baseline": self.behavior_baseline,
            "vulnerabilities": self.vulnerabilities,
            "groups": self.groups
        }

class DeviceManager:
    """设备管理类，负责设备发现、识别和管理"""
    
    def __init__(self, config: Config):
        """初始化设备管理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.devices: Dict[str, Device] = {}  # MAC地址 -> Device对象
        self.db_path = config.get("device_manager.device_db_path", "../../data/devices.db")
        self.scan_interval = config.get("device_manager.scan_interval_seconds", 300)
        self.unknown_device_alert = config.get("device_manager.unknown_device_alert", True)
        
        # 初始化数据库
        self._init_database()
        
        # 加载设备数据
        self._load_devices()
    
    def _init_database(self) -> None:
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建设备表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    mac_address TEXT PRIMARY KEY,
                    ip_address TEXT,
                    hostname TEXT,
                    device_type TEXT,
                    manufacturer TEXT,
                    model TEXT,
                    os TEXT,
                    status TEXT,
                    first_seen INTEGER,
                    last_seen INTEGER,
                    behavior_baseline TEXT,
                    vulnerabilities TEXT,
                    groups TEXT
                )
            """)
            
            # 创建分组表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_groups (
                    group_id TEXT PRIMARY KEY,
                    group_name TEXT,
                    description TEXT,
                    created_at INTEGER
                )
            """)
            
            # 创建默认分组
            self._create_default_groups(cursor)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def _create_default_groups(self, cursor) -> None:
        """创建默认分组"""
        default_groups = [
            ("all", "所有设备", "包含所有设备", get_current_timestamp()),
            ("computer", "电脑", "台式机和笔记本电脑", get_current_timestamp()),
            ("mobile", "移动设备", "手机和平板电脑", get_current_timestamp()),
            ("iot", "物联网设备", "智能家电和IoT设备", get_current_timestamp()),
            ("camera", "摄像头", "网络摄像头", get_current_timestamp()),
            ("guest", "访客设备", "临时接入的设备", get_current_timestamp())
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO device_groups VALUES (?, ?, ?, ?)",
            default_groups
        )
    
    def _load_devices(self) -> None:
        """从数据库加载设备数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM devices")
            rows = cursor.fetchall()
            
            for row in rows:
                mac_address = row[0]
                ip_address = row[1]
                
                # 跳过广播地址、多播地址和网络地址
                if (ip_address == "255.255.255.255" or  # 广播地址
                    ip_address.startswith("224.") or  # 多播地址
                    ip_address.startswith("239.") or  # 多播地址
                    ip_address.endswith(".0") or  # 网络地址
                    ip_address.endswith(".255")):  # 广播地址
                    continue
                
                device = Device(mac_address, ip_address)
                device.hostname = row[2]
                device.device_type = row[3]
                device.manufacturer = row[4]
                device.model = row[5]
                device.os = row[6]
                device.status = row[7]
                device.first_seen = row[8]
                device.last_seen = row[9]
                
                # 解析JSON字段
                import json
                device.behavior_baseline = json.loads(row[10] if row[10] else "{}")
                device.vulnerabilities = json.loads(row[11] if row[11] else "[]")
                device.groups = json.loads(row[12] if row[12] else "[]")
                
                self.devices[device.mac_address] = device
            
            conn.close()
        except Exception as e:
            logger.error(f"Error loading devices from database: {e}")
    
    def scan_devices(self) -> List[Device]:
        """扫描网络设备
        
        Returns:
            发现的设备列表
        """
        logger.info("Scanning network devices...")
        
        # 使用arp-scan命令扫描设备
        try:
            # 在Windows上使用arp命令
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode != 0:
                logger.error(f"Error running arp scan: {result.stderr}")
                return []
            
            devices = self._parse_arp_output(result.stdout)
            
            # 对每个设备进行更详细的识别
            for device in devices:
                self._identify_device(device)
                
            # 更新设备状态
            self._update_device_status(devices)
            
            return devices
        except Exception as e:
            logger.error(f"Error scanning devices: {e}")
            return []
    
    def _parse_arp_output(self, output: str) -> List[Device]:
        """解析arp命令输出
        
        Args:
            output: arp命令输出
            
        Returns:
            设备列表
        """
        devices = []
        
        # 匹配MAC地址和IP地址的正则表达式
        pattern = r'([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})'
        
        matches = re.finditer(pattern, output)
        
        for match in matches:
            ip_address = match.group(1)
            mac_address = match.group(2).replace("-", ":").lower()
            
            # 跳过无效MAC地址
            if mac_address == "00:00:00:00:00:00":
                continue
            
            # 跳过广播地址、多播地址和网络地址
            if (ip_address == "255.255.255.255" or  # 广播地址
                ip_address.startswith("224.") or  # 多播地址
                ip_address.startswith("239.") or  # 多播地址
                ip_address.endswith(".0") or  # 网络地址
                ip_address.endswith(".255")):  # 广播地址
                continue
            
            device = Device(mac_address, ip_address)
            devices.append(device)
        
        return devices
    
    def _identify_device(self, device: Device) -> None:
        """识别设备信息
        
        Args:
            device: 设备对象
        """
        # 1. 根据MAC地址识别厂商
        self._identify_manufacturer(device)
        
        # 2. 使用nmap进行更详细的设备识别
        self._nmap_device_scan(device)
        
        # 3. 根据设备特征推断设备类型
        self._infer_device_type(device)
    
    def _identify_manufacturer(self, device: Device) -> None:
        """根据MAC地址识别厂商
        
        Args:
            device: 设备对象
        """
        # MAC地址前三位(OUI)对应厂商
        oui = device.mac_address[:8].upper()
        
        # 简单的厂商映射表（实际应用中应使用更完整的OUI数据库）
        oui_map = {
            "00:0C:29": "VMware",
            "00:50:56": "VMware",
            "08:00:27": "Oracle VirtualBox",
            "52:54:00": "QEMU/KVM",
            "FC:AA:14": "Raspberry Pi",
            "00:11:22": "Generic",
            "00:00:00": "Unknown"
        }
        
        device.manufacturer = oui_map.get(oui, "unknown")
    
    def _nmap_device_scan(self, device: Device) -> None:
        """使用nmap扫描设备详细信息
        
        Args:
            device: 设备对象
        """
        try:
            # 使用nmap进行OS检测和服务扫描
            result = subprocess.run(
                ["nmap", "-O", "-sV", "-T4", device.ip_address],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self._parse_nmap_output(device, result.stdout)
        except Exception as e:
            logger.debug(f"Error running nmap scan on {device.ip_address}: {e}")
    
    def _parse_nmap_output(self, device: Device, output: str) -> None:
        """解析nmap输出
        
        Args:
            device: 设备对象
            output: nmap输出
        """
        # 解析OS信息
        os_match = re.search(r"Running: (.+?)\n", output)
        if os_match:
            device.os = os_match.group(1)
        
        # 解析设备类型
        device_type_match = re.search(r"Device type: (.+?)\n", output)
        if device_type_match:
            device.device_type = device_type_match.group(1)
        
        # 解析主机名
        hostname_match = re.search(r"Hostname: (.+?)\n", output)
        if hostname_match:
            device.hostname = hostname_match.group(1)
    
    def _infer_device_type(self, device: Device) -> None:
        """根据设备特征推断设备类型
        
        Args:
            device: 设备对象
        """
        # 根据设备类型关键词推断
        type_keywords = {
            "computer": ["Windows", "Linux", "macOS", "Ubuntu", "Debian"],
            "mobile": ["Android", "iOS", "iPhone", "iPad"],
            "iot": ["IoT", "Smart", "Embedded", "Home"],
            "camera": ["Camera", "IP Camera", "Webcam"]
        }
        
        for device_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in device.os or keyword in device.hostname or keyword in device.manufacturer:
                    device.device_type = device_type
                    break
    
    def _update_device_status(self, discovered_devices: List[Device]) -> None:
        """更新设备状态
        
        Args:
            discovered_devices: 发现的设备列表
        """
        current_macs = {dev.mac_address for dev in discovered_devices}
        
        # 更新在线设备
        for dev in discovered_devices:
            if dev.mac_address in self.devices:
                # 更新现有设备信息
                existing_dev = self.devices[dev.mac_address]
                existing_dev.ip_address = dev.ip_address
                existing_dev.status = "online"
                existing_dev.last_seen = get_current_timestamp()
                existing_dev.hostname = dev.hostname or existing_dev.hostname
                existing_dev.device_type = dev.device_type or existing_dev.device_type
                existing_dev.manufacturer = dev.manufacturer or existing_dev.manufacturer
                existing_dev.os = dev.os or existing_dev.os
            else:
                # 新设备
                logger.info(f"New device discovered: {dev.mac_address} ({dev.ip_address})")
                dev.status = "online"
                dev.last_seen = get_current_timestamp()
                self.devices[dev.mac_address] = dev
                
                # 添加到默认分组
                dev.groups.append("all")
                if dev.device_type in ["computer", "mobile", "iot", "camera"]:
                    dev.groups.append(dev.device_type)
                
                # 保存到数据库
                self._save_device_to_db(dev)
                
                # 未知设备告警
                if self.unknown_device_alert:
                    logger.warning(f"Unknown device detected: {dev.mac_address} ({dev.ip_address})")
        
        # 更新离线设备
        for mac, device in self.devices.items():
            if mac not in current_macs:
                device.status = "offline"
                self._save_device_to_db(device)
    
    def _save_device_to_db(self, device: Device) -> None:
        """保存设备到数据库
        
        Args:
            device: 设备对象
        """
        try:
            import json
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO devices 
                (mac_address, ip_address, hostname, device_type, manufacturer, model, os, status, 
                 first_seen, last_seen, behavior_baseline, vulnerabilities, groups) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                device.mac_address,
                device.ip_address,
                device.hostname,
                device.device_type,
                device.manufacturer,
                device.model,
                device.os,
                device.status,
                device.first_seen,
                device.last_seen,
                json.dumps(device.behavior_baseline),
                json.dumps(device.vulnerabilities),
                json.dumps(device.groups)
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving device to database: {e}")
    
    def get_device(self, mac_address: str) -> Optional[Device]:
        """根据MAC地址获取设备
        
        Args:
            mac_address: MAC地址
            
        Returns:
            设备对象，不存在则返回None
        """
        return self.devices.get(mac_address)
    
    def get_devices(self, filters: Dict = None) -> List[Device]:
        """获取设备列表，支持过滤
        
        Args:
            filters: 过滤条件，如 {"status": "online", "device_type": "iot"}
            
        Returns:
            设备列表
        """
        if not filters:
            return list(self.devices.values())
        
        result = []
        for device in self.devices.values():
            match = True
            for key, value in filters.items():
                if getattr(device, key, None) != value:
                    match = False
                    break
            if match:
                result.append(device)
        
        return result
    
    def update_device_behavior(self, mac_address: str, behavior_data: Dict) -> None:
        """更新设备行为数据
        
        Args:
            mac_address: MAC地址
            behavior_data: 行为数据
        """
        device = self.get_device(mac_address)
        if device:
            # 更新流量统计
            if "traffic" in behavior_data:
                traffic = behavior_data["traffic"]
                device.traffic_stats["bytes_in"] += traffic.get("bytes_in", 0)
                device.traffic_stats["bytes_out"] += traffic.get("bytes_out", 0)
                device.traffic_stats["packets_in"] += traffic.get("packets_in", 0)
                device.traffic_stats["packets_out"] += traffic.get("packets_out", 0)
            
            # 更新行为基线
            if "baseline" in behavior_data:
                device.behavior_baseline.update(behavior_data["baseline"])
            
            # 保存到数据库
            self._save_device_to_db(device)
    
    def add_device_to_group(self, mac_address: str, group_id: str) -> bool:
        """将设备添加到分组
        
        Args:
            mac_address: MAC地址
            group_id: 分组ID
            
        Returns:
            是否添加成功
        """
        device = self.get_device(mac_address)
        if device and group_id not in device.groups:
            device.groups.append(group_id)
            self._save_device_to_db(device)
            return True
        return False
    
    def remove_device_from_group(self, mac_address: str, group_id: str) -> bool:
        """将设备从分组中移除
        
        Args:
            mac_address: MAC地址
            group_id: 分组ID
            
        Returns:
            是否移除成功
        """
        device = self.get_device(mac_address)
        if device and group_id in device.groups:
            device.groups.remove(group_id)
            self._save_device_to_db(device)
            return True
        return False
    
    def get_devices_by_group(self, group_id: str) -> List[Device]:
        """根据分组获取设备
        
        Args:
            group_id: 分组ID
            
        Returns:
            设备列表
        """
        result = []
        for device in self.devices.values():
            if group_id in device.groups:
                result.append(device)
        return result
