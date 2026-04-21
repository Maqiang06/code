"""
进化系统主控制器

功能：协调所有自我进化系统模块，实现系统的整体管理和控制

主要功能：
1. 系统初始化：初始化所有模块和数据库
2. 任务调度：调度定期优化、搜索安装、新功能创建等任务
3. 协调控制：协调各个模块之间的协作和数据流
4. 状态监控：监控系统运行状态和性能指标
5. 进化决策：基于用户需求和系统状态做出进化决策
6. 报告生成：生成系统进化报告和性能分析

控制流程：
1. 收集用户使用数据和需求
2. 分析当前系统状态和性能
3. 制定进化策略和优先级
4. 执行优化、搜索安装、新功能创建等任务
5. 验证进化效果和收集反馈
6. 持续改进和优化进化策略
"""

import json
import sqlite3
import time
import threading
import schedule
import os
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import logging

# 导入各个模块
from .usage_tracker import UsagePatternTracker, get_global_tracker
from .demand_analyzer import DemandAnalyzer
from .auto_optimizer import AutoOptimizer
from .auto_search_installer import AutoSearchInstaller
from .new_function_creator import NewFunctionCreator

# 导入机器学习预测器
try:
    from .ml_predictor import get_ml_predictor
    HAS_ML_PREDICTOR = True
except ImportError:
    HAS_ML_PREDICTOR = False
    get_ml_predictor = None

# 导入实时监控模块
try:
    from .real_time_monitor import get_global_monitor
    HAS_REAL_TIME_MONITOR = True
except ImportError:
    HAS_REAL_TIME_MONITOR = False
    get_global_monitor = None

# 导入反馈学习模块
try:
    from .feedback_learner import get_global_feedback_learner
    HAS_FEEDBACK_LEARNER = True
except ImportError:
    HAS_FEEDBACK_LEARNER = False
    get_global_feedback_learner = None


class EvolutionPhase(Enum):
    """进化阶段枚举"""
    INITIALIZATION = "初始化"
    MONITORING = "监控中"
    ANALYSIS = "分析中"
    PLANNING = "计划中"
    EXECUTION = "执行中"
    VALIDATION = "验证中"
    REPORTING = "报告中"
    IDLE = "空闲"


class EvolutionPriority(Enum):
    """进化优先级枚举"""
    CRITICAL = "紧急"
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"
    BACKGROUND = "后台"


@dataclass
class EvolutionTask:
    """进化任务数据类"""
    id: Optional[int] = None
    task_type: str = ""
    description: str = ""
    priority: str = EvolutionPriority.MEDIUM.value
    target_module: str = ""
    parameters: Dict[str, Any] = None
    scheduled_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    duration: float = 0.0
    status: str = "待执行"
    result: Dict[str, Any] = None
    error_message: str = ""
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.result is None:
            self.result = {}
        if self.scheduled_at is None:
            self.scheduled_at = datetime.now()


@dataclass
class EvolutionReport:
    """进化报告数据类"""
    id: Optional[int] = None
    report_type: str = ""
    title: str = ""
    content: str = ""
    generated_at: datetime = None
    time_range_start: datetime = None
    time_range_end: datetime = None
    summary: Dict[str, Any] = None
    recommendations: List[str] = None
    attachments: Dict[str, str] = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()
        if self.time_range_end is None:
            self.time_range_end = datetime.now()
        if self.time_range_start is None:
            self.time_range_start = self.time_range_end - timedelta(days=7)
        if self.summary is None:
            self.summary = {}
        if self.recommendations is None:
            self.recommendations = []
        if self.attachments is None:
            self.attachments = {}


class EvolutionController:
    """进化控制器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化进化控制器
        
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
        self.db_path = os.path.join(self.data_dir, "evolution_control.db")
        
        # 初始化数据库
        self._init_database()
        
        # 调度器
        self.scheduler = schedule.Scheduler()
        
        # 线程锁
        self.lock = threading.Lock()
        
        # 日志
        self._setup_logging()
        
        # 初始化各个模块
        self._initialize_modules()
        
        # 系统状态
        self.current_phase = EvolutionPhase.INITIALIZATION.value
        self.is_running = False
        self.last_heartbeat = datetime.now()
        
        # 任务队列
        self.task_queue = []
        self.completed_tasks = []
        
        # 启动心跳
        self._start_heartbeat()
        
        # 启动调度器线程
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("进化控制器初始化完成")
    
    def _init_database(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建进化任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evolution_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                target_module TEXT,
                parameters TEXT,
                scheduled_at DATETIME,
                started_at DATETIME,
                completed_at DATETIME,
                duration REAL,
                status TEXT NOT NULL,
                result TEXT,
                error_message TEXT
            )
        """)
        
        # 创建进化报告表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evolution_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                generated_at DATETIME,
                time_range_start DATETIME,
                time_range_end DATETIME,
                summary TEXT,
                recommendations TEXT,
                attachments TEXT
            )
        """)
        
        # 创建系统状态表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                phase TEXT NOT NULL,
                is_running INTEGER,
                active_tasks INTEGER,
                completed_tasks INTEGER,
                error_count INTEGER,
                performance_metrics TEXT
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON evolution_tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_scheduled ON evolution_tasks(scheduled_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_generated ON evolution_reports(generated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_timestamp ON system_status(timestamp)")
        
        conn.commit()
        conn.close()
    
    def _initialize_modules(self):
        """初始化各个模块"""
        try:
            self.logger = logging.getLogger(__name__)
            
            # 使用模式跟踪模块
            usage_db_path = os.path.join(self.data_dir, "usage_tracking.db")
            self.usage_tracker = UsagePatternTracker(db_path=usage_db_path)
            self.logger.info("使用模式跟踪模块初始化成功")
            import time
            time.sleep(0.2)  # 添加延迟以避免数据库锁定
            
            # 功能需求分析模块
            demand_db_path = os.path.join(self.data_dir, "demand_analysis.db")
            self.demand_analyzer = DemandAnalyzer(db_path=demand_db_path)
            self.logger.info("功能需求分析模块初始化成功")
            time.sleep(0.2)
            
            # 自动优化模块
            optimizer_db_path = os.path.join(self.data_dir, "auto_optimization.db")
            self.auto_optimizer = AutoOptimizer(db_path=optimizer_db_path)
            self.logger.info("自动优化模块初始化成功")
            time.sleep(0.2)
            
            # 自动搜索安装模块
            installer_db_path = os.path.join(self.data_dir, "auto_installation.db")
            self.auto_installer = AutoSearchInstaller(db_path=installer_db_path)
            self.logger.info("自动搜索安装模块初始化成功")
            time.sleep(0.2)
            
            # 新功能创建模块
            creator_db_path = os.path.join(self.data_dir, "function_creation.db")
            self.new_function_creator = NewFunctionCreator(db_path=creator_db_path)
            self.logger.info("新功能创建模块初始化成功")
            time.sleep(0.2)
            
            # 机器学习预测器模块
            if HAS_ML_PREDICTOR:
                model_dir = os.path.join(self.base_dir, "models")
                self.ml_predictor = get_ml_predictor(
                    db_path=usage_db_path,  # 使用使用跟踪数据库作为数据源
                    model_dir=model_dir
                )
                self.logger.info("机器学习预测器模块初始化成功")
                
                # 启动后台训练
                self.ml_predictor.start_background_training(interval_hours=24)
                self.logger.info("机器学习后台训练已启动")
            else:
                self.ml_predictor = None
                self.logger.warning("机器学习预测器不可用，将使用简化预测模式")
            
            # 实时监控模块
            if HAS_REAL_TIME_MONITOR:
                self.real_time_monitor = get_global_monitor({
                    "collection_interval": 5.0,  # 5秒收集一次
                    "retention_days": 30,
                    "alerts_enabled": True,
                    "thresholds": {
                        "cpu_usage": {"warning": 80.0, "error": 90.0},
                        "memory_usage": {"warning": 85.0, "error": 95.0},
                        "disk_usage": {"warning": 85.0, "error": 95.0},
                        "function_execution_time": {"warning": 10.0, "error": 30.0},
                        "error_rate": {"warning": 5.0, "error": 10.0},
                    }
                })
                self.logger.info("实时监控模块初始化成功")
            else:
                self.real_time_monitor = None
                self.logger.warning("实时监控模块不可用")
            
            # 反馈学习模块
            if HAS_FEEDBACK_LEARNER:
                self.feedback_learner = get_global_feedback_learner({
                    "data_dir": os.path.join(self.base_dir, "feedback_learning"),
                    "memory_limit_hot": 100,
                    "memory_limit_warm": 200,
                    "confirmation_threshold": 3,
                    "archive_days": 90,
                    "demote_days": 30,
                    "auto_maintenance": True
                })
                self.logger.info("反馈学习模块初始化成功")
                
                # 启动定期维护
                def maintenance_job():
                    try:
                        self.feedback_learner.run_maintenance()
                    except Exception as e:
                        self.logger.error(f"反馈学习维护任务失败: {str(e)}")
                
                # 每天执行一次维护
                self.scheduler.every().day.at("03:00").do(maintenance_job)
                self.logger.info("反馈学习维护任务已安排")
            else:
                self.feedback_learner = None
                self.logger.warning("反馈学习模块不可用")
            
            self.logger.info("所有模块初始化成功")
            
        except Exception as e:
            self.logger.error(f"模块初始化失败: {str(e)}")
            raise
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"evolution_controller_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _start_heartbeat(self):
        """启动心跳"""
        def heartbeat_job():
            with self.lock:
                self.last_heartbeat = datetime.now()
                # 记录系统状态
                self._record_system_status()
        
        # 每分钟执行一次心跳
        self.scheduler.every(1).minutes.do(heartbeat_job)
        self.logger.info("心跳服务已启动")
    
    def _run_scheduler(self):
        """运行调度器"""
        while True:
            try:
                self.scheduler.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"调度器运行异常: {str(e)}")
                time.sleep(10)
    
    def _record_system_status(self):
        """记录系统状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取活动任务数量
            cursor.execute("""
                SELECT COUNT(*) FROM evolution_tasks 
                WHERE status IN ('待执行', '执行中')
            """)
            active_tasks = cursor.fetchone()[0]
            
            # 获取已完成任务数量
            cursor.execute("""
                SELECT COUNT(*) FROM evolution_tasks 
                WHERE status = '已完成'
            """)
            completed_tasks = cursor.fetchone()[0]
            
            # 获取错误数量
            cursor.execute("""
                SELECT COUNT(*) FROM evolution_tasks 
                WHERE status = '失败'
            """)
            error_count = cursor.fetchone()[0]
            
            # 性能指标（简化）
            performance_metrics = {
                "memory_usage": "待实现",
                "cpu_usage": "待实现",
                "disk_usage": "待实现",
                "response_time": "待实现"
            }
            
            cursor.execute("""
                INSERT INTO system_status 
                (timestamp, phase, is_running, active_tasks, completed_tasks, error_count, performance_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                self.current_phase,
                1 if self.is_running else 0,
                active_tasks,
                completed_tasks,
                error_count,
                json.dumps(performance_metrics, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"记录系统状态失败: {str(e)}")
    
    def start(self):
        """启动进化系统"""
        if self.is_running:
            self.logger.warning("进化系统已经在运行中")
            return False
        
        try:
            self.is_running = True
            self.current_phase = EvolutionPhase.MONITORING.value
            
            # 启动定期任务
            self._setup_periodic_tasks()
            
            # 开始监控用户行为
            self._start_user_monitoring()
            
            # 启动实时监控
            if self.real_time_monitor:
                try:
                    self.real_time_monitor.start()
                    self.logger.info("实时监控启动成功")
                except Exception as e:
                    self.logger.error(f"实时监控启动失败: {str(e)}")
            
            self.logger.info("进化系统启动成功")
            return True
            
        except Exception as e:
            self.is_running = False
            self.current_phase = EvolutionPhase.IDLE.value
            self.logger.error(f"进化系统启动失败: {str(e)}")
            return False
    
    def stop(self):
        """停止进化系统"""
        if not self.is_running:
            self.logger.warning("进化系统已经停止")
            return False
        
        try:
            self.is_running = False
            self.current_phase = EvolutionPhase.IDLE.value
            
            # 停止所有调度任务
            schedule.clear()
            
            # 停止实时监控
            if self.real_time_monitor:
                try:
                    self.real_time_monitor.stop()
                    self.logger.info("实时监控停止成功")
                except Exception as e:
                    self.logger.error(f"实时监控停止失败: {str(e)}")
            
            # 等待当前任务完成
            self._wait_for_tasks()
            
            self.logger.info("进化系统停止成功")
            return True
            
        except Exception as e:
            self.logger.error(f"进化系统停止失败: {str(e)}")
            return False
    
    def _setup_periodic_tasks(self):
        """设置定期任务"""
        try:
            # 每6小时执行一次系统分析
            self.scheduler.every(6).hours.do(self.schedule_task, 
                EvolutionTask(
                    task_type="系统分析",
                    description="定期系统分析和状态评估",
                    priority=EvolutionPriority.BACKGROUND.value,
                    target_module="evolution_controller"
                )
            )
            
            # 每12小时执行一次性能优化
            self.scheduler.every(12).hours.do(self.schedule_task,
                EvolutionTask(
                    task_type="性能优化",
                    description="定期性能优化分析",
                    priority=EvolutionPriority.MEDIUM.value,
                    target_module="auto_optimizer"
                )
            )
            
            # 每天执行一次需求分析
            self.scheduler.every().day.at("02:00").do(self.schedule_task,
                EvolutionTask(
                    task_type="需求分析",
                    description="每日需求分析和趋势预测",
                    priority=EvolutionPriority.HIGH.value,
                    target_module="demand_analyzer"
                )
            )
            
            # 每周执行一次系统报告生成
            self.scheduler.every().monday.at("03:00").do(self.schedule_task,
                EvolutionTask(
                    task_type="系统报告",
                    description="每周系统进化报告",
                    priority=EvolutionPriority.MEDIUM.value,
                    target_module="evolution_controller"
                )
            )
            
            self.logger.info("定期任务设置完成")
            
        except Exception as e:
            self.logger.error(f"设置定期任务失败: {str(e)}")
    
    def _start_user_monitoring(self):
        """开始用户监控"""
        # 这里可以设置用户行为监控的初始化和启动
        # 当前版本主要依赖已有的使用模式跟踪模块
        self.logger.info("用户监控已启动")
    
    def _wait_for_tasks(self):
        """等待任务完成"""
        # 简化版本：等待5秒
        time.sleep(5)
    
    def schedule_task(self, task: EvolutionTask) -> int:
        """
        调度任务
        
        Args:
            task: 进化任务
            
        Returns:
            任务ID
        """
        try:
            with self.lock:
                # 添加到任务队列
                self.task_queue.append(task)
                
                # 保存到数据库
                task_id = self._save_task(task)
                task.id = task_id
                
                # 立即执行（如果是高优先级任务）
                if task.priority in [EvolutionPriority.CRITICAL.value, EvolutionPriority.HIGH.value]:
                    self._execute_task_async(task)
                
                self.logger.info(f"任务已调度: {task.description} (ID: {task_id})")
                return task_id
                
        except Exception as e:
            self.logger.error(f"调度任务失败: {str(e)}")
            return -1
    
    def _save_task(self, task: EvolutionTask) -> int:
        """保存任务到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO evolution_tasks 
            (task_type, description, priority, target_module, parameters,
             scheduled_at, started_at, completed_at, duration, status,
             result, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.task_type,
            task.description,
            task.priority,
            task.target_module,
            json.dumps(task.parameters, ensure_ascii=False),
            task.scheduled_at.isoformat(),
            task.started_at.isoformat() if task.started_at else None,
            task.completed_at.isoformat() if task.completed_at else None,
            task.duration,
            task.status,
            json.dumps(task.result, ensure_ascii=False),
            task.error_message
        ))
        
        task_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return task_id
    
    def _update_task_status(self, task_id: int, status: str, result: Dict[str, Any] = None, error_message: str = ""):
        """更新任务状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            update_fields = ["status = ?"]
            params = [status]
            
            if status == "执行中":
                update_fields.append("started_at = ?")
                params.append(datetime.now().isoformat())
            elif status in ["已完成", "失败"]:
                update_fields.append("completed_at = ?")
                params.append(datetime.now().isoformat())
                
                # 计算持续时间
                cursor.execute("SELECT started_at FROM evolution_tasks WHERE id = ?", (task_id,))
                started_at_str = cursor.fetchone()[0]
                if started_at_str:
                    started_at = datetime.fromisoformat(started_at_str)
                    duration = (datetime.now() - started_at).total_seconds()
                    update_fields.append("duration = ?")
                    params.append(duration)
            
            if result is not None:
                update_fields.append("result = ?")
                params.append(json.dumps(result, ensure_ascii=False))
            
            if error_message:
                update_fields.append("error_message = ?")
                params.append(error_message)
            
            params.append(task_id)
            
            update_sql = f"UPDATE evolution_tasks SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(update_sql, params)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"更新任务状态失败: {str(e)}")
    
    def _execute_task_async(self, task: EvolutionTask):
        """异步执行任务"""
        def task_runner():
            self._execute_task(task)
        
        thread = threading.Thread(target=task_runner, daemon=True)
        thread.start()
    
    def _execute_task(self, task: EvolutionTask):
        """执行任务"""
        try:
            # 更新任务状态
            self._update_task_status(task.id, "执行中")
            
            self.logger.info(f"开始执行任务: {task.description} (ID: {task.id})")
            
            # 根据任务类型执行相应的操作
            result = {}
            
            if task.task_type == "系统分析":
                result = self._execute_system_analysis()
            elif task.task_type == "性能优化":
                result = self._execute_performance_optimization()
            elif task.task_type == "需求分析":
                result = self._execute_demand_analysis()
            elif task.task_type == "系统报告":
                result = self._generate_system_report()
            elif task.task_type == "功能优化":
                result = self._execute_function_optimization(task.parameters)
            elif task.task_type == "搜索安装":
                result = self._execute_search_installation(task.parameters)
            elif task.task_type == "新功能创建":
                result = self._execute_new_function_creation(task.parameters)
            else:
                result = {"error": f"未知任务类型: {task.task_type}"}
            
            # 更新任务状态
            if "error" in result:
                self._update_task_status(task.id, "失败", result, result.get("error", ""))
                self.logger.error(f"任务执行失败: {task.description} (ID: {task.id})")
            else:
                self._update_task_status(task.id, "已完成", result)
                self.logger.info(f"任务执行完成: {task.description} (ID: {task.id})")
                
                # 从任务队列移除，添加到已完成队列
                with self.lock:
                    if task in self.task_queue:
                        self.task_queue.remove(task)
                    self.completed_tasks.append(task)
                
        except Exception as e:
            error_msg = f"任务执行异常: {str(e)}"
            self._update_task_status(task.id, "失败", {"error": error_msg}, error_msg)
            self.logger.error(error_msg)
    
    def _execute_system_analysis(self) -> Dict[str, Any]:
        """执行系统分析"""
        try:
            analysis_result = {
                "timestamp": datetime.now().isoformat(),
                "system_status": {},
                "module_status": {},
                "performance_metrics": {},
                "recommendations": []
            }
            
            # 获取系统状态
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT phase, is_running, active_tasks, completed_tasks, error_count
                FROM system_status
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            system_status = cursor.fetchone()
            
            if system_status:
                analysis_result["system_status"] = {
                    "phase": system_status[0],
                    "is_running": bool(system_status[1]),
                    "active_tasks": system_status[2],
                    "completed_tasks": system_status[3],
                    "error_count": system_status[4]
                }
            
            # 检查模块状态
            module_checks = [
                ("usage_tracker", self.usage_tracker is not None),
                ("demand_analyzer", self.demand_analyzer is not None),
                ("auto_optimizer", self.auto_optimizer is not None),
                ("auto_installer", self.auto_installer is not None),
                ("new_function_creator", self.new_function_creator is not None),
            ]
            
            for module_name, is_ready in module_checks:
                analysis_result["module_status"][module_name] = {
                    "is_ready": is_ready,
                    "status": "正常" if is_ready else "异常"
                }
            
            # 性能指标
            analysis_result["performance_metrics"] = {
                "cpu_usage": "待实现",
                "memory_usage": "待实现",
                "disk_usage": "待实现",
                "response_time": "待实现"
            }
            
            # 建议
            if system_status and system_status[4] > 10:  # 错误数量超过10
                analysis_result["recommendations"].append("系统错误数量较多，建议检查日志")
            
            conn.close()
            
            return analysis_result
            
        except Exception as e:
            return {"error": f"系统分析失败: {str(e)}"}
    
    def _execute_performance_optimization(self) -> Dict[str, Any]:
        """执行性能优化"""
        try:
            # 获取使用统计数据
            usage_stats = self._get_usage_statistics()
            
            if not usage_stats:
                return {"status": "跳过", "reason": "无使用统计数据"}
            
            # 分析性能
            metrics = self.auto_optimizer.analyze_performance(usage_stats)
            
            # 识别瓶颈
            bottlenecks = self.auto_optimizer.identify_bottlenecks(metrics)
            
            if not bottlenecks:
                return {"status": "跳过", "reason": "未发现性能瓶颈"}
            
            # 创建优化计划
            plans = self.auto_optimizer.create_optimization_plans(bottlenecks, metrics)
            
            if not plans:
                return {"status": "跳过", "reason": "无法创建优化计划"}
            
            # 执行优化（只执行第一个计划作为示例）
            plan = plans[0]
            result = self.auto_optimizer.execute_optimization(plan)
            
            optimization_result = {
                "status": "完成",
                "optimized_function": plan.target_function,
                "improvement_rate": result.improvement_rate,
                "execution_time": result.duration,
                "details": asdict(result)
            }
            
            return optimization_result
            
        except Exception as e:
            return {"error": f"性能优化失败: {str(e)}"}
    
    def _get_usage_statistics(self) -> List[Dict[str, Any]]:
        """获取使用统计数据"""
        # 简化版本：返回模拟数据
        return [
            {
                "function_name": "query_stock_price",
                "avg_execution_time": 2.5,
                "success_rate": 0.85,
                "call_count": 25,
                "last_called": datetime.now().isoformat()
            },
            {
                "function_name": "analyze_financial_data",
                "avg_execution_time": 8.2,
                "success_rate": 0.92,
                "call_count": 12,
                "last_called": datetime.now().isoformat()
            },
            {
                "function_name": "generate_report",
                "avg_execution_time": 15.7,
                "success_rate": 0.78,
                "call_count": 8,
                "last_called": datetime.now().isoformat()
            }
        ]
    
    def _execute_demand_analysis(self) -> Dict[str, Any]:
        """执行需求分析"""
        try:
            # 获取最近的用户请求（模拟）
            recent_requests = [
                "我需要查询股票实时价格",
                "能不能添加技术指标分析功能",
                "系统响应太慢了，需要优化",
                "希望集成更多的数据源",
                "需要生成PDF格式的报告"
            ]
            
            all_demands = []
            
            for request in recent_requests:
                demands = self.demand_analyzer.analyze_explicit_demand(request)
                all_demands.extend(demands)
            
            # 获取综合推荐
            recommendations = self.demand_analyzer.get_comprehensive_recommendation()
            
            analysis_result = {
                "status": "完成",
                "analyzed_requests": len(recent_requests),
                "identified_demands": len(all_demands),
                "demand_categories": {},
                "recommendations": recommendations
            }
            
            # 按类别统计需求
            for demand in all_demands:
                category = demand.demand_type
                if category not in analysis_result["demand_categories"]:
                    analysis_result["demand_categories"][category] = 0
                analysis_result["demand_categories"][category] += 1
            
            return analysis_result
            
        except Exception as e:
            return {"error": f"需求分析失败: {str(e)}"}
    
    def _execute_search_installation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行搜索安装"""
        try:
            demand_text = parameters.get("demand_text", "")
            context = parameters.get("context", {})
            
            if not demand_text:
                return {"status": "跳过", "reason": "需求文本为空"}
            
            result = self.auto_installer.process_demand(demand_text, context)
            
            return {
                "status": "完成" if result.get("success", False) else "失败",
                "demand_text": demand_text,
                "steps": result.get("steps", []),
                "installation_results": result.get("installation_results", []),
                "success": result.get("success", False)
            }
            
        except Exception as e:
            return {"error": f"搜索安装失败: {str(e)}"}
    
    def _execute_function_optimization(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行功能优化"""
        try:
            function_name = parameters.get("function_name", "")
            
            if not function_name:
                return {"status": "跳过", "reason": "函数名称为空"}
            
            # 获取函数使用统计（模拟）
            usage_stats = [
                {
                    "function_name": function_name,
                    "avg_execution_time": 3.8,
                    "success_rate": 0.88,
                    "call_count": 18,
                }
            ]
            
            # 分析性能
            metrics = self.auto_optimizer.analyze_performance(usage_stats)
            
            # 创建优化计划
            bottlenecks = self.auto_optimizer.identify_bottlenecks(metrics)
            plans = self.auto_optimizer.create_optimization_plans(bottlenecks, metrics)
            
            if not plans:
                return {"status": "跳过", "reason": "无法创建优化计划"}
            
            # 执行优化
            plan = plans[0]
            result = self.auto_optimizer.execute_optimization(plan)
            
            return {
                "status": "完成",
                "function_name": function_name,
                "optimization_plan": asdict(plan),
                "optimization_result": asdict(result)
            }
            
        except Exception as e:
            return {"error": f"功能优化失败: {str(e)}"}
    
    def _execute_new_function_creation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行新功能创建"""
        try:
            demand_text = parameters.get("demand_text", "")
            context = parameters.get("context", {})
            
            if not demand_text:
                return {"status": "跳过", "reason": "需求文本为空"}
            
            # 调用新功能创建模块
            result = self.new_function_creator.create_new_function(demand_text, context)
            
            return {
                "status": "完成" if result.get("function_created", False) else "失败",
                "demand_text": demand_text,
                "steps": result.get("steps", []),
                "function_name": result.get("function_name", ""),
                "request_id": result.get("request_id", ""),
                "success": result.get("function_created", False)
            }
            
        except Exception as e:
            return {"error": f"新功能创建失败: {str(e)}"}
    
    def _generate_system_report(self) -> Dict[str, Any]:
        """生成系统报告"""
        try:
            # 获取任务统计
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = '已完成' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN status = '失败' THEN 1 ELSE 0 END) as failed_tasks,
                    AVG(duration) as avg_duration
                FROM evolution_tasks
                WHERE scheduled_at >= datetime('now', '-7 days')
            """)
            task_stats = cursor.fetchone()
            
            # 获取系统状态趋势
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    AVG(error_count) as avg_errors,
                    AVG(active_tasks) as avg_active_tasks
                FROM system_status
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            trend_data = cursor.fetchall()
            
            conn.close()
            
            # 生成报告内容
            report_content = f"""
# 自我进化系统周报
## 报告周期: {(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')}

## 一、任务执行情况
- 总任务数: {task_stats[0] if task_stats else 0}
- 成功任务数: {task_stats[1] if task_stats else 0}
- 失败任务数: {task_stats[2] if task_stats else 0}
- 平均任务耗时: {task_stats[3] if task_stats else 0:.2f}秒

## 二、系统状态趋势
"""
            
            for row in trend_data:
                report_content += f"- {row[0]}: 平均错误数 {row[1]:.1f}, 平均活动任务数 {row[2]:.1f}\n"
            
            report_content += """
## 三、主要成就
1. 系统持续稳定运行
2. 定期性能优化执行
3. 用户需求持续分析

## 四、改进建议
1. 增加更多性能监控指标
2. 优化任务调度算法
3. 扩展新功能创建能力

## 五、下一步计划
1. 实现新功能创建模块
2. 增强系统自我修复能力
3. 优化用户交互体验
"""
            
            # 创建报告对象
            report = EvolutionReport(
                report_type="周报",
                title="自我进化系统周报",
                content=report_content,
                summary={
                    "total_tasks": task_stats[0] if task_stats else 0,
                    "completed_tasks": task_stats[1] if task_stats else 0,
                    "failed_tasks": task_stats[2] if task_stats else 0,
                    "avg_duration": task_stats[3] if task_stats else 0
                },
                recommendations=[
                    "增加性能监控指标",
                    "优化任务调度",
                    "扩展功能创建能力"
                ]
            )
            
            # 保存报告
            report_id = self._save_report(report)
            
            return {
                "status": "完成",
                "report_id": report_id,
                "report_title": report.title,
                "generated_at": report.generated_at.isoformat()
            }
            
        except Exception as e:
            return {"error": f"生成系统报告失败: {str(e)}"}
    
    def _save_report(self, report: EvolutionReport) -> int:
        """保存报告到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO evolution_reports 
            (report_type, title, content, generated_at, time_range_start,
             time_range_end, summary, recommendations, attachments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report.report_type,
            report.title,
            report.content,
            report.generated_at.isoformat(),
            report.time_range_start.isoformat(),
            report.time_range_end.isoformat(),
            json.dumps(report.summary, ensure_ascii=False),
            json.dumps(report.recommendations, ensure_ascii=False),
            json.dumps(report.attachments, ensure_ascii=False)
        ))
        
        report_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return report_id
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            with self.lock:
                status = {
                    "timestamp": datetime.now().isoformat(),
                    "is_running": self.is_running,
                    "current_phase": self.current_phase,
                    "last_heartbeat": self.last_heartbeat.isoformat(),
                    "task_queue_size": len(self.task_queue),
                    "completed_tasks_count": len(self.completed_tasks),
                    "modules_status": {
                        "usage_tracker": self.usage_tracker is not None,
                        "demand_analyzer": self.demand_analyzer is not None,
                        "auto_optimizer": self.auto_optimizer is not None,
                        "auto_installer": self.auto_installer is not None,
                        "new_function_creator": self.new_function_creator is not None,
                    }
                }
                
                # 获取数据库中的统计信息
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM evolution_tasks WHERE status = '待执行'")
                pending_tasks = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM evolution_tasks WHERE status = '执行中'")
                executing_tasks = cursor.fetchone()[0]
                
                conn.close()
                
                status["pending_tasks"] = pending_tasks
                status["executing_tasks"] = executing_tasks
                
                return status
                
        except Exception as e:
            return {"error": f"获取系统状态失败: {str(e)}"}
    
    def optimize_function(self, function_name: str, priority: str = EvolutionPriority.MEDIUM.value) -> int:
        """
        优化特定功能
        
        Args:
            function_name: 函数名称
            priority: 优先级
            
        Returns:
            任务ID
        """
        task = EvolutionTask(
            task_type="功能优化",
            description=f"优化函数: {function_name}",
            priority=priority,
            target_module="auto_optimizer",
            parameters={"function_name": function_name}
        )
        
        return self.schedule_task(task)
    
    def search_and_install(self, demand_text: str, priority: str = EvolutionPriority.MEDIUM.value) -> int:
        """
        搜索并安装所需功能
        
        Args:
            demand_text: 需求文本
            priority: 优先级
            
        Returns:
            任务ID
        """
        task = EvolutionTask(
            task_type="搜索安装",
            description=f"搜索安装: {demand_text[:50]}...",
            priority=priority,
            target_module="auto_installer",
            parameters={"demand_text": demand_text}
        )
        
        return self.schedule_task(task)
    
    def analyze_user_demand(self, demand_text: str) -> Dict[str, Any]:
        """
        分析用户需求
        
        Args:
            demand_text: 需求文本
            
        Returns:
            需求分析结果
        """
        try:
            demands = self.demand_analyzer.analyze_explicit_demand(demand_text)
            
            return {
                "status": "完成",
                "demand_text": demand_text,
                "identified_demands": [asdict(d) for d in demands],
                "recommendations": []  # 暂时返回空推荐列表
            }
            
        except Exception as e:
            return {"error": f"需求分析失败: {str(e)}"}
    
    def get_recent_reports(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近的报告"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, report_type, title, generated_at
                FROM evolution_reports
                ORDER BY generated_at DESC
                LIMIT ?
            """, (limit,))
            
            reports = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "id": row[0],
                    "report_type": row[1],
                    "title": row[2],
                    "generated_at": row[3]
                }
                for row in reports
            ]
            
        except Exception as e:
            self.logger.error(f"获取报告失败: {str(e)}")
            return []
    
    def create_new_function(self, demand_text: str, priority: str = EvolutionPriority.MEDIUM.value) -> int:
        """
        创建新功能
        
        Args:
            demand_text: 需求文本
            priority: 优先级
            
        Returns:
            任务ID
        """
        task = EvolutionTask(
            task_type="新功能创建",
            description=f"创建新功能: {demand_text[:50]}...",
            priority=priority,
            target_module="new_function_creator",
            parameters={"demand_text": demand_text}
        )
        
        return self.schedule_task(task)
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """清理旧数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            # 删除旧任务记录（保留已完成和失败的任务）
            cursor.execute("""
                DELETE FROM evolution_tasks 
                WHERE completed_at IS NOT NULL 
                AND completed_at < ?
                AND status IN ('已完成', '失败')
            """, (cutoff_date,))
            
            # 删除旧系统状态记录
            cursor.execute("""
                DELETE FROM system_status 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            deleted_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.logger.info(f"清理了 {deleted_rows} 条旧数据记录")
            return {"status": "完成", "deleted_rows": deleted_rows}
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {str(e)}")
            return {"error": f"清理失败: {str(e)}"}
    
    # ===== 机器学习预测功能 =====
    
    def predict_next_function(self, user_id: str = None, context: Dict[str, Any] = None, 
                            top_n: int = 5) -> Dict[str, Any]:
        """
        预测用户下一步可能使用的功能
        
        Args:
            user_id: 用户ID
            context: 上下文信息
            top_n: 返回前N个预测结果
            
        Returns:
            预测结果
        """
        try:
            if self.ml_predictor:
                predictions = self.ml_predictor.predict_next_function(user_id, context, top_n)
                
                # 转换为字典格式
                predictions_dict = []
                for pred in predictions:
                    pred_dict = {
                        "target": pred.target,
                        "confidence": pred.confidence,
                        "predicted_value": pred.predicted_value,
                        "explanation": pred.explanation,
                        "features": pred.features
                    }
                    predictions_dict.append(pred_dict)
                
                return {
                    "status": "成功",
                    "predictions": predictions_dict,
                    "count": len(predictions_dict),
                    "ml_used": True
                }
            else:
                # 如果机器学习预测器不可用，使用简单规则
                current_time = datetime.now()
                hour = current_time.hour
                
                # 简单的时间规则
                if 9 <= hour <= 17:
                    predictions = ["股票查询", "数据分析", "系统配置"]
                else:
                    predictions = ["系统监控", "数据备份", "系统维护"]
                
                predictions_dict = []
                for i, func in enumerate(predictions[:top_n]):
                    confidence = 0.8 - (i * 0.1)  # 递减的置信度
                    predictions_dict.append({
                        "target": func,
                        "confidence": confidence,
                        "predicted_value": func,
                        "explanation": f"基于时间模式的简单预测（当前时间: {hour}:00）",
                        "features": {"hour": hour, "rule_based": True}
                    })
                
                return {
                    "status": "成功",
                    "predictions": predictions_dict,
                    "count": len(predictions_dict),
                    "ml_used": False
                }
                
        except Exception as e:
            self.logger.error(f"预测功能使用失败: {str(e)}")
            return {"error": f"预测失败: {str(e)}"}
    
    def get_performance_prediction(self, metric_name: str = "execution_time", 
                                 lookback_days: int = 7, forecast_days: int = 3) -> Dict[str, Any]:
        """
        获取性能趋势预测
        
        Args:
            metric_name: 指标名称
            lookback_days: 回顾天数
            forecast_days: 预测天数
            
        Returns:
            性能预测结果
        """
        try:
            if self.ml_predictor:
                prediction = self.ml_predictor.predict_performance_trend(
                    metric_name, lookback_days, forecast_days
                )
                
                return {
                    "status": "成功",
                    "prediction": {
                        "target": prediction.target,
                        "confidence": prediction.confidence,
                        "predicted_value": prediction.predicted_value,
                        "explanation": prediction.explanation,
                        "features": prediction.features
                    },
                    "ml_used": True
                }
            else:
                # 简单预测
                import random
                base_value = 100.0
                trend = 1.02  # 轻微上升趋势
                predicted_value = base_value * (trend ** forecast_days)
                
                return {
                    "status": "成功",
                    "prediction": {
                        "target": metric_name,
                        "confidence": 0.6,
                        "predicted_value": predicted_value,
                        "explanation": f"基于简单趋势模型的{forecast_days}天预测",
                        "features": {
                            "lookback_days": lookback_days,
                            "forecast_days": forecast_days,
                            "method": "simple_trend"
                        }
                    },
                    "ml_used": False
                }
                
        except Exception as e:
            self.logger.error(f"性能预测失败: {str(e)}")
            return {"error": f"性能预测失败: {str(e)}"}
    
    def detect_usage_anomalies(self, lookback_days: int = 7) -> Dict[str, Any]:
        """
        检测使用模式异常
        
        Args:
            lookback_days: 回顾天数
            
        Returns:
            异常检测结果
        """
        try:
            # 获取使用数据
            recent_usage = self._get_recent_usage_data(lookback_days)
            
            if not recent_usage or len(recent_usage) < 10:
                return {
                    "status": "成功",
                    "anomalies": [],
                    "count": 0,
                    "message": "数据不足，无法进行异常检测"
                }
            
            if self.ml_predictor:
                # 准备特征
                features = ["execution_time", "hour", "weekday"]
                data_points = []
                
                for usage in recent_usage:
                    point = {
                        "execution_time": usage.get("execution_time", 0),
                        "hour": usage.get("hour", 0),
                        "weekday": usage.get("weekday", 0)
                    }
                    data_points.append(point)
                
                anomalies = self.ml_predictor.detect_anomalies(data_points, features)
                
                return {
                    "status": "成功",
                    "anomalies": anomalies,
                    "count": len(anomalies),
                    "ml_used": True
                }
            else:
                # 简单异常检测：基于执行时间的标准差
                execution_times = [u.get("execution_time", 0) for u in recent_usage]
                
                if len(execution_times) >= 5:
                    import statistics
                    mean_val = statistics.mean(execution_times)
                    stdev_val = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
                    
                    anomalies = []
                    for i, exec_time in enumerate(execution_times):
                        if stdev_val > 0 and abs(exec_time - mean_val) > 2 * stdev_val:
                            anomalies.append({
                                "index": i,
                                "execution_time": exec_time,
                                "mean": mean_val,
                                "stdev": stdev_val,
                                "z_score": (exec_time - mean_val) / stdev_val if stdev_val > 0 else 0,
                                "is_anomaly": True,
                                "detection_method": "std_dev"
                            })
                    
                    return {
                        "status": "成功",
                        "anomalies": anomalies,
                        "count": len(anomalies),
                        "ml_used": False
                    }
                else:
                    return {
                        "status": "成功",
                        "anomalies": [],
                        "count": 0,
                        "ml_used": False,
                        "message": "数据不足，无法进行异常检测"
                    }
                
        except Exception as e:
            self.logger.error(f"异常检测失败: {str(e)}")
            return {"error": f"异常检测失败: {str(e)}"}
    
    def _get_recent_usage_data(self, lookback_days: int) -> List[Dict[str, Any]]:
        """
        获取最近的使用数据
        
        Args:
            lookback_days: 回顾天数
            
        Returns:
            使用数据列表
        """
        try:
            # 这里应该从数据库获取实际数据
            # 为简化，我们返回示例数据
            import random
            from datetime import datetime, timedelta
            
            data = []
            for i in range(lookback_days * 10):  # 每天10个示例记录
                day_offset = i // 10
                hour = (i % 10) + 8  # 8:00-17:00
                weekday = (datetime.now() - timedelta(days=day_offset)).weekday()
                
                record = {
                    "execution_time": random.uniform(0.5, 5.0),
                    "hour": hour,
                    "weekday": weekday,
                    "function_name": random.choice(["股票查询", "数据分析", "系统配置", "文件操作"]),
                    "success": random.random() > 0.1  # 90%成功率
                }
                data.append(record)
            
            return data
            
        except Exception as e:
            self.logger.error(f"获取使用数据失败: {str(e)}")
            return []
    
    def get_ml_stats(self) -> Dict[str, Any]:
        """
        获取机器学习统计信息
        
        Returns:
            机器学习统计信息
        """
        try:
            if self.ml_predictor:
                stats = self.ml_predictor.get_stats()
                return {
                    "status": "成功",
                    "ml_available": True,
                    "stats": stats
                }
            else:
                return {
                    "status": "成功",
                    "ml_available": False,
                    "message": "机器学习预测器不可用"
                }
                
        except Exception as e:
            self.logger.error(f"获取机器学习统计失败: {str(e)}")
            return {"error": f"获取统计失败: {str(e)}"}
    
    # ================== 实时监控API方法 ==================
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """
        获取监控状态
        
        Returns:
            监控状态信息
        """
        try:
            if self.real_time_monitor:
                return {
                    "status": "成功",
                    "monitoring_available": True,
                    "is_running": self.real_time_monitor.is_running,
                    "collection_interval": self.real_time_monitor.collection_interval,
                    "alerts_enabled": self.real_time_monitor.alerts_enabled
                }
            else:
                return {
                    "status": "成功",
                    "monitoring_available": False,
                    "message": "实时监控模块不可用"
                }
                
        except Exception as e:
            self.logger.error(f"获取监控状态失败: {str(e)}")
            return {"error": f"获取监控状态失败: {str(e)}"}
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        获取当前指标
        
        Returns:
            当前指标数据
        """
        try:
            if self.real_time_monitor:
                metrics = self.real_time_monitor.get_current_metrics()
                return {
                    "status": "成功",
                    "metrics_available": True,
                    "data": metrics
                }
            else:
                return {
                    "status": "成功",
                    "metrics_available": False,
                    "message": "实时监控模块不可用"
                }
                
        except Exception as e:
            self.logger.error(f"获取当前指标失败: {str(e)}")
            return {"error": f"获取当前指标失败: {str(e)}"}
    
    def get_performance_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """
        获取性能总结
        
        Args:
            minutes: 时间范围（分钟）
            
        Returns:
            性能总结数据
        """
        try:
            if self.real_time_monitor:
                summary = self.real_time_monitor.get_performance_summary(minutes)
                return {
                    "status": "成功",
                    "summary_available": True,
                    "data": summary
                }
            else:
                return {
                    "status": "成功",
                    "summary_available": False,
                    "message": "实时监控模块不可用"
                }
                
        except Exception as e:
            self.logger.error(f"获取性能总结失败: {str(e)}")
            return {"error": f"获取性能总结失败: {str(e)}"}
    
    def get_alerts(self, severity: str = None, acknowledged: bool = None, 
                  hours: int = 24) -> Dict[str, Any]:
        """
        获取警报
        
        Args:
            severity: 严重级别过滤
            acknowledged: 是否已确认过滤
            hours: 时间范围（小时）
            
        Returns:
            警报数据
        """
        try:
            if self.real_time_monitor:
                alerts = self.real_time_monitor.get_alerts(severity, acknowledged, hours)
                return {
                    "status": "成功",
                    "alerts_available": True,
                    "count": len(alerts),
                    "data": alerts
                }
            else:
                return {
                    "status": "成功",
                    "alerts_available": False,
                    "message": "实时监控模块不可用"
                }
                
        except Exception as e:
            self.logger.error(f"获取警报失败: {str(e)}")
            return {"error": f"获取警报失败: {str(e)}"}
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> Dict[str, Any]:
        """
        确认警报
        
        Args:
            alert_id: 警报ID
            acknowledged_by: 确认者
            
        Returns:
            确认结果
        """
        try:
            if self.real_time_monitor:
                success = self.real_time_monitor.acknowledge_alert(alert_id, acknowledged_by)
                return {
                    "status": "成功" if success else "失败",
                    "acknowledged": success,
                    "alert_id": alert_id,
                    "acknowledged_by": acknowledged_by
                }
            else:
                return {
                    "status": "失败",
                    "message": "实时监控模块不可用",
                    "acknowledged": False
                }
                
        except Exception as e:
            self.logger.error(f"确认警报失败: {str(e)}")
            return {"error": f"确认警报失败: {str(e)}"}
    
    def track_function_execution(self, function_name: str, execution_time: float, 
                                success: bool = True, tags: Dict[str, str] = None, 
                                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        跟踪函数执行
        
        Args:
            function_name: 函数名称
            execution_time: 执行时间（秒）
            success: 是否成功
            tags: 标签
            metadata: 元数据
            
        Returns:
            跟踪结果
        """
        try:
            if self.real_time_monitor:
                self.real_time_monitor.track_function_execution(
                    function_name, execution_time, success, tags, metadata
                )
                return {
                    "status": "成功",
                    "tracked": True,
                    "function_name": function_name,
                    "execution_time": execution_time,
                    "success": success
                }
            else:
                # 如果没有监控模块，至少记录到日志
                self.logger.info(f"函数执行: {function_name}, 时间: {execution_time:.3f}秒, 成功: {success}")
                return {
                    "status": "成功",
                    "tracked": False,
                    "message": "实时监控模块不可用，已记录到日志",
                    "function_name": function_name
                }
                
        except Exception as e:
            self.logger.error(f"跟踪函数执行失败: {str(e)}")
            return {"error": f"跟踪函数执行失败: {str(e)}"}
    
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
            if self.real_time_monitor:
                report = self.real_time_monitor.get_metrics_report(metric_type, start_time, end_time)
                return {
                    "status": "成功",
                    "report_available": True,
                    "data": report
                }
            else:
                return {
                    "status": "成功",
                    "report_available": False,
                    "message": "实时监控模块不可用"
                }
                
        except Exception as e:
            self.logger.error(f"获取指标报告失败: {str(e)}")
            return {"error": f"获取指标报告失败: {str(e)}"}
    
    def record_user_feedback(self, trigger: str, context: str, incorrect: str, correct: str,
                           pattern_type: str = "general", namespace: str = "global") -> Dict[str, Any]:
        """
        记录用户反馈
        
        Args:
            trigger: 触发类型
            context: 上下文描述
            incorrect: 错误行为描述
            correct: 正确行为描述
            pattern_type: 模式类型
            namespace: 命名空间
            
        Returns:
            反馈记录结果
        """
        try:
            if self.feedback_learner:
                correction = self.feedback_learner.log_correction(
                    trigger, context, incorrect, correct, pattern_type, namespace
                )
                
                return {
                    "status": "成功",
                    "recorded": True,
                    "correction_id": correction.id,
                    "stage": correction.stage,
                    "confirmation_count": correction.confirmation_count,
                    "message": "用户反馈已记录"
                }
            else:
                return {
                    "status": "失败",
                    "recorded": False,
                    "message": "反馈学习模块不可用"
                }
                
        except Exception as e:
            self.logger.error(f"记录用户反馈失败: {str(e)}")
            return {"error": f"记录用户反馈失败: {str(e)}"}
    
    def get_learned_patterns(self, namespace: str = None, stage: str = None,
                           limit: int = 50) -> Dict[str, Any]:
        """
        获取学习到的模式
        
        Args:
            namespace: 命名空间过滤
            stage: 阶段过滤
            limit: 限制数量
            
        Returns:
            模式列表
        """
        try:
            if self.feedback_learner:
                patterns = self.feedback_learner.get_patterns(namespace, stage, limit)
                
                # 转换为字典列表
                patterns_data = []
                for pattern in patterns:
                    patterns_data.append({
                        "pattern_key": pattern.key,
                        "pattern_value": pattern.value,
                        "stage": pattern.stage,
                        "namespace": pattern.namespace,
                        "created_at": pattern.created_at,
                        "last_used": pattern.last_used,
                        "usage_count": pattern.usage_count,
                        "confirmation_count": pattern.confirmation_count
                    })
                
                return {
                    "status": "成功",
                    "patterns_available": True,
                    "patterns_count": len(patterns_data),
                    "patterns": patterns_data
                }
            else:
                return {
                    "status": "成功",
                    "patterns_available": False,
                    "message": "反馈学习模块不可用",
                    "patterns_count": 0,
                    "patterns": []
                }
                
        except Exception as e:
            self.logger.error(f"获取学习模式失败: {str(e)}")
            return {"error": f"获取学习模式失败: {str(e)}"}
    
    def confirm_pattern(self, pattern_key: str, namespace: str = "global",
                       always: bool = True, context: str = None) -> Dict[str, Any]:
        """
        确认模式
        
        Args:
            pattern_key: 模式键
            namespace: 命名空间
            always: 是否始终应用
            context: 上下文限制
            
        Returns:
            确认结果
        """
        try:
            if self.feedback_learner:
                success = self.feedback_learner.confirm_pattern(pattern_key, namespace, always, context)
                
                return {
                    "status": "成功" if success else "失败",
                    "confirmed": success,
                    "pattern_key": pattern_key,
                    "namespace": namespace,
                    "always": always,
                    "context": context,
                    "message": "模式已确认" if success else "模式确认失败"
                }
            else:
                return {
                    "status": "失败",
                    "confirmed": False,
                    "message": "反馈学习模块不可用"
                }
                
        except Exception as e:
            self.logger.error(f"确认模式失败: {str(e)}")
            return {"error": f"确认模式失败: {str(e)}"}
    
    def get_recommendations(self, context: str, namespace: str = "global") -> Dict[str, Any]:
        """
        获取推荐模式
        
        Args:
            context: 当前上下文
            namespace: 命名空间
            
        Returns:
            推荐模式列表
        """
        try:
            if self.feedback_learner:
                recommendations = self.feedback_learner.get_recommendations(context, namespace)
                
                return {
                    "status": "成功",
                    "recommendations_available": len(recommendations) > 0,
                    "recommendations_count": len(recommendations),
                    "recommendations": recommendations
                }
            else:
                # 如果没有反馈学习模块，返回基本推荐
                return {
                    "status": "成功",
                    "recommendations_available": False,
                    "recommendations_count": 0,
                    "recommendations": [],
                    "message": "反馈学习模块不可用，使用基本推荐"
                }
                
        except Exception as e:
            self.logger.error(f"获取推荐失败: {str(e)}")
            return {"error": f"获取推荐失败: {str(e)}"}
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """
        获取学习统计信息
        
        Returns:
            统计信息
        """
        try:
            if self.feedback_learner:
                stats = self.feedback_learner.get_stats()
                
                return {
                    "status": "成功",
                    "stats_available": True,
                    "stats": stats
                }
            else:
                return {
                    "status": "成功",
                    "stats_available": False,
                    "message": "反馈学习模块不可用"
                }
                
        except Exception as e:
            self.logger.error(f"获取学习统计失败: {str(e)}")
            return {"error": f"获取学习统计失败: {str(e)}"}
    
    def export_learning_memory(self, output_path: str = None) -> Dict[str, Any]:
        """
        导出学习内存
        
        Args:
            output_path: 输出路径
            
        Returns:
            导出结果
        """
        try:
            if self.feedback_learner:
                export_path = self.feedback_learner.export_memory(output_path)
                
                return {
                    "status": "成功",
                    "exported": True,
                    "export_path": export_path,
                    "message": f"学习内存已导出到: {export_path}"
                }
            else:
                return {
                    "status": "失败",
                    "exported": False,
                    "message": "反馈学习模块不可用"
                }
                
        except Exception as e:
            self.logger.error(f"导出学习内存失败: {str(e)}")
            return {"error": f"导出学习内存失败: {str(e)}"}