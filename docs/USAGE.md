# 使用指南

本文档详细介绍了量化交易助手自我进化系统的使用方法，包括安装、配置、命令行工具和Python API。

## 目录

1. [安装指南](#安装指南)
2. [快速开始](#快速开始)
3. [命令行工具](#命令行工具)
4. [Python API](#python-api)
5. [Web控制面板](#web控制面板)
6. [配置系统](#配置系统)
7. [数据管理](#数据管理)
8. [故障排除](#故障排除)

## 安装指南

### 系统要求

- Python 3.8 或更高版本
- 支持的操作系统: Windows 10+, macOS 10.15+, Linux (Ubuntu 18.04+, CentOS 7+)
- 磁盘空间: 至少100MB可用空间
- 内存: 至少2GB RAM

### 安装方法

#### 从PyPI安装（推荐）

```bash
# 安装核心功能（必需）
pip install qtassist-self-evolution

# 安装完整功能（包含所有可选功能）
pip install qtassist-self-evolution[all]

# 仅安装Web界面
pip install qtassist-self-evolution[web]

# 仅安装机器学习功能
pip install qtassist-self-evolution[ml]

# 安装开发版本
pip install qtassist-self-evolution[dev]
```

#### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/ptrade-code/qtassist-self-evolution.git
cd qtassist-self-evolution

# 安装依赖
pip install -r requirements.txt

# 安装包
pip install -e .

# 或安装为可编辑模式
pip install -e ".[dev,all]"
```

### 验证安装

```bash
# 检查命令行工具
qtassist-evolution --version

# 检查Python导入
python -c "import qtassist_self_evolution; print(qtassist_self_evolution.get_version())"
```

## 快速开始

### 启动Web控制面板（最简单的方式）

```bash
# 启动Web控制面板
qtassist-evolution web

# 使用自定义端口
qtassist-evolution web --port 8080

# 允许外部访问
qtassist-evolution web --host 0.0.0.0 --port 8080
```

访问 http://localhost:5001 （或你指定的端口）查看控制面板。

### 启动后台服务

```bash
# 启动后台服务（包含Web界面）
qtassist-evolution start

# 以守护进程方式运行
qtassist-evolution start --daemon

# 使用配置文件
qtassist-evolution start --config config.yaml
```

### 基本操作流程

1. **初始化系统**
   ```bash
   qtassist-evolution init
   ```

2. **启动系统**
   ```bash
   qtassist-evolution start
   ```

3. **查看状态**
   ```bash
   qtassist-evolution status
   ```

4. **使用系统** - 系统会自动开始跟踪你的操作

5. **查看进化结果**
   - 通过Web控制面板查看
   - 使用命令行查看统计数据
   ```bash
   qtassist-evolution stats
   ```

## 命令行工具

### 命令概览

```
qtassist-evolution [命令] [选项]
```

### 常用命令

#### web - 启动Web控制面板

```bash
qtassist-evolution web [选项]
```

选项:
- `--host`: 监听主机地址 (默认: 127.0.0.1)
- `--port`: 监听端口 (默认: 5001)
- `--debug`: 启用调试模式

示例:
```bash
# 启动在默认端口
qtassist-evolution web

# 启动在8080端口，允许外部访问
qtassist-evolution web --host 0.0.0.0 --port 8080

# 启用调试模式
qtassist-evolution web --debug
```

#### start - 启动后台服务

```bash
qtassist-evolution start [选项]
```

选项:
- `--config`: 配置文件路径
- `--daemon`: 以守护进程方式运行

示例:
```bash
# 启动后台服务
qtassist-evolution start

# 使用配置文件启动
qtassist-evolution start --config my_config.yaml

# 以守护进程方式运行
qtassist-evolution start --daemon
```

#### status - 查看系统状态

```bash
qtassist-evolution status
```

显示当前系统状态，包括:
- 运行时间
- CPU、内存、磁盘使用率
- 活跃警报数量
- 系统模块状态

#### stats - 查看统计数据

```bash
qtassist-evolution stats
```

显示使用统计数据，包括:
- 总使用次数
- 跟踪功能数
- 高频功能列表
- 使用时间分布

#### config - 配置管理

```bash
qtassist-evolution config [选项]
```

选项:
- `--show`: 显示当前配置
- `--set KEY VALUE`: 设置配置项

示例:
```bash
# 显示当前配置
qtassist-evolution config --show

# 设置Web界面端口
qtassist-evolution config --set webui.port 8080

# 设置数据库路径
qtassist-evolution config --set database.path data/my_evolution.db
```

#### init - 初始化系统

```bash
qtassist-evolution init [选项]
```

选项:
- `--reset`: 重置系统数据（危险！）

示例:
```bash
# 初始化系统
qtassist-evolution init

# 重置系统（清除所有数据）
qtassist-evolution init --reset
```

#### evolve - 手动触发进化

```bash
qtassist-evolution evolve [选项]
```

选项:
- `--module`: 指定进化模块 (all, optimizer, search, creator)

示例:
```bash
# 触发所有进化模块
qtassist-evolution evolve

# 仅触发自动优化
qtassist-evolution evolve --module optimizer

# 仅触发新功能创建
qtassist-evolution evolve --module creator
```

## Python API

### 基本导入

```python
# 导入整个包
import qtassist_self_evolution as qta

# 导入特定模块
from qtassist_self_evolution import EvolutionController, start_system
from qtassist_self_evolution import UsagePatternTracker, get_global_tracker
from qtassist_self_evolution import get_ml_predictor, get_global_monitor
```

### 核心类和方法

#### EvolutionController - 进化控制器

```python
# 创建控制器
controller = EvolutionController()

# 启动系统
controller.start()

# 停止系统
controller.stop()

# 获取系统状态
status = controller.get_status()

# 手动触发进化
controller.trigger_evolution()

# 获取进化报告
report = controller.get_evolution_report()
```

#### UsagePatternTracker - 使用模式跟踪器

```python
# 获取全局跟踪器实例
tracker = get_global_tracker()

# 或创建新实例
tracker = UsagePatternTracker()

# 记录使用
tracker.record_usage(
    function_name="stock_query",
    parameters={"symbol": "000001.SZ", "market": "SZ"},
    execution_time=0.25,
    success=True
)

# 获取统计数据
stats = tracker.get_statistics()

# 获取高频功能
top_functions = tracker.get_top_functions(limit=10)

# 获取使用历史
history = tracker.get_usage_history(days=7)
```

#### MLPredictor - 机器学习预测器

```python
# 获取预测器实例
predictor = get_ml_predictor()

# 预测功能使用
predictions = predictor.predict_function_usage(limit=5)

# 预测性能趋势
performance_predictions = predictor.predict_performance_trend()

# 检测异常
anomalies = predictor.detect_anomalies()

# 获取模型统计
stats = predictor.get_stats()

# 手动训练模型
predictor.train_models()
```

#### RealTimeMonitor - 实时监控器

```python
# 获取监控器实例
monitor = get_global_monitor()

# 获取当前指标
metrics = monitor.get_current_metrics()

# 获取历史数据
history = monitor.get_metric_history(
    metric_type="cpu_usage",
    time_range="1h"  # 1h, 24h, 7d, 30d
)

# 获取系统状态
system_status = monitor.get_system_status()

# 获取警报
alerts = monitor.get_active_alerts()

# 确认警报
monitor.acknowledge_alert(alert_id)
```

#### DatabaseManager - 数据库管理器

```python
from qtassist_self_evolution import db_manager

# 执行查询
results = db_manager.execute_query(
    "SELECT * FROM usage_records WHERE date >= ?",
    ("2024-01-01",)
)

# 批量插入
records = [...]
db_manager.batch_insert("usage_records", records)

# 获取数据库统计
stats = db_manager.get_stats()
```

### 完整示例

#### 示例1: 集成到现有应用

```python
import qtassist_self_evolution as qta
from datetime import datetime

class MyTradingApp:
    def __init__(self):
        # 初始化自我进化系统
        self.evolution = qta.start_system()
        
        # 获取跟踪器
        self.tracker = qta.get_global_tracker()
        
    def query_stock(self, symbol):
        """查询股票数据"""
        start_time = datetime.now()
        
        try:
            # 执行查询逻辑
            result = self._execute_query(symbol)
            
            # 记录使用
            self.tracker.record_usage(
                function_name="stock_query",
                parameters={"symbol": symbol},
                execution_time=(datetime.now() - start_time).total_seconds(),
                success=True
            )
            
            return result
            
        except Exception as e:
            # 记录失败使用
            self.tracker.record_usage(
                function_name="stock_query",
                parameters={"symbol": symbol},
                execution_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                error=str(e)
            )
            raise
    
    def get_recommendations(self):
        """获取功能推荐"""
        predictor = qta.get_ml_predictor()
        predictions = predictor.predict_function_usage(limit=3)
        
        return [
            {
                "function": pred.predicted_value,
                "confidence": pred.confidence,
                "reason": pred.explanation
            }
            for pred in predictions
        ]
    
    def _execute_query(self, symbol):
        # 实际的查询逻辑
        pass
```

#### 示例2: 自定义进化配置

```python
from qtassist_self_evolution import EvolutionController
from qtassist_self_evolution.config import get_config

# 自定义配置
custom_config = {
    "database": {
        "path": "data/my_trading.db",
        "pool_size": 10
    },
    "monitoring": {
        "collection_interval": 30,  # 每30秒收集一次
        "cpu_threshold": 75.0
    },
    "evolution": {
        "auto_optimize_enabled": True,
        "optimization_interval_hours": 12  # 每12小时优化一次
    }
}

# 使用自定义配置
controller = EvolutionController(custom_config)
controller.start()

# 或者通过配置文件
config = get_config("config/my_config.yaml")
controller2 = EvolutionController(config)
controller2.start()
```

#### 示例3: 监控和警报

```python
from qtassist_self_evolution import get_global_monitor
import time

class SystemMonitor:
    def __init__(self):
        self.monitor = get_global_monitor()
        
    def check_and_alert(self):
        """检查系统状态并触发警报"""
        status = self.monitor.get_system_status()
        
        if status.get("cpu_usage", 0) > 80:
            print(f"警告: CPU使用率过高: {status['cpu_usage']}%")
            
        if status.get("memory_usage", 0) > 85:
            print(f"警告: 内存使用率过高: {status['memory_usage']}%")
            
        # 获取活跃警报
        alerts = self.monitor.get_active_alerts()
        for alert in alerts:
            print(f"警报: {alert['message']} (严重度: {alert['severity']})")
    
    def monitor_loop(self, interval=60):
        """监控循环"""
        while True:
            self.check_and_alert()
            time.sleep(interval)

# 使用监控
monitor = SystemMonitor()
monitor.monitor_loop()
```

## Web控制面板

### 功能介绍

Web控制面板提供以下功能:

1. **系统概览**
   - 实时系统状态（CPU、内存、磁盘）
   - 运行时间统计
   - 活跃警报显示

2. **性能监控**
   - 实时性能图表
   - 历史趋势分析
   - 资源使用详情

3. **使用分析**
   - 功能使用频率
   - 使用时间分布
   - 高频功能识别

4. **机器学习预测**
   - 功能使用预测
   - 性能趋势预测
   - 异常检测结果

5. **进化控制**
   - 启动/停止进化
   - 查看进化历史
   - 手动触发进化

6. **警报管理**
   - 查看活跃警报
   - 确认/解决警报
   - 警报历史记录

### API端点

Web控制面板提供以下REST API:

#### 系统状态
- `GET /api/status` - 获取系统状态
- `GET /api/metrics` - 获取性能指标
- `GET /api/alerts` - 获取警报列表

#### 使用数据
- `GET /api/usage/stats` - 获取使用统计
- `GET /api/usage/top` - 获取高频功能
- `GET /api/usage/history` - 获取使用历史

#### 机器学习
- `GET /api/ml/predictions` - 获取预测结果
- `GET /api/ml/stats` - 获取模型统计
- `POST /api/ml/train` - 手动训练模型

#### 进化控制
- `POST /api/evolution/start` - 启动进化
- `POST /api/evolution/stop` - 停止进化
- `GET /api/evolution/report` - 获取进化报告

## 配置系统

### 配置文件格式

系统支持YAML和JSON格式的配置文件:

#### YAML格式 (推荐)

```yaml
# config.yaml
database:
  path: "data/evolution.db"
  pool_size: 5
  wal_mode: true

monitoring:
  enabled: true
  collection_interval: 60
  alert_enabled: true
  cpu_threshold: 80.0
  memory_threshold: 85.0
  disk_threshold: 90.0

ml:
  enabled: true
  prediction_enabled: true
  anomaly_detection_enabled: true
  model_save_path: "models/"
  training_interval_hours: 24

webui:
  enabled: true
  host: "127.0.0.1"
  port: 5001
  debug: false

evolution:
  auto_optimize_enabled: true
  auto_search_enabled: true
  auto_create_enabled: true
  optimization_interval_hours: 24
  search_interval_hours: 168
  creation_interval_hours: 336

log_level: "INFO"
data_dir: "data/"
logs_dir: "logs/"
```

#### JSON格式

```json
{
  "database": {
    "path": "data/evolution.db",
    "pool_size": 5,
    "wal_mode": true
  },
  "monitoring": {
    "enabled": true,
    "collection_interval": 60
  },
  "log_level": "INFO"
}
```

### 配置加载顺序

系统按以下顺序加载配置（后面的覆盖前面的）:

1. **默认配置** - 内置的合理默认值
2. **环境变量** - 通过环境变量覆盖
3. **配置文件** - 从配置文件加载
4. **运行时配置** - 通过API动态修改

### 环境变量

可以通过环境变量覆盖配置:

```bash
# 数据库配置
export EVOLUTION_DB_PATH="data/custom.db"
export EVOLUTION_DB_POOL_SIZE="10"

# Web界面配置
export EVOLUTION_WEBUI_HOST="0.0.0.0"
export EVOLUTION_WEBUI_PORT="8080"
export EVOLUTION_WEBUI_DEBUG="true"

# 监控配置
export EVOLUTION_MONITORING_ENABLED="true"
export EVOLUTION_CPU_THRESHOLD="75.0"

# 日志配置
export EVOLUTION_LOG_LEVEL="DEBUG"
export EVOLUTION_DATA_DIR="/var/lib/evolution"
```

## 数据管理

### 数据目录结构

```
data/
├── evolution.db              # SQLite数据库
├── models/                   # 机器学习模型
│   ├── function_predictor.joblib
│   ├── performance_predictor.joblib
│   └── anomaly_detector.joblib
├── feedback/                 # 反馈学习数据
│   ├── hot_patterns.json
│   ├── warm_patterns.json
│   └── cold_patterns.json
└── backups/                  # 备份数据
```

### 数据库模式

主要数据表:

1. **usage_records** - 使用记录
   - id, function_name, parameters, execution_time, success, timestamp

2. **function_stats** - 功能统计
   - function_name, usage_count, avg_time, last_used, category

3. **system_metrics** - 系统指标
   - metric_type, value, timestamp, tags

4. **evolution_tasks** - 进化任务
   - task_type, description, status, created_at, completed_at

5. **alerts** - 警报记录
   - alert_type, severity, message, acknowledged, created_at

### 数据备份

```bash
# 手动备份数据库
cp data/evolution.db data/backups/evolution_$(date +%Y%m%d).db

# 使用系统工具备份
python -m qtassist_self_evolution.tools.backup --output backup.tar.gz

# 恢复备份
python -m qtassist_self_evolution.tools.restore --input backup.tar.gz
```

### 数据清理

```bash
# 清理旧数据（保留最近30天）
python -m qtassist_self_evolution.tools.cleanup --days 30

# 清理特定类型数据
python -m qtassist_self_evolution.tools.cleanup --type metrics --days 7
```

## 故障排除

### 常见问题

#### 1. Web界面无法启动

**问题**: `qtassist-evolution web` 命令失败

**解决方案**:
```bash
# 检查Flask是否安装
pip install Flask

# 检查端口是否被占用
qtassist-evolution web --port 5002

# 检查防火墙设置
sudo ufw allow 5001/tcp  # Ubuntu
```

#### 2. 数据库锁定错误

**问题**: `sqlite3.OperationalError: database is locked`

**解决方案**:
```bash
# 停止所有相关进程
pkill -f qtassist-evolution

# 删除锁文件
rm -f data/evolution.db-* data/evolution.db-journal

# 重启服务
qtassist-evolution start
```

#### 3. 机器学习模块不可用

**问题**: 机器学习预测显示"未训练"或"不可用"

**解决方案**:
```bash
# 安装机器学习依赖
pip install numpy scikit-learn pandas joblib

# 手动训练模型
python -c "from qtassist_self_evolution import get_ml_predictor; get_ml_predictor().train_models()"

# 检查训练数据
python -c "from qtassist_self_evolution import get_global_tracker; print(get_global_tracker().get_statistics())"
```

#### 4. 性能监控数据不更新

**问题**: 系统监控显示静态数据或无数据

**解决方案**:
```bash
# 检查psutil是否安装
pip install psutil

# 重启监控服务
qtassist-evolution restart

# 检查日志
tail -f logs/evolution.log
```

### 日志文件

系统生成以下日志文件:

```
logs/
├── evolution.log          # 主日志文件
├── error.log             # 错误日志
├── access.log            # Web访问日志
└── ml_training.log       # 机器学习训练日志
```

查看日志:
```bash
# 查看实时日志
tail -f logs/evolution.log

# 查看错误日志
cat logs/error.log

# 按时间筛选日志
grep "ERROR" logs/evolution.log
```

### 调试模式

启用调试模式获取更多信息:

```bash
# 命令行调试
qtassist-evolution web --debug

# 环境变量调试
export EVOLUTION_LOG_LEVEL="DEBUG"
qtassist-evolution start

# Python脚本调试
import logging
logging.basicConfig(level=logging.DEBUG)
from qtassist_self_evolution import start_system
start_system()
```

### 获取帮助

```bash
# 查看命令行帮助
qtassist-evolution --help
qtassist-evolution web --help
qtassist-evolution start --help

# 查看版本信息
qtassist-evolution --version

# 查看系统信息
python -c "import qtassist_self_evolution; print(qtassist_self_evolution.get_version())"
```

### 联系支持

如果问题无法解决:

1. 查看GitHub Issues: https://github.com/ptrade-code/qtassist-self-evolution/issues
2. 提交新Issue，包含:
   - 错误日志
   - 系统信息
   - 复现步骤
   - 预期行为

---

**提示**: 本指南基于版本1.0.0编写，具体功能可能随版本更新而变化。请查阅对应版本的文档获取最新信息。