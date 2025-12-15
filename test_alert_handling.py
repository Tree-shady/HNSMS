#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试告警处理功能
"""

import requests
import time

# API基础URL
BASE_URL = "http://127.0.0.1:8082/api"

def test_alert_handling():
    """测试告警处理流程"""
    print("=== 测试告警处理功能 ===")
    
    # 1. 获取当前告警列表
    print("1. 获取当前告警列表...")
    response = requests.get(f"{BASE_URL}/alerts")
    data = response.json()
    print(f"   当前告警数量: {len(data['data']['alerts'])}")
    
    # 2. 创建新告警（通过API直接调用，模拟系统生成告警）
    print("2. 创建新告警...")
    
    # 注意：当前系统没有公开的创建告警API，所以我们直接测试已有的告警
    # 我们将使用一个已有的告警来测试状态更新
    
    # 3. 查找一个已关闭的告警，测试重新打开（通过API直接调用）
    print("3. 测试告警状态更新...")
    
    # 获取第一个告警ID
    if len(data['data']['alerts']) > 0:
        alert_id = data['data']['alerts'][0]['alert_id']
        print(f"   选择告警: {alert_id}")
        
        # 4. 测试确认告警
        print("4. 测试确认告警...")
        response = requests.post(f"{BASE_URL}/alerts/{alert_id}/acknowledge")
        if response.status_code == 200:
            print("   确认告警成功")
        else:
            print(f"   确认告警失败: {response.json()}")
        
        # 5. 测试解决告警
        print("5. 测试解决告警...")
        response = requests.post(f"{BASE_URL}/alerts/{alert_id}/resolve")
        if response.status_code == 200:
            print("   解决告警成功")
        else:
            print(f"   解决告警失败: {response.json()}")
        
        # 6. 测试关闭告警
        print("6. 测试关闭告警...")
        response = requests.post(f"{BASE_URL}/alerts/{alert_id}/close")
        if response.status_code == 200:
            print("   关闭告警成功")
        else:
            print(f"   关闭告警失败: {response.json()}")
        
        # 7. 再次获取告警列表，检查状态
        print("7. 验证告警状态更新...")
        response = requests.get(f"{BASE_URL}/alerts")
        data = response.json()
        updated_alert = next((a for a in data['data']['alerts'] if a['alert_id'] == alert_id), None)
        if updated_alert:
            print(f"   告警状态: {updated_alert['status']}")
            print(f"   确认时间: {updated_alert['acknowledged_at']}")
            print(f"   解决时间: {updated_alert['resolved_at']}")
        else:
            print("   未找到更新后的告警")
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_alert_handling()
