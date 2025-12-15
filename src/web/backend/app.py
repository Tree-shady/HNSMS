#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
家庭网络安全监控系统 - Web后端API
基于Flask框架实现
"""

import os
from flask import Flask, render_template, jsonify, request, redirect, send_from_directory
from flask_cors import CORS

# 设置Flask应用，指定静态文件目录
app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # 允许跨域请求

# 全局变量，用于存储系统实例引用
warefire_system = None


# 直接导入所需的函数
from web.backend.controllers.traffic_controller import get_traffic_stats, get_active_sessions, get_top_talkers, get_protocol_distribution
from web.backend.controllers.status_controller import get_status
from web.backend.controllers.device_controller import get_devices, get_device, isolate_device, release_device
from web.backend.controllers.alert_controller import get_alerts, acknowledge_alert, resolve_alert, close_alert
from web.backend.controllers.config_controller import get_config, update_config


# 直接注册所有路由，使用装饰器方式
# 系统状态相关路由
@app.route('/api/status', methods=['GET'])
def api_get_status():
    return get_status(warefire_system)


# 设备管理相关路由
@app.route('/api/devices', methods=['GET'])
def api_get_devices():
    return get_devices(warefire_system)


@app.route('/api/devices/<string:mac_address>', methods=['GET'])
def api_get_device(mac_address):
    return get_device(warefire_system, mac_address)


@app.route('/api/devices/<string:mac_address>/isolate', methods=['POST'])
def api_isolate_device(mac_address):
    return isolate_device(warefire_system, mac_address)


@app.route('/api/devices/<string:mac_address>/release', methods=['POST'])
def api_release_device(mac_address):
    return release_device(warefire_system, mac_address)


# 告警相关路由
@app.route('/api/alerts', methods=['GET'])
def api_get_alerts():
    return get_alerts(warefire_system)


@app.route('/api/alerts/<string:alert_id>/acknowledge', methods=['POST'])
def api_acknowledge_alert(alert_id):
    return acknowledge_alert(warefire_system, alert_id)


@app.route('/api/alerts/<string:alert_id>/resolve', methods=['POST'])
def api_resolve_alert(alert_id):
    return resolve_alert(warefire_system, alert_id)


@app.route('/api/alerts/<string:alert_id>/close', methods=['POST'])
def api_close_alert(alert_id):
    return close_alert(warefire_system, alert_id)


# 流量统计相关路由
@app.route('/api/traffic/stats', methods=['GET'])
def api_get_traffic_stats():
    return get_traffic_stats(warefire_system)


@app.route('/api/traffic/sessions', methods=['GET'])
def api_get_active_sessions():
    return get_active_sessions(warefire_system)


# 流量排名路由，这是我们的主要目标
@app.route('/api/traffic/top-talkers', methods=['GET'])
def api_get_top_talkers():
    return get_top_talkers(warefire_system)


@app.route('/api/traffic/protocol-distribution', methods=['GET'])
def api_get_protocol_distribution():
    return get_protocol_distribution(warefire_system)


# 配置管理相关路由
@app.route('/api/config', methods=['GET'])
def api_get_config():
    return get_config(warefire_system)


@app.route('/api/config', methods=['POST'])
def api_update_config():
    return update_config(warefire_system, request.get_json())


# Web界面路由
@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    return render_template('dashboard.html')


@app.route('/devices')
def devices_page():
    """设备管理页面"""
    return render_template('devices.html')


@app.route('/alerts')
def alerts_page():
    """告警中心页面"""
    return render_template('alerts.html')


@app.route('/traffic')
def traffic_page():
    """流量监控页面"""
    return render_template('traffic.html')


@app.route('/settings')
def settings_page():
    """系统配置页面"""
    return render_template('settings.html')


@app.route('/users')
def users_page():
    """用户管理页面"""
    return render_template('users.html')


@app.route('/about')
def about_page():
    """关于系统页面"""
    return render_template('about.html')


# 初始化应用，传入系统实例
def init_app(system):
    """初始化应用，传入系统实例
    
    Args:
        system: WarefireSystem实例
    """
    global warefire_system
    warefire_system = system
    
    print("初始化应用成功！")
    return app


# 主函数，用于直接运行
def main():
    """主函数"""
    # 启动Flask应用
    app.run(host='127.0.0.1', port=8081, debug=True)


if __name__ == '__main__':
    main()