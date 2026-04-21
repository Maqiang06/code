"""
量化交易助手自我进化系统 - Skill SDK
提供统一的接口来调用自我进化系统功能

安装:
    pip install qtassist-self-evolution
    
使用:
    from qtassist_self_evolution import SelfEvolutionSkill
    
    skill = SelfEvolutionSkill()
    
    # 获取系统状态
    status = skill.get_system_status()
    
    # 获取性能指标
    metrics = skill.get_performance_metrics()
    
    # 获取ML预测
    predictions = skill.get_ml_predictions()
"""

import json
import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class SelfEvolutionSkill:
    """自我进化系统Skill主类"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:5001",
        api_prefix: str = "/api",
        timeout: int = 30
    ):
        """
        初始化Skill
        
        Args:
            base_url: 服务基础URL
            api_prefix: API前缀
            timeout: 请求超时时间(秒)
        """
        self.base_url = base_url.rstrip("/")
        self.api_prefix = api_prefix
        self.timeout = timeout
        self._session = requests.Session()
        self._session.timeout = timeout
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        try:
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": f"无法连接到服务: {url}",
                "error": "connection_error"
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "请求超时",
                "error": "timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "error": "unknown"
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统运行状态
        
        Returns:
            dict: 包含is_running, current_phase, last_heartbeat等信息
        """
        return self._request("GET", "/system/status")
    
    def get_performance_metrics(
        self,
        refresh: bool = False
    ) -> Dict[str, Any]:
        """
        获取性能指标
        
        Args:
            refresh: 是否强制刷新
            
        Returns:
            dict: 包含cpu_usage, memory_usage等
        """
        return self._request(
            "GET",
            f"/monitoring/metrics?refresh={refresh}"
        )
    
    def get_performance_trend(
        self,
        minutes: int = 5
    ) -> Dict[str, Any]:
        """
        获取性能趋势
        
        Args:
            minutes: 时间范围(5/15/30/60分钟)
            
        Returns:
            dict: 包含时间序列数据
        """
        return self._request(
            "GET",
            f"/monitoring/performance-summary?minutes={minutes}"
        )
    
    def get_ml_predictions(
        self,
        prediction_type: str = "all"
    ) -> Dict[str, Any]:
        """
        获取机器学习预测
        
        Args:
            prediction_type: 预测类型(function/performance/anomaly/all)
            
        Returns:
            dict: 预测结果
        """
        return self._request(
            "GET",
            f"/ml/predictions?type={prediction_type}"
        )
    
    def get_module_status(self) -> Dict[str, Any]:
        """
        获取模块状态
        
        Returns:
            dict: 各模块状态
        """
        return self._request("GET", "/system/status")
    
    def get_alerts(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        获取系统警报
        
        Args:
            hours: 时间范围(小时)
            
        Returns:
            dict: 警报列表
        """
        return self._request(
            "GET",
            f"/monitoring/alerts?hours={hours}"
        )
    
    def start(self) -> Dict[str, Any]:
        """
        启动系统
        
        Returns:
            dict: 启动结果
        """
        return self._request("POST", "/system/control/start")
    
    def stop(self) -> Dict[str, Any]:
        """
        停止系统
        
        Returns:
            dict: 停止结果
        """
        return self._request("POST", "/system/control/stop")
    
    def is_running(self) -> bool:
        """
        检查系统是否运行
        
        Returns:
            bool: 系统运行状态
        """
        result = self.get_system_status()
        return result.get("is_running", False)
    
    def get_skill_definition(self) -> Dict[str, Any]:
        """
        获取Skill定义(用于AI集成)
        
        Returns:
            dict: OpenAI格式的tool定义
        """
        return {
            "name": "qtassist_self_evolution_system",
            "description": "量化交易助手自我进化系统",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "get_system_status",
                            "get_performance_metrics",
                            "get_performance_trend",
                            "get_ml_predictions",
                            "get_module_status",
                            "get_alerts",
                            "start",
                            "stop"
                        ],
                        "description": "要执行的操作"
                    },
                    "params": {
                        "type": "object",
                        "description": "操作参数"
                    }
                },
                "required": ["action"]
            }
        }
    
    def __repr__(self) -> str:
        return f"SelfEvolutionSkill(base_url='{self.base_url}')"


def create_skill_client(
    base_url: str = "http://localhost:5001",
    **kwargs
) -> SelfEvolutionSkill:
    """
    创建Skill客户端的便捷函数
    
    Args:
        base_url: 服务地址
        **kwargs: 其他参数
        
    Returns:
        SelfEvolutionSkill: Skill客户端实例
    """
    return SelfEvolutionSkill(base_url=base_url, **kwargs)


# Skill Actions - 用于AI对话中调用
SKILL_ACTIONS = {
    "get_system_status": {
        "description": "获取自我进化系统的运行状态",
        "parameters": {}
    },
    "get_performance_metrics": {
        "description": "获取CPU、内存、磁盘等性能指标",
        "parameters": {"refresh": "boolean"}
    },
    "get_performance_trend": {
        "description": "获取性能趋势数据用于绘图",
        "parameters": {"minutes": "5/15/30/60"}
    },
    "get_ml_predictions": {
        "description": "获取机器学习预测结果",
        "parameters": {"prediction_type": "function/performance/anomaly/all"}
    },
    "get_module_status": {
        "description": "获取各模块(使用跟踪、ML等)的状态",
        "parameters": {}
    },
    "get_alerts": {
        "description": "获取系统警报和警告",
        "parameters": {"hours": "integer"}
    },
    "start": {
        "description": "启动自我进化系统",
        "parameters": {}
    },
    "stop": {
        "description": "停止自我进化系统",
        "parameters": {}
    }
}


if __name__ == "__main__":
    # 测试
    skill = SelfEvolutionSkill()
    print(f"系统状态: {skill.get_system_status()}")
    print(f"性能指标: {skill.get_performance_metrics()}")
    print(f"ML预测: {skill.get_ml_predictions()}")