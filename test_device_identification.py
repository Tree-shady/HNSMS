#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试设备识别优化
"""

from src.core.device_manager import Device, DeviceManager
from src.core.config import Config

def test_device_identification():
    """测试设备识别"""
    print("测试设备识别优化...")
    
    try:
        # 创建配置和设备管理器
        config = Config()
        device_manager = DeviceManager(config)
        
        # 测试设备列表
        test_devices = [
            # 苹果设备
            Device("AC:BC:32:12:34:56", "192.168.0.101"),
            # 戴尔设备
            Device("00:19:B9:65:43:21", "192.168.0.102"),
            # 联想设备
            Device("B0:5A:DA:AA:BB:CC", "192.168.0.103"),
            # Raspberry Pi
            Device("B8:27:EB:DD:EE:FF", "192.168.0.104"),
            # 未知设备
            Device("00:11:22:11:22:33", "192.168.0.105")
        ]
        
        print("✓ 创建测试设备成功")
        
        # 对每个设备进行识别
        for device in test_devices:
            device_manager._identify_device(device)
            print(f"\n设备: {device.mac_address} ({device.ip_address})")
            print(f"  厂商: {device.manufacturer}")
            print(f"  主机名: {device.hostname}")
            print(f"  设备类型: {device.device_type}")
        
        # 验证识别结果
        success = True
        
        # 验证苹果设备
        if test_devices[0].manufacturer != "Apple":
            print(f"\n✗ 苹果设备厂商识别失败，预期: Apple, 实际: {test_devices[0].manufacturer}")
            success = False
        
        # 验证戴尔设备
        if test_devices[1].manufacturer != "Dell":
            print(f"\n✗ 戴尔设备厂商识别失败，预期: Dell, 实际: {test_devices[1].manufacturer}")
            success = False
        
        # 验证联想设备
        if test_devices[2].manufacturer != "Lenovo":
            print(f"\n✗ 联想设备厂商识别失败，预期: Lenovo, 实际: {test_devices[2].manufacturer}")
            success = False
        
        # 验证Raspberry Pi
        if test_devices[3].manufacturer != "Raspberry Pi":
            print(f"\n✗ Raspberry Pi厂商识别失败，预期: Raspberry Pi, 实际: {test_devices[3].manufacturer}")
            success = False
        
        # 验证默认设备类型
        for device in test_devices:
            if device.device_type == "unknown":
                print(f"\n✗ 设备类型识别失败，预期: 非unknown, 实际: {device.device_type}")
                success = False
        
        # 验证默认名称生成
        for device in test_devices:
            if not device.hostname:
                print(f"\n✗ 默认名称生成失败，预期: 有名称, 实际: 空")
                success = False
        
        if success:
            print("\n✓ 所有设备识别测试通过！")
        else:
            print("\n✗ 设备识别测试失败！")
            
        return success
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("设备识别优化测试")
    print("=" * 30)
    
    if test_device_identification():
        print("\n✓ 测试通过！设备识别优化成功")
        exit(0)
    else:
        print("\n✗ 测试失败！设备识别优化未完全成功")
        exit(1)
