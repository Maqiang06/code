"""
量化交易助手自我进化系统 - MCP服务器适配器
支持 Claude Code, OpenCLAW, Hermes Agent 等通过 MCP 协议调用

MCP (Model Context Protocol) 是一个让AI模型调用外部工具的标准协议
"""

import json
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class ToolCall:
    """工具调用请求"""
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """工具调用结果"""
    content: List[Dict[str, Any]]
    isError: bool = False


class SelfEvolutionMCPServer:
    """自我进化系统 MCP 服务器"""
    
    # 工具定义
    TOOLS = [
        ToolDefinition(
            name="get_system_status",
            description="获取量化交易助手自我进化系统的运行状态，包括各模块是否正常工作、系统阶段等。",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ),
        ToolDefinition(
            name="get_performance_metrics",
            description="获取系统性能指标，包括CPU使用率、内存使用率、磁盘使用率、函数执行时间等实时数据。",
            input_schema={
                "type": "object",
                "properties": {
                    "refresh": {
                        "type": "boolean",
                        "description": "是否强制刷新数据",
                        "default": False
                    }
                }
            }
        ),
        ToolDefinition(
            name="get_performance_trend",
            description="获取性能趋势数据，用于在图表中绘制性能变化曲线。",
            input_schema={
                "type": "object",
                "properties": {
                    "minutes": {
                        "type": "integer",
                        "description": "时间范围(分钟)",
                        "default": 5,
                        "enum": [5, 15, 30, 60]
                    }
                },
                "required": ["minutes"]
            }
        ),
        ToolDefinition(
            name="get_ml_predictions",
            description="获取机器学习预测结果，包括功能预测、性能预测和异常检测。",
            input_schema={
                "type": "object",
                "properties": {
                    "prediction_type": {
                        "type": "string",
                        "description": "预测类型",
                        "default": "all",
                        "enum": ["function", "performance", "anomaly", "all"]
                    }
                }
            }
        ),
        ToolDefinition(
            name="get_module_status",
            description="获取各功能模块的状态，包括使用跟踪、需求分析、自动优化等模块。",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ),
        ToolDefinition(
            name="get_alerts",
            description="获取系统警报，包括错误、警告和信息性消息。",
            input_schema={
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "integer",
                        "description": "时间范围(小时)",
                        "default": 24
                    }
                }
            }
        ),
        ToolDefinition(
            name="start_evolution_system",
            description="启动自我进化系统，开始自动化分析和优化流程。",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ),
        ToolDefinition(
            name="stop_evolution_system",
            description="停止自我进化系统。",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ),
        ToolDefinition(
            name="get_usage_patterns",
            description="获取使用模式分析，了解用户使用系统的习惯和趋势。",
            input_schema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "分析天数",
                        "default": 7
                    }
                }
            }
        ),
        ToolDefinition(
            name="get_function_predictions",
            description="预测用户下一步可能使用的功能，基于历史使用模式。",
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制",
                        "default": 5
                    }
                }
            }
        )
    ]
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        """初始化MCP服务器"""
        self.base_url = base_url.rstrip("/")
        self.api_prefix = "/api"
        self._session = None
        logger.info(f"MCP服务器初始化完成: {base_url}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发送HTTP请求"""
        import requests
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": f"无法连接到服务: {url}",
                "is_running": False
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def list_tools(self) -> List[ToolDefinition]:
        """列出所有可用工具"""
        return self.TOOLS
    
    def call_tool(self, tool_call: ToolCall) -> ToolResult:
        """调用工具"""
        try:
            # 根据工具名称调用对应的API
            if tool_call.name == "get_system_status":
                data = self._make_request("GET", "/system/status")
            elif tool_call.name == "get_performance_metrics":
                refresh = tool_call.arguments.get("refresh", False)
                data = self._make_request("GET", f"/monitoring/metrics?refresh={refresh}")
            elif tool_call.name == "get_performance_trend":
                minutes = tool_call.arguments.get("minutes", 5)
                data = self._make_request("GET", f"/monitoring/performance-summary?minutes={minutes}")
            elif tool_call.name == "get_ml_predictions":
                ptype = tool_call.arguments.get("prediction_type", "all")
                data = self._make_request("GET", f"/ml/predictions?type={ptype}")
            elif tool_call.name == "get_module_status":
                data = self._make_request("GET", "/system/status")
            elif tool_call.name == "get_alerts":
                hours = tool_call.arguments.get("hours", 24)
                data = self._make_request("GET", f"/monitoring/alerts?hours={hours}")
            elif tool_call.name == "start_evolution_system":
                data = self._make_request("POST", "/system/control/start")
            elif tool_call.name == "stop_evolution_system":
                data = self._make_request("POST", "/system/control/stop")
            elif tool_call.name == "get_usage_patterns":
                days = tool_call.arguments.get("days", 7)
                data = self._make_request("GET", f"/evolution/usage-patterns?days={days}")
            elif tool_call.name == "get_function_predictions":
                limit = tool_call.arguments.get("limit", 5)
                data = self._make_request("GET", f"/ml/function-predictions?limit={limit}")
            else:
                return ToolResult(
                    content=[{"type": "text", "text": f"未知工具: {tool_call.name}"}],
                    isError=True
                )
            
            return ToolResult(
                content=[{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}]
            )
        except Exception as e:
            logger.error(f"工具调用失败: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"错误: {str(e)}"}],
                isError=True
            )
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """获取OpenAI格式的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            }
            for tool in self.TOOLS
        ]
    
    def start_server(self):
        """启动MCP服务器"""
        logger.info("MCP服务器已启动，等待工具调用...")
        # 注意：实际的MCP协议需要使用stdio或HTTP传输
        # 这里提供一个简单的stdio接口
        try:
            while True:
                line = input()
                if line.strip():
                    request = json.loads(line)
                    if request.get("method") == "tools/list":
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": {
                                "tools": [
                                    {
                                        "name": t.name,
                                        "description": t.description,
                                        "inputSchema": t.input_schema
                                    }
                                    for t in self.TOOLS
                                ]
                            }
                        }
                        print(json.dumps(response))
                    elif request.get("method") == "tools/call":
                        tool_name = request.get("params", {}).get("name")
                        tool_args = request.get("params", {}).get("arguments", {})
                        result = self.call_tool(ToolCall(name=tool_name, arguments=tool_args))
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": {
                                "content": result.content,
                                "isError": result.isError
                            }
                        }
                        print(json.dumps(response))
        except KeyboardInterrupt:
            logger.info("MCP服务器已停止")
        except Exception as e:
            logger.error(f"服务器错误: {e}")


def main():
    """主入口"""
    import argparse
    parser = argparse.ArgumentParser(description="量化交易助手自我进化系统 MCP服务器")
    parser.add_argument("--url", default="http://localhost:5001", help="服务地址")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    server = SelfEvolutionMCPServer(base_url=args.url)
    server.start_server()


if __name__ == "__main__":
    main()