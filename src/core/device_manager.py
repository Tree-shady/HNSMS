#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import re
import sqlite3
import sys
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
        self.main_router_ip = config.get("device_manager.main_router_ip", "")
        self.include_local_machine = config.get("device_manager.include_local_machine", False)
        
        # 获取本机IP和MAC地址
        self.local_ips, self.local_macs = self._get_local_addresses()
        
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
        
        # 使用arp命令扫描设备
        try:
            # 在Windows上使用arp命令，添加超时处理
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=10  # 添加10秒超时
            )
            
            if result.returncode != 0:
                logger.error(f"Error running arp scan: {result.stderr}")
                return []
            
            devices = self._parse_arp_output(result.stdout)
            
            # 对每个设备进行更详细的识别，使用异步方式避免阻塞
            for device in devices:
                try:
                    self._identify_device(device)
                except Exception as e:
                    logger.error(f"Error identifying device {device.mac_address}: {e}")
                    # 即使识别失败，也继续处理其他设备
                    continue
                
            # 更新设备状态
            self._update_device_status(devices)
            
            logger.info(f"Found {len(devices)} devices on the network")
            return devices
        except subprocess.TimeoutExpired:
            logger.error("ARP scan timed out")
            return []
        except Exception as e:
            logger.error(f"Error scanning devices: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _get_local_addresses(self) -> tuple:
        """获取本机IP和MAC地址
        
        Returns:
            (local_ips, local_macs) - 本机IP地址列表和MAC地址列表
        """
        import socket
        import subprocess
        import re
        
        local_ips = []
        local_macs = []
        
        try:
            # 获取本机IP地址
            hostname = socket.gethostname()
            local_ips = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
            local_ips = [addr[4][0] for addr in local_ips]
            
            # 获取本机MAC地址
            if sys.platform == "win32":
                # Windows系统使用ipconfig命令
                result = subprocess.run(
                    ["ipconfig", "/all"],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                
                # 解析MAC地址
                mac_pattern = r"Physical Address.*?: ([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})"
                mac_matches = re.findall(mac_pattern, result.stdout)
                local_macs = [mac.replace("-", ":").lower() for mac in mac_matches]
            else:
                # Linux/macOS系统使用ifconfig或ip命令
                result = subprocess.run(
                    ["ifconfig"],
                    capture_output=True,
                    text=True
                )
                
                # 解析MAC地址
                mac_pattern = r"ether ([0-9a-f:]{17})"
                mac_matches = re.findall(mac_pattern, result.stdout)
                local_macs = [mac.lower() for mac in mac_matches]
                
        except Exception as e:
            logger.error(f"Error getting local addresses: {e}")
        
        return local_ips, local_macs
    
    def _parse_arp_output(self, output: str) -> List[Device]:
        """解析arp命令输出
        
        Args:
            output: arp命令输出
            
        Returns:
            设备列表
        """
        devices = []
        seen_macs = set()  # 用于去重
        
        # 匹配MAC地址和IP地址的正则表达式（优化版，支持多种ARP输出格式）
        # 格式1: IP地址 物理地址 类型
        # 格式2: IP地址          MAC地址
        # 支持多种分隔符：空格、制表符等
        pattern = r'([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})'
        
        matches = re.finditer(pattern, output, re.IGNORECASE)
        
        for match in matches:
            ip_address = match.group(1)
            mac_address = match.group(2).replace("-", ":").lower()
            
            # 跳过无效MAC地址
            if mac_address == "00:00:00:00:00:00" or mac_address == "ff:ff:ff:ff:ff:ff":
                continue
            
            # 跳过重复设备
            if mac_address in seen_macs:
                continue
            seen_macs.add(mac_address)
            
            # 跳过广播地址、多播地址和网络地址
            if (ip_address == "255.255.255.255" or  # 广播地址
                ip_address.startswith("224.") or  # 多播地址
                ip_address.startswith("239.") or  # 多播地址
                ip_address.endswith(".0") or  # 网络地址
                ip_address.endswith(".255")):  # 广播地址
                continue
            
            # 跳过本机设备（如果配置了不包含）
            if not self.include_local_machine:
                if ip_address in self.local_ips or mac_address in self.local_macs:
                    continue
            
            device = Device(mac_address, ip_address)
            
            # 标记主路由器
            if ip_address == self.main_router_ip:
                device.hostname = "Main Router"
                device.device_type = "router"
                device.manufacturer = "Router"
            
            devices.append(device)
        
        return devices
    
    def _identify_device(self, device: Device) -> None:
        """识别设备信息
        
        Args:
            device: 设备对象
        """
        # 1. 根据MAC地址识别厂商
        self._identify_manufacturer(device)
        
        # 2. DNS反向查询获取主机名
        self._dns_reverse_lookup(device)
        
        # 3. 使用nmap进行更详细的设备识别
        self._nmap_device_scan(device)
        
        # 4. 根据设备特征推断设备类型
        self._infer_device_type(device)
        
        # 5. 生成默认设备名称（如果没有主机名）
        self._generate_default_name(device)
    
    def _identify_manufacturer(self, device: Device) -> None:
        """根据MAC地址识别厂商
        
        Args:
            device: 设备对象
        """
        # MAC地址前三位(OUI)对应厂商
        oui = device.mac_address[:8].upper()
        
        # 扩展厂商映射表
        oui_map = {
            # 虚拟设备
            "00:0C:29": "VMware",
            "00:50:56": "VMware",
            "08:00:27": "Oracle VirtualBox",
            "52:54:00": "QEMU/KVM",
            "FC:AA:14": "Raspberry Pi",
            
            # 主流厂商
            "00:18:E7": "Apple",
            "00:1C:42": "Apple",
            "18:5E:0F": "Apple",
            "2C:F0:5D": "Apple",
            "AC:BC:32": "Apple",
            "F0:18:98": "Apple",
            "00:09:6B": "Dell",
            "00:11:22": "Dell",
            "00:14:22": "Dell",
            "00:15:C5": "Dell",
            "00:19:B9": "Dell",
            "00:1B:21": "Dell",
            "00:22:48": "Dell",
            "00:50:56": "Dell",
            "3C:52:82": "Dell",
            "44:8A:5B": "Dell",
            "58:20:B1": "Dell",
            "78:2B:CB": "Dell",
            "00:0D:3A": "HP",
            "00:17:A4": "HP",
            "00:1A:4B": "HP",
            "00:1E:0B": "HP",
            "00:24:81": "HP",
            "00:25:B3": "HP",
            "00:30:48": "HP",
            "08:62:66": "HP",
            "10:1F:74": "HP",
            "18:67:B0": "HP",
            "28:80:88": "HP",
            "38:BA:F8": "HP",
            "48:F8:B3": "HP",
            "5C:B9:01": "HP",
            "6C:B3:11": "HP",
            "B8:CA:3A": "HP",
            "00:23:15": "Lenovo",
            "00:25:64": "Lenovo",
            "00:26:18": "Lenovo",
            "00:27:10": "Lenovo",
            "00:50:56": "Lenovo",
            "34:97:F6": "Lenovo",
            "48:51:B7": "Lenovo",
            "5C:B1:3E": "Lenovo",
            "7C:D1:C3": "Lenovo",
            "AC:81:12": "Lenovo",
            "B0:5A:DA": "Lenovo",
            "D0:50:99": "Lenovo",
            "EC:F4:BB": "Lenovo",
            "00:1A:6B": "ASUS",
            "00:1E:8C": "ASUS",
            "00:24:81": "ASUS",
            "08:62:66": "ASUS",
            "10:1F:74": "ASUS",
            "18:67:B0": "ASUS",
            "28:80:88": "ASUS",
            "30:5A:3A": "ASUS",
            "40:8D:5C": "ASUS",
            "50:46:5D": "ASUS",
            "5C:F3:FC": "ASUS",
            "70:85:C2": "ASUS",
            "74:2F:68": "ASUS",
            "78:45:C4": "ASUS",
            "8C:7B:9D": "ASUS",
            "9C:B6:54": "ASUS",
            "AC:22:0B": "ASUS",
            "BC:5F:F4": "ASUS",
            "CC:46:D6": "ASUS",
            "DC:FB:48": "ASUS",
            "E0:CB:4E": "ASUS",
            "FC:34:97": "ASUS",
            "00:16:EA": "Samsung",
            "00:23:A3": "Samsung",
            "00:24:1D": "Samsung",
            "00:25:64": "Samsung",
            "00:26:18": "Samsung",
            "00:27:10": "Samsung",
            "00:2B:67": "Samsung",
            "00:30:67": "Samsung",
            "00:31:92": "Samsung",
            "00:40:5C": "Samsung",
            "08:30:6B": "Samsung",
            "10:6F:3F": "Samsung",
            "14:C2:CC": "Samsung",
            "18:65:90": "Samsung",
            "20:79:18": "Samsung",
            "28:39:26": "Samsung",
            "30:B4:9E": "Samsung",
            "34:E8:94": "Samsung",
            "38:2C:4A": "Samsung",
            "40:0E:85": "Samsung",
            "5C:3A:45": "Samsung",
            "5C:F8:A1": "Samsung",
            "7C:5C:F8": "Samsung",
            "88:B1:11": "Samsung",
            "90:E7:C4": "Samsung",
            "A0:99:9B": "Samsung",
            "AC:22:0B": "Samsung",
            "B4:B5:2F": "Samsung",
            "C0:18:85": "Samsung",
            "C4:8E:8F": "Samsung",
            "C8:3A:35": "Samsung",
            "D0:21:F9": "Samsung",
            "D4:6E:0E": "Samsung",
            "DC:53:60": "Samsung",
            "E0:94:67": "Samsung",
            "E8:04:62": "Samsung",
            "F8:B1:56": "Samsung",
            "00:25:9C": "Microsoft",
            "00:50:F2": "Microsoft",
            "00:90:4B": "Microsoft",
            "3C:52:82": "Microsoft",
            "5C:51:88": "Microsoft",
            "70:77:81": "Microsoft",
            "D8:BB:C1": "Microsoft",
            "D8:F2:CA": "Microsoft",
            "FC:AA:14": "Raspberry Pi",
            "B8:27:EB": "Raspberry Pi",
            "DC:A6:32": "Raspberry Pi",
            "E4:5F:01": "Raspberry Pi",
            "00:16:3E": "Google",
            "00:1A:11": "Google",
            "00:21:F6": "Google",
            "00:23:12": "Google",
            "00:24:1D": "Google",
            "00:25:90": "Google",
            "00:26:18": "Google",
            "00:27:10": "Google",
            "00:30:67": "Google",
            "00:31:92": "Google",
            "00:40:5C": "Google",
            "00:40:96": "Google",
            "00:40:9D": "Google",
            "00:50:56": "Google",
            "00:50:C2": "Google",
            "00:50:F2": "Google",
            "00:A0:C9": "Intel",
            "00:1B:21": "Intel",
            "00:1C:C0": "Intel",
            "00:1E:67": "Intel",
            "00:1F:29": "Intel",
            "00:21:9B": "Intel",
            "00:22:41": "Intel",
            "00:23:45": "Intel",
            "00:24:7E": "Intel",
            "00:25:90": "Intel",
            "00:26:B9": "Intel",
            "00:27:0E": "Intel",
            "00:30:67": "Intel",
            "00:31:92": "Intel",
            "00:40:96": "Intel",
            "00:40:9D": "Intel",
            "00:50:56": "Intel",
            "00:50:F2": "Intel",
            "00:60:6E": "Intel",
            "00:A0:C9": "Intel",
            "00:E0:4C": "Realtek",
            "70:85:C2": "Realtek",
            "00:00:00": "Unknown"
        }
        
        device.manufacturer = oui_map.get(oui, "unknown")
    
    def _nmap_device_scan(self, device: Device) -> None:
        """使用nmap扫描设备详细信息
        
        Args:
            device: 设备对象
        """
        try:
            # 检查nmap是否可用
            subprocess.run(
                ["nmap", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # 使用nmap进行OS检测和服务扫描
            result = subprocess.run(
                ["nmap", "-O", "-sV", "-T4", device.ip_address],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self._parse_nmap_output(device, result.stdout)
            else:
                logger.debug(f"nmap scan returned non-zero exit code for {device.ip_address}: {result.stderr}")
        except FileNotFoundError:
            logger.debug(f"nmap is not installed, skipping device scan for {device.ip_address}")
        except subprocess.TimeoutExpired:
            logger.debug(f"nmap scan timed out for {device.ip_address}")
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
    
    def _dns_reverse_lookup(self, device: Device) -> None:
        """DNS反向查询获取主机名
        
        Args:
            device: 设备对象
        """
        if not device.ip_address:
            return
        
        try:
            # 检查nslookup是否可用
            subprocess.run(
                ["nslookup", "--version"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            # 使用nslookup进行反向查询
            result = subprocess.run(
                ["nslookup", device.ip_address],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # 解析反向查询结果（支持多种格式）
                # 格式1: name = hostname.example.com
                hostname_match = re.search(r"name\s*=\s*(.+?)\.\s*\n", result.stdout, re.IGNORECASE)
                if hostname_match and hostname_match.group(1):
                    device.hostname = hostname_match.group(1)
                else:
                    # 格式2: hostname.example.com
                    hostname_match = re.search(r"^[^\s]+\s*\n\s*(.+?)\.\s*\n", result.stdout, re.MULTILINE)
                    if hostname_match and hostname_match.group(1):
                        device.hostname = hostname_match.group(1)
        except FileNotFoundError:
            logger.debug(f"nslookup is not installed, skipping DNS lookup for {device.ip_address}")
        except subprocess.TimeoutExpired:
            logger.debug(f"DNS lookup timed out for {device.ip_address}")
        except Exception as e:
            logger.debug(f"Error performing DNS lookup on {device.ip_address}: {e}")
    
    def _infer_device_type(self, device: Device) -> None:
        """根据设备特征推断设备类型
        
        Args:
            device: 设备对象
        """
        # 如果已经有设备类型，直接返回
        if device.device_type != "unknown":
            return
        
        # 根据设备类型关键词推断，优先级：OS > 主机名 > 厂商
        type_keywords = {
            "computer": ["Windows", "Linux", "macOS", "Ubuntu", "Debian", "Fedora", "CentOS", "Red Hat", "Arch Linux"],
            "mobile": ["Android", "iOS", "iPhone", "iPad", "iPod", "Galaxy", "Pixel", "Nexus"],
            "iot": ["IoT", "Smart", "Embedded", "Home", "Smart Home", "Smart Speaker", "Smart TV", "Smart Watch"],
            "camera": ["Camera", "IP Camera", "Webcam", "Security Camera", "Surveillance"],
            "printer": ["Printer", "Print Server"],
            "router": ["Router", "Gateway", "Modem", "Access Point", "Wireless"],
            "switch": ["Switch", "Network Switch", "Ethernet Switch"]
        }
        
        # 多轮匹配，确保找到最准确的设备类型
        for device_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in device.os or keyword.lower() in device.os.lower() or \
                   keyword in device.hostname or keyword.lower() in device.hostname.lower() or \
                   keyword in device.manufacturer or keyword.lower() in device.manufacturer.lower():
                    device.device_type = device_type
                    return
        
        # 如果还是未知，默认设为computer
        device.device_type = "computer"
    
    def _generate_default_name(self, device: Device) -> None:
        """生成默认设备名称
        
        Args:
            device: 设备对象
        """
        if not device.hostname:
            # 使用厂商+MAC地址后6位生成默认名称
            short_mac = device.mac_address[-8:].replace(":", "")
            device.hostname = f"{device.manufacturer.capitalize()}-{short_mac}"
    
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
