#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试告警状态持久化
"""

import os
import time
from src.core.config import Config
from src.core.alert_engine import AlertEngine

def test_alert_persistence():
    """测试告警状态持久化"""
    print("测试告警状态持久化...")
    
    try:
        # 测试数据库路径
        test_db_path = "../../data/test_alerts.db"
        
        # 清理之前的测试文件
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # 创建配置，使用测试数据库
        config = Config()
        config.set("alert_engine.alert_db_path", test_db_path)
        
        # 1. 创建并配置第一个告警引擎实例
        print("✓ 创建第一个告警引擎实例")
        alert_engine1 = AlertEngine(config)
        
        # 2. 创建一个测试告警
        alert = alert_engine1.create_alert(
            alert_type="test",
            severity="info",
            source="test_script",
            description="Test alert for persistence"
        )
        print(f"✓ 创建测试告警: {alert.alert_id}")
        
        # 3. 关闭告警
        alert_engine1.close_alert(alert.alert_id, "test_user")
        print(f"✓ 关闭告警: {alert.alert_id}")
        
        # 4. 验证告警状态已变更
        updated_alert = alert_engine1.get_alert(alert.alert_id)
        if updated_alert and updated_alert.status == "closed":
            print(f"✓ 告警状态已更新为 closed")
        else:
            print(f"✗ 告警状态更新失败: {updated_alert.status if updated_alert else '告警不存在'}")
            return False
        
        # 5. 保存当前告警数量
        alert_count1 = len(alert_engine1.alerts)
        print(f"✓ 当前告警数量: {alert_count1}")
        
        # 6. 创建第二个告警引擎实例，模拟系统重启
        print("\n✓ 创建第二个告警引擎实例（模拟系统重启）")
        alert_engine2 = AlertEngine(config)
        
        # 7. 验证告警数量
        alert_count2 = len(alert_engine2.alerts)
        print(f"✓ 重启后告警数量: {alert_count2}")
        
        if alert_count1 == alert_count2:
            print("✓ 告警数量一致")
        else:
            print(f"✗ 告警数量不一致，预期: {alert_count1}, 实际: {alert_count2}")
            return False
        
        # 8. 验证告警状态是否持久化
        reloaded_alert = alert_engine2.get_alert(alert.alert_id)
        if reloaded_alert and reloaded_alert.status == "closed":
            print(f"✓ 告警状态已持久化，重启后仍为 closed")
        else:
            print(f"✗ 告警状态未持久化，重启后状态: {reloaded_alert.status if reloaded_alert else '告警不存在'}")
            return False
        
        # 9. 清理测试文件
        os.remove(test_db_path)
        print("✓ 测试文件清理成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("告警状态持久化测试")
    print("=" * 30)
    
    if test_alert_persistence():
        print("\n✓ 测试通过！告警状态持久化功能正常")
        exit(0)
    else:
        print("\n✗ 测试失败！告警状态持久化功能异常")
        exit(1)
