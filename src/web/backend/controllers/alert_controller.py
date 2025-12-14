#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
告警管理控制器
"""

from flask import jsonify

def get_alerts(warefire_system):
    """获取告警列表
    
    Args:
        warefire_system: WarefireSystem实例
        
    Returns:
        JSON格式的告警列表
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取告警列表
        alerts = warefire_system.alert_engine.alerts
        alert_list = [alert.to_dict() for alert in alerts.values()]
        
        return jsonify({
            "success": True,
            "data": {
                "alerts": alert_list,
                "total": len(alert_list)
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def acknowledge_alert(warefire_system, alert_id):
    """确认告警
    
    Args:
        warefire_system: WarefireSystem实例
        alert_id: 告警ID
        
    Returns:
        JSON格式的操作结果
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取告警
        alert = warefire_system.alert_engine.alerts.get(alert_id)
        if not alert:
            return jsonify({
                "success": False,
                "error": f"Alert {alert_id} not found"
            }), 404
        
        # 确认告警
        alert.acknowledge("web_user")
        
        return jsonify({
            "success": True,
            "message": f"Alert {alert_id} has been acknowledged"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def resolve_alert(warefire_system, alert_id):
    """解决告警
    
    Args:
        warefire_system: WarefireSystem实例
        alert_id: 告警ID
        
    Returns:
        JSON格式的操作结果
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取告警
        alert = warefire_system.alert_engine.alerts.get(alert_id)
        if not alert:
            return jsonify({
                "success": False,
                "error": f"Alert {alert_id} not found"
            }), 404
        
        # 解决告警
        alert.resolve("web_user")
        
        return jsonify({
            "success": True,
            "message": f"Alert {alert_id} has been resolved"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def close_alert(warefire_system, alert_id):
    """关闭告警
    
    Args:
        warefire_system: WarefireSystem实例
        alert_id: 告警ID
        
    Returns:
        JSON格式的操作结果
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取告警
        alert = warefire_system.alert_engine.alerts.get(alert_id)
        if not alert:
            return jsonify({
                "success": False,
                "error": f"Alert {alert_id} not found"
            }), 404
        
        # 关闭告警
        alert.close("web_user")
        
        return jsonify({
            "success": True,
            "message": f"Alert {alert_id} has been closed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
