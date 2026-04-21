"""
实时监控模块

功能：提供细粒度的实时性能监控和系统指标收集

主要功能：
1. 系统资源监控：CPU、内存、磁盘、网络使用率
2. 应用程序监控：函数执行时间、错误率、数据库性能
3. 实时数据收集：高频率指标采集和存储
4. 性能分析：识别性能瓶颈和异常模式
5. 警报系统：基于阈值的实时警报
6. 数据聚合：分钟、小时、天级别的数据聚合

监控指标：
1. 系统指标：
   - CPU使用率（用户、系统、空闲）
   - 内存使用率（已用、可用、缓存）
   - 磁盘使用率（读写速度、IOPS、空间）
   - 网络指标（带宽、延迟、连接数）
   
2. 应用程序指标：
   - 函数执行时间（平均值、最大值、P95、P99）
   - 错误率和异常计数
   - 数据库查询性能
   - 并发连接数和线程数
   
3. 业务指标：
   - 用户活动频率
   - 功能使用分布
   - 系统响应时间
   - 任务完成率

数据存储：
- 原始指标：高频率存储（每秒/每分钟）
- 聚合指标：降采样存储（每小时/每天）
- 历史数据：长期存储用于趋势分析
"""

import time
import threading
import sqlite3
import json
import psutil
import os
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import logging
import statistics
from collections import deque, defaultdict
import traceback

# 导入数据库管理器
try:
    from .database_manager import db_manager
    USE_DB_MANAGER = True
except ImportError:
    USE_DB_MANAGER = False
    import sqlite3


class MetricType(Enum):
    """指标类型枚举"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    FUNCTION_EXECUTION = "function_execution"
    DATABASE_QUERY = "database_query"
    ERROR_COUNT = "error_count"
    USER_ACTIVITY = "user_activity"
    SYSTEM_LOAD = "system_load"


class AlertSeverity(Enum):
    """警报严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricData:
    """指标数据类"""
    metric_type: str
    metric_name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class Alert:
    """警报数据类"""
    id: Optional[int] = None
    alert_id: str = ""
    severity: str = AlertSeverity.WARNING.value
    title: str = ""
    message: str = ""
    metric_type: str = ""
    metric_name: str = ""
    threshold: float = 0.0
    current_value: float = 0.0
    triggered_at: datetime = None
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    def __post_init__(self):
        if self.triggered_at is None:
            self.triggered_at = datetime.now()
        if not self.alert_id:
            self.alert_id = f"alert_{int(time.time())}_{self.metric_type}_{self.metric_name}"


@dataclass
class PerformanceSummary:
    """性能总结数据类"""
    timestamp: datetime
    time_range_minutes: int = 5
    cpu_avg: float = 0.0
    cpu_max: float = 0.0
    memory_avg: float = 0.0
    memory_max: float = 0.0
    disk_read_avg: float = 0.0
    disk_write_avg: float = 0.0
    function_calls: int = 0
    avg_execution_time: float = 0.0
    error_count: int = 0
    error_rate: float = 0.0


class RealTimeMonitor:
    """实时监控器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化实时监控器
        
        Args:
            config: 配置参数
        """
        if config is None:
            config = {}
        
        self.config = config
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 数据库路径
        self.db_path = os.path.join(self.data_dir, "real_time_monitor.db")
        
        # 日志
        self._setup_logging()
        
        # 初始化数据库
        self._init_database()
        
        # 监控配置
        self.collection_interval = config.get("collection_interval", 5.0)  # 秒
        self.retention_days = config.get("retention_days", 30)
        self.alerts_enabled = config.get("alerts_enabled", True)
        
        # 阈值配置
        self.thresholds = config.get("thresholds", {
            "cpu_usage": {"warning": 80.0, "error": 90.0},
            "memory_usage": {"warning": 85.0, "error": 95.0},
            "disk_usage": {"warning": 85.0, "error": 95.0},
            "function_execution_time": {"warning": 10.0, "error": 30.0},  # 秒
            "error_rate": {"warning": 5.0, "error": 10.0},  # 百分比
        })
        
        # 状态变量
        self.is_running = False
        self.collection_thread = None
        self.aggregation_thread = None
        
        # 缓冲区
        self.metric_buffer = deque(maxlen=1000)
        self.alert_buffer = deque(maxlen=100)
        
        # 性能数据缓存
        self.performance_cache = {}
        self.last_collection_time = None
        
        # 网络和磁盘基准
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_net_time = time.time()
        self.last_disk_time = time.time()
        
        # 函数执行追踪
        self.function_executions = {}
        
        # 警报处理器
        self.alert_handlers = []
        
        self.logger.info("实时监控器初始化完成")
    
    def _init_database(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        if USE_DB_MANAGER:
            conn = db_manager.get_connection(self.db_path)
        else:
            conn = sqlite3.connect(self.db_path)
        
        cursor = conn.cursor()
        
        # 创建指标数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp DATETIME NOT NULL,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        # 创建聚合指标表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aggregated_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                aggregation_type TEXT NOT NULL,
                time_window TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp DATETIME NOT NULL,
                sample_count INTEGER NOT NULL
            )
        """)
        
        # 创建警报表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL UNIQUE,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                threshold REAL NOT NULL,
                current_value REAL NOT NULL,
                triggered_at DATETIME NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0,
                acknowledged_at DATETIME,
                acknowledged_by TEXT
            )
        """)
        
        # 创建性能总结表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                time_range_minutes INTEGER NOT NULL,
                cpu_avg REAL NOT NULL,
                cpu_max REAL NOT NULL,
                memory_avg REAL NOT NULL,
                memory_max REAL NOT NULL,
                disk_read_avg REAL NOT NULL,
                disk_write_avg REAL NOT NULL,
                function_calls INTEGER NOT NULL,
                avg_execution_time REAL NOT NULL,
                error_count INTEGER NOT NULL,
                error_rate REAL NOT NULL
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_type_timestamp ON metrics(metric_type, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aggregated_metrics_window ON aggregated_metrics(time_window, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_triggered ON alerts(triggered_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity, acknowledged)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_summaries_timestamp ON performance_summaries(timestamp)")
        
        conn.commit()
        if not USE_DB_MANAGER:
            conn.close()
        
        self.logger.info("监控数据库初始化完成")
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"real_time_monitor_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """启动监控"""
        if self.is_running:
            self.logger.warning("监控已经在运行中")
            return False
        
        try:
            self.is_running = True
            
            # 启动数据收集线程
            self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
            self.collection_thread.start()
            
            # 启动数据聚合线程
            self.aggregation_thread = threading.Thread(target=self._aggregation_loop, daemon=True)
            self.aggregation_thread.start()
            
            self.logger.info("实时监控启动成功")
            return True
            
        except Exception as e:
            self.is_running = False
            self.logger.error(f"监控启动失败: {str(e)}")
            return False
    
    def stop(self):
        """停止监控"""
        if not self.is_running:
            self.logger.warning("监控已经停止")
            return False
        
        try:
            self.is_running = False
            
            # 等待线程结束
            if self.collection_thread:
                self.collection_thread.join(timeout=5.0)
            if self.aggregation_thread:
                self.aggregation_thread.join(timeout=5.0)
            
            # 清空缓冲区
            self._flush_buffers()
            
            self.logger.info("监控停止成功")
            return True
            
        except Exception as e:
            self.logger.error(f"监控停止失败: {str(e)}")
            return False
    
    def _collection_loop(self):
        """数据收集循环"""
        self.logger.info("开始数据收集循环")
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # 收集系统指标
                self._collect_system_metrics()
                
                # 收集应用程序指标
                self._collect_application_metrics()
                
                # 处理缓冲区
                self._process_buffer()
                
                # 检查警报
                if self.alerts_enabled:
                    self._check_thresholds()
                
                # 计算收集时间
                collection_time = time.time() - start_time
                
                # 如果收集时间超过间隔的80%，记录警告
                if collection_time > self.collection_interval * 0.8:
                    self.logger.warning(f"数据收集时间过长: {collection_time:.2f}秒")
                
                # 等待下一个收集周期
                sleep_time = max(0.1, self.collection_interval - collection_time)
                time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"数据收集循环出错: {str(e)}")
                time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self):
        """收集系统指标"""
        current_time = datetime.now()
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_times = psutil.cpu_times_percent(interval=0.1)
            
            self._add_metric(MetricType.CPU_USAGE.value, "total", cpu_percent, current_time)
            self._add_metric(MetricType.CPU_USAGE.value, "user", cpu_times.user, current_time)
            self._add_metric(MetricType.CPU_USAGE.value, "system", cpu_times.system, current_time)
            self._add_metric(MetricType.CPU_USAGE.value, "idle", cpu_times.idle, current_time)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            self._add_metric(MetricType.MEMORY_USAGE.value, "total", memory.percent, current_time)
            self._add_metric(MetricType.MEMORY_USAGE.value, "used_gb", memory.used / 1024**3, current_time)
            self._add_metric(MetricType.MEMORY_USAGE.value, "available_gb", memory.available / 1024**3, current_time)
            
            # 磁盘使用率
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    self._add_metric(MetricType.DISK_USAGE.value, partition.mountpoint, usage.percent, current_time)
                except Exception:
                    continue
            
            # 磁盘IO
            current_time_sec = time.time()
            current_disk_io = psutil.disk_io_counters()
            
            if self.last_disk_io and self.last_disk_time:
                time_diff = current_time_sec - self.last_disk_time
                if time_diff > 0:
                    read_speed = (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_diff
                    write_speed = (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_diff
                    
                    self._add_metric(MetricType.DISK_IO.value, "read_speed_mb", read_speed / 1024**2, current_time)
                    self._add_metric(MetricType.DISK_IO.value, "write_speed_mb", write_speed / 1024**2, current_time)
            
            self.last_disk_io = current_disk_io
            self.last_disk_time = current_time_sec
            
            # 网络IO
            current_net_io = psutil.net_io_counters()
            
            if self.last_net_io and self.last_net_time:
                time_diff = current_time_sec - self.last_net_time
                if time_diff > 0:
                    bytes_sent_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_diff
                    bytes_recv_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_diff
                    
                    self._add_metric(MetricType.NETWORK_IO.value, "sent_speed_mb", bytes_sent_speed / 1024**2, current_time)
                    self._add_metric(MetricType.NETWORK_IO.value, "recv_speed_mb", bytes_recv_speed / 1024**2, current_time)
            
            self.last_net_io = current_net_io
            self.last_net_time = current_time_sec
            
            # 系统负载
            load_avg = psutil.getloadavg()
            self._add_metric(MetricType.SYSTEM_LOAD.value, "1min", load_avg[0], current_time)
            self._add_metric(MetricType.SYSTEM_LOAD.value, "5min", load_avg[1], current_time)
            self._add_metric(MetricType.SYSTEM_LOAD.value, "15min", load_avg[2], current_time)
            
            # 进程信息
            process = psutil.Process()
            self._add_metric("process", "cpu_percent", process.cpu_percent(interval=0.1), current_time)
            self._add_metric("process", "memory_percent", process.memory_percent(), current_time)
            self._add_metric("process", "memory_rss_mb", process.memory_info().rss / 1024**2, current_time)
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {str(e)}")
    
    def _collect_application_metrics(self):
        """收集应用程序指标"""
        current_time = datetime.now()
        
        try:
            # 从数据库获取函数执行统计
            if USE_DB_MANAGER:
                conn = db_manager.get_connection(self.db_path)
            else:
                conn = sqlite3.connect(self.db_path)
            
            cursor = conn.cursor()
            
            # 获取最近5分钟的函数执行统计
            five_minutes_ago = (current_time - timedelta(minutes=5)).isoformat()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as call_count,
                    AVG(value) as avg_time,
                    MAX(value) as max_time
                FROM metrics 
                WHERE metric_type = ? AND timestamp >= ?
            """, (MetricType.FUNCTION_EXECUTION.value, five_minutes_ago))
            
            result = cursor.fetchone()
            call_count = 0  # 初始化call_count
            if result and result[0] > 0:
                call_count, avg_time, max_time = result
                self._add_metric("application", "function_call_count", call_count, current_time)
                self._add_metric("application", "function_avg_time", avg_time, current_time)
                self._add_metric("application", "function_max_time", max_time, current_time)
            
            # 获取错误统计
            cursor.execute("""
                SELECT COUNT(*) as error_count
                FROM metrics 
                WHERE metric_type = ? AND timestamp >= ?
            """, (MetricType.ERROR_COUNT.value, five_minutes_ago))
            
            result = cursor.fetchone()
            if result:
                error_count = result[0]
                error_rate = (error_count / max(call_count, 1)) * 100 if call_count > 0 else 0
                self._add_metric("application", "error_count", error_count, current_time)
                self._add_metric("application", "error_rate_percent", error_rate, current_time)
            
            if not USE_DB_MANAGER:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"收集应用程序指标失败: {str(e)}")
    
    def _add_metric(self, metric_type: str, metric_name: str, value: float, timestamp: datetime, 
                   tags: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """添加指标到缓冲区"""
        if tags is None:
            tags = {}
        if metadata is None:
            metadata = {}
        
        metric = MetricData(
            metric_type=metric_type,
            metric_name=metric_name,
            value=float(value),
            timestamp=timestamp,
            tags=tags,
            metadata=metadata
        )
        
        self.metric_buffer.append(metric)
    
    def _process_buffer(self):
        """处理缓冲区数据"""
        if not self.metric_buffer:
            return
        
        try:
            metrics_to_insert = []
            while self.metric_buffer:
                metric = self.metric_buffer.popleft()
                metrics_to_insert.append(metric)
            
            # 批量插入数据库
            self._batch_insert_metrics(metrics_to_insert)
            
        except Exception as e:
            self.logger.error(f"处理缓冲区失败: {str(e)}")
            # 重新放回缓冲区
            for metric in metrics_to_insert:
                self.metric_buffer.appendleft(metric)
    
    def _batch_insert_metrics(self, metrics: List[MetricData]):
        """批量插入指标数据"""
        if not metrics:
            return
        
        try:
            if USE_DB_MANAGER:
                conn = db_manager.get_connection(self.db_path)
            else:
                conn = sqlite3.connect(self.db_path)
            
            cursor = conn.cursor()
            
            # 使用批量插入
            cursor.execute("BEGIN TRANSACTION")
            
            for metric in metrics:
                cursor.execute("""
                    INSERT INTO metrics (metric_type, metric_name, value, timestamp, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    metric.metric_type,
                    metric.metric_name,
                    metric.value,
                    metric.timestamp.isoformat(),
                    json.dumps(metric.tags, ensure_ascii=False),
                    json.dumps(metric.metadata, ensure_ascii=False)
                ))
            
            cursor.execute("COMMIT")
            
            if not USE_DB_MANAGER:
                conn.close()
            
            # 更新性能缓存
            self._update_performance_cache(metrics)
            
        except Exception as e:
            self.logger.error(f"批量插入指标失败: {str(e)}")
            # 如果使用数据库管理器，可能需要重试
            if USE_DB_MANAGER:
                try:
                    # 使用数据库管理器的重试机制
                    for metric in metrics:
                        db_manager.execute_with_retry(
                            self.db_path,
                            """
                            INSERT INTO metrics (metric_type, metric_name, value, timestamp, tags, metadata)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                metric.metric_type,
                                metric.metric_name,
                                metric.value,
                                metric.timestamp.isoformat(),
                                json.dumps(metric.tags, ensure_ascii=False),
                                json.dumps(metric.metadata, ensure_ascii=False)
                            )
                        )
                except Exception as e2:
                    self.logger.error(f"重试插入指标也失败: {str(e2)}")
    
    def _update_performance_cache(self, metrics: List[MetricData]):
        """更新性能缓存"""
        current_time = datetime.now()
        cache_key = current_time.strftime("%Y%m%d%H%M")
        
        if cache_key not in self.performance_cache:
            self.performance_cache[cache_key] = {
                "timestamp": current_time,
                "metrics": defaultdict(list)
            }
        
        cache_entry = self.performance_cache[cache_key]
        
        for metric in metrics:
            metric_key = f"{metric.metric_type}_{metric.metric_name}"
            cache_entry["metrics"][metric_key].append(metric.value)
        
        # 清理旧缓存
        cache_keys_to_delete = []
        for key in self.performance_cache.keys():
            cache_time = datetime.strptime(key, "%Y%m%d%H%M")
            if (current_time - cache_time).total_seconds() > 3600:  # 1小时前
                cache_keys_to_delete.append(key)
        
        for key in cache_keys_to_delete:
            del self.performance_cache[key]
    
    def _check_thresholds(self):
        """检查阈值并触发警报"""
        try:
            current_time = datetime.now()
            
            # 获取最近5分钟的性能数据
            recent_metrics = self._get_recent_metrics(minutes=5)
            
            for metric_type, thresholds in self.thresholds.items():
                if metric_type not in recent_metrics:
                    continue
                
                avg_value = statistics.mean(recent_metrics[metric_type]) if recent_metrics[metric_type] else 0
                
                # 检查警告阈值
                if "warning" in thresholds and avg_value >= thresholds["warning"]:
                    self._trigger_alert(
                        severity=AlertSeverity.WARNING.value,
                        metric_type=metric_type,
                        metric_name="avg",
                        current_value=avg_value,
                        threshold=thresholds["warning"],
                        title=f"{metric_type} 超过警告阈值",
                        message=f"{metric_type} 平均值 {avg_value:.1f}% 超过警告阈值 {thresholds['warning']}%"
                    )
                
                # 检查错误阈值
                if "error" in thresholds and avg_value >= thresholds["error"]:
                    self._trigger_alert(
                        severity=AlertSeverity.ERROR.value,
                        metric_type=metric_type,
                        metric_name="avg",
                        current_value=avg_value,
                        threshold=thresholds["error"],
                        title=f"{metric_type} 超过错误阈值",
                        message=f"{metric_type} 平均值 {avg_value:.1f}% 超过错误阈值 {thresholds['error']}%"
                    )
        
        except Exception as e:
            self.logger.error(f"检查阈值失败: {str(e)}")
    
    def _get_recent_metrics(self, minutes: int = 5) -> Dict[str, List[float]]:
        """获取最近指定分钟数的指标数据"""
        result = defaultdict(list)
        
        try:
            time_cutoff = (datetime.now() - timedelta(minutes=minutes)).isoformat()
            
            if USE_DB_MANAGER:
                conn = db_manager.get_connection(self.db_path)
            else:
                conn = sqlite3.connect(self.db_path)
            
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT metric_type, metric_name, value
                FROM metrics
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 1000
            """, (time_cutoff,))
            
            for row in cursor.fetchall():
                metric_type, metric_name, value = row
                key = metric_type  # 使用metric_type作为键
                result[key].append(value)
            
            if not USE_DB_MANAGER:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"获取最近指标失败: {str(e)}")
        
        return result
    
    def _trigger_alert(self, severity: str, metric_type: str, metric_name: str, 
                      current_value: float, threshold: float, title: str, message: str):
        """触发警报"""
        alert = Alert(
            severity=severity,
            title=title,
            message=message,
            metric_type=metric_type,
            metric_name=metric_name,
            threshold=threshold,
            current_value=current_value,
            triggered_at=datetime.now()
        )
        
        # 添加到缓冲区
        self.alert_buffer.append(alert)
        
        # 立即保存到数据库
        self._save_alert(alert)
        
        # 调用警报处理器
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"警报处理器出错: {str(e)}")
        
        self.logger.warning(f"触发警报: {title} - {message}")
    
    def _save_alert(self, alert: Alert):
        """保存警报到数据库"""
        try:
            if USE_DB_MANAGER:
                conn = db_manager.get_connection(self.db_path)
            else:
                conn = sqlite3.connect(self.db_path)
            
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO alerts 
                (alert_id, severity, title, message, metric_type, metric_name, threshold, current_value, triggered_at, acknowledged, acknowledged_at, acknowledged_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id,
                alert.severity,
                alert.title,
                alert.message,
                alert.metric_type,
                alert.metric_name,
                alert.threshold,
                alert.current_value,
                alert.triggered_at.isoformat(),
                1 if alert.acknowledged else 0,
                alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                alert.acknowledged_by
            ))
            
            conn.commit()
            
            if not USE_DB_MANAGER:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"保存警报失败: {str(e)}")
    
    def _aggregation_loop(self):
        """数据聚合循环"""
        self.logger.info("开始数据聚合循环")
        
        while self.is_running:
            try:
                # 每分钟执行一次聚合
                time.sleep(60)
                
                # 执行聚合
                self._aggregate_metrics()
                
                # 生成性能总结
                self._generate_performance_summary()
                
                # 清理旧数据
                self._cleanup_old_data()
                
            except Exception as e:
                self.logger.error(f"数据聚合循环出错: {str(e)}")
    
    def _aggregate_metrics(self):
        """聚合指标数据"""
        try:
            current_time = datetime.now()
            
            # 聚合时间窗口：1分钟、5分钟、1小时
            time_windows = [
                ("1min", timedelta(minutes=1)),
                ("5min", timedelta(minutes=5)),
                ("1hour", timedelta(hours=1)),
            ]
            
            for window_name, window_delta in time_windows:
                time_cutoff = (current_time - window_delta).isoformat()
                
                if USE_DB_MANAGER:
                    conn = db_manager.get_connection(self.db_path)
                else:
                    conn = sqlite3.connect(self.db_path)
                
                cursor = conn.cursor()
                
                # 按指标类型和名称聚合
                cursor.execute("""
                    SELECT 
                        metric_type,
                        metric_name,
                        COUNT(*) as sample_count,
                        AVG(value) as avg_value,
                        MIN(value) as min_value,
                        MAX(value) as max_value,
                        SUM(value) as sum_value
                    FROM metrics
                    WHERE timestamp >= ?
                    GROUP BY metric_type, metric_name
                """, (time_cutoff,))
                
                for row in cursor.fetchall():
                    metric_type, metric_name, sample_count, avg_value, min_value, max_value, sum_value = row
                    
                    # 保存聚合结果
                    cursor.execute("""
                        INSERT INTO aggregated_metrics 
                        (metric_type, metric_name, aggregation_type, time_window, value, timestamp, sample_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metric_type,
                        metric_name,
                        "avg",
                        window_name,
                        avg_value,
                        current_time.isoformat(),
                        sample_count
                    ))
                
                if not USE_DB_MANAGER:
                    conn.close()
                    
        except Exception as e:
            self.logger.error(f"聚合指标失败: {str(e)}")
    
    def _generate_performance_summary(self):
        """生成性能总结"""
        try:
            current_time = datetime.now()
            time_cutoff = (current_time - timedelta(minutes=5)).isoformat()
            
            if USE_DB_MANAGER:
                conn = db_manager.get_connection(self.db_path)
            else:
                conn = sqlite3.connect(self.db_path)
            
            cursor = conn.cursor()
            
            # 获取CPU使用率统计
            cursor.execute("""
                SELECT AVG(value), MAX(value)
                FROM metrics
                WHERE metric_type = ? AND metric_name = ? AND timestamp >= ?
            """, (MetricType.CPU_USAGE.value, "total", time_cutoff))
            
            cpu_avg, cpu_max = cursor.fetchone() or (0.0, 0.0)
            
            # 获取内存使用率统计
            cursor.execute("""
                SELECT AVG(value), MAX(value)
                FROM metrics
                WHERE metric_type = ? AND metric_name = ? AND timestamp >= ?
            """, (MetricType.MEMORY_USAGE.value, "total", time_cutoff))
            
            memory_avg, memory_max = cursor.fetchone() or (0.0, 0.0)
            
            # 获取磁盘IO统计
            cursor.execute("""
                SELECT AVG(value), MAX(value)
                FROM metrics
                WHERE metric_type = ? AND metric_name = ? AND timestamp >= ?
            """, (MetricType.DISK_IO.value, "read_speed_mb", time_cutoff))
            
            disk_read_avg, _ = cursor.fetchone() or (0.0, 0.0)
            
            cursor.execute("""
                SELECT AVG(value), MAX(value)
                FROM metrics
                WHERE metric_type = ? AND metric_name = ? AND timestamp >= ?
            """, (MetricType.DISK_IO.value, "write_speed_mb", time_cutoff))
            
            disk_write_avg, _ = cursor.fetchone() or (0.0, 0.0)
            
            # 获取函数调用统计
            cursor.execute("""
                SELECT COUNT(*) as call_count, AVG(value) as avg_time
                FROM metrics
                WHERE metric_type = ? AND timestamp >= ?
            """, (MetricType.FUNCTION_EXECUTION.value, time_cutoff))
            
            function_result = cursor.fetchone()
            function_calls = function_result[0] if function_result else 0
            avg_execution_time = function_result[1] if function_result and function_result[0] > 0 else 0.0
            
            # 获取错误统计
            cursor.execute("""
                SELECT COUNT(*) as error_count
                FROM metrics
                WHERE metric_type = ? AND timestamp >= ?
            """, (MetricType.ERROR_COUNT.value, time_cutoff))
            
            error_result = cursor.fetchone()
            error_count = error_result[0] if error_result else 0
            error_rate = (error_count / max(function_calls, 1)) * 100 if function_calls > 0 else 0.0
            
            # 创建性能总结
            summary = PerformanceSummary(
                timestamp=current_time,
                time_range_minutes=5,
                cpu_avg=float(cpu_avg or 0.0),
                cpu_max=float(cpu_max or 0.0),
                memory_avg=float(memory_avg or 0.0),
                memory_max=float(memory_max or 0.0),
                disk_read_avg=float(disk_read_avg or 0.0),
                disk_write_avg=float(disk_write_avg or 0.0),
                function_calls=int(function_calls or 0),
                avg_execution_time=float(avg_execution_time or 0.0),
                error_count=int(error_count or 0),
                error_rate=float(error_rate or 0.0)
            )
            
            # 保存到数据库
            cursor.execute("""
                INSERT INTO performance_summaries 
                (timestamp, time_range_minutes, cpu_avg, cpu_max, memory_avg, memory_max, 
                 disk_read_avg, disk_write_avg, function_calls, avg_execution_time, error_count, error_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                summary.timestamp.isoformat(),
                summary.time_range_minutes,
                summary.cpu_avg,
                summary.cpu_max,
                summary.memory_avg,
                summary.memory_max,
                summary.disk_read_avg,
                summary.disk_write_avg,
                summary.function_calls,
                summary.avg_execution_time,
                summary.error_count,
                summary.error_rate
            ))
            
            conn.commit()
            
            if not USE_DB_MANAGER:
                conn.close()
            
            self.logger.info(f"生成性能总结: CPU平均{cpu_avg:.1f}%, 内存平均{memory_avg:.1f}%, 函数调用{function_calls}次")
            
        except Exception as e:
            self.logger.error(f"生成性能总结失败: {str(e)}")
    
    def _cleanup_old_data(self):
        """清理旧数据"""
        try:
            retention_cutoff = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
            
            if USE_DB_MANAGER:
                conn = db_manager.get_connection(self.db_path)
            else:
                conn = sqlite3.connect(self.db_path)
            
            cursor = conn.cursor()
            
            # 删除旧的指标数据
            cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (retention_cutoff,))
            metrics_deleted = cursor.rowcount
            
            # 删除旧的聚合数据（保留更长时间）
            aggregation_cutoff = (datetime.now() - timedelta(days=self.retention_days * 2)).isoformat()
            cursor.execute("DELETE FROM aggregated_metrics WHERE timestamp < ?", (aggregation_cutoff,))
            aggregated_deleted = cursor.rowcount
            
            # 删除旧的性能总结（保留更长时间）
            summary_cutoff = (datetime.now() - timedelta(days=self.retention_days * 7)).isoformat()
            cursor.execute("DELETE FROM performance_summaries WHERE timestamp < ?", (summary_cutoff,))
            summaries_deleted = cursor.rowcount
            
            # 删除已确认的旧警报
            alert_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("DELETE FROM alerts WHERE acknowledged = 1 AND triggered_at < ?", (alert_cutoff,))
            alerts_deleted = cursor.rowcount
            
            conn.commit()
            
            if not USE_DB_MANAGER:
                conn.close()
            
            if metrics_deleted > 0 or aggregated_deleted > 0 or summaries_deleted > 0 or alerts_deleted > 0:
                self.logger.info(f"数据清理完成: 指标{metrics_deleted}条, 聚合{aggregated_deleted}条, 总结{summaries_deleted}条, 警报{alerts_deleted}条")
                
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {str(e)}")
    
    def _flush_buffers(self):
        """清空缓冲区"""
        try:
            # 处理剩余的指标
            self._process_buffer()
            
            # 处理剩余的警报
            while self.alert_buffer:
                alert = self.alert_buffer.popleft()
                self._save_alert(alert)
                
        except Exception as e:
            self.logger.error(f"清空缓冲区失败: {str(e)}")
    
    # ================== 公共API方法 ==================
    
    def track_function_execution(self, function_name: str, execution_time: float, 
                                success: bool = True, tags: Dict[str, str] = None, 
                                metadata: Dict[str, Any] = None):
        """
        跟踪函数执行
        
        Args:
            function_name: 函数名称
            execution_time: 执行时间（秒）
            success: 是否成功
            tags: 标签
            metadata: 元数据
        """
        current_time = datetime.now()
        
        # 记录执行时间
        self._add_metric(
            MetricType.FUNCTION_EXECUTION.value,
            function_name,
            execution_time,
            current_time,
            tags=tags,
            metadata=metadata
        )
        
        # 记录错误
        if not success:
            self._add_metric(
                MetricType.ERROR_COUNT.value,
                function_name,
                1.0,
                current_time,
                tags=tags,
                metadata=metadata
            )
    
    def track_database_query(self, query_type: str, execution_time: float, 
                            success: bool = True, rows_affected: int = 0):
        """
        跟踪数据库查询
        
        Args:
            query_type: 查询类型（SELECT, INSERT, UPDATE, DELETE等）
            execution_time: 执行时间（秒）
            success: 是否成功
            rows_affected: 影响的行数
        """
        current_time = datetime.now()
        
        self._add_metric(
            MetricType.DATABASE_QUERY.value,
            query_type,
            execution_time,
            current_time,
            tags={"rows_affected": str(rows_affected)},
            metadata={"success": success}
        )
        
        if not success:
            self._add_metric(
                MetricType.ERROR_COUNT.value,
                f"db_{query_type}",
                1.0,
                current_time
            )
    
    def track_user_activity(self, user_id: str, activity_type: str, 
                           duration: float = 0.0, metadata: Dict[str, Any] = None):
        """
        跟踪用户活动
        
        Args:
            user_id: 用户ID
            activity_type: 活动类型
            duration: 持续时间（秒）
            metadata: 元数据
        """
        current_time = datetime.now()
        
        self._add_metric(
            MetricType.USER_ACTIVITY.value,
            activity_type,
            duration,
            current_time,
            tags={"user_id": user_id},
            metadata=metadata
        )
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """
        添加警报处理器
        
        Args:
            handler: 警报处理函数
        """
        self.alert_handlers.append(handler)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        获取当前指标
        
        Returns:
            当前指标数据
        """
        try:
            current_time = datetime.now()
            
            # 从缓存获取最新数据
            cache_key = current_time.strftime("%Y%m%d%H%M")
            if cache_key in self.performance_cache:
                cache_entry = self.performance_cache[cache_key]
                
                result = {
                    "timestamp": cache_entry["timestamp"].isoformat(),
                    "metrics": {}
                }
                
                for metric_key, values in cache_entry["metrics"].items():
                    if values:
                        result["metrics"][metric_key] = {
                            "current": values[-1],
                            "avg": statistics.mean(values) if len(values) > 1 else values[0],
                            "min": min(values),
                            "max": max(values),
                            "count": len(values)
                        }
                
                return result
            
            return {"timestamp": current_time.isoformat(), "metrics": {}}
            
        except Exception as e:
            self.logger.error(f"获取当前指标失败: {str(e)}")
            return {"error": str(e)}
    
    def get_performance_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """
        获取性能总结
        
        Args:
            minutes: 时间范围（分钟）
            
        Returns:
            性能总结数据
        """
        try:
            time_cutoff = (datetime.now() - timedelta(minutes=minutes)).isoformat()
            
            if USE_DB_MANAGER:
                conn = db_manager.get_connection(self.db_path)
            else:
                conn = sqlite3.connect(self.db_path)
            
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM performance_summaries 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (time_cutoff,))
            
            row = cursor.fetchone()
            
            if not USE_DB_MANAGER:
                conn.close()
            
            if row:
                # 解析结果
                columns = [description[0] for description in cursor.description]
                result = dict(zip(columns, row))
                
                # 转换时间戳
                if "timestamp" in result:
                    result["timestamp"] = datetime.fromisoformat(result["timestamp"])
                
                return result
            
            return {"message": f"最近{minutes}分钟内没有性能总结数据"}
            
        except Exception as e:
            self.logger.error(f"获取性能总结失败: {str(e)}")
            return {"error": str(e)}
    
    def get_alerts(self, severity: str = None, acknowledged: bool = None, 
                  hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取警报
        
        Args:
            severity: 严重级别过滤
            acknowledged: 是否已确认过滤
            hours: 时间范围（小时）
            
        Returns:
            警报列表
        """
        try:
            time_cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            if USE_DB_MANAGER:
                conn = db_manager.get_connection(self.db_path)
            else:
                conn = sqlite3.connect(self.db_path)
            
            cursor = conn.cursor()
            
            query = "SELECT * FROM alerts WHERE triggered_at >= ?"
            params = [time_cutoff]
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            if acknowledged is not None:
                query += " AND acknowledged = ?"
                params.append(1 if acknowledged else 0)
            
            query += " ORDER BY triggered_at DESC"
            
            cursor.execute(query, params)
            
            alerts = []
            for row in cursor.fetchall():
                columns = [description[0] for description in cursor.description]
                alert_dict = dict(zip(columns, row))
                
                # 转换时间戳
                for time_field in ["triggered_at", "acknowledged_at"]:
                    if alert_dict.get(time_field):
                        alert_dict[time_field] = datetime.fromisoformat(alert_dict[time_field])
                
                alerts.append(alert_dict)
            
            if not USE_DB_MANAGER:
                conn.close()
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"获取警报失败: {str(e)}")
            return []
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """
        确认警报
        
        Args:
            alert_id: 警报ID
            acknowledged_by: 确认者
            
        Returns:
            是否成功
        """
        try:
            if USE_DB_MANAGER:
                conn = db_manager.get_connection(self.db_path)
            else:
                conn = sqlite3.connect(self.db_path)
            
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE alerts 
                SET acknowledged = 1, acknowledged_at = ?, acknowledged_by = ?
                WHERE alert_id = ?
            """, (datetime.now().isoformat(), acknowledged_by, alert_id))
            
            updated = cursor.rowcount > 0
            
            conn.commit()
            
            if not USE_DB_MANAGER:
                conn.close()
            
            if updated:
                self.logger.info(f"警报 {alert_id} 已被 {acknowledged_by} 确认")
            
            return updated
            
        except Exception as e:
            self.logger.error(f"确认警报失败: {str(e)}")
            return False
    
    def get_metrics_report(self, metric_type: str = None, start_time: datetime = None, 
                          end_time: datetime = None) -> Dict[str, Any]:
        """
        获取指标报告
        
        Args:
            metric_type: 指标类型过滤
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            指标报告
        """
        try:
            if start_time is None:
                start_time = datetime.now() - timedelta(hours=1)
            if end_time is None:
                end_time = datetime.now()
            
            if USE_DB_MANAGER:
                conn = db_manager.get_connection(self.db_path)
            else:
                conn = sqlite3.connect(self.db_path)
            
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    metric_type,
                    metric_name,
                    COUNT(*) as count,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    SUM(value) as sum_value
                FROM metrics
                WHERE timestamp BETWEEN ? AND ?
            """
            
            params = [start_time.isoformat(), end_time.isoformat()]
            
            if metric_type:
                query += " AND metric_type = ?"
                params.append(metric_type)
            
            query += " GROUP BY metric_type, metric_name ORDER BY metric_type, metric_name"
            
            cursor.execute(query, params)
            
            report = {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "metrics": []
            }
            
            for row in cursor.fetchall():
                metric_type, metric_name, count, avg_value, min_value, max_value, sum_value = row
                
                report["metrics"].append({
                    "metric_type": metric_type,
                    "metric_name": metric_name,
                    "count": count,
                    "avg": float(avg_value or 0.0),
                    "min": float(min_value or 0.0),
                    "max": float(max_value or 0.0),
                    "sum": float(sum_value or 0.0)
                })
            
            if not USE_DB_MANAGER:
                conn.close()
            
            return report
            
        except Exception as e:
            self.logger.error(f"获取指标报告失败: {str(e)}")
            return {"error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """
        获取系统状态统计
        
        Returns:
            包含系统状态的字典
        """
        try:
            # 获取最近5分钟的指标
            recent_metrics = self._get_recent_metrics(minutes=5)
            
            # 计算平均CPU使用率
            cpu_values = recent_metrics.get("cpu_usage_total", [])
            cpu_avg = statistics.mean(cpu_values) if cpu_values else 0.0
            
            # 计算平均内存使用率
            memory_values = recent_metrics.get("memory_usage", [])
            memory_avg = statistics.mean(memory_values) if memory_values else 0.0
            
            # 计算平均磁盘使用率
            disk_values = recent_metrics.get("disk_usage_percent", [])
            disk_avg = statistics.mean(disk_values) if disk_values else 0.0
            
            # 获取未确认的警报数量
            active_alerts = 0
            try:
                if USE_DB_MANAGER:
                    conn = db_manager.get_connection(self.db_path)
                else:
                    conn = sqlite3.connect(self.db_path)
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM alerts 
                    WHERE acknowledged = 0 
                    AND triggered_at >= datetime('now', '-1 day')
                """)
                result = cursor.fetchone()
                active_alerts = result[0] if result else 0
                
                if not USE_DB_MANAGER:
                    conn.close()
            except:
                active_alerts = 0
            
            # 计算运行时间（如果监控器已启动）
            uptime = "未知"
            if self.last_collection_time:
                uptime_seconds = (datetime.now() - self.last_collection_time).total_seconds()
                uptime = self._format_duration(uptime_seconds)
            
            return {
                "uptime": uptime,
                "cpu_usage": {"current": round(cpu_avg, 1), "avg": round(cpu_avg, 1)},
                "memory_usage": {"current": round(memory_avg, 1), "avg": round(memory_avg, 1)},
                "disk_usage": {"current": round(disk_avg, 1), "avg": round(disk_avg, 1)},
                "active_alerts": active_alerts
            }
            
        except Exception as e:
            self.logger.error(f"获取系统状态失败: {str(e)}")
            return {
                "uptime": "未知",
                "cpu_usage": {"current": 0, "avg": 0},
                "memory_usage": {"current": 0, "avg": 0},
                "disk_usage": {"current": 0, "avg": 0},
                "active_alerts": 0
            }

    def _format_duration(self, seconds: float) -> str:
        """格式化持续时间"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f}分钟"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}小时"
        else:
            days = seconds / 86400
            return f"{days:.1f}天"


# 全局监控器实例
_global_monitor = None


def get_global_monitor(config: Dict[str, Any] = None) -> RealTimeMonitor:
    """
    获取全局监控器实例（单例模式）
    
    Args:
        config: 配置参数
        
    Returns:
        全局监控器实例
    """
    global _global_monitor
    
    if _global_monitor is None:
        if config is None:
            config = {}
        _global_monitor = RealTimeMonitor(config)
    
    return _global_monitor