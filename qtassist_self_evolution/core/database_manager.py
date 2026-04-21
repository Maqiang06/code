#!/usr/bin/env python3
"""
数据库连接管理器

解决SQLite并发访问锁定问题，提供连接池和批量写入功能
"""

import sqlite3
import threading
import time
import json
import os
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import queue
import logging

class DatabaseManager:
    """数据库连接管理器 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = logging.getLogger(__name__)
        
        # 连接池配置
        self.max_pool_size = 5
        self.max_retries = 3
        self.retry_delay = 0.5
        
        # 连接池
        self._connection_pool = {}
        self._pool_lock = threading.Lock()
        
        # 线程本地存储
        self._thread_local = threading.local()
        
        # 批量写入队列
        self._batch_queues = {}
        self._batch_locks = {}
        self._batch_threads = {}
        self._batch_running = {}
        
        # 统计信息
        self.stats = {
            "connections_created": 0,
            "connections_reused": 0,
            "batch_writes": 0,
            "immediate_writes": 0,
            "lock_timeouts": 0,
            "retries": 0
        }
    
    def get_connection(self, db_path: str, timeout: float = 10.0) -> sqlite3.Connection:
        """
        获取数据库连接
        
        Args:
            db_path: 数据库文件路径
            timeout: 超时时间（秒）
            
        Returns:
            SQLite连接对象
        """
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 尝试从线程本地存储获取连接
        if hasattr(self._thread_local, 'connections'):
            connections = self._thread_local.connections
            if db_path in connections:
                try:
                    # 测试连接是否仍然有效
                    connections[db_path].execute("SELECT 1")
                    self.stats["connections_reused"] += 1
                    return connections[db_path]
                except sqlite3.Error:
                    # 连接已失效，创建新连接
                    pass
        
        # 创建新连接
        for attempt in range(self.max_retries):
            try:
                conn = sqlite3.connect(db_path, timeout=timeout)
                
                # 设置优化参数
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=5000")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA cache_size=-2000")  # 2MB缓存
                cursor.execute("PRAGMA temp_store=MEMORY")
                
                # 存储在线程本地
                if not hasattr(self._thread_local, 'connections'):
                    self._thread_local.connections = {}
                self._thread_local.connections[db_path] = conn
                
                self.stats["connections_created"] += 1
                return conn
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < self.max_retries - 1:
                    self.stats["retries"] += 1
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    self.stats["lock_timeouts"] += 1
                    self.logger.error(f"数据库连接失败: {str(e)}")
                    raise
            except Exception as e:
                self.logger.error(f"数据库连接错误: {str(e)}")
                raise
    
    def execute_with_retry(self, db_path: str, sql: str, params: tuple = (), 
                          timeout: float = 10.0, max_retries: int = 3) -> Any:
        """
        执行SQL语句并支持重试
        
        Args:
            db_path: 数据库文件路径
            sql: SQL语句
            params: SQL参数
            timeout: 超时时间
            max_retries: 最大重试次数
            
        Returns:
            执行结果
        """
        for attempt in range(max_retries):
            try:
                conn = self.get_connection(db_path, timeout)
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                return cursor
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    self.stats["retries"] += 1
                    time.sleep(self.retry_delay * (attempt + 1))
                    
                    # 重置连接
                    if hasattr(self._thread_local, 'connections'):
                        if db_path in self._thread_local.connections:
                            try:
                                self._thread_local.connections[db_path].close()
                            except:
                                pass
                            del self._thread_local.connections[db_path]
                    continue
                else:
                    self.stats["lock_timeouts"] += 1
                    self.logger.error(f"SQL执行失败: {str(e)}")
                    raise
            except Exception as e:
                self.logger.error(f"SQL执行错误: {str(e)}")
                raise
    
    def execute_many_with_retry(self, db_path: str, sql: str, params_list: List[tuple],
                               timeout: float = 10.0, max_retries: int = 3) -> None:
        """
        批量执行SQL语句
        
        Args:
            db_path: 数据库文件路径
            sql: SQL语句
            params_list: 参数列表
            timeout: 超时时间
            max_retries: 最大重试次数
        """
        if not params_list:
            return
        
        for attempt in range(max_retries):
            try:
                conn = self.get_connection(db_path, timeout)
                cursor = conn.cursor()
                cursor.executemany(sql, params_list)
                conn.commit()
                return
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    self.stats["retries"] += 1
                    time.sleep(self.retry_delay * (attempt + 1))
                    
                    # 重置连接
                    if hasattr(self._thread_local, 'connections'):
                        if db_path in self._thread_local.connections:
                            try:
                                self._thread_local.connections[db_path].close()
                            except:
                                pass
                            del self._thread_local.connections[db_path]
                    continue
                else:
                    self.stats["lock_timeouts"] += 1
                    self.logger.error(f"批量SQL执行失败: {str(e)}")
                    raise
            except Exception as e:
                self.logger.error(f"批量SQL执行错误: {str(e)}")
                raise
    
    def batch_write(self, db_path: str, table_name: str, records: List[Dict[str, Any]], 
                   batch_size: int = 100, timeout: float = 10.0) -> None:
        """
        批量写入记录
        
        Args:
            db_path: 数据库文件路径
            table_name: 表名
            records: 记录列表
            batch_size: 批量大小
            timeout: 超时时间
        """
        if not records:
            return
        
        # 将记录分组为批次
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            # 构建批量插入SQL
            if batch:
                # 假设所有记录有相同的键
                sample_record = batch[0]
                columns = list(sample_record.keys())
                placeholders = ', '.join(['?' for _ in columns])
                column_names = ', '.join(columns)
                
                sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                
                # 准备参数
                params_list = []
                for record in batch:
                    params = []
                    for col in columns:
                        value = record.get(col)
                        # 处理特殊类型
                        if isinstance(value, dict) or isinstance(value, list):
                            params.append(json.dumps(value, ensure_ascii=False))
                        elif isinstance(value, datetime):
                            params.append(value.isoformat())
                        else:
                            params.append(value)
                    params_list.append(tuple(params))
                
                # 执行批量插入
                self.execute_many_with_retry(db_path, sql, params_list, timeout)
                self.stats["batch_writes"] += 1
    
    def start_batch_processor(self, db_path: str, table_name: str, 
                            flush_interval: float = 5.0, batch_size: int = 100) -> str:
        """
        启动批量处理器
        
        Args:
            db_path: 数据库文件路径
            table_name: 表名
            flush_interval: 刷新间隔（秒）
            batch_size: 批量大小
            
        Returns:
            处理器ID
        """
        processor_id = f"{db_path}:{table_name}"
        
        if processor_id in self._batch_running and self._batch_running[processor_id]:
            return processor_id
        
        # 创建队列和锁
        self._batch_queues[processor_id] = queue.Queue()
        self._batch_locks[processor_id] = threading.Lock()
        self._batch_running[processor_id] = True
        
        # 启动处理线程
        def batch_worker():
            buffer = []
            last_flush = time.time()
            
            while self._batch_running.get(processor_id, False):
                try:
                    # 非阻塞获取记录
                    try:
                        record = self._batch_queues[processor_id].get_nowait()
                        buffer.append(record)
                    except queue.Empty:
                        pass
                    
                    # 检查是否需要刷新
                    current_time = time.time()
                    if (len(buffer) >= batch_size or 
                        (current_time - last_flush >= flush_interval and buffer)):
                        
                        if buffer:
                            try:
                                self.batch_write(db_path, table_name, buffer, batch_size)
                                buffer = []
                                last_flush = current_time
                            except Exception as e:
                                self.logger.error(f"批量写入失败: {str(e)}")
                                # 保留缓冲区的记录以便重试
                        
                        self._batch_queues[processor_id].task_done()
                    
                    time.sleep(0.1)  # 避免过高的CPU使用
                    
                except Exception as e:
                    self.logger.error(f"批量处理器错误: {str(e)}")
                    time.sleep(1)
        
        thread = threading.Thread(target=batch_worker, daemon=True)
        self._batch_threads[processor_id] = thread
        thread.start()
        
        return processor_id
    
    def stop_batch_processor(self, processor_id: str):
        """停止批量处理器"""
        self._batch_running[processor_id] = False
        
        # 等待线程结束
        if processor_id in self._batch_threads:
            thread = self._batch_threads[processor_id]
            if thread.is_alive():
                thread.join(timeout=5.0)
            
            # 清空队列中的剩余记录
            if processor_id in self._batch_queues:
                try:
                    buffer = []
                    while not self._batch_queues[processor_id].empty():
                        record = self._batch_queues[processor_id].get_nowait()
                        buffer.append(record)
                    
                    # 写入剩余记录
                    if buffer:
                        db_path, table_name = processor_id.split(':')
                        self.batch_write(db_path, table_name, buffer)
                        
                except Exception as e:
                    self.logger.error(f"停止批量处理器时错误: {str(e)}")
    
    def queue_batch_record(self, processor_id: str, record: Dict[str, Any]):
        """
        将记录添加到批量队列
        
        Args:
            processor_id: 处理器ID
            record: 记录字典
        """
        if processor_id in self._batch_queues:
            self._batch_queues[processor_id].put(record)
        else:
            raise ValueError(f"处理器 {processor_id} 不存在")
    
    def close_all_connections(self):
        """关闭所有连接"""
        if hasattr(self._thread_local, 'connections'):
            for db_path, conn in self._thread_local.connections.items():
                try:
                    conn.close()
                except:
                    pass
            self._thread_local.connections = {}
        
        # 停止所有批量处理器
        for processor_id in list(self._batch_running.keys()):
            if self._batch_running[processor_id]:
                self.stop_batch_processor(processor_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "stats": self.stats,
            "batch_processors": len(self._batch_running),
            "thread_local_connections": len(getattr(self._thread_local, 'connections', {}))
        }


# 全局数据库管理器实例
db_manager = DatabaseManager()