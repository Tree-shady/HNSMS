#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time

# 测试连接到Web服务
def test_web_connection():
    url = 'http://127.0.0.1:8080'
    print(f"测试连接到: {url}")
    
    try:
        # 尝试连接
        response = requests.get(url, timeout=5)
        print(f"✓ 连接成功！状态码: {response.status_code}")
        print(f"  响应内容: {response.text[:100]}...")
        return True
    except requests.exceptions.ConnectionError:
        print(f"✗ 连接失败: 无法建立连接到 {url}")
        print("  可能的原因:")
        print("  1. Web服务未运行")
        print("  2. 防火墙阻止了连接")
        print("  3. 端口被其他程序占用")
        print("  4. 网络配置问题")
    except requests.exceptions.Timeout:
        print(f"✗ 连接失败: 连接超时")
    except requests.exceptions.RequestException as e:
        print(f"✗ 连接失败: {e}")
    
    return False

# 测试静态文件访问
def test_static_files():
    static_urls = [
        'http://127.0.0.1:8080/static/css/style.css',
        'http://127.0.0.1:8080/static/js/main.js'
    ]
    
    print("\n测试静态文件访问:")
    all_successful = True
    
    for url in static_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ {url} - 访问成功")
            else:
                print(f"✗ {url} - 访问失败，状态码: {response.status_code}")
                all_successful = False
        except Exception as e:
            print(f"✗ {url} - 访问失败: {e}")
            all_successful = False
    
    return all_successful

# 测试API端点
def test_api_endpoints():
    api_urls = [
        'http://127.0.0.1:8080/api/status',
        'http://127.0.0.1:8080/api/config'
    ]
    
    print("\n测试API端点:")
    all_successful = True
    
    for url in api_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ {url} - 访问成功")
                # 尝试解析JSON响应
                try:
                    data = response.json()
                    print(f"  ✓ JSON响应解析成功")
                except ValueError:
                    print(f"  ✗ JSON响应解析失败")
                    all_successful = False
            else:
                print(f"✗ {url} - 访问失败，状态码: {response.status_code}")
                all_successful = False
        except Exception as e:
            print(f"✗ {url} - 访问失败: {e}")
            all_successful = False
    
    return all_successful

if __name__ == "__main__":
    print("Web服务连接测试")
    print("=" * 40)
    
    # 等待1秒，确保Web服务已经完全启动
    time.sleep(1)
    
    # 运行所有测试
    connection_ok = test_web_connection()
    static_ok = test_static_files()
    api_ok = test_api_endpoints()
    
    print("\n" + "=" * 40)
    print("测试结果汇总:")
    print(f"连接测试: {'✓ 成功' if connection_ok else '✗ 失败'}")
    print(f"静态文件: {'✓ 成功' if static_ok else '✗ 失败'}")
    print(f"API端点: {'✓ 成功' if api_ok else '✗ 失败'}")
    
    if connection_ok and static_ok and api_ok:
        print("\n✓ 所有测试通过！Web服务运行正常")
        print("\n请尝试在浏览器中访问:")
        print("http://127.0.0.1:8080")
        exit(0)
    else:
        print("\n✗ 部分测试失败，请检查Web服务配置")
        exit(1)