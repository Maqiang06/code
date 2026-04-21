# 量化交易助手自我进化系统 (Quantitative Trading Assistant Self-Evolution System)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PTrade](https://img.shields.io/badge/PTrade-Compatible-green.svg)](http://dict.thinktrader.net/)
[![CI Status](https://github.com/Maqiang06/code/actions/workflows/ci.yml/badge.svg)](https://github.com/Maqiang06/code/actions/workflows/ci.yml)
[![Release Status](https://github.com/Maqiang06/code/actions/workflows/release.yml/badge.svg)](https://github.com/Maqiang06/code/actions/workflows/release.yml)
[![GitHub Release](https://img.shields.io/github/v/release/Maqiang06/code)](https://github.com/Maqiang06/code/releases)

一个基于机器学习的自动化量化交易系统优化平台，能够自我监控、分析和进化，专门为PTrade量化交易助手设计。

## 🌟 核心特性

### 1. 智能自我进化
- **使用模式跟踪**: 记录和分析用户操作模式
- **需求分析**: 基于使用数据识别系统改进需求
- **自动优化**: 自动优化系统配置和性能
- **功能搜索安装**: 自动搜索并安装缺失功能
- **新功能创建**: 基于需求自动生成新功能代码

### 2. 机器学习预测
- **功能使用预测**: 基于历史模式预测用户下一步可能使用的功能
- **性能趋势预测**: 预测系统性能瓶颈
- **异常检测**: 检测异常使用模式和系统问题
- **需求预测**: 基于用户行为预测未来需求

### 3. 实时监控系统
- **系统资源监控**: CPU、内存、磁盘、网络使用率
- **应用程序监控**: 函数执行时间、错误率、数据库性能
- **实时警报**: 基于阈值的实时性能警报
- **性能分析**: 识别性能瓶颈和优化机会

### 4. 反馈学习机制
- **用户反馈学习**: 从用户纠正中学习并改进系统
- **分层记忆存储**: HOT/WARM/COLD三层存储架构
- **模式演进**: tentative→emerging→pending→confirmed→archived
- **命名空间隔离**: 不同用户和环境的独立学习空间

### 5. 可视化控制面板
- **Web界面**: 基于Flask的响应式Web控制面板
- **实时图表**: 使用Chart.js展示性能指标
- **系统控制**: 启动/停止进化任务，配置系统参数
- **警报管理**: 查看和确认系统警报

## 🚀 快速开始

### 安装

#### 方法1: 从PyPI安装（推荐）

```bash
# 安装核心功能
pip install qtassist-self-evolution

# 安装完整功能（包括Web界面和机器学习）
pip install qtassist-self-evolution[all]

# 仅安装Web界面
pip install qtassist-self-evolution[web]

# 仅安装机器学习功能
pip install qtassist-self-evolution[ml]
```

#### 方法2: 从源码安装

```bash
# 克隆仓库
git clone https://github.com/ptrade-code/qtassist-self-evolution.git
cd qtassist-self-evolution

# 安装依赖
pip install -r requirements.txt

# 安装包
pip install -e .
```

### 基本使用

#### 启动Web控制面板

**方法1: 使用命令行工具（推荐）**

```bash
# 如果已经安装了包
qtassist-evolution web --port 5001
```

**方法2: 从源代码直接运行**

如果尚未安装包，可以直接从源代码运行：

```bash
# 使用虚拟环境的Python
python -m qtassist_self_evolution.webui.app --port 5001

# 或使用提供的启动脚本
./start_webui.sh
# 或
python start_webui.py --port 5001
```

**方法3: 手动启动**

```bash
# 激活虚拟环境（如果有）
source venv/bin/activate

# 运行Flask应用
cd qtassist_self_evolution/webui
python app.py --port 5001
```

访问 http://localhost:5001 查看控制面板。

#### 启动后台服务

```bash
qtassist-evolution start
```

#### 查看系统状态

```bash
qtassist-evolution status
```

#### 查看使用统计数据

```bash
qtassist-evolution stats
```

### 作为Python库使用

```python
from qtassist_self_evolution import EvolutionController, start_system

# 方式1: 创建控制器并手动启动
controller = EvolutionController()
controller.start()

# 方式2: 使用简化接口
controller = start_system()

# 使用跟踪功能
from qtassist_self_evolution import UsagePatternTracker
tracker = UsagePatternTracker()
tracker.record_usage("stock_query", {"symbol": "000001.SZ"})

# 获取机器学习预测
from qtassist_self_evolution import get_ml_predictor
predictor = get_ml_predictor()
predictions = predictor.predict_function_usage()
```

## 📁 项目结构

```
qtassist-self-evolution/
├── qtassist_self_evolution/     # 主包目录
│   ├── core/                    # 核心模块
│   │   ├── evolution_controller.py  # 进化控制器
│   │   ├── usage_tracker.py     # 使用模式跟踪器
│   │   ├── demand_analyzer.py   # 需求分析器
│   │   ├── auto_optimizer.py    # 自动优化器
│   │   ├── auto_search_installer.py # 自动搜索安装器
│   │   ├── new_function_creator.py  # 新功能创建器
│   │   ├── ml_predictor.py      # 机器学习预测器
│   │   ├── real_time_monitor.py # 实时监控器
│   │   ├── feedback_learner.py  # 反馈学习器
│   │   └── database_manager.py  # 数据库管理器
│   ├── webui/                   # Web界面
│   │   ├── app.py               # Flask应用
│   │   ├── static/              # 静态文件
│   │   └── templates/           # HTML模板
│   ├── cli.py                   # 命令行接口
│   ├── config.py                # 配置管理
│   └── __init__.py              # 包初始化
├── tests/                       # 测试目录
├── data/                        # 数据目录（运行时生成）
├── logs/                        # 日志目录（运行时生成）
├── pyproject.toml               # 项目配置
├── requirements.txt             # 依赖列表
├── README.md                    # 项目说明
└── LICENSE                      # MIT许可证
```

## 🔧 配置系统

### 配置文件

系统支持多种配置方式：

1. **默认配置**: 内置合理的默认值
2. **环境变量**: 通过环境变量覆盖配置
3. **配置文件**: YAML或JSON格式的配置文件
4. **运行时配置**: 通过API动态修改配置

### 配置文件示例 (config.yaml)

```yaml
database:
  path: "data/evolution.db"
  pool_size: 5
  wal_mode: true

monitoring:
  enabled: true
  collection_interval: 60
  cpu_threshold: 80.0
  memory_threshold: 85.0

ml:
  enabled: true
  prediction_enabled: true
  training_interval_hours: 24

webui:
  enabled: true
  host: "127.0.0.1"
  port: 5001

evolution:
  auto_optimize_enabled: true
  optimization_interval_hours: 24
```

### 环境变量

```bash
# 数据库配置
export EVOLUTION_DB_PATH="data/custom.db"

# Web界面配置
export EVOLUTION_WEBUI_HOST="0.0.0.0"
export EVOLUTION_WEBUI_PORT="8080"

# 日志级别
export EVOLUTION_LOG_LEVEL="DEBUG"
```

## 📊 系统架构

### 核心模块

1. **进化控制器 (EvolutionController)**
   - 协调所有模块的工作流
   - 调度定期任务
   - 管理进化决策过程

2. **使用模式跟踪器 (UsagePatternTracker)**
   - 记录用户所有交互操作
   - 统计功能使用频率
   - 识别高频使用场景

3. **需求分析器 (DemandAnalyzer)**
   - 分析使用数据识别改进需求
   - 计算需求优先级
   - 生成优化建议

4. **自动优化器 (AutoOptimizer)**
   - 自动优化系统配置
   - 性能调优
   - 资源分配优化

5. **机器学习预测器 (MLPredictor)**
   - 使用随机森林、线性回归等算法
   - 预测用户行为和系统性能
   - 异常检测和趋势分析

6. **实时监控器 (RealTimeMonitor)**
   - 系统资源监控
   - 性能指标收集
   - 实时警报系统

7. **反馈学习器 (FeedbackLearner)**
   - 从用户反馈中学习
   - 分层记忆存储
   - 模式演进和确认

### 数据流

```
用户操作 → 使用跟踪 → 需求分析 → 进化决策
    ↓          ↓           ↓          ↓
实时监控 → 性能分析 → 优化建议 → 执行进化
    ↓          ↓           ↓          ↓
机器学习 → 预测分析 → 异常检测 → 反馈学习
```

## 🧪 测试

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-cov

# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=qtassist_self_evolution tests/

# 运行特定测试模块
pytest tests/test_evolution_controller.py
```

### 测试结构

```
tests/
├── test_evolution_controller.py
├── test_usage_tracker.py
├── test_demand_analyzer.py
├── test_auto_optimizer.py
├── test_ml_predictor.py
├── test_real_time_monitor.py
└── test_feedback_learner.py
```

## 📈 性能指标

系统提供丰富的性能监控指标：

### 系统资源指标
- CPU使用率（用户、系统、空闲）
- 内存使用率（已用、可用、缓存）
- 磁盘使用率（读写速度、IOPS、空间）
- 网络指标（带宽、延迟、连接数）

### 应用程序指标
- 函数执行时间（平均值、最大值、P95、P99）
- 错误率和异常计数
- 数据库查询性能
- 并发连接数和线程数

### 业务指标
- 用户活动频率
- 功能使用分布
- 系统响应时间
- 任务完成率

## 🤝 贡献指南

我们欢迎贡献！请查看[贡献指南](CONTRIBUTING.md)了解如何参与项目开发。

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/ptrade-code/qtassist-self-evolution.git
cd qtassist-self-evolution

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev,all]"

# 运行代码检查
black qtassist_self_evolution tests/
flake8 qtassist_self_evolution tests/
mypy qtassist_self_evolution/
```

### 提交代码

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与联系

- **问题反馈**: [GitHub Issues](https://github.com/ptrade-code/qtassist-self-evolution/issues)
- **文档**: [项目Wiki](https://github.com/ptrade-code/qtassist-self-evolution/wiki)
- **邮箱**: ptrade-code@example.com

## 🙏 致谢

感谢以下开源项目的贡献：

- [Flask](https://flask.palletsprojects.com/) - Web框架
- [scikit-learn](https://scikit-learn.org/) - 机器学习库
- [psutil](https://github.com/giampaolo/psutil) - 系统监控
- [Chart.js](https://www.chartjs.org/) - 数据可视化
- [Bootstrap](https://getbootstrap.com/) - 前端框架

---

**提示**: 本系统专为PTrade量化交易助手设计，遵循PTrade API规范和要求。使用前请确保已安装PTrade交易系统并配置正确的环境。