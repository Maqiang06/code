"""
量化交易助手自我进化系统 - Skill 模块
提供统一的接口让AI智能体调用自我进化系统
"""

from .skill_sdk import SelfEvolutionSkill, SKILL_ACTIONS, create_skill_client

__all__ = [
    "SelfEvolutionSkill",
    "SKILL_ACTIONS",
    "create_skill_client",
]

# Skill 定义 (OpenAI 格式)
SKILL_DEFINITION = {
    "name": "qtassist_self_evolution_system",
    "description": "量化交易助手自我进化系统 - AI驱动的自动化量化交易辅助系统",
    "version": "1.0.0",
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_system_status",
                "description": "获取自我进化系统的运行状态",
                "parameters": {"type": "object", "properties": {}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_performance_metrics",
                "description": "获取CPU、内存、磁盘等性能指标",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "refresh": {"type": "boolean", "default": False}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_performance_trend",
                "description": "获取性能趋势数据",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "minutes": {"type": "integer", "enum": [5, 15, 30, 60], "default": 5}
                    },
                    "required": ["minutes"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_ml_predictions",
                "description": "获取机器学习预测结果",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prediction_type": {
                            "type": "string",
                            "enum": ["function", "performance", "anomaly", "all"],
                            "default": "all"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_module_status",
                "description": "获取各功能模块的状态",
                "parameters": {"type": "object", "properties": {}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_alerts",
                "description": "获取系统警报",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hours": {"type": "integer", "default": 24}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "start_evolution_system",
                "description": "启动自我进化系统",
                "parameters": {"type": "object", "properties": {}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "stop_evolution_system",
                "description": "停止自我进化系统",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    ]
}

__version__ = "1.0.0"