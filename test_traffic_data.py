#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试流量数据生成和统计
"""

import time
from src.core.config import Config
from src.core.device_manager import DeviceManager
from src.core.traffic_analyzer import TrafficAnalyzer

def test_traffic_analyzer():
    """测试流量分析器"""
    print("测试流量分析器...")
    
    try:
        # 创建配置和设备管理器
        config = Config()
        device_manager = DeviceManager(config)
        
        # 创建流量分析器
        traffic_analyzer = TrafficAnalyzer(config, device_manager)
        
        # 启动流量分析器
        print("✓ 启动流量分析器")
        traffic_analyzer.start()
        
        # 等待一段时间，让模拟数据生成
        print("✓ 等待模拟数据生成...")
        time.sleep(3)
        
        # 获取流量统计
        stats = traffic_analyzer.get_traffic_stats()
        print(f"✓ 获取流量统计: {stats}")
        
        # 检查统计数据是否更新
        if stats["total_packets"] > 0 or stats["total_bytes"] > 0:
            print("✓ 流量统计已更新")
            return True
        else:
            print("✗ 流量统计未更新，仍为0")
            # 调试信息：检查模拟数据线程是否在运行
            if hasattr(traffic_analyzer, 'mock_data_thread'):
                print(f"  模拟数据线程状态: {'运行中' if traffic_analyzer.mock_data_thread.is_alive() else '已停止'}")
            if hasattr(traffic_analyzer, 'analysis_thread'):
                print(f"  分析线程状态: {'运行中' if traffic_analyzer.analysis_thread.is_alive() else '已停止'}")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 停止流量分析器
        traffic_analyzer.stop()

if __name__ == "__main__":
    print("流量分析器测试")
    print("=" * 30)
    
    if test_traffic_analyzer():
        print("\n✓ 测试通过！流量分析器正常工作")
        exit(0)
    else:
        print("\n✗ 测试失败！流量分析器未生成数据")
        exit(1)
