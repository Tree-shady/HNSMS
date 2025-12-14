#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统状态控制器
"""

from flask import jsonify

def get_status(warefire_system):
    """获取系统状态
    
    Args:
        warefire_system: WarefireSystem实例
        
    Returns:
        JSON格式的系统状态信息
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取系统状态
        status = warefire_system.get_status()
        
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
