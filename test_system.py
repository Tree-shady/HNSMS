#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
家庭网络安全监控系统 - 简单测试脚本
"""

import sys
import time

def test_module_import():
    """测试模块导入"""
    print("测试模块导入...")
    try:
        from src.core import (
            Config,
            DeviceManager,
            TrafficAnalyzer,
            SignatureDetector,
            AnomalyDetector,
            ThreatIntelligence,
            AlertEngine
        )
        print("✓ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_config_loading():
    """测试配置加载"""
    print("\n测试配置加载...")
    try:
        from src.core import Config
        config = Config()
        print(f"✓ 配置加载成功")
        print(f"  系统模式: {config.get('system.mode')}")
        print(f"  学习期: {config.get('system.learning_period_days')}天")
        print(f"  日志级别: {config.get('system.log_level')}")
        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False

def test_device_manager():
    """测试设备管理器"""
    print("\n测试设备管理器...")
    try:
        from src.core import Config, DeviceManager
        config = Config()
        device_manager = DeviceManager(config)
        print(f"✓ 设备管理器初始化成功")
        
        # 扫描设备
        devices = device_manager.scan_devices()
        print(f"✓ 设备扫描完成，发现 {len(devices)} 个设备")
        return True
    except Exception as e:
        print(f"✗ 设备管理器测试失败: {e}")
        return False

def test_alert_engine():
    """测试告警引擎"""
    print("\n测试告警引擎...")
    try:
        from src.core import Config, AlertEngine
        config = Config()
        alert_engine = AlertEngine(config)
        print(f"✓ 告警引擎初始化成功")
        
        # 创建测试告警
        alert = alert_engine.create_alert(
            alert_type="test",
            severity="info",
            source="test_script",
            description="测试告警",
            details={"test_key": "test_value"}
        )
        print(f"✓ 创建测试告警成功，告警ID: {alert.alert_id}")
        
        # 获取告警统计
        stats = alert_engine.get_alert_stats()
        print(f"✓ 告警统计: {stats}")
        return True
    except Exception as e:
        print(f"✗ 告警引擎测试失败: {e}")
        return False

def test_system_initialization():
    """测试系统初始化"""
    print("\n测试系统初始化...")
    try:
        from src.core import WarefireSystem
        system = WarefireSystem()
        print(f"✓ 系统初始化成功")
        
        # 获取系统状态
        status = system.get_status()
        print(f"✓ 系统状态: {status}")
        return True
    except Exception as e:
        print(f"✗ 系统初始化失败: {e}")
        return False

if __name__ == "__main__":
    print("家庭网络安全监控系统 - 测试脚本")
    print("=" * 40)
    
    # 运行所有测试
    tests = [
        test_module_import,
        test_config_loading,
        test_alert_engine,
        test_device_manager,
        test_system_initialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"测试结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("✓ 所有测试通过！系统准备就绪")
        sys.exit(0)
    else:
        print(f"✗ {total - passed} 个测试失败")
        sys.exit(1)
