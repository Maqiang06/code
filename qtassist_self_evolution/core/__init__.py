"""
自我进化系统核心模块

包含所有核心功能模块：
1. evolution_controller: 进化控制器 - 协调所有模块
2. usage_tracker: 使用模式跟踪器
3. demand_analyzer: 需求分析器
4. auto_optimizer: 自动优化器
5. auto_search_installer: 自动搜索安装器
6. new_function_creator: 新功能创建器
7. ml_predictor: 机器学习预测器
8. real_time_monitor: 实时监控器
9. feedback_learner: 反馈学习器
10. database_manager: 数据库管理器
"""

from .evolution_controller import EvolutionController
from .usage_tracker import UsagePatternTracker, get_global_tracker
from .demand_analyzer import DemandAnalyzer
from .auto_optimizer import AutoOptimizer
from .auto_search_installer import AutoSearchInstaller
from .new_function_creator import NewFunctionCreator
from .ml_predictor import get_ml_predictor
from .real_time_monitor import get_global_monitor
from .feedback_learner import get_global_feedback_learner
from .database_manager import DatabaseManager, db_manager

__all__ = [
    "EvolutionController",
    "UsagePatternTracker",
    "get_global_tracker",
    "DemandAnalyzer",
    "AutoOptimizer",
    "AutoSearchInstaller",
    "NewFunctionCreator",
    "get_ml_predictor",
    "get_global_monitor",
    "get_global_feedback_learner",
    "DatabaseManager",
    "db_manager",
]