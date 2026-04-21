"""
量化交易助手自我进化系统 (Quantitative Trading Assistant Self-Evolution System)

一个基于机器学习的自动化量化交易系统优化平台，能够自我监控、分析和进化。

主要功能：
1. 使用模式跟踪：记录和分析用户操作模式
2. 需求分析：基于使用数据识别系统改进需求
3. 自动优化：自动优化系统配置和性能
4. 功能搜索安装：自动搜索并安装缺失功能
5. 新功能创建：基于需求自动生成新功能代码
6. 机器学习预测：预测用户行为、性能趋势和异常
7. 实时监控：监控系统资源和性能指标
8. 反馈学习：从用户反馈中学习并改进系统
9. Web控制面板：可视化监控和控制界面

版本: 1.0.0
作者: PTrade Code
许可证: MIT
"""

__version__ = "1.0.0"
__author__ = "PTrade Code"
__license__ = "MIT"

# 导出主要类和函数
from .core.evolution_controller import EvolutionController
from .core.usage_tracker import UsagePatternTracker, get_global_tracker
from .core.demand_analyzer import DemandAnalyzer
from .core.auto_optimizer import AutoOptimizer
from .core.auto_search_installer import AutoSearchInstaller
from .core.new_function_creator import NewFunctionCreator
from .core.ml_predictor import get_ml_predictor
from .core.real_time_monitor import get_global_monitor
from .core.feedback_learner import get_global_feedback_learner
from .core.database_manager import DatabaseManager, db_manager

# 简化导入
def create_controller(config=None):
    """创建进化控制器实例"""
    return EvolutionController(config)

def start_system(config=None):
    """启动自我进化系统"""
    controller = create_controller(config)
    controller.start()
    return controller

def get_version():
    """获取当前版本"""
    return __version__

__all__ = [
    "EvolutionController",
    "UsagePatternTracker",
    "DemandAnalyzer",
    "AutoOptimizer",
    "AutoSearchInstaller",
    "NewFunctionCreator",
    "get_ml_predictor",
    "get_global_monitor",
    "get_global_feedback_learner",
    "DatabaseManager",
    "db_manager",
    "create_controller",
    "start_system",
    "get_version",
]