#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试配置管理功能
"""

import os
import time
from src.core.config import Config

def test_config_persistence():
    """测试配置持久化"""
    print("测试配置持久化...")
    
    try:
        # 测试配置文件路径
        test_config_path = "../../data/test_config.json"
        
        # 清理之前的测试文件
        if os.path.exists(test_config_path):
            os.remove(test_config_path)
        
        # 创建并保存配置
        config1 = Config()
        
        # 修改配置
        config1.set("system.mode", "detection")
        config1.set("system.log_level", "DEBUG")
        config1.set("device_manager.scan_interval_seconds", 600)
        
        # 保存配置
        config1.save(test_config_path)
        print(f"✓ 配置保存成功: {test_config_path}")
        
        # 重新加载配置
        config2 = Config(test_config_path)
        
        # 验证配置是否一致
        if config2.get("system.mode") == "detection" and \
           config2.get("system.log_level") == "DEBUG" and \
           config2.get("device_manager.scan_interval_seconds") == 600:
            print("✓ 配置加载成功，数据一致")
        else:
            print("✗ 配置加载失败，数据不一致")
            print(f"  Expected: mode=detection, log_level=DEBUG, scan_interval=600")
            print(f"  Actual: mode={config2.get('system.mode')}, log_level={config2.get('system.log_level')}, scan_interval={config2.get('device_manager.scan_interval_seconds')}")
            return False
            
        # 清理测试文件
        os.remove(test_config_path)
        print("✓ 测试文件清理成功")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_merge():
    """测试配置合并功能"""
    print("\n测试配置合并功能...")
    
    try:
        # 创建测试配置
        test_config_path = "../../data/test_merge_config.json"
        
        # 清理之前的测试文件
        if os.path.exists(test_config_path):
            os.remove(test_config_path)
        
        # 创建自定义配置
        custom_config = {
            "system": {
                "mode": "detection",
                "log_level": "DEBUG"
            },
            "device_manager": {
                "scan_interval_seconds": 600
netsh advfirewall firewall add rule name="Warefire Web Service (8082)" dir=in action=allow protocol=TCP localport=8082            },
            "network": {
                "proxy": {
                    "enabled": True,
                    "host": "127.0.0.1",
                    "port": 3128
                }
            },
            "performance": {
                "threads": {
                    "traffic_analyzer": 8
                }
            }
        }
        
        # 保存自定义配置
        import json
        with open(test_config_path, 'w') as f:
            json.dump(custom_config, f, indent=2)
        
        # 加载配置，验证合并是否正确
        config = Config(test_config_path)
        
        # 验证默认配置是否保留，自定义配置是否覆盖
        if config.get("system.mode") == "detection" and \
           config.get("system.log_level") == "DEBUG" and \
           config.get("device_manager.scan_interval_seconds") == 600 and \
           config.get("system.learning_period_days") == 14 and \
           config.get("network.proxy.enabled") == True and \
           config.get("network.proxy.host") == "127.0.0.1" and \
           config.get("performance.threads.traffic_analyzer") == 8:
            print("✓ 配置合并成功")
        else:
            print("✗ 配置合并失败")
            return False
            
        # 清理测试文件
        os.remove(test_config_path)
        print("✓ 测试文件清理成功")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_validation():
    """测试配置验证功能"""
    print("\n测试配置验证功能...")
    
    try:
        config = Config()
        
        # 设置无效的系统模式
        config.set("system.mode", "invalid_mode")
        if config.get("system.mode") == "learning":
            print("✓ 系统模式验证成功")
        else:
            print("✗ 系统模式验证失败")
            return False
        
        # 设置无效的日志级别
        config.set("system.log_level", "INVALID")
        if config.get("system.log_level") == "INFO":
            print("✓ 日志级别验证成功")
        else:
            print("✗ 日志级别验证失败")
            return False
        
        # 设置无效的检测阈值
        config.set("anomaly_detection.detection_threshold", 1.5)
        if config.get("anomaly_detection.detection_threshold") == 0.95:
            print("✓ 检测阈值验证成功")
        else:
            print("✗ 检测阈值验证失败")
            return False
        
        # 设置无效的线程数
        config.set("performance.threads.traffic_analyzer", 0)
        if config.get("performance.threads.traffic_analyzer") == 1:
            print("✓ 线程数验证成功")
        else:
            print("✗ 线程数验证失败")
            return False
        
        # 设置无效的主题
        config.set("ui.theme", "invalid_theme")
        if config.get("ui.theme") == "dark":
            print("✓ 主题验证成功")
        else:
            print("✗ 主题验证失败")
            return False
        
        # 验证validate_config方法返回值
        if config.validate_config():
            print("✓ 配置验证方法返回值正确")
        else:
            print("✗ 配置验证方法返回值错误")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_observer():
    """测试配置变更事件通知功能"""
    print("\n测试配置变更事件通知功能...")
    
    try:
        config = Config()
        
        # 用于记录通知的列表
        notifications = []
        
        # 定义观察者函数
        def observer(key, old_value, new_value):
            notifications.append((key, old_value, new_value))
        
        # 添加观察者
        config.add_observer(observer)
        
        # 修改配置
        config.set("system.mode", "detection")
        config.set("system.log_level", "DEBUG")
        config.set("device_manager.scan_interval_seconds", 600)
        
        # 验证通知是否正确
        if len(notifications) == 3:
            print(f"✓ 收到 {len(notifications)} 个通知")
            
            # 验证通知内容
            expected_keys = ["system.mode", "system.log_level", "device_manager.scan_interval_seconds"]
            for i, (key, old_value, new_value) in enumerate(notifications):
                if key == expected_keys[i]:
                    print(f"✓ 通知 {i+1} 键正确: {key}")
                else:
                    print(f"✗ 通知 {i+1} 键错误: 预期 {expected_keys[i]}, 实际 {key}")
                    return False
        else:
            print(f"✗ 通知数量错误: 预期 3, 实际 {len(notifications)}")
            return False
        
        # 移除观察者
        config.remove_observer(observer)
        
        # 再次修改配置，不应收到通知
        notifications.clear()
        config.set("system.mode", "learning")
        
        if len(notifications) == 0:
            print("✓ 移除观察者后不再收到通知")
        else:
            print(f"✗ 移除观察者后仍收到通知: {len(notifications)} 个")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_new_config_sections():
    """测试新增配置部分"""
    print("\n测试新增配置部分...")
    
    try:
        config = Config()
        
        # 测试网络配置
        if config.get("network.proxy.enabled") is not None and \
           config.get("network.dns.servers") is not None:
            print("✓ 网络配置存在")
        else:
            print("✗ 网络配置不存在")
            return False
        
        # 测试存储配置
        if config.get("storage.database.type") is not None and \
           config.get("storage.file_storage.type") is not None:
            print("✓ 存储配置存在")
        else:
            print("✗ 存储配置不存在")
            return False
        
        # 测试性能配置
        if config.get("performance.threads") is not None and \
           config.get("performance.memory.max_usage_mb") is not None:
            print("✓ 性能配置存在")
        else:
            print("✗ 性能配置不存在")
            return False
        
        # 测试安全配置
        if config.get("security.encryption.enabled") is not None and \
           config.get("security.authentication.enabled") is not None:
            print("✓ 安全配置存在")
        else:
            print("✗ 安全配置不存在")
            return False
        
        # 测试备份配置
        if config.get("backup.enabled") is not None and \
           config.get("backup.schedule.frequency") is not None:
            print("✓ 备份配置存在")
        else:
            print("✗ 备份配置不存在")
            return False
        
        # 测试UI配置
        if config.get("ui.theme") is not None and \
           config.get("ui.language") is not None:
            print("✓ UI配置存在")
        else:
            print("✗ UI配置不存在")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("配置管理功能测试")
    print("=" * 30)
    
    tests = [
        test_config_persistence,
        test_config_merge,
        test_config_validation,
        test_config_observer,
        test_new_config_sections
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 30)
    print(f"测试结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("✓ 所有测试通过！配置管理功能正常")
        exit(0)
    else:
        print(f"✗ {total - passed} 个测试失败")
        exit(1)
