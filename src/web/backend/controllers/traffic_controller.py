#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
流量监控控制器
"""

from flask import jsonify

def get_traffic_stats(warefire_system):
    """获取流量统计信息
    
    Args:
        warefire_system: WarefireSystem实例
        
    Returns:
        JSON格式的流量统计信息
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取流量统计
        stats = warefire_system.traffic_analyzer.get_traffic_stats()
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def get_active_sessions(warefire_system):
    """获取活跃会话列表
    
    Args:
        warefire_system: WarefireSystem实例
        
    Returns:
        JSON格式的活跃会话列表
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取活跃会话
        sessions = warefire_system.traffic_analyzer.get_active_sessions()
        
        return jsonify({
            "success": True,
            "data": {
                "sessions": sessions,
                "total": len(sessions)
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
