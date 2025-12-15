#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import queue
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .config import Config
from .utils import logger, get_current_timestamp

# 尝试导入scapy库，用于流量捕获和解析
try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP, ARP, Ether
    SCAPY_AVAILABLE = True
    logger.info("Scapy library loaded successfully")
except ImportError as e:
    SCAPY_AVAILABLE = False
    logger.warning(f"Scapy library not available: {e}")

class TrafficPacket:
    """流量数据包类，封装数据包信息"""
    
    def __init__(self):
        self.timestamp = get_current_timestamp()
        self.mac_src = ""
        self.mac_dst = ""
        self.ip_src = ""
        self.ip_dst = ""
        self.port_src = 0
        self.port_dst = 0
        self.protocol = ""
        self.packet_size = 0
        self.payload_size = 0
        self.payload = b""
        self.tcp_flags = ""
        self.tcp_seq = 0
        self.tcp_ack = 0
        self.udp_length = 0
        self.icmp_type = 0
        self.icmp_code = 0
    
    def to_dict(self) -> Dict:
        """转换为字典
        
        Returns:
            数据包信息字典
        """
        return {
            "timestamp": self.timestamp,
            "mac_src": self.mac_src,
            "mac_dst": self.mac_dst,
            "ip_src": self.ip_src,
            "ip_dst": self.ip_dst,
            "port_src": self.port_src,
            "port_dst": self.port_dst,
            "protocol": self.protocol,
            "packet_size": self.packet_size,
            "payload_size": self.payload_size,
            "payload": self.payload.hex() if self.payload else "",
            "tcp_flags": self.tcp_flags,
            "tcp_seq": self.tcp_seq,
            "tcp_ack": self.tcp_ack,
            "udp_length": self.udp_length,
            "icmp_type": self.icmp_type,
            "icmp_code": self.icmp_code
        }

class FlowSession:
    """流量会话类，代表一个完整的网络连接"""
    
    def __init__(self, mac_src: str, mac_dst: str, ip_src: str, ip_dst: str, port_src: int, port_dst: int, protocol: str):
        """初始化流量会话
        
        Args:
            mac_src: 源MAC地址
            mac_dst: 目标MAC地址
            ip_src: 源IP地址
            ip_dst: 目标IP地址
            port_src: 源端口
            port_dst: 目标端口
            protocol: 协议类型
        """
        self.mac_src = mac_src
        self.mac_dst = mac_dst
        self.ip_src = ip_src
        self.ip_dst = ip_dst
        self.port_src = port_src
        self.port_dst = port_dst
        self.protocol = protocol
        self.start_time = get_current_timestamp()
        self.end_time = 0
        self.packets_in = 0
        self.packets_out = 0
        self.bytes_in = 0
        self.bytes_out = 0
        self.state = "active"  # active, closed, timeout
    
    def update(self, packet: TrafficPacket, direction: str) -> None:
        """更新会话信息
        
        Args:
            packet: 数据包
            direction: 方向，"in"或"out"
        """
        if direction == "in":
            self.packets_in += 1
            self.bytes_in += packet.packet_size
        else:
            self.packets_out += 1
            self.bytes_out += packet.packet_size
        
        self.end_time = get_current_timestamp()
    
    def to_dict(self) -> Dict:
        """转换为字典
        
        Returns:
            会话信息字典
        """
        return {
            "mac_src": self.mac_src,
            "mac_dst": self.mac_dst,
            "ip_src": self.ip_src,
            "ip_dst": self.ip_dst,
            "port_src": self.port_src,
            "port_dst": self.port_dst,
            "protocol": self.protocol,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time if self.end_time > 0 else 0,
            "packets_in": self.packets_in,
            "packets_out": self.packets_out,
            "bytes_in": self.bytes_in,
            "bytes_out": self.bytes_out,
            "total_bytes": self.bytes_in + self.bytes_out,
            "state": self.state
        }

class TrafficAnalyzer:
    """流量分析器，负责捕获和分析网络流量"""
    
    def __init__(self, config: Config, device_manager):
        """初始化流量分析器
        
        Args:
            config: 配置对象
            device_manager: 设备管理器对象
        """
        self.config = config
        self.device_manager = device_manager
        self.enabled = config.get("traffic_analyzer.enabled", True)
        self.interfaces = config.get("traffic_analyzer.interfaces", ["eth0", "wlan0"])
        self.capture_filter = config.get("traffic_analyzer.capture_filter", "")
        self.max_packet_size = config.get("traffic_analyzer.max_packet_size", 1518)
        self.buffer_size = config.get("traffic_analyzer.buffer_size", 1024 * 1024 * 100)
        
        self.is_running = False
        self.capture_threads = []
        self.packet_queue = queue.Queue(maxsize=10000)
        self.analysis_thread = None
        
        # 流量会话管理
        self.flow_sessions = {}
        self.session_timeout = 300  # 会话超时时间（秒）
        
        # 流量统计
        self.traffic_stats = {
            "total_packets": 0,
            "total_bytes": 0,
            "inbound_packets": 0,
            "inbound_bytes": 0,
            "outbound_packets": 0,
            "outbound_bytes": 0,
            "protocol_distribution": {},
            "top_talkers": {},
            "top_destinations": {},
            "traffic_rate": 0,  # 字节/秒
            "packets_per_second": 0
        }
        
        # 用于计算速率的历史数据
        self._rate_history = []  # (timestamp, bytes) 列表
        self._rate_window = 5  # 速率计算窗口（秒）
        
        # 在Windows系统上，使用更通用的接口列表
        if sys.platform == "win32":
            logger.info("Running on Windows, using 'all' as network interface")
            self.interfaces = ["all"]
    
    def start(self) -> None:
        """启动流量分析器"""
        if not self.enabled:
            logger.info("Traffic analyzer is disabled by configuration")
            return
        
        if self.is_running:
            logger.warning("Traffic analyzer is already running")
            return
        
        logger.info("Starting traffic analyzer...")
        
        # 先设置运行标志，确保线程能正常执行
        self.is_running = True
        
        # 在Windows系统上或Scapy不可用时，使用模拟数据生成
        if sys.platform == "win32" or not SCAPY_AVAILABLE:
            logger.info("Using mock data generation for traffic analyzer")
            # 启动数据包分析线程
            self.analysis_thread = threading.Thread(target=self._analyze_packets, daemon=True)
            self.analysis_thread.start()
            
            # 启动会话清理线程
            self.cleanup_thread = threading.Thread(target=self._cleanup_sessions, daemon=True)
            self.cleanup_thread.start()
            
            # 启动模拟数据生成线程
            self.mock_data_thread = threading.Thread(target=self._generate_mock_data, daemon=True)
            self.mock_data_thread.start()
        else:
            # 启动数据包捕获线程
            for interface in self.interfaces:
                thread = threading.Thread(target=self._capture_traffic, args=(interface,), daemon=True)
                self.capture_threads.append(thread)
                thread.start()
            
            # 启动数据包分析线程
            self.analysis_thread = threading.Thread(target=self._analyze_packets, daemon=True)
            self.analysis_thread.start()
            
            # 启动会话清理线程
            self.cleanup_thread = threading.Thread(target=self._cleanup_sessions, daemon=True)
            self.cleanup_thread.start()
        
        logger.info("Traffic analyzer started successfully")
    
    def stop(self) -> None:
        """停止流量分析器"""
        if not self.is_running:
            return
        
        logger.info("Stopping traffic analyzer...")
        
        self.is_running = False
        
        # 等待捕获线程结束
        for thread in self.capture_threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        # 等待分析线程结束
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=5)
        
        # 等待清理线程结束
        if hasattr(self, 'cleanup_thread') and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
        
        self.capture_threads.clear()
        logger.info("Traffic analyzer stopped")
    
    def _capture_traffic(self, interface: str) -> None:
        """捕获指定接口的流量
        
        Args:
            interface: 网络接口名称
        """
        logger.info(f"Starting traffic capture on interface {interface}")
        
        try:
            sniff(
                iface=interface,
                filter=self.capture_filter,
                prn=self._process_packet,
                store=False,
                stop_filter=lambda x: not self.is_running
            )
        except Exception as e:
            logger.error(f"Error capturing traffic on interface {interface}: {e}")
        
        logger.info(f"Stopped traffic capture on interface {interface}")
    
    def _process_packet(self, scapy_packet) -> None:
        """处理捕获到的数据包
        
        Args:
            scapy_packet: Scapy数据包对象
        """
        try:
            # 解析数据包
            packet = self._parse_scapy_packet(scapy_packet)
            if packet:
                # 将数据包放入队列进行后续分析
                self.packet_queue.put(packet, block=False)
        except Exception as e:
            logger.debug(f"Error processing packet: {e}")
    
    def _parse_scapy_packet(self, scapy_packet) -> Optional[TrafficPacket]:
        """解析Scapy数据包
        
        Args:
            scapy_packet: Scapy数据包对象
            
        Returns:
            解析后的TrafficPacket对象，解析失败返回None
        """
        packet = TrafficPacket()
        
        # 设置数据包大小
        packet.packet_size = len(scapy_packet)
        
        # 解析以太网层
        if Ether in scapy_packet:
            packet.mac_src = scapy_packet[Ether].src
            packet.mac_dst = scapy_packet[Ether].dst
        
        # 解析IP层
        if IP in scapy_packet:
            packet.ip_src = scapy_packet[IP].src
            packet.ip_dst = scapy_packet[IP].dst
            
            # 解析传输层
            if TCP in scapy_packet:
                packet.protocol = "TCP"
                packet.port_src = scapy_packet[TCP].sport
                packet.port_dst = scapy_packet[TCP].dport
                packet.tcp_flags = self._get_tcp_flags(scapy_packet[TCP].flags)
                packet.tcp_seq = scapy_packet[TCP].seq
                packet.tcp_ack = scapy_packet[TCP].ack
                packet.payload = bytes(scapy_packet[TCP].payload)
            elif UDP in scapy_packet:
                packet.protocol = "UDP"
                packet.port_src = scapy_packet[UDP].sport
                packet.port_dst = scapy_packet[UDP].dport
                packet.udp_length = scapy_packet[UDP].len
                packet.payload = bytes(scapy_packet[UDP].payload)
            elif ICMP in scapy_packet:
                packet.protocol = "ICMP"
                packet.icmp_type = scapy_packet[ICMP].type
                packet.icmp_code = scapy_packet[ICMP].code
                packet.payload = bytes(scapy_packet[ICMP].payload)
        elif ARP in scapy_packet:
            packet.protocol = "ARP"
            packet.mac_src = scapy_packet[ARP].hwsrc
            packet.mac_dst = scapy_packet[ARP].hwdst
            packet.ip_src = scapy_packet[ARP].psrc
            packet.ip_dst = scapy_packet[ARP].pdst
        
        packet.payload_size = len(packet.payload)
        return packet
    
    def _get_tcp_flags(self, flags) -> str:
        """获取TCP标志字符串
        
        Args:
            flags: TCP标志值
            
        Returns:
            TCP标志字符串，如 "SYN, ACK"
        """
        flag_names = {
            0x01: "FIN",
            0x02: "SYN",
            0x04: "RST",
            0x08: "PSH",
            0x10: "ACK",
            0x20: "URG",
            0x40: "ECE",
            0x80: "CWR"
        }
        
        set_flags = []
        for flag_val, flag_name in flag_names.items():
            if flags & flag_val:
                set_flags.append(flag_name)
        
        return ", ".join(set_flags)
    
    def _analyze_packets(self) -> None:
        """分析队列中的数据包"""
        logger.info("Starting packet analysis thread")
        
        while self.is_running:
            try:
                packet = self.packet_queue.get(timeout=1)
                self._analyze_single_packet(packet)
                self.packet_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error analyzing packet: {e}")
        
        logger.info("Stopped packet analysis thread")
    
    def _analyze_single_packet(self, packet: TrafficPacket) -> None:
        """分析单个数据包
        
        Args:
            packet: 数据包对象
        """
        # 更新总体流量统计
        self._update_traffic_stats(packet)
        
        # 管理流量会话
        self._manage_flow_session(packet)
        
        # 更新设备流量统计
        self._update_device_traffic(packet)
        
        # TODO: 进一步分析，如协议识别、应用识别等
    
    def _update_traffic_stats(self, packet: TrafficPacket) -> None:
        """更新流量统计信息
        
        Args:
            packet: 数据包对象
        """
        current_time = get_current_timestamp()
        
        # 更新总流量统计
        self.traffic_stats["total_packets"] += 1
        self.traffic_stats["total_bytes"] += packet.packet_size
        
        # 简单区分入站和出站流量（实际应用中需要根据网络拓扑区分）
        # 这里假设本地网络是192.168.0.0/24网段
        is_inbound = not packet.ip_src.startswith("192.168.0.") and packet.ip_dst.startswith("192.168.0.")
        is_outbound = packet.ip_src.startswith("192.168.0.") and not packet.ip_dst.startswith("192.168.0.")
        
        if is_inbound:
            self.traffic_stats["inbound_packets"] += 1
            self.traffic_stats["inbound_bytes"] += packet.packet_size
        elif is_outbound:
            self.traffic_stats["outbound_packets"] += 1
            self.traffic_stats["outbound_bytes"] += packet.packet_size
        else:
            # 同一网段内的流量，平均分配到入站和出站
            self.traffic_stats["inbound_packets"] += 0.5
            self.traffic_stats["inbound_bytes"] += packet.packet_size / 2
            self.traffic_stats["outbound_packets"] += 0.5
            self.traffic_stats["outbound_bytes"] += packet.packet_size / 2
        
        # 更新协议分布
        if packet.protocol not in self.traffic_stats["protocol_distribution"]:
            self.traffic_stats["protocol_distribution"][packet.protocol] = 0
        self.traffic_stats["protocol_distribution"][packet.protocol] += 1
        
        # 更新Top Talkers
        for ip in [packet.ip_src, packet.ip_dst]:
            if ip not in self.traffic_stats["top_talkers"]:
                self.traffic_stats["top_talkers"][ip] = 0
            self.traffic_stats["top_talkers"][ip] += packet.packet_size
        
        # 更新Top Destinations
        if packet.ip_dst not in self.traffic_stats["top_destinations"]:
            self.traffic_stats["top_destinations"][packet.ip_dst] = 0
        self.traffic_stats["top_destinations"][packet.ip_dst] += packet.packet_size
        
        # 更新速率历史
        self._rate_history.append((current_time, packet.packet_size))
        
        # 计算流量速率
        self._calculate_rate()
    
    def _calculate_rate(self) -> None:
        """计算流量速率"""
        current_time = get_current_timestamp()
        
        # 清理旧数据
        cutoff_time = current_time - self._rate_window
        self._rate_history = [entry for entry in self._rate_history if entry[0] >= cutoff_time]
        
        if not self._rate_history:
            # 没有数据时重置速率
            self.traffic_stats["traffic_rate"] = 0
            self.traffic_stats["packets_per_second"] = 0
            return
        
        # 计算总字节数和数据包数
        total_bytes = sum(entry[1] for entry in self._rate_history)
        total_packets = len(self._rate_history)
        
        # 计算持续时间
        duration = current_time - self._rate_history[0][0] or 1  # 避免除以0
        
        # 计算速率
        self.traffic_stats["traffic_rate"] = total_bytes / duration
        self.traffic_stats["packets_per_second"] = total_packets / duration
    
    def _manage_flow_session(self, packet: TrafficPacket) -> None:
        """管理流量会话
        
        Args:
            packet: 数据包对象
        """
        if not packet.ip_src or not packet.ip_dst:
            return
        
        # 生成会话ID（源IP:源端口-目标IP:目标端口-协议）
        session_key = f"{packet.ip_src}:{packet.port_src}-{packet.ip_dst}:{packet.port_dst}-{packet.protocol}"
        reverse_key = f"{packet.ip_dst}:{packet.port_dst}-{packet.ip_src}:{packet.port_src}-{packet.protocol}"
        
        # 检查会话是否已存在
        session = self.flow_sessions.get(session_key)
        if not session:
            session = self.flow_sessions.get(reverse_key)
            if session:
                # 反向会话，更新为入站流量
                session.update(packet, "in")
            else:
                # 新会话
                session = FlowSession(
                    packet.mac_src,
                    packet.mac_dst,
                    packet.ip_src,
                    packet.ip_dst,
                    packet.port_src,
                    packet.port_dst,
                    packet.protocol
                )
                session.update(packet, "out")
                self.flow_sessions[session_key] = session
        else:
            # 现有会话，更新为出站流量
            session.update(packet, "out")
    
    def _update_device_traffic(self, packet: TrafficPacket) -> None:
        """更新设备流量统计
        
        Args:
            packet: 数据包对象
        """
        # 更新源设备流量
        if packet.mac_src:
            device = self.device_manager.get_device(packet.mac_src)
            if device:
                behavior_data = {
                    "traffic": {
                        "bytes_out": packet.packet_size,
                        "packets_out": 1
                    }
                }
                self.device_manager.update_device_behavior(packet.mac_src, behavior_data)
        
        # 更新目标设备流量（如果是本地设备）
        if packet.mac_dst:
            device = self.device_manager.get_device(packet.mac_dst)
            if device:
                behavior_data = {
                    "traffic": {
                        "bytes_in": packet.packet_size,
                        "packets_in": 1
                    }
                }
                self.device_manager.update_device_behavior(packet.mac_dst, behavior_data)
    
    def _cleanup_sessions(self) -> None:
        """清理超时的流量会话"""
        logger.info("Starting session cleanup thread")
        
        while self.is_running:
            current_time = get_current_timestamp()
            expired_sessions = []
            
            # 检查所有会话
            for session_key, session in self.flow_sessions.items():
                if current_time - session.end_time > self.session_timeout:
                    session.state = "timeout"
                    expired_sessions.append(session_key)
            
            # 移除超时会话
            for session_key in expired_sessions:
                del self.flow_sessions[session_key]
            
            # 每60秒清理一次
            import time
            time.sleep(60)
        
        logger.info("Stopped session cleanup thread")
    
    def get_traffic_stats(self) -> Dict:
        """获取流量统计信息
        
        Returns:
            流量统计字典
        """
        return self.traffic_stats
    
    def get_active_sessions(self) -> List[Dict]:
        """获取活跃会话列表
        
        Returns:
            活跃会话列表
        """
        active_sessions = []
        for session in self.flow_sessions.values():
            if session.state == "active":
                active_sessions.append(session.to_dict())
        return active_sessions
    
    def get_top_talkers(self, limit: int = 10) -> List[Tuple[str, int]]:
        """获取Top Talkers列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            Top Talkers列表，格式：[(IP, 流量大小), ...]
        """
        top_talkers = sorted(
            self.traffic_stats["top_talkers"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        return top_talkers[:limit]
    
    def get_protocol_distribution(self) -> Dict:
        """获取协议分布
        
        Returns:
            协议分布字典
        """
        return self.traffic_stats["protocol_distribution"]
    
    def _generate_mock_data(self) -> None:
        """生成模拟流量数据，用于Windows系统测试"""
        logger.info("Starting mock data generation...")
        
        protocols = ["TCP", "UDP", "ICMP", "ARP"]
        
        # 扩展IP列表，包含更多真实外部IP和常见网站IP
        internal_ips = ["192.168.0.1", "192.168.0.2", "192.168.0.3", "192.168.0.4", "192.168.0.5"]
        external_ips = [
            # 常见DNS服务器
            "8.8.8.8", "8.8.4.4", "114.114.114.114", "223.5.5.5",
            # GitHub IP地址
            "140.82.113.3", "140.82.114.3", "140.82.114.4", "140.82.112.4",
            # 其他常见网站IP
            "104.244.42.129",  # Twitter
            "157.240.1.35",    # Facebook
            "93.184.216.34",    # Wikipedia
            "208.67.222.222",   # OpenDNS
            "1.1.1.1",          # Cloudflare
            "209.85.220.138",   # Google
            "52.217.0.25",      # AWS
            "51.103.5.138",     # Azure
            "185.199.108.153",  # GitHub
            "185.199.109.153",  # GitHub
            "185.199.110.153",  # GitHub
            "185.199.111.153"   # GitHub
        ]
        
        # 合并所有IP
        ips = internal_ips + external_ips
        macs = ["00:00:00:00:00:01", "00:00:00:00:00:02", "00:00:00:00:00:03", "00:00:00:00:00:04", "00:00:00:00:00:05"]
        
        import time
        import random
        
        while self.is_running:
            try:
                # 创建模拟数据包
                packet = TrafficPacket()
                packet.timestamp = get_current_timestamp()
                
                # 使用随机选择，使模拟数据更真实
                packet.mac_src = random.choice(macs)
                packet.mac_dst = random.choice(macs)
                
                # 70%的概率是内部到外部的流量，30%是内部到内部的流量
                if random.random() < 0.7:
                    # 内部到外部
                    packet.ip_src = random.choice(internal_ips)
                    packet.ip_dst = random.choice(external_ips)
                else:
                    # 内部到内部
                    packet.ip_src = random.choice(internal_ips)
                    packet.ip_dst = random.choice(internal_ips)
                    # 确保源IP和目标IP不同
                    while packet.ip_src == packet.ip_dst:
                        packet.ip_dst = random.choice(internal_ips)
                
                packet.protocol = random.choice(protocols)
                packet.packet_size = 64 + random.randint(0, 1000)
                
                # 放入队列进行分析
                self.packet_queue.put(packet, block=False)
                
                # 每100ms生成一个数据包
                time.sleep(0.1)
            except queue.Full:
                continue
            except Exception as e:
                logger.error(f"Error generating mock data: {e}")
                time.sleep(1)
