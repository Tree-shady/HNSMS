#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Flask应用是否能正常运行
"""

import sys
import os

# 添加src目录到Python路径
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

from web.backend.app import app

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=True)
