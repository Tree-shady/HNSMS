#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
家庭网络安全监控系统 - Web后端API
基于Flask框架实现
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS

# 导入控制器
import sys
import os

# 获取当前文件所在目录的父目录，也就是backend目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将backend目录添加到Python路径中，这样就能找到controllers模块
sys.path.insert(0, current_dir)

from controllers import status_controller, device_controller, alert_controller, traffic_controller

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量，用于存储系统实例引用
warefire_system = None

def init_app(system):
    """初始化应用，传入系统实例
    
    Args:
        system: WarefireSystem实例
    """
    global warefire_system
    warefire_system = system
    
    # 注册路由
    register_routes()
    
    return app

def register_routes():
    """注册API路由"""
    # 系统状态相关路由
    app.route('/api/status', methods=['GET'], endpoint='get_status')(lambda: status_controller.get_status(warefire_system))
    
    # 设备管理相关路由
    app.route('/api/devices', methods=['GET'], endpoint='get_devices')(lambda: device_controller.get_devices(warefire_system))
    app.route('/api/devices/<string:mac_address>', methods=['GET'], endpoint='get_device')(lambda mac_address: device_controller.get_device(warefire_system, mac_address))
    app.route('/api/devices/<string:mac_address>/isolate', methods=['POST'], endpoint='isolate_device')(lambda mac_address: device_controller.isolate_device(warefire_system, mac_address))
    app.route('/api/devices/<string:mac_address>/release', methods=['POST'], endpoint='release_device')(lambda mac_address: device_controller.release_device(warefire_system, mac_address))
    
    # 告警相关路由
    app.route('/api/alerts', methods=['GET'], endpoint='get_alerts')(lambda: alert_controller.get_alerts(warefire_system))
    app.route('/api/alerts/<string:alert_id>/acknowledge', methods=['POST'], endpoint='acknowledge_alert')(lambda alert_id: alert_controller.acknowledge_alert(warefire_system, alert_id))
    app.route('/api/alerts/<string:alert_id>/resolve', methods=['POST'], endpoint='resolve_alert')(lambda alert_id: alert_controller.resolve_alert(warefire_system, alert_id))
    app.route('/api/alerts/<string:alert_id>/close', methods=['POST'], endpoint='close_alert')(lambda alert_id: alert_controller.close_alert(warefire_system, alert_id))
    
    # 流量统计相关路由
    app.route('/api/traffic/stats', methods=['GET'], endpoint='get_traffic_stats')(lambda: traffic_controller.get_traffic_stats(warefire_system))
    app.route('/api/traffic/sessions', methods=['GET'], endpoint='get_active_sessions')(lambda: traffic_controller.get_active_sessions(warefire_system))
    
    # Web界面路由
    app.route('/')(index)
    app.route('/dashboard')(dashboard)
    app.route('/devices')(devices_page)
    app.route('/alerts')(alerts_page)
    app.route('/traffic')(traffic_page)
    app.route('/settings')(settings_page)
    app.route('/users')(users_page)
    app.route('/about')(about_page)

# Web界面路由处理
def index():
    """首页"""
    return render_template('index.html')

def dashboard():
    """仪表盘页面"""
    return render_template('dashboard.html')

def devices_page():
    """设备管理页面"""
    return render_template('devices.html')

def alerts_page():
    """告警中心页面"""
    return render_template('alerts.html')

def traffic_page():
    """流量监控页面"""
    return render_template('traffic.html')

def settings_page():
    """系统配置页面"""
    return render_template('settings.html')

def users_page():
    """用户管理页面"""
    return render_template('users.html')

def about_page():
    """关于系统页面"""
    return render_template('about.html')

# 主函数，用于直接运行
def main():
    """主函数"""
    # 注册路由
    register_routes()
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == '__main__':
    main()
