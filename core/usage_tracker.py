"""
使用模式跟踪模块

功能：记录用户所有交互操作，统计功能使用频率，分析使用时间模式，识别高频使用场景

主要功能：
1. 记录用户操作：记录用户每次调用的功能、参数、执行时间等
2. 统计使用频率：分析各功能的使用频率和趋势
3. 模式识别：识别用户的使用习惯和模式
4. 数据持久化：将使用记录保存到数据库中

数据模型：
- UsageRecord: 单次使用记录
- FunctionStats: 功能使用统计
- UserPattern: 用户使用模式
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import os
from collections import defaultdict
from enum import Enum

# 导入数据库管理器
try:
    from .database_manager import db_manager
    USE_DB_MANAGER = True
except ImportError:
    USE_DB_MANAGER = False
    import sqlite3


class FunctionCategory(Enum):
    """功能分类枚举"""
    STOCK_QUERY = "股票查询"
    DATA_ANALYSIS = "数据分析"
    SYSTEM_CONFIG = "系统配置"
    FILE_OPERATION = "文件操作"
    CODE_GENERATION = "代码生成"
    TOOL_EXECUTION = "工具执行"
    SEARCH = "搜索"
    OTHER = "其他"


@dataclass
class UsageRecord:
    """使用记录数据类"""
    id: Optional[int] = None
    timestamp: datetime = None
    session_id: str = ""
    function_name: str = ""
    function_category: str = FunctionCategory.OTHER.value
    parameters: Dict[str, Any] = None
    execution_time: float = 0.0
    success: bool = True
    error_message: str = ""
    user_feedback: str = ""
    context_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.parameters is None:
            self.parameters = {}
        if self.context_info is None:
            self.context_info = {}


@dataclass
class FunctionStats:
    """功能使用统计数据类"""
    function_name: str = ""
    function_category: str = FunctionCategory.OTHER.value
    total_calls: int = 0
    recent_calls: int = 0  # 最近7天调用次数
    avg_execution_time: float = 0.0
    success_rate: float = 1.0
    last_called: datetime = None
    peak_hour: int = 0  # 最常使用的小时（0-23）
    
    def __post_init__(self):
        if self.last_called is None:
            self.last_called = datetime.now()


@dataclass
class UserPattern:
    """用户使用模式数据类"""
    pattern_name: str = ""
    description: str = ""
    functions: List[str] = None
    frequency: str = ""  # 频率：每天、每周、每月
    time_range: str = ""  # 时间范围：如"09:00-11:00"
    confidence: float = 0.0  # 模式置信度（0-1）
    
    def __post_init__(self):
        if self.functions is None:
            self.functions = []


class UsagePatternTracker:
    """使用模式跟踪器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化使用模式跟踪器
        
        Args:
            db_path: SQLite数据库路径，如果为None则使用默认路径
        """
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "data", "usage_tracking.db")
        
        self.db_path = db_path
        self._init_database()
        
        # 内存缓存
        self._recent_records = []
        self._stats_cache = {}
        self._patterns_cache = []
        
        # 批量处理器
        self._batch_processor_id = None
        if USE_DB_MANAGER:
            try:
                # 启动批量处理器用于使用记录
                self._batch_processor_id = db_manager.start_batch_processor(
                    self.db_path, 
                    "usage_records",
                    flush_interval=3.0,  # 3秒刷新间隔
                    batch_size=50        # 每批50条记录
                )
            except Exception as e:
                print(f"警告: 无法启动批量处理器: {str(e)}")
                self._batch_processor_id = None
    
    def __del__(self):
        """析构函数，清理资源"""
        if USE_DB_MANAGER and self._batch_processor_id:
            try:
                db_manager.stop_batch_processor(self._batch_processor_id)
            except:
                pass
    
    def _init_database(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 启用WAL模式以减少锁定和提高并发性能
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")  # 5秒超时
        cursor.execute("PRAGMA foreign_keys=ON")
        
        # 创建使用记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                session_id TEXT NOT NULL,
                function_name TEXT NOT NULL,
                function_category TEXT NOT NULL,
                parameters TEXT,
                execution_time REAL,
                success BOOLEAN,
                error_message TEXT,
                user_feedback TEXT,
                context_info TEXT
            )
        """)
        
        # 创建功能统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS function_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_name TEXT UNIQUE NOT NULL,
                function_category TEXT NOT NULL,
                total_calls INTEGER DEFAULT 0,
                recent_calls INTEGER DEFAULT 0,
                avg_execution_time REAL DEFAULT 0.0,
                success_rate REAL DEFAULT 1.0,
                last_called DATETIME,
                peak_hour INTEGER DEFAULT 0
            )
        """)
        
        # 创建用户模式表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                description TEXT,
                functions TEXT,
                frequency TEXT,
                time_range TEXT,
                confidence REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON usage_records(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_function ON usage_records(function_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_session ON usage_records(session_id)")
        
        conn.commit()
        conn.close()
    
    def record_usage(self, record: UsageRecord) -> int:
        """
        记录用户使用情况
        
        Args:
            record: 使用记录
            
        Returns:
            记录ID（对于批量写入返回-1表示已排队）
        """
        # 添加到内存缓存
        self._recent_records.append(record)
        if len(self._recent_records) > 1000:  # 限制缓存大小
            self._recent_records = self._recent_records[-500:]
        
        # 尝试批量写入
        if USE_DB_MANAGER and self._batch_processor_id:
            try:
                # 准备批量记录
                batch_record = {
                    "timestamp": record.timestamp.isoformat(),
                    "session_id": record.session_id,
                    "function_name": record.function_name,
                    "function_category": record.function_category,
                    "parameters": json.dumps(record.parameters, ensure_ascii=False),
                    "execution_time": record.execution_time,
                    "success": record.success,
                    "error_message": record.error_message,
                    "user_feedback": record.user_feedback,
                    "context_info": json.dumps(record.context_info, ensure_ascii=False)
                }
                
                # 添加到批量队列
                db_manager.queue_batch_record(self._batch_processor_id, batch_record)
                
                # 更新功能统计（异步进行）
                self._update_function_stats_async(record)
                
                # 批量写入不返回实际的记录ID
                return -1
                
            except Exception as e:
                print(f"批量写入失败，回退到直接写入: {str(e)}")
                # 回退到直接写入
        
        # 直接写入模式
        max_retries = 10
        retry_delay = 1.0  # 秒
        
        for attempt in range(max_retries):
            try:
                if USE_DB_MANAGER:
                    # 使用数据库管理器执行
                    cursor = db_manager.execute_with_retry(
                        self.db_path,
                        """
                        INSERT INTO usage_records 
                        (timestamp, session_id, function_name, function_category, parameters, 
                         execution_time, success, error_message, user_feedback, context_info)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record.timestamp.isoformat(),
                            record.session_id,
                            record.function_name,
                            record.function_category,
                            json.dumps(record.parameters, ensure_ascii=False),
                            record.execution_time,
                            record.success,
                            record.error_message,
                            record.user_feedback,
                            json.dumps(record.context_info, ensure_ascii=False)
                        )
                    )
                    record_id = cursor.lastrowid
                else:
                    # 传统方式
                    conn = sqlite3.connect(self.db_path, timeout=10.0)  # 设置超时
                    cursor = conn.cursor()
                    
                    # 设置数据库优化参数
                    cursor.execute("PRAGMA busy_timeout=5000")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    
                    # 插入使用记录
                    cursor.execute("""
                        INSERT INTO usage_records 
                        (timestamp, session_id, function_name, function_category, parameters, 
                         execution_time, success, error_message, user_feedback, context_info)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record.timestamp.isoformat(),
                        record.session_id,
                        record.function_name,
                        record.function_category,
                        json.dumps(record.parameters, ensure_ascii=False),
                        record.execution_time,
                        record.success,
                        record.error_message,
                        record.user_feedback,
                        json.dumps(record.context_info, ensure_ascii=False)
                    ))
                    
                    record_id = cursor.lastrowid
                    conn.commit()
                    conn.close()
                
                # 更新功能统计
                self._update_function_stats(record)
                
                return record_id
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 指数退避
                    continue
                else:
                    raise
            except Exception as e:
                raise
    
    def _update_function_stats(self, record: UsageRecord):
        """更新功能统计"""
        max_retries = 10
        retry_delay = 1.0  # 秒
        
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                cursor = conn.cursor()
                
                # 设置数据库优化参数
                cursor.execute("PRAGMA busy_timeout=5000")
                cursor.execute("PRAGMA synchronous=NORMAL")
                
                # 获取现有统计
                cursor.execute(
                    "SELECT * FROM function_stats WHERE function_name = ?",
                    (record.function_name,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有统计
                    stats_id, function_name, category, total_calls, recent_calls, \
                    avg_time, success_rate, last_called, peak_hour = existing
                    
                    # 计算新的平均值
                    new_total = total_calls + 1
                    new_avg = (avg_time * total_calls + record.execution_time) / new_total
                    
                    # 计算新的成功率
                    new_success = (success_rate * total_calls + (1 if record.success else 0)) / new_total
                    
                    # 更新时间
                    record_time = record.timestamp.hour
                    
                    cursor.execute("""
                        UPDATE function_stats SET
                        total_calls = ?,
                        recent_calls = ?,
                        avg_execution_time = ?,
                        success_rate = ?,
                        last_called = ?,
                        peak_hour = CASE 
                            WHEN ? = peak_hour THEN peak_hour 
                            ELSE (SELECT hour FROM (
                                SELECT strftime('%H', timestamp) as hour, COUNT(*) as cnt
                                FROM usage_records 
                                WHERE function_name = ?
                                GROUP BY strftime('%H', timestamp)
                                ORDER BY cnt DESC
                                LIMIT 1
                            ))
                        END
                        WHERE id = ?
                    """, (
                        new_total,
                        recent_calls,  # 最近调用次数需要另外计算
                        new_avg,
                        new_success,
                        record.timestamp.isoformat(),
                        record_time,
                        record.function_name,
                        stats_id
                    ))
                else:
                    # 插入新统计
                    cursor.execute("""
                        INSERT INTO function_stats 
                        (function_name, function_category, total_calls, recent_calls, 
                         avg_execution_time, success_rate, last_called, peak_hour)
                        VALUES (?, ?, 1, 0, ?, ?, ?, ?)
                    """, (
                        record.function_name,
                        record.function_category,
                        record.execution_time,
                        1.0 if record.success else 0.0,
                        record.timestamp.isoformat(),
                        record.timestamp.hour
                    ))
                
                conn.commit()
                conn.close()
                return
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise
            except Exception as e:
                raise
    
    def _update_function_stats_async(self, record: UsageRecord):
        """异步更新功能统计（用于批量写入）"""
        try:
            # 使用数据库管理器的批量操作
            if USE_DB_MANAGER:
                # 这里可以进一步优化为批量更新统计
                # 目前先简单调用_update_function_stats
                # 在实际生产环境中，可以累积统计更新并批量执行
                self._update_function_stats(record)
            else:
                self._update_function_stats(record)
        except Exception as e:
            # 异步更新失败不影响主流程
            print(f"异步更新功能统计失败: {str(e)}")
    
    def get_function_stats(self, function_name: str = None) -> List[FunctionStats]:
        """
        获取功能使用统计
        
        Args:
            function_name: 功能名称，如果为None则返回所有功能统计
            
        Returns:
            功能统计列表
        """
        max_retries = 3
        retry_delay = 0.3
        
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=5.0)
                cursor = conn.cursor()
                
                # 设置数据库优化参数
                cursor.execute("PRAGMA busy_timeout=5000")
                cursor.execute("PRAGMA synchronous=NORMAL")
                
                if function_name:
                    cursor.execute(
                        "SELECT * FROM function_stats WHERE function_name = ?",
                        (function_name,)
                    )
                else:
                    cursor.execute("SELECT * FROM function_stats ORDER BY total_calls DESC")
                
                results = []
                for row in cursor.fetchall():
                    stats_id, function_name, category, total_calls, recent_calls, \
                    avg_time, success_rate, last_called, peak_hour = row
                    
                    results.append(FunctionStats(
                        function_name=function_name,
                        function_category=category,
                        total_calls=total_calls,
                        recent_calls=recent_calls,
                        avg_execution_time=avg_time,
                        success_rate=success_rate,
                        last_called=datetime.fromisoformat(last_called) if last_called else None,
                        peak_hour=peak_hour
                    ))
                
                conn.close()
                return results
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise
            except Exception as e:
                raise

    
    def get_most_frequent_functions(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """
        获取最常使用的功能
        
        Args:
            limit: 返回数量限制
            days: 统计最近多少天的数据
            
        Returns:
            功能使用频率列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT function_name, COUNT(*) as call_count,
                   AVG(execution_time) as avg_time,
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM usage_records
            WHERE timestamp >= ?
            GROUP BY function_name
            ORDER BY call_count DESC
            LIMIT ?
        """, (start_date, limit))
        
        results = []
        for row in cursor.fetchall():
            function_name, call_count, avg_time, success_rate = row
            results.append({
                "function_name": function_name,
                "call_count": call_count,
                "avg_execution_time": avg_time,
                "success_rate": success_rate
            })
        
        conn.close()
        return results
    
    def analyze_user_patterns(self) -> List[UserPattern]:
        """
        分析用户使用模式
        
        Returns:
            用户使用模式列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 分析每日使用模式
        cursor.execute("""
            SELECT 
                strftime('%H', timestamp) as hour,
                function_category,
                COUNT(*) as call_count
            FROM usage_records
            WHERE timestamp >= datetime('now', '-30 days')
            GROUP BY strftime('%H', timestamp), function_category
            ORDER BY hour, call_count DESC
        """)
        
        hourly_patterns = defaultdict(list)
        for hour, category, count in cursor.fetchall():
            if count > 3:  # 只有超过3次调用才认为是模式
                hourly_patterns[int(hour)].append((category, count))
        
        # 分析功能组合模式
        cursor.execute("""
            SELECT 
                session_id,
                GROUP_CONCAT(function_name, ',') as functions,
                COUNT(*) as function_count
            FROM (
                SELECT session_id, function_name
                FROM usage_records
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY session_id, function_name
            )
            GROUP BY session_id
            HAVING function_count >= 2
        """)
        
        combo_patterns = defaultdict(int)
        for session_id, functions_str, count in cursor.fetchall():
            functions = functions_str.split(',')
            if len(functions) >= 2:
                key = tuple(sorted(functions))
                combo_patterns[key] += 1
        
        # 生成模式对象
        patterns = []
        
        # 时间模式
        for hour, categories in hourly_patterns.items():
            if categories:
                main_category = categories[0][0]
                patterns.append(UserPattern(
                    pattern_name=f"每日{hour}时使用习惯",
                    description=f"用户在{hour}时最常使用{main_category}功能",
                    functions=[f"hour_{hour}"],
                    frequency="每天",
                    time_range=f"{hour:02d}:00-{hour+1:02d}:00",
                    confidence=min(1.0, categories[0][1] / 10.0)
                ))
        
        # 功能组合模式
        for func_combo, count in combo_patterns.items():
            if count >= 3:  # 至少出现3次
                patterns.append(UserPattern(
                    pattern_name=f"功能组合：{', '.join(func_combo[:3])}" + 
                                ("..." if len(func_combo) > 3 else ""),
                    description=f"用户经常同时使用这些功能",
                    functions=list(func_combo),
                    frequency="频繁",
                    time_range="",
                    confidence=min(1.0, count / 10.0)
                ))
        
        # 保存模式到数据库
        cursor.execute("DELETE FROM user_patterns")
        for pattern in patterns:
            cursor.execute("""
                INSERT INTO user_patterns 
                (pattern_name, description, functions, frequency, time_range, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pattern.pattern_name,
                pattern.description,
                json.dumps(pattern.functions, ensure_ascii=False),
                pattern.frequency,
                pattern.time_range,
                pattern.confidence
            ))
        
        conn.commit()
        conn.close()
        
        self._patterns_cache = patterns
        return patterns
    
    def get_recent_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取最近使用情况摘要
        
        Args:
            hours: 统计最近多少小时
            
        Returns:
            使用情况摘要
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        # 总调用次数
        cursor.execute("""
            SELECT COUNT(*) FROM usage_records WHERE timestamp >= ?
        """, (start_time,))
        total_calls = cursor.fetchone()[0]
        
        # 不同功能数量
        cursor.execute("""
            SELECT COUNT(DISTINCT function_name) FROM usage_records WHERE timestamp >= ?
        """, (start_time,))
        unique_functions = cursor.fetchone()[0]
        
        # 最常使用的功能
        cursor.execute("""
            SELECT function_name, COUNT(*) as call_count
            FROM usage_records
            WHERE timestamp >= ?
            GROUP BY function_name
            ORDER BY call_count DESC
            LIMIT 5
        """, (start_time,))
        top_functions = cursor.fetchall()
        
        # 成功率
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM usage_records
            WHERE timestamp >= ?
        """, (start_time,))
        success_rate = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        return {
            "period_hours": hours,
            "total_calls": total_calls,
            "unique_functions": unique_functions,
            "success_rate": success_rate,
            "top_functions": [
                {"function_name": name, "call_count": count}
                for name, count in top_functions
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    def export_usage_data(self, output_path: str = None, days: int = 30):
        """
        导出使用数据
        
        Args:
            output_path: 输出文件路径
            days: 导出最近多少天的数据
        """
        if output_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_path = os.path.join(base_dir, "exports", f"usage_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # 获取使用记录
        cursor.execute("""
            SELECT * FROM usage_records WHERE timestamp >= ?
        """, (start_date,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                "id": row[0],
                "timestamp": row[1],
                "session_id": row[2],
                "function_name": row[3],
                "function_category": row[4],
                "parameters": json.loads(row[5]) if row[5] else {},
                "execution_time": row[6],
                "success": bool(row[7]),
                "error_message": row[8],
                "user_feedback": row[9],
                "context_info": json.loads(row[10]) if row[10] else {}
            })
        
        # 获取功能统计
        cursor.execute("SELECT * FROM function_stats")
        
        stats = []
        for row in cursor.fetchall():
            stats.append({
                "id": row[0],
                "function_name": row[1],
                "function_category": row[2],
                "total_calls": row[3],
                "recent_calls": row[4],
                "avg_execution_time": row[5],
                "success_rate": row[6],
                "last_called": row[7],
                "peak_hour": row[8]
            })
        
        # 获取用户模式
        cursor.execute("SELECT * FROM user_patterns")
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                "id": row[0],
                "pattern_name": row[1],
                "description": row[2],
                "functions": json.loads(row[3]) if row[3] else [],
                "frequency": row[4],
                "time_range": row[5],
                "confidence": row[6],
                "created_at": row[7],
                "updated_at": row[8]
            })
        
        conn.close()
        
        # 生成导出数据
        export_data = {
            "export_time": datetime.now().isoformat(),
            "data_range_days": days,
            "total_records": len(records),
            "usage_records": records,
            "function_stats": stats,
            "user_patterns": patterns,
            "summary": self.get_recent_usage_summary(24)
        }
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        return output_path
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        清理旧数据
        
        Args:
            days_to_keep: 保留多少天的数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        # 删除旧的使用记录
        cursor.execute("DELETE FROM usage_records WHERE timestamp < ?", (cutoff_date,))
        
        # 更新功能统计中的recent_calls
        cursor.execute("""
            UPDATE function_stats 
            SET recent_calls = (
                SELECT COUNT(*) 
                FROM usage_records ur 
                WHERE ur.function_name = function_stats.function_name 
                AND ur.timestamp >= datetime('now', '-7 days')
            )
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def get_usage_insights(self) -> Dict[str, Any]:
        """
        获取使用洞察
        
        Returns:
            使用洞察信息
        """
        # 获取最近7天使用情况
        recent_stats = self.get_most_frequent_functions(days=7, limit=20)
        
        # 获取用户模式
        patterns = self.analyze_user_patterns()
        
        # 获取性能洞察
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 最慢的功能
        cursor.execute("""
            SELECT function_name, AVG(execution_time) as avg_time
            FROM usage_records
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY function_name
            HAVING COUNT(*) >= 5
            ORDER BY avg_time DESC
            LIMIT 5
        """)
        slowest_functions = cursor.fetchall()
        
        # 成功率最低的功能
        cursor.execute("""
            SELECT function_name, 
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM usage_records
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY function_name
            HAVING COUNT(*) >= 3
            ORDER BY success_rate ASC
            LIMIT 5
        """)
        low_success_functions = cursor.fetchall()
        
        conn.close()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "most_frequent_functions": recent_stats,
            "user_patterns": [asdict(p) for p in patterns],
            "performance_insights": {
                "slowest_functions": [
                    {"function_name": name, "avg_execution_time": avg_time}
                    for name, avg_time in slowest_functions
                ],
                "low_success_functions": [
                    {"function_name": name, "success_rate": success_rate}
                    for name, success_rate in low_success_functions
                ]
            },
            "recommendations": self._generate_recommendations(recent_stats, patterns)
        }
    
    def _generate_recommendations(self, recent_stats: List, patterns: List[UserPattern]) -> List[Dict]:
        """生成优化建议"""
        recommendations = []
        
        # 基于使用频率的建议
        for stat in recent_stats[:5]:  # 最常使用的5个功能
            if stat["avg_execution_time"] > 1.0:  # 执行时间超过1秒
                recommendations.append({
                    "type": "性能优化",
                    "priority": "高",
                    "function": stat["function_name"],
                    "reason": f"该功能平均执行时间{stat['avg_execution_time']:.2f}秒，使用频率高，优化后能显著提升用户体验",
                    "suggestion": "优化算法、添加缓存、并行处理"
                })
            
            if stat["success_rate"] < 0.8:  # 成功率低于80%
                recommendations.append({
                    "type": "稳定性改进",
                    "priority": "高",
                    "function": stat["function_name"],
                    "reason": f"该功能成功率仅{stat['success_rate']*100:.1f}%，影响用户体验",
                    "suggestion": "修复错误、增加错误处理、改进输入验证"
                })
        
        # 基于用户模式的建议
        for pattern in patterns:
            if pattern.confidence > 0.7:  # 高置信度模式
                recommendations.append({
                    "type": "功能增强",
                    "priority": "中",
                    "pattern": pattern.pattern_name,
                    "reason": f"检测到稳定的用户模式：{pattern.description}",
                    "suggestion": f"为{pattern.functions}创建快捷方式或自动化流程"
                })
        
        return recommendations


# 全局跟踪器实例
_global_tracker = None

def get_global_tracker() -> UsagePatternTracker:
    """获取全局跟踪器实例"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = UsagePatternTracker()
    return _global_tracker


def track_usage_decorator(function_category: str = FunctionCategory.OTHER.value):
    """
    使用跟踪装饰器
    
    Args:
        function_category: 功能分类
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracker = get_global_tracker()
            start_time = time.time()
            
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # 记录成功使用
                record = UsageRecord(
                    function_name=func.__name__,
                    function_category=function_category,
                    parameters={
                        "args": str(args)[:500],  # 限制长度
                        "kwargs": str(kwargs)[:500]
                    },
                    execution_time=execution_time,
                    success=True,
                    context_info={
                        "module": func.__module__,
                        "function": func.__qualname__
                    }
                )
                tracker.record_usage(record)
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # 记录失败使用
                record = UsageRecord(
                    function_name=func.__name__,
                    function_category=function_category,
                    parameters={
                        "args": str(args)[:500],
                        "kwargs": str(kwargs)[:500]
                    },
                    execution_time=execution_time,
                    success=False,
                    error_message=str(e)[:1000],
                    context_info={
                        "module": func.__module__,
                        "function": func.__qualname__
                    }
                )
                tracker.record_usage(record)
                
                raise
        
        return wrapper
    return decorator