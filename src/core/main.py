#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import threading
from typing import List, Dict

from .config import Config
from .device_manager import DeviceManager
from .traffic_analyzer import TrafficAnalyzer
from .signature_detection import SignatureDetector
from .anomaly_detection import AnomalyDetector
from .threat_intelligence import ThreatIntelligence
from .alert_engine import AlertEngine
from .utils import logger, setup_logging

# 导入Web服务模块
try:
    # 添加项目根目录和src目录到Python路径，以便能正确导入web模块
    import sys
    import os
    src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(src_path)
    sys.path.insert(0, project_root)
    sys.path.insert(0, src_path)
    
    from web.backend.app import init_app as init_web_app
    logger.info("✓ Web服务模块导入成功")
except ImportError as e:
    logger.warning(f"Failed to import web module: {e}")
    logger.error(f"导入错误详情: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
    init_web_app = None

class WarefireSystem:
    """家庭网络安全监控系统主类"""
    
    def __init__(self, config_path: str = None):
        """初始化系统
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置，优先使用提供的配置路径，否则尝试加载保存的配置
        if not config_path:
            import os
            saved_config_path = "../../data/config.json"
            if os.path.exists(saved_config_path):
                config_path = saved_config_path
        
        # 加载配置
        self.config = Config(config_path)
        
        # 设置日志
        log_level = self.config.get("system.log_level", "INFO")
        log_path = self.config.get("system.log_path", "../../data/logs/system.log")
        setup_logging(log_level, log_path)
        
        logger.info("Initializing Warefire System...")
        
        # 初始化各个模块
        self.device_manager = DeviceManager(self.config)
        self.threat_intelligence = ThreatIntelligence(self.config)
        self.alert_engine = AlertEngine(self.config)
        self.signature_detector = SignatureDetector(self.config)
        self.anomaly_detector = AnomalyDetector(self.config, self.device_manager)
        self.traffic_analyzer = TrafficAnalyzer(self.config, self.device_manager)
        
        logger.info("Warefire System initialized successfully")
    
    def start(self) -> None:
        """启动系统"""
        logger.info("Starting Warefire System...")
        
        # 启动各个模块
        self.signature_detector.start()
        self.anomaly_detector.start()
        self.traffic_analyzer.start()
        
        logger.info("Warefire System started successfully")
        
        # 启动Web服务
        self._start_web_service()
        
        # 设备扫描
        self._scan_devices()
        
        # 进入主循环
        self._main_loop()
    
    def _start_web_service(self) -> None:
        """启动Web服务"""
        if init_web_app:
            try:
                logger.info("Starting Web Service...")
                app = init_web_app(self)
                
                # 在单独的线程中运行Web服务
                web_thread = threading.Thread(
                    target=app.run,
                    kwargs={
                        'host': '0.0.0.0',
                        'port': 8082,
                        'debug': False,
                        'use_reloader': False
                    },
                    daemon=True
                )
                web_thread.start()
                logger.info("Web Service started successfully on http://0.0.0.0:8082")
            except Exception as e:
                logger.error(f"Failed to start Web Service: {e}")
        else:
            logger.warning("Web Service not available, skipping...")
    
    def stop(self) -> None:
        """停止系统"""
        logger.info("Stopping Warefire System...")
        
        # 停止各个模块
        self.traffic_analyzer.stop()
        self.anomaly_detector.stop()
        self.signature_detector.stop()
        
        logger.info("Warefire System stopped")
    
    def _scan_devices(self) -> None:
        """扫描网络设备"""
        logger.info("Scanning network devices...")
        devices = self.device_manager.scan_devices()
        logger.info(f"Found {len(devices)} devices on the network")
    
    def _main_loop(self) -> None:
        """系统主循环"""
        try:
            while True:
                # 每30秒执行一次设备扫描
                self._scan_devices()
                
                # 记录系统状态
                self._log_system_status()
                
                # 等待30秒
                time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, stopping system")
            self.stop()
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            self.stop()
            sys.exit(1)
    
    def _log_system_status(self) -> None:
        """记录系统状态"""
        # 获取系统统计信息
        alert_stats = self.alert_engine.get_alert_stats()
        threat_stats = self.threat_intelligence.get_stats()
        device_count = len(self.device_manager.devices)
        online_devices = len(self.device_manager.get_devices({"status": "online"}))
        
        logger.info(f"System Status - Devices: {online_devices}/{device_count} online, Alerts: {alert_stats['total_alerts']} total, Malicious IPs: {threat_stats['malicious_ips_count']}")
    
    def get_status(self) -> Dict:
        """获取系统状态
        
        Returns:
            系统状态字典
        """
        return {
            "system": {
                "mode": self.config.get("system.mode"),
                "log_level": self.config.get("system.log_level")
            },
            "devices": {
                "total": len(self.device_manager.devices),
                "online": len(self.device_manager.get_devices({"status": "online"}))
            },
            "alerts": self.alert_engine.get_alert_stats(),
            "threat_intelligence": self.threat_intelligence.get_stats(),
            "traffic": self.traffic_analyzer.get_traffic_stats()
        }

def main():
    """主函数"""
    system = WarefireSystem()
    system.start()

if __name__ == "__main__":
    main()
