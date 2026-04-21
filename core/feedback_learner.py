# coding: utf-8
"""
用户反馈学习模块 - 借鉴Claude自我进化系统的核心设计理念
实现从用户交互中学习、模式确认、分层记忆存储等功能
"""

import os
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging


class LearningTrigger(Enum):
    """学习触发类型"""
    USER_CORRECTION = "user_correction"  # 用户明确纠正
    USER_PREFERENCE = "user_preference"  # 用户明确偏好
    REPEATED_PATTERN = "repeated_pattern"  # 重复模式(3次以上)
    SELF_REFLECTION = "self_reflection"  # 自我反思
    PERFORMANCE_FEEDBACK = "performance_feedback"  # 性能反馈


class PatternStage(Enum):
    """模式演进阶段"""
    TENTATIVE = "tentative"  # 单次纠正，观察重复性
    EMERGING = "emerging"  # 2次纠正，可能成为模式
    PENDING_CONFIRMATION = "pending_confirmation"  # 3次纠正，等待确认
    CONFIRMED = "confirmed"  # 用户确认，永久规则
    ARCHIVED = "archived"  # 90天未使用，归档


class NamespaceType(Enum):
    """命名空间类型"""
    GLOBAL = "global"  # 全局规则
    DOMAIN = "domain"  # 领域规则(如:量化交易、数据处理等)
    PROJECT = "project"  # 项目特定规则
    USER = "user"  # 用户特定规则


@dataclass
class Correction:
    """纠正记录"""
    id: int
    timestamp: str
    trigger: str
    context: str
    incorrect_behavior: str
    correct_behavior: str
    pattern_type: str
    namespace: str
    stage: str
    confirmation_count: int
    last_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Pattern:
    """模式记录"""
    id: int
    key: str
    value: str
    stage: str
    namespace: str
    created_at: str
    last_used: str
    usage_count: int
    confirmation_count: int
    source_correction_ids: List[int]
    metadata: Optional[Dict[str, Any]] = None


class FeedbackLearner:
    """用户反馈学习模块"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            "data_dir": "~/self_evolution_learning",
            "memory_limit_hot": 100,  # HOT层最大条目数
            "memory_limit_warm": 200,  # WARM层最大条目数
            "confirmation_threshold": 3,  # 确认阈值(3次重复)
            "archive_days": 90,  # 归档天数
            "demote_days": 30,  # 降级天数
            "auto_maintenance": True,  # 自动维护
        }
        
        # 数据目录
        self.data_dir = os.path.expanduser(self.config["data_dir"])
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 数据库路径
        self.db_path = os.path.join(self.data_dir, "feedback_learning.db")
        
        # 线程锁
        self.lock = threading.Lock()
        
        # 日志
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            log_file = os.path.join(self.data_dir, "feedback_learner.log")
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 初始化数据库
        self._init_database()
        
        # 锁
        self.lock = threading.RLock()
        
        # 内存缓存
        self.hot_memory: Dict[str, Pattern] = {}  # HOT层内存
        self.warm_memory: Dict[str, Pattern] = {}  # WARM层内存缓存
        
        self.logger.info(f"用户反馈学习模块初始化完成，数据目录: {self.data_dir}")
    
    def _init_database(self):
        """初始化数据库"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 纠正记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    trigger TEXT NOT NULL,
                    context TEXT NOT NULL,
                    incorrect_behavior TEXT NOT NULL,
                    correct_behavior TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    confirmation_count INTEGER DEFAULT 0,
                    last_used TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 模式记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_key TEXT NOT NULL,
                    pattern_value TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    confirmation_count INTEGER DEFAULT 0,
                    source_correction_ids TEXT,
                    metadata TEXT,
                    UNIQUE(pattern_key, namespace)
                )
            """)
            
            # 使用历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id INTEGER,
                    timestamp TEXT NOT NULL,
                    context TEXT,
                    result TEXT,
                    FOREIGN KEY (pattern_id) REFERENCES patterns (id)
                )
            """)
            
            # 索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_corrections_timestamp ON corrections (timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_corrections_namespace ON corrections (namespace)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_corrections_stage ON corrections (stage)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_namespace ON patterns (namespace)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_stage ON patterns (stage)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_last_used ON patterns (last_used)")
            
            conn.commit()
            conn.close()
            
            self.logger.info("数据库初始化完成")
    
    def log_correction(self, trigger: str, context: str, incorrect: str, correct: str, 
                      pattern_type: str = "general", namespace: str = "global") -> Correction:
        """
        记录用户纠正
        
        Args:
            trigger: 触发类型
            context: 上下文描述
            incorrect: 错误行为描述
            correct: 正确行为描述
            pattern_type: 模式类型
            namespace: 命名空间
            
        Returns:
            Correction: 纠正记录
        """
        with self.lock:
            timestamp = datetime.now().isoformat()
            
            # 检查是否重复纠正
            duplicate_id = self._find_duplicate_correction(incorrect, correct, namespace)
            if duplicate_id:
                # 重复纠正，增加计数
                self._increment_confirmation_count(duplicate_id)
                correction = self._get_correction(duplicate_id)
                confirmation_count = correction.confirmation_count
                
                self.logger.info(f"重复纠正记录，ID: {duplicate_id}，确认次数: {confirmation_count}")
                
                # 如果达到确认阈值，检查是否需要升级为确认模式
                if confirmation_count >= self.config["confirmation_threshold"]:
                    self._check_pattern_promotion(correction)
                
                return correction
            
            # 新纠正记录
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO corrections 
                (timestamp, trigger, context, incorrect_behavior, correct_behavior, 
                 pattern_type, namespace, stage, confirmation_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, trigger, context, incorrect, correct, pattern_type, 
                  namespace, PatternStage.TENTATIVE.value, 1))
            
            correction_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            correction = Correction(
                id=correction_id,
                timestamp=timestamp,
                trigger=trigger,
                context=context,
                incorrect_behavior=incorrect,
                correct_behavior=correct,
                pattern_type=pattern_type,
                namespace=namespace,
                stage=PatternStage.TENTATIVE.value,
                confirmation_count=1
            )
            
            self.logger.info(f"新纠正记录，ID: {correction_id}，命名空间: {namespace}")
            
            return correction
    
    def _find_duplicate_correction(self, incorrect: str, correct: str, namespace: str) -> Optional[int]:
        """查找重复纠正记录"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 简单匹配：检查是否有类似的纠正记录
            cursor.execute("""
                SELECT id FROM corrections 
                WHERE namespace = ? 
                AND incorrect_behavior LIKE ? 
                AND correct_behavior LIKE ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (namespace, f"%{incorrect}%", f"%{correct}%"))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
    
    def _increment_confirmation_count(self, correction_id: int):
        """增加确认计数"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE corrections 
                SET confirmation_count = confirmation_count + 1,
                    stage = CASE 
                        WHEN confirmation_count + 1 >= 3 THEN 'pending_confirmation'
                        WHEN confirmation_count + 1 >= 2 THEN 'emerging'
                        ELSE stage
                    END
                WHERE id = ?
            """, (correction_id,))
            
            conn.commit()
            conn.close()
    
    def _get_correction(self, correction_id: int) -> Optional[Correction]:
        """获取纠正记录"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM corrections WHERE id = ?", (correction_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return Correction(
                id=row[0],
                timestamp=row[1],
                trigger=row[2],
                context=row[3],
                incorrect_behavior=row[4],
                correct_behavior=row[5],
                pattern_type=row[6],
                namespace=row[7],
                stage=row[8],
                confirmation_count=row[9],
                last_used=row[10],
                metadata=json.loads(row[11]) if row[11] else None
            )
    
    def _check_pattern_promotion(self, correction: Correction):
        """
        检查是否将纠正升级为模式
        当纠正达到确认阈值时调用
        """
        with self.lock:
            # 检查是否已存在类似模式
            pattern_key = self._generate_pattern_key(correction)
            existing_pattern = self._get_pattern(pattern_key, correction.namespace)
            
            if existing_pattern:
                # 更新现有模式
                self._update_pattern_usage(existing_pattern.id, correction)
            else:
                # 创建新模式
                self._create_pattern_from_correction(correction)
    
    def _generate_pattern_key(self, correction: Correction) -> str:
        """生成模式键"""
        # 基于上下文和纠正类型生成唯一键
        context_hash = hash(f"{correction.context}:{correction.pattern_type}")
        return f"pattern_{abs(context_hash)}"
    
    def _get_pattern(self, pattern_key: str, namespace: str) -> Optional[Pattern]:
        """获取模式"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM patterns 
                WHERE pattern_key = ? AND namespace = ?
            """, (pattern_key, namespace))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return Pattern(
                id=row[0],
                key=row[1],
                value=row[2],
                stage=row[3],
                namespace=row[4],
                created_at=row[5],
                last_used=row[6],
                usage_count=row[7],
                confirmation_count=row[8],
                source_correction_ids=json.loads(row[9]) if row[9] else [],
                metadata=json.loads(row[10]) if row[10] else None
            )
    
    def _create_pattern_from_correction(self, correction: Correction):
        """从纠正创建模式"""
        with self.lock:
            pattern_key = self._generate_pattern_key(correction)
            timestamp = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO patterns 
                (pattern_key, pattern_value, stage, namespace, created_at, 
                 last_used, usage_count, confirmation_count, source_correction_ids)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern_key,
                correction.correct_behavior,
                PatternStage.PENDING_CONFIRMATION.value,
                correction.namespace,
                timestamp,
                timestamp,
                1,
                correction.confirmation_count,
                json.dumps([correction.id])
            ))
            
            pattern_id = cursor.lastrowid
            
            # 更新纠正记录，关联模式
            cursor.execute("""
                UPDATE corrections 
                SET stage = 'pending_confirmation',
                    metadata = ?
                WHERE id = ?
            """, (json.dumps({"pattern_id": pattern_id}), correction.id))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"创建新模式，键: {pattern_key}，命名空间: {correction.namespace}")
    
    def _update_pattern_usage(self, pattern_id: int, correction: Correction):
        """更新模式使用记录"""
        with self.lock:
            timestamp = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 更新模式使用信息
            cursor.execute("""
                UPDATE patterns 
                SET last_used = ?,
                    usage_count = usage_count + 1,
                    confirmation_count = confirmation_count + 1,
                    source_correction_ids = json_insert(
                        COALESCE(source_correction_ids, '[]'), 
                        '$[#]', 
                        ?
                    )
                WHERE id = ?
            """, (timestamp, correction.id, pattern_id))
            
            # 记录使用历史
            cursor.execute("""
                INSERT INTO usage_history (pattern_id, timestamp, context)
                VALUES (?, ?, ?)
            """, (pattern_id, timestamp, correction.context))
            
            conn.commit()
            conn.close()
    
    def confirm_pattern(self, pattern_key: str, namespace: str, always: bool = True, 
                       context: str = None) -> bool:
        """
        确认模式
        
        Args:
            pattern_key: 模式键
            namespace: 命名空间
            always: 是否始终应用
            context: 上下文限制
            
        Returns:
            bool: 是否成功
        """
        with self.lock:
            pattern = self._get_pattern(pattern_key, namespace)
            if not pattern:
                self.logger.warning(f"未找到模式: {pattern_key} ({namespace})")
                return False
            
            # 更新模式阶段
            new_stage = PatternStage.CONFIRMED.value
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE patterns 
                SET stage = ?,
                    metadata = json_insert(
                        COALESCE(metadata, '{}'), 
                        '$.confirmed_at', ?,
                        '$.confirmed_always', ?,
                        '$.confirmed_context', ?
                    )
                WHERE pattern_key = ? AND namespace = ?
            """, (new_stage, datetime.now().isoformat(), always, context, pattern_key, namespace))
            
            # 更新相关纠正记录
            if pattern.source_correction_ids:
                placeholders = ','.join(['?'] * len(pattern.source_correction_ids))
                cursor.execute(f"""
                    UPDATE corrections 
                    SET stage = 'confirmed'
                    WHERE id IN ({placeholders})
                """, tuple(pattern.source_correction_ids))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"模式确认完成: {pattern_key} ({namespace})")
            
            # 加载到HOT内存
            self._load_hot_memory()
            
            return True
    
    def get_patterns(self, namespace: str = None, stage: str = None, 
                    limit: int = 50) -> List[Pattern]:
        """
        获取模式列表
        
        Args:
            namespace: 命名空间过滤
            stage: 阶段过滤
            limit: 限制数量
            
        Returns:
            List[Pattern]: 模式列表
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM patterns WHERE 1=1"
            params = []
            
            if namespace:
                query += " AND namespace = ?"
                params.append(namespace)
            
            if stage:
                query += " AND stage = ?"
                params.append(stage)
            
            query += " ORDER BY last_used DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            patterns = []
            for row in rows:
                patterns.append(Pattern(
                    id=row[0],
                    key=row[1],
                    value=row[2],
                    stage=row[3],
                    namespace=row[4],
                    created_at=row[5],
                    last_used=row[6],
                    usage_count=row[7],
                    confirmation_count=row[8],
                    source_correction_ids=json.loads(row[9]) if row[9] else [],
                    metadata=json.loads(row[10]) if row[10] else None
                ))
            
            return patterns
    
    def get_recommendations(self, context: str, namespace: str = "global") -> List[Dict[str, Any]]:
        """
        获取推荐模式
        
        Args:
            context: 当前上下文
            namespace: 命名空间
            
        Returns:
            List[Dict[str, Any]]: 推荐模式列表
        """
        with self.lock:
            # 首先检查HOT内存
            recommendations = []
            
            # 从数据库查询相关模式
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询确认的模式
            cursor.execute("""
                SELECT pattern_key, pattern_value, stage, usage_count
                FROM patterns 
                WHERE namespace = ? 
                AND stage IN ('confirmed', 'pending_confirmation')
                ORDER BY usage_count DESC, last_used DESC
                LIMIT 10
            """, (namespace,))
            
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                pattern_key, pattern_value, stage, usage_count = row
                
                # 计算相关性分数
                relevance_score = self._calculate_relevance(pattern_value, context)
                
                if relevance_score > 0.1:  # 最小相关性阈值
                    recommendations.append({
                        "pattern_key": pattern_key,
                        "pattern_value": pattern_value,
                        "stage": stage,
                        "usage_count": usage_count,
                        "relevance_score": relevance_score,
                        "source": "learned_pattern"
                    })
            
            # 按相关性排序
            recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return recommendations
    
    def _calculate_relevance(self, pattern_value: str, context: str) -> float:
        """计算模式与上下文的相关性"""
        # 简单实现：检查关键词重叠
        pattern_words = set(pattern_value.lower().split())
        context_words = set(context.lower().split())
        
        if not pattern_words:
            return 0.0
        
        overlap = len(pattern_words.intersection(context_words))
        return overlap / len(pattern_words)
    
    def _load_hot_memory(self):
        """加载HOT层内存"""
        with self.lock:
            self.hot_memory.clear()
            
            # 加载确认的模式到HOT内存
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT pattern_key, pattern_value, namespace
                FROM patterns 
                WHERE stage = 'confirmed'
                ORDER BY usage_count DESC
                LIMIT ?
            """, (self.config["memory_limit_hot"],))
            
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                pattern_key, pattern_value, namespace = row
                full_key = f"{namespace}:{pattern_key}"
                
                # 创建简化模式对象
                pattern = Pattern(
                    id=0,
                    key=pattern_key,
                    value=pattern_value,
                    stage=PatternStage.CONFIRMED.value,
                    namespace=namespace,
                    created_at=datetime.now().isoformat(),
                    last_used=datetime.now().isoformat(),
                    usage_count=1,
                    confirmation_count=1,
                    source_correction_ids=[]
                )
                
                self.hot_memory[full_key] = pattern
            
            self.logger.info(f"HOT内存加载完成，条目数: {len(self.hot_memory)}")
    
    def run_maintenance(self):
        """运行维护任务"""
        with self.lock:
            self.logger.info("开始运行维护任务")
            
            # 归档长时间未使用的模式
            archive_date = (datetime.now() - timedelta(days=self.config["archive_days"])).isoformat()
            demote_date = (datetime.now() - timedelta(days=self.config["demote_days"])).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 归档长时间未使用的模式
            cursor.execute("""
                UPDATE patterns 
                SET stage = 'archived'
                WHERE stage = 'confirmed' 
                AND last_used < ?
            """, (archive_date,))
            
            archived_count = cursor.rowcount
            
            # 将确认模式降级为pending（如果30天未使用）
            cursor.execute("""
                UPDATE patterns 
                SET stage = 'pending_confirmation'
                WHERE stage = 'confirmed' 
                AND last_used < ?
                AND last_used >= ?
            """, (demote_date, archive_date))
            
            demoted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            # 重新加载HOT内存
            self._load_hot_memory()
            
            self.logger.info(f"维护完成: 归档{archived_count}个模式，降级{demoted_count}个模式")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 模式统计
            cursor.execute("""
                SELECT stage, COUNT(*) as count, 
                       SUM(usage_count) as total_usage
                FROM patterns 
                GROUP BY stage
            """)
            
            pattern_stats = {}
            for row in cursor.fetchall():
                stage, count, total_usage = row
                pattern_stats[stage] = {
                    "count": count,
                    "total_usage": total_usage or 0
                }
            
            # 纠正统计
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT namespace) as namespace_count,
                       SUM(confirmation_count) as total_confirmations
                FROM corrections
            """)
            
            total, namespace_count, total_confirmations = cursor.fetchone()
            
            # 近期活动
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) as recent_corrections
                FROM corrections 
                WHERE timestamp > ?
            """, (week_ago,))
            
            recent_corrections = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "pattern_stats": pattern_stats,
                "correction_stats": {
                    "total": total,
                    "namespace_count": namespace_count,
                    "total_confirmations": total_confirmations or 0,
                    "recent_corrections": recent_corrections
                },
                "memory_stats": {
                    "hot_count": len(self.hot_memory),
                    "memory_limit_hot": self.config["memory_limit_hot"],
                    "memory_limit_warm": self.config["memory_limit_warm"]
                },
                "config": self.config
            }
    
    def export_memory(self, output_path: str = None) -> str:
        """导出内存数据"""
        with self.lock:
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(self.data_dir, f"memory_export_{timestamp}.json")
            
            # 收集所有数据
            export_data = {
                "export_time": datetime.now().isoformat(),
                "stats": self.get_stats(),
                "confirmed_patterns": [],
                "corrections": []
            }
            
            # 获取确认的模式
            confirmed_patterns = self.get_patterns(stage=PatternStage.CONFIRMED.value)
            for pattern in confirmed_patterns:
                export_data["confirmed_patterns"].append(asdict(pattern))
            
            # 获取最近的纠正记录
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM corrections 
                ORDER BY timestamp DESC 
                LIMIT 100
            """)
            
            for row in cursor.fetchall():
                correction = Correction(
                    id=row[0],
                    timestamp=row[1],
                    trigger=row[2],
                    context=row[3],
                    incorrect_behavior=row[4],
                    correct_behavior=row[5],
                    pattern_type=row[6],
                    namespace=row[7],
                    stage=row[8],
                    confirmation_count=row[9],
                    last_used=row[10],
                    metadata=json.loads(row[11]) if row[11] else None
                )
                export_data["corrections"].append(asdict(correction))
            
            conn.close()
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"内存数据已导出到: {output_path}")
            
            return output_path


# 全局实例
_global_feedback_learner = None


def get_global_feedback_learner(config: Dict[str, Any] = None) -> FeedbackLearner:
    """获取全局反馈学习器实例"""
    global _global_feedback_learner
    if _global_feedback_learner is None:
        _global_feedback_learner = FeedbackLearner(config)
    return _global_feedback_learner