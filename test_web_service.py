#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web服务诊断脚本
用于检查树莓派上Web服务的运行状态和配置
"""

import os
import sys
import socket
import subprocess
import platform


def check_port_listening(port=8082):
    """检查指定端口是否正在监听"""
    print(f"检查端口 {port} 是否正在监听...")
    
    try:
        # 创建一个套接字连接到本地端口
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(('0.0.0.0', port))
            if result == 0:
                print(f"✓ 端口 {port} 正在监听")
                return True
            else:
                print(f"✗ 端口 {port} 未在监听")
                return False
    except Exception as e:
        print(f"✗ 检查端口时出错: {e}")
        return False


def check_process_running(process_name):
    """检查指定进程是否正在运行"""
    print(f"检查进程 '{process_name}' 是否正在运行...")
    
    try:
        system = platform.system()
        if system == "Linux":
            # 在Linux上使用ps命令
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if process_name in result.stdout:
                print(f"✓ 进程 '{process_name}' 正在运行")
                return True
            else:
                print(f"✗ 进程 '{process_name}' 未在运行")
                return False
        elif system == "Windows":
            # 在Windows上使用tasklist命令
            result = subprocess.run(['tasklist'], capture_output=True, text=True)
            if process_name in result.stdout:
                print(f"✓ 进程 '{process_name}' 正在运行")
                return True
            else:
                print(f"✗ 进程 '{process_name}' 未在运行")
                return False
        else:
            print(f"✗ 不支持的操作系统: {system}")
            return False
    except Exception as e:
        print(f"✗ 检查进程时出错: {e}")
        return False


def check_firewall_rules(port=8082):
    """检查防火墙设置是否允许指定端口的访问"""
    print(f"检查防火墙规则是否允许端口 {port} 的访问...")
    
    try:
        system = platform.system()
        if system == "Linux":
            # 在Linux上检查防火墙规则
            print("  尝试检查ufw防火墙规则...")
            result = subprocess.run(['sudo', 'ufw', 'status'], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                if str(port) in result.stdout:
                    print(f"✓ ufw防火墙允许端口 {port} 的访问")
                else:
                    print(f"⚠ ufw防火墙可能未允许端口 {port} 的访问")
                    
            print("  尝试检查iptables规则...")
            result = subprocess.run(['sudo', 'iptables', '-L', '-n'], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                if str(port) in result.stdout:
                    print(f"✓ iptables允许端口 {port} 的访问")
                else:
                    print(f"⚠ iptables可能未允许端口 {port} 的访问")
        elif system == "Windows":
            # 在Windows上检查防火墙规则
            result = subprocess.run(['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'], capture_output=True, text=True)
            if str(port) in result.stdout:
                print(f"✓ Windows防火墙允许端口 {port} 的访问")
            else:
                print(f"⚠ Windows防火墙可能未允许端口 {port} 的访问")
        else:
            print(f"✗ 不支持的操作系统: {system}")
    except Exception as e:
        print(f"✗ 检查防火墙规则时出错: {e}")


def check_network_interfaces():
    """检查网络接口配置"""
    print("检查网络接口配置...")
    
    try:
        system = platform.system()
        if system == "Linux":
            # 在Linux上检查网络接口
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            print("当前网络接口配置:")
            print(result.stdout)
        elif system == "Windows":
            # 在Windows上检查网络接口
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            print("当前网络接口配置:")
            print(result.stdout)
        else:
            print(f"✗ 不支持的操作系统: {system}")
    except Exception as e:
        print(f"✗ 检查网络接口时出错: {e}")


def check_web_service_accessibility(port=8082):
    """检查Web服务是否可以本地访问"""
    print(f"检查Web服务是否可以本地访问...")
    
    try:
        # 使用curl或wget检查本地访问
        system = platform.system()
        if system == "Linux":
            # 在Linux上使用curl
            result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', f'http://localhost:{port}'], capture_output=True, text=True)
            if result.returncode == 0:
                http_code = result.stdout.strip()
                if http_code == '200':
                    print(f"✓ Web服务可以本地访问，返回状态码: {http_code}")
                else:
                    print(f"⚠ Web服务可以本地访问，但返回状态码: {http_code}")
            else:
                print(f"✗ 无法本地访问Web服务: {result.stderr}")
        else:
            print(f"✗ 不支持的操作系统: {system}")
    except Exception as e:
        print(f"✗ 检查Web服务可访问性时出错: {e}")


def main():
    """主函数"""
    print("=== Web服务诊断脚本 ===")
    print(f"运行在: {platform.system()} {platform.machine()}")
    print()
    
    # 检查端口监听
    port = 8082
    is_listening = check_port_listening(port)
    print()
    
    # 检查进程运行状态
    check_process_running("python -m src.core.main")
    print()
    
    # 检查防火墙规则
    check_firewall_rules(port)
    print()
    
    # 检查网络接口配置
    check_network_interfaces()
    print()
    
    # 检查Web服务可访问性
    check_web_service_accessibility(port)
    print()
    
    # 提供解决方案建议
    print("=== 解决方案建议 ===")
    if not is_listening:
        print("1. 检查系统日志，确认Web服务是否正常启动")
        print("2. 检查端口是否被其他程序占用: sudo lsof -i :8082")
        print("3. 尝试手动启动Web服务: python -m src.core.main")
    
    print("4. 如果使用ufw防火墙，添加规则: sudo ufw allow 8082/tcp")
    print("5. 如果使用iptables，添加规则: sudo iptables -A INPUT -p tcp --dport 8082 -j ACCEPT")
    print("6. 确保树莓派和访问设备在同一子网中")
    print("7. 检查树莓派的IP地址: ip addr")
    print("8. 尝试从树莓派本地访问: curl http://localhost:8082")
    print()
    print("=== 诊断结束 ===")


if __name__ == "__main__":
    main()
