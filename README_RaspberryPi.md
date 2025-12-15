# 树莓派部署指南

本指南提供了在树莓派上部署和配置家庭网络安全监控系统的详细步骤，以及常见问题的解决方案。

## 系统要求

| 组件 | 要求 |
|------|------|
| 硬件 | 树莓派 4B 或更高版本 |
| 内存 | 至少 4GB RAM |
| 存储 | 至少 32GB SD卡或SSD |
| 网络 | 有线或无线网络连接 |
| 操作系统 | Raspberry Pi OS Bullseye 或 Bookworm |

## 安装步骤

### 1. 准备树莓派系统

1. 下载并安装最新的 Raspberry Pi OS
2. 启用 SSH（推荐）
3. 连接到网络
4. 更新系统：
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
5. 安装必要的系统依赖：
   ```bash
   sudo apt install -y python3-pip python3-venv git
   ```

### 2. 克隆仓库

```bash
git clone https://github.com/warefire/warefire.git
cd warefire
```

### 3. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置系统

```bash
# 复制示例配置文件（如果需要）
cp config.example.yml config.yml
# 编辑配置文件
nano config.yml
```

### 5. 启动系统

```bash
# 直接启动系统
python -m src.core.main

# 或使用 nohup 在后台运行
nohup python -m src.core.main > output.log 2>&1 &
```

## 访问 Web 管理界面

系统启动后，可以通过以下方式访问 Web 管理界面：

- 本地访问：http://localhost:8082
- 网络访问：http://<树莓派IP地址>:8082

## 常见问题及解决方案

### 1. 无法访问 Web 管理界面（连接失败）

**症状**：浏览器无法连接到 http://<树莓派IP地址>:8082，显示 "连接失败" 或 "无法访问此网站"

**解决方案**：

#### 步骤 1：检查系统是否正在运行

```bash
# 检查进程是否正在运行
ps aux | grep "python -m src.core.main"

# 如果没有运行，重新启动系统
python -m src.core.main
```

#### 步骤 2：检查端口是否正在监听

```bash
# 检查 8082 端口是否正在监听
sudo netstat -tlnp | grep 8082
# 或使用 ss 命令
sudo ss -tlnp | grep 8082

# 如果端口没有监听，检查系统日志
python -m src.core.main
```

#### 步骤 3：检查防火墙设置

```bash
# 检查 ufw 状态
sudo ufw status

# 如果 ufw 已启用，添加 8082 端口规则
sudo ufw allow 8082/tcp

# 或使用 iptables 添加规则
sudo iptables -A INPUT -p tcp --dport 8082 -j ACCEPT
sudo iptables-save
```

#### 步骤 4：检查端口是否被占用

```bash
# 检查 8082 端口是否被其他程序占用
sudo lsof -i :8082
```

#### 步骤 5：检查网络连接

```bash
# 检查树莓派的 IP 地址
ip addr

# 测试网络连接
ping 8.8.8.8
```

#### 步骤 6：检查 Web 服务配置

确保 `src/core/main.py` 中的 Web 服务配置正确：

```python
# 在 _start_web_service 方法中
web_thread = threading.Thread(
    target=app.run,
    kwargs={
        'host': '0.0.0.0',  # 确保绑定到所有地址
        'port': 8082,       # 确保端口为 8082
        'debug': False,
        'use_reloader': False
    },
    daemon=True
)
```

### 2. 系统运行缓慢

**症状**：系统运行缓慢，CPU 或内存使用率高

**解决方案**：

#### 调整性能配置

编辑 `src/core/config.py`，调整性能配置：

```python
"performance": {
    "threads": {
        "traffic_analyzer": 1,  # 减少线程数
        "signature_detection": 1,
        "anomaly_detection": 1,
        "threat_intelligence": 1,
        "device_manager": 1,
        "alert_engine": 1
    },
    "memory": {
        "max_usage_mb": 512,  # 减少内存使用
        "buffer_size_mb": 25,
        "cache_size_mb": 125
    },
    "cpu": {
        "max_usage_percent": 60,  # 降低最大 CPU 使用率
        "affinity": []
    },
    "queue_size": 2500  # 减少队列大小
}
```

#### 优化流量分析器

如果不需要实时流量分析，可以禁用或调整流量分析器的配置：

```python
"traffic_analyzer": {
    "enabled": True,
    "interfaces": ["eth0"],  # 只监控需要的接口
    "capture_filter": "",
    "max_packet_size": 1518,
    "buffer_size": 1024 * 1024 * 50  # 减少缓冲区大小
}
```

### 3. 设备识别不准确

**症状**：系统识别的设备类型或名称不准确

**解决方案**：

1. 手动修改设备信息：在 Web 管理界面的 "设备管理" 页面手动修改设备类型和名称
2. 等待系统学习：系统会在学习期内不断优化设备识别
3. 提交反馈：通过 GitHub Issues 提交设备识别问题，帮助改进算法

## 最佳实践

1. **使用有线网络**：树莓派通过有线网络连接到路由器，可以获得更稳定的性能
2. **定期更新系统**：定期更新系统和依赖，确保安全性
3. **监控系统资源**：使用 `htop` 或 `top` 监控系统资源使用情况
4. **备份配置**：定期备份配置文件和数据库
5. **合理调整日志级别**：根据需要调整日志级别，避免日志过大

## 命令行工具

### 系统状态检查

```bash
# 检查系统日志
python -m src.core.main

# 使用诊断脚本
python test_web_service.py
```

### 性能监控

```bash
# 监控 CPU 和内存使用情况
top
# 或使用 htop（需要安装）
sudo apt install -y htop
top

# 监控网络流量
sudo iftop
# 或使用 nload（需要安装）
sudo apt install -y nload
nload
```

## 高级配置

### 1. 配置为系统服务

可以将系统配置为 systemd 服务，实现开机自启动：

1. 创建服务文件：
   ```bash
sudo nano /etc/systemd/system/warefire.service
   ```

2. 添加以下内容：
   ```ini
   [Unit]
   Description=Warefire Home Network Security Monitoring System
   After=network.target
   
   [Service]
   Type=simple
   User=<your_username>
   WorkingDirectory=/home/<your_username>/warefire
   ExecStart=/home/<your_username>/warefire/venv/bin/python -m src.core.main
   Restart=on-failure
   
   [Install]
   WantedBy=multi-user.target
   ```

3. 启用并启动服务：
   ```bash
sudo systemctl enable warefire
sudo systemctl start warefire
   ```

4. 查看服务状态：
   ```bash
sudo systemctl status warefire
   ```

### 2. 配置 HTTPS

可以使用 Nginx 或 Apache 作为反向代理，为 Web 管理界面添加 HTTPS 支持：

#### 使用 Nginx

1. 安装 Nginx：
   ```bash
sudo apt install -y nginx
   ```

2. 创建 Nginx 配置文件：
   ```bash
sudo nano /etc/nginx/sites-available/warefire
   ```

3. 添加以下内容：
   ```nginx
   server {
       listen 80;
       server_name <your_domain>;
       
       location / {
           proxy_pass http://localhost:8082;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. 启用配置：
   ```bash
sudo ln -s /etc/nginx/sites-available/warefire /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
   ```

5. 使用 Let's Encrypt 获取 SSL 证书：
   ```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d <your_domain>
   ```

## 故障排除

如果遇到其他问题，可以尝试以下方法：

1. **查看系统日志**：
   ```bash
   python -m src.core.main
   ```

2. **使用诊断脚本**：
   ```bash
   python test_web_service.py
   ```

3. **检查依赖版本**：
   ```bash
   pip list
   ```

4. **重新安装依赖**：
   ```bash
   pip install --force-reinstall -r requirements.txt
   ```

5. **提交问题**：
   如果问题仍然存在，可以通过 GitHub Issues 提交详细的错误信息和系统环境。

## 联系我们

- 项目主页：https://github.com/warefire/warefire
- 问题反馈：https://github.com/warefire/warefire/issues
- 邮件：contact@warefire.com

---

**Warefire - 让家庭网络更安全** 🛡️
