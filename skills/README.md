# 量化交易助手自我进化系统 - Universal Skill

这是一个通用 Skill 包，可以让 Claude Code、Hermes Agent、OpenCLAW 等AI智能体调用**量化交易助手自我进化系统**的功能。

## 支持的平台

- ✅ **Claude Code** - Anthropic AI 开发工具
- ✅ **Hermes Agent** - Mistral AI 智能体框架
- ✅ **OpenCLAW** - 开放智能体平台
- ✅ **Ollama** - 本地LLM运行
- ✅ **LM Studio** - 本地模型运行
- ✅ **任何支持 OpenAI Tool Calling 的系统**

## 安装

### 作为Python包安装
```bash
pip install qtassist-self-evolution
```

### 单独安装 Skill 文件
```bash
# 克隆仓库
git clone https://github.com/Maqiang06/code.git
cd code/skills
```

## 使用方法

### 1. 通过 Python SDK

```python
from qtassist_self_evolution.skills import SelfEvolutionSkill

# 创建 Skill 客户端
skill = SelfEvolutionSkill(base_url="http://localhost:5001")

# 获取系统状态
status = skill.get_system_status()
print(status)

# 获取性能指标
metrics = skill.get_performance_metrics()

# 获取 ML 预测
predictions = skill.get_ml_predictions()
```

### 2. 通过 MCP 服务器

```bash
# 启动 MCP 服务器
python -m qtassist_self_evolution.skills.mcp_server --url http://localhost:5001

# 在 Claude Code 中使用
# /skill qtassist_self_evolution
```

### 3. 直接使用 JSON 定义

```python
import json
from qtassist_self_evolution.skills import SKILL_DEFINITION

# 获取 OpenAI 格式的工具定义
tools = SKILL_DEFINITION["tools"]

# 在 AI 对话中调用
# response = openai.ChatCompletion.create(
#     messages=[...],
#     tools=tools
# )
```

## Skill 工具列表

| 工具名称 | 功能描述 |
|---------|---------|
| `get_system_status` | 获取系统运行状态 |
| `get_performance_metrics` | 获取性能指标 (CPU、内存等) |
| `get_performance_trend` | 获取性能趋势数据 |
| `get_ml_predictions` | 获取机器学习预测 |
| `get_module_status` | 获取模块状态 |
| `get_alerts` | 获取系统警报 |
| `start_evolution_system` | 启动系统 |
| `stop_evolution_system` | 停止系统 |
| `get_usage_patterns` | 获取使用模式分析 |
| `get_function_predictions` | 预测下一步功能 |

## 配置

### Claude Code

在 `~/.claude/settings.json` 中添加：

```json
{
  "skills": {
    "qtassist-self-evolution": {
      "url": "http://localhost:5001",
      "enabled": true
    }
  }
}
```

### Hermes Agent

```yaml
# hermes_config.yaml
skills:
  - name: qtassist-self-evolution
    type: mcp
    server: python
    command: python -m qtassist_self_evolution.skills.mcp_server
```

### OpenCLAW

在 `openclaw.json` 中配置：

```json
{
  "skills": [
    {
      "name": "qtassist-self-evolution",
      "type": "http",
      "base_url": "http://localhost:5001/api"
    }
  ]
}
```

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/system/status` | GET | 获取系统状态 |
| `/api/system/control/start` | POST | 启动系统 |
| `/api/system/control/stop` | POST | 停止系统 |
| `/api/monitoring/metrics` | GET | 获取性能指标 |
| `/api/monitoring/performance-summary` | GET | 获取性能趋势 |
| `/api/monitoring/alerts` | GET | 获取警报 |
| `/api/ml/predictions` | GET | 获取 ML 预测 |
| `/api/ml/function-predictions` | GET | 功能预测 |

## 要求

- Python 3.8+
- 自我进化系统服务运行中 (默认: http://localhost:5001)

## 许可证

MIT License