#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试MAC地址文件名处理
"""

import os
import json
from src.core.config import Config
from src.core.anomaly_detection import AnomalyDetector, BehaviorBaseline

def test_mac_filename_fix():
    """测试MAC地址文件名处理"""
    print("测试MAC地址文件名处理...")
    
    try:
        # 创建配置和异常检测器
        config = Config()
        
        # 模拟设备管理器
        class MockDeviceManager:
            def __init__(self):
                self.devices = {}
            
            def get_device(self, mac):
                return None
        
        device_manager = MockDeviceManager()
        anomaly_detector = AnomalyDetector(config, device_manager)
        
        # 创建测试基线
        test_mac = "56:d6:b8:80:3d:a4"
        baseline = BehaviorBaseline(test_mac)
        
        # 保存基线
        anomaly_detector.save_baseline(baseline)
        print(f"✓ 基线保存成功")
        
        # 检查文件是否存在，使用安全的文件名格式
        safe_mac = test_mac.replace(':', '-')
        expected_file = os.path.join(anomaly_detector.models_dir, f"{safe_mac}.baseline.json")
        
        if os.path.exists(expected_file):
            print(f"✓ 基线文件已创建: {expected_file}")
            
            # 验证文件内容
            with open(expected_file, 'r') as f:
                content = json.load(f)
                if content.get('device_mac') == test_mac:
                    print(f"✓ 文件内容正确，包含原始MAC地址")
                    return True
                else:
                    print(f"✗ 文件内容错误，MAC地址不匹配")
                    return False
        else:
            print(f"✗ 基线文件未创建: {expected_file}")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("MAC地址文件名处理测试")
    print("=" * 30)
    
    if test_mac_filename_fix():
        print("\n✓ 测试通过！MAC地址文件名处理正常")
        exit(0)
    else:
        print("\n✗ 测试失败！MAC地址文件名处理异常")
        exit(1)
