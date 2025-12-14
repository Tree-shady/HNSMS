#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设备管理控制器
"""

from flask import jsonify, request

def get_devices(warefire_system):
    """获取设备列表
    
    Args:
        warefire_system: WarefireSystem实例
        
    Returns:
        JSON格式的设备列表
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取设备列表
        devices = warefire_system.device_manager.devices
        device_list = [device.to_dict() for device in devices.values()]
        
        return jsonify({
            "success": True,
            "data": {
                "devices": device_list,
                "total": len(device_list)
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def get_device(warefire_system, mac_address):
    """获取单个设备详情
    
    Args:
        warefire_system: WarefireSystem实例
        mac_address: 设备MAC地址
        
    Returns:
        JSON格式的设备详情
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取设备
        device = warefire_system.device_manager.get_device(mac_address)
        if not device:
            return jsonify({
                "success": False,
                "error": f"Device {mac_address} not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": device.to_dict()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def isolate_device(warefire_system, mac_address):
    """隔离设备
    
    Args:
        warefire_system: WarefireSystem实例
        mac_address: 设备MAC地址
        
    Returns:
        JSON格式的操作结果
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取设备
        device = warefire_system.device_manager.get_device(mac_address)
        if not device:
            return jsonify({
                "success": False,
                "error": f"Device {mac_address} not found"
            }), 404
        
        # TODO: 实现设备隔离逻辑
        # 例如：将设备添加到隔离组，或通过防火墙规则隔离
        device.status = "isolated"
        
        return jsonify({
            "success": True,
            "message": f"Device {mac_address} has been isolated"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def release_device(warefire_system, mac_address):
    """释放设备
    
    Args:
        warefire_system: WarefireSystem实例
        mac_address: 设备MAC地址
        
    Returns:
        JSON格式的操作结果
    """
    try:
        if warefire_system is None:
            return jsonify({"error": "System not initialized"}), 500
        
        # 获取设备
        device = warefire_system.device_manager.get_device(mac_address)
        if not device:
            return jsonify({
                "success": False,
                "error": f"Device {mac_address} not found"
            }), 404
        
        # TODO: 实现设备释放逻辑
        # 例如：将设备从隔离组移除，或删除防火墙隔离规则
        device.status = "online"
        
        return jsonify({
            "success": True,
            "message": f"Device {mac_address} has been released"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
