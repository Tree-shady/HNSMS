#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import threading
import time
from typing import Dict, List, Optional

from .config import Config
from .utils import logger, get_current_timestamp, get_current_datetime

class Alert:
    """告警类，代表一个安全事件告警"""
    
    def __init__(self, alert_type: str, severity: str, source: str, description: str, details: Dict = None):
        """初始化告警
        
        Args:
            alert_type: 告警类型
            severity: 严重程度
            source: 告警来源
            description: 告警描述
            details: 告警详细信息
        """
        self.alert_id = f"alert_{get_current_timestamp()}_{int(time.time() * 1000) % 1000}"
        self.timestamp = get_current_timestamp()
        self.alert_type = alert_type
        self.severity = severity.lower()  # low, medium, high, critical
        self.source = source
        self.description = description
        self.details = details or {}
        self.status = "new"  # new, acknowledged, resolved, closed
        self.acknowledged_by = ""
        self.acknowledged_at = 0
        self.resolved_by = ""
        self.resolved_at = 0
    
    def to_dict(self) -> Dict:
        """转换为字典
        
        Returns:
            告警信息字典
        """
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp,
            "datetime": get_current_datetime(),
            "alert_type": self.alert_type,
            "severity": self.severity,
            "source": self.source,
            "description": self.description,
            "details": self.details,
            "status": self.status,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at
        }
    
    def acknowledge(self, user: str) -> None:
        """确认告警
        
        Args:
            user: 确认用户
        """
        self.status = "acknowledged"
        self.acknowledged_by = user
        self.acknowledged_at = get_current_timestamp()
    
    def resolve(self, user: str) -> None:
        """解决告警
        
        Args:
            user: 解决用户
        """
        self.status = "resolved"
        self.resolved_by = user
        self.resolved_at = get_current_timestamp()
    
    def close(self, user: str) -> None:
        """关闭告警
        
        Args:
            user: 关闭用户
        """
        self.status = "closed"
        self.resolved_by = user
        self.resolved_at = get_current_timestamp()

class AlertEngine:
    """告警引擎，负责生成和管理告警"""
    
    def __init__(self, config: Config):
        """初始化告警引擎
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.enabled = config.get("alert_engine.enabled", True)
        self.alert_levels = config.get("alert_engine.alert_levels", ["info", "warning", "critical"])
        self.notification_methods = config.get("alert_engine.notification_methods", ["web", "mobile"])
        self.db_path = config.get("alert_engine.alert_db_path", "../../data/alerts.db")
        self.max_alerts_per_hour = config.get("alert_engine.max_alerts_per_hour", 100)
        
        self.alerts: Dict[str, Alert] = {}  # 告警ID -> 告警对象
        self.alert_count_in_last_hour = 0
        self.last_hour_reset = get_current_timestamp()
        
        # 初始化数据库
        self._init_database()
        
        # 加载现有告警
        self._load_alerts()
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self._cleanup_old_alerts, daemon=True)
        self.cleanup_thread.start()
    
    def _init_database(self) -> None:
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建告警表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    timestamp INTEGER,
                    alert_type TEXT,
                    severity TEXT,
                    source TEXT,
                    description TEXT,
                    details TEXT,
                    status TEXT,
                    acknowledged_by TEXT,
                    acknowledged_at INTEGER,
                    resolved_by TEXT,
                    resolved_at INTEGER
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error initializing alerts database: {e}")
    
    def _load_alerts(self) -> None:
        """加载现有告警"""
        logger.info(f"Loading alerts from {self.db_path}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 1000")
            rows = cursor.fetchall()
            
            for row in rows:
                alert = Alert(
                    alert_type=row[2],
                    severity=row[3],
                    source=row[4],
                    description=row[5]
                )
                alert.alert_id = row[0]
                alert.timestamp = row[1]
                alert.details = eval(row[6]) if row[6] else {}
                alert.status = row[7]
                alert.acknowledged_by = row[8]
                alert.acknowledged_at = row[9]
                alert.resolved_by = row[10]
                alert.resolved_at = row[11]
                self.alerts[alert.alert_id] = alert
            
            conn.close()
            logger.info(f"Loaded {len(self.alerts)} alerts")
        except Exception as e:
            logger.error(f"Error loading alerts: {e}")
    
    def _save_alert_to_db(self, alert: Alert) -> None:
        """保存告警到数据库
        
        Args:
            alert: 告警对象
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id,
                alert.timestamp,
                alert.alert_type,
                alert.severity,
                alert.source,
                alert.description,
                str(alert.details),
                alert.status,
                alert.acknowledged_by,
                alert.acknowledged_at,
                alert.resolved_by,
                alert.resolved_at
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving alert to database: {e}")
    
    def create_alert(self, alert_type: str, severity: str, source: str, description: str, details: Dict = None) -> Alert:
        """创建新告警
        
        Args:
            alert_type: 告警类型
            severity: 严重程度
            source: 告警来源
            description: 告警描述
            details: 告警详细信息
            
        Returns:
            创建的告警对象
        """
        # 检查告警级别是否在配置的级别列表中
        if severity.lower() not in self.alert_levels:
            logger.warning(f"Alert severity {severity} not in configured levels, skipping")
            return
        
        # 检查每小时告警数量限制
        current_time = get_current_timestamp()
        if current_time - self.last_hour_reset > 3600:
            self.alert_count_in_last_hour = 0
            self.last_hour_reset = current_time
        
        if self.alert_count_in_last_hour >= self.max_alerts_per_hour:
            logger.warning(f"Exceeded maximum alerts per hour ({self.max_alerts_per_hour}), skipping")
            return
        
        # 创建告警
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            source=source,
            description=description,
            details=details
        )
        
        # 保存到内存和数据库
        self.alerts[alert.alert_id] = alert
        self._save_alert_to_db(alert)
        
        # 发送通知
        self._send_notifications(alert)
        
        self.alert_count_in_last_hour += 1
        logger.info(f"Created new alert: {alert.alert_id} - {description}")
        
        return alert
    
    def _send_notifications(self, alert: Alert) -> None:
        """发送告警通知
        
        Args:
            alert: 告警对象
        """
        for method in self.notification_methods:
            if method == "web":
                self._send_web_notification(alert)
            elif method == "mobile":
                self._send_mobile_notification(alert)
    
    def _send_web_notification(self, alert: Alert) -> None:
        """发送Web通知
        
        Args:
            alert: 告警对象
        """
        # 简化实现，实际应该通过WebSocket或其他机制发送实时通知
        logger.debug(f"Sending web notification for alert: {alert.alert_id}")
    
    def _send_mobile_notification(self, alert: Alert) -> None:
        """发送移动通知
        
        Args:
            alert: 告警对象
        """
        # 简化实现，实际应该通过推送服务发送通知
        logger.debug(f"Sending mobile notification for alert: {alert.alert_id}")
    
    def get_alerts(self, filters: Dict = None, limit: int = 100, offset: int = 0) -> List[Alert]:
        """获取告警列表
        
        Args:
            filters: 过滤条件
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            告警列表
        """
        # 从内存中获取告警
        alerts = list(self.alerts.values())
        
        # 应用过滤条件
        if filters:
            filtered_alerts = []
            for alert in alerts:
                match = True
                for key, value in filters.items():
                    if getattr(alert, key, None) != value:
                        match = False
                        break
                if match:
                    filtered_alerts.append(alert)
            alerts = filtered_alerts
        
        # 按时间排序
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 应用分页
        return alerts[offset:offset+limit]
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """根据ID获取告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            告警对象，不存在则返回None
        """
        return self.alerts.get(alert_id)
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """确认告警
        
        Args:
            alert_id: 告警ID
            user: 确认用户
            
        Returns:
            是否确认成功
        """
        alert = self.get_alert(alert_id)
        if alert:
            alert.acknowledge(user)
            self._save_alert_to_db(alert)
            logger.info(f"Alert {alert_id} acknowledged by {user}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str, user: str) -> bool:
        """解决告警
        
        Args:
            alert_id: 告警ID
            user: 解决用户
            
        Returns:
            是否解决成功
        """
        alert = self.get_alert(alert_id)
        if alert:
            alert.resolve(user)
            self._save_alert_to_db(alert)
            logger.info(f"Alert {alert_id} resolved by {user}")
            return True
        return False
    
    def close_alert(self, alert_id: str, user: str) -> bool:
        """关闭告警
        
        Args:
            alert_id: 告警ID
            user: 关闭用户
            
        Returns:
            是否关闭成功
        """
        alert = self.get_alert(alert_id)
        if alert:
            alert.close(user)
            self._save_alert_to_db(alert)
            logger.info(f"Alert {alert_id} closed by {user}")
            return True
        return False
    
    def delete_alert(self, alert_id: str) -> bool:
        """删除告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            是否删除成功
        """
        alert = self.get_alert(alert_id)
        if alert:
            del self.alerts[alert_id]
            
            # 从数据库中删除
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM alerts WHERE alert_id = ?", (alert_id,))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error deleting alert from database: {e}")
            
            logger.info(f"Alert {alert_id} deleted")
            return True
        return False
    
    def _cleanup_old_alerts(self) -> None:
        """清理旧告警"""
        logger.info("Starting old alerts cleanup thread")
        
        while True:
            # 保留最近30天的告警
            thirty_days_ago = get_current_timestamp() - (30 * 24 * 3600)
            old_alerts = [alert_id for alert_id, alert in self.alerts.items() if alert.timestamp < thirty_days_ago]
            
            for alert_id in old_alerts:
                self.delete_alert(alert_id)
            
            # 每24小时清理一次
            time.sleep(24 * 3600)
    
    def get_alert_stats(self) -> Dict:
        """获取告警统计信息
        
        Returns:
            告警统计字典
        """
        stats = {
            "total_alerts": len(self.alerts),
            "by_status": {
                "new": 0,
                "acknowledged": 0,
                "resolved": 0,
                "closed": 0
            },
            "by_severity": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            },
            "by_type": {}
        }
        
        for alert in self.alerts.values():
            # 按状态统计
            if alert.status in stats["by_status"]:
                stats["by_status"][alert.status] += 1
            
            # 按严重程度统计
            if alert.severity in stats["by_severity"]:
                stats["by_severity"][alert.severity] += 1
            
            # 按类型统计
            if alert.alert_type not in stats["by_type"]:
                stats["by_type"][alert.alert_type] = 0
            stats["by_type"][alert.alert_type] += 1
        
        return stats
