#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web服务调试脚本
用于调试树莓派上8082端口未监听的问题
"""

import os
import sys
import logging
import traceback

# 设置日志级别为DEBUG，以便查看详细信息
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('debug_web_service')

# 添加项目根目录和src目录到Python路径，以便能正确导入web模块
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)


def test_web_service_init():
    """测试Web服务初始化"""
    logger.info("=== 测试Web服务初始化 ===")
    
    try:
        logger.debug("尝试导入Web服务模块...")
        from web.backend.app import app as flask_app
        logger.info("✓ Web服务模块导入成功")
        
        # 测试Flask应用是否可以运行
        logger.debug("尝试测试Flask应用...")
        
        # 创建一个测试客户端
        with flask_app.test_client() as client:
            response = client.get('/')
            logger.info(f"✓ Flask应用测试成功，返回状态码: {response.status_code}")
            logger.debug(f"返回内容: {response.data[:100]}...")
        
        return True
    except Exception as e:
        logger.error(f"✗ Web服务初始化失败: {e}")
        logger.error(traceback.format_exc())
        return False


def test_system_start():
    """测试系统启动，重点关注Web服务"""
    logger.info("\n=== 测试系统启动，重点关注Web服务 ===")
    
    try:
        logger.debug("尝试导入系统模块...")
        from src.core.main import WarefireSystem
        logger.info("✓ 系统模块导入成功")
        
        # 创建系统实例，但不启动主循环
        logger.debug("创建系统实例...")
        system = WarefireSystem()
        logger.info("✓ 系统实例创建成功")
        
        # 只启动Web服务进行测试
        logger.debug("尝试启动Web服务...")
        
        # 导入Web服务模块
        from web.backend.app import init_app as init_web_app
        
        # 初始化Web服务
        app = init_web_app(system)
        logger.info("✓ Web服务初始化成功")
        
        # 测试Web服务配置
        logger.debug(f"Web服务配置 - 主机: {app.config.get('SERVER_NAME', '0.0.0.0')}")
        logger.debug(f"Web服务配置 - 调试模式: {app.debug}")
        
        # 测试路由
        logger.debug("测试Web服务路由...")
        with app.test_client() as client:
            response = client.get('/')
            logger.info(f"✓ Web服务路由测试成功，返回状态码: {response.status_code}")
            logger.debug(f"返回内容: {response.data[:100]}...")
        
        return True
    except Exception as e:
        logger.error(f"✗ 系统启动失败: {e}")
        logger.error(traceback.format_exc())
        return False


def check_port_config():
    """检查端口配置"""
    logger.info("\n=== 检查端口配置 ===")
    
    # 检查主入口文件中的端口配置
    main_file_path = os.path.join(src_path, 'core', 'main.py')
    
    try:
        with open(main_file_path, 'r') as f:
            content = f.read()
            
        # 查找端口配置
        import re
        port_match = re.search(r'port\s*=\s*(\d+)', content)
        if port_match:
            port = port_match.group(1)
            logger.info(f"✓ 在 main.py 中找到端口配置: {port}")
        else:
            logger.warning(f"⚠ 在 main.py 中未找到明确的端口配置")
        
        # 查找主机配置
        host_match = re.search(r'host\s*=\s*(["\'])(.*?)\1', content)
        if host_match:
            host = host_match.group(2)
            logger.info(f"✓ 在 main.py 中找到主机配置: {host}")
        else:
            logger.warning(f"⚠ 在 main.py 中未找到明确的主机配置")
        
        return True
    except Exception as e:
        logger.error(f"✗ 检查端口配置失败: {e}")
        logger.error(traceback.format_exc())
        return False


def check_venv_status():
    """检查虚拟环境状态"""
    logger.info("\n=== 检查虚拟环境状态 ===")
    
    # 检查是否在虚拟环境中
    if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
        logger.info(f"✓ 当前正在虚拟环境中运行: {sys.prefix}")
    else:
        logger.warning(f"⚠ 未在虚拟环境中运行，可能导致依赖问题")
    
    # 检查Flask是否已安装
    try:
        import flask
        logger.info(f"✓ Flask已安装，版本: {flask.__version__}")
    except ImportError:
        logger.error(f"✗ Flask未安装")
        return False
    
    # 检查Flask-Restx是否已安装
    try:
        import flask_restx
        logger.info(f"✓ Flask-Restx已安装，版本: {flask_restx.__version__}")
    except ImportError:
        logger.error(f"✗ Flask-Restx未安装")
        return False
    
    return True


def main():
    """主函数"""
    logger.info("Web服务调试脚本启动")
    
    # 检查虚拟环境状态
    check_venv_status()
    
    # 检查端口配置
    check_port_config()
    
    # 测试Web服务初始化
    test_web_service_init()
    
    # 测试系统启动
    test_system_start()
    
    logger.info("\n=== 调试完成 ===")
    logger.info("如果问题仍然存在，建议:")
    logger.info("1. 检查系统日志，查看详细错误信息")
    logger.info("2. 确保所有依赖都已正确安装: pip install -r requirements.txt")
    logger.info("3. 检查是否有其他程序占用8082端口: sudo lsof -i :8082")
    logger.info("4. 检查防火墙设置: sudo ufw status")
    logger.info("5. 尝试使用不同的端口启动系统")


if __name__ == "__main__":
    main()
