#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统配置控制器
"""

from flask import jsonify

def get_config(warefire_system):
    """获取系统配置
    
    Args:
        warefire_system: WarefireSystem实例
        
    Returns:
        JSON格式的系统配置
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取完整配置
        config = warefire_system.config.config
        
        return jsonify({
            "success": True,
            "data": config
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def update_config(warefire_system, config_data):
    """更新系统配置
    
    Args:
        warefire_system: WarefireSystem实例
        config_data: 新的配置数据
        
    Returns:
        JSON格式的更新结果
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 更新配置
        for key, value in config_data.items():
            warefire_system.config.set(key, value)
        
        # 保存配置到文件
        config_path = "../../data/config.json"
        warefire_system.config.save(config_path)
        
        return jsonify({
            "success": True,
            "message": "Configuration updated successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
