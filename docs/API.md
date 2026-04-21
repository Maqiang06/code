# API 文档

本文档详细介绍了量化交易助手自我进化系统的所有API接口，包括Python API和REST API。

## 目录

1. [Python API 概览](#python-api-概览)
2. [核心模块 API](#核心模块-api)
   - [EvolutionController](#evolutioncontroller)
   - [UsagePatternTracker](#usagepatterntracker)
   - [DemandAnalyzer](#demandanalyzer)
   - [AutoOptimizer](#autooptimizer)
   - [AutoSearchInstaller](#autosearchinstaller)
   - [NewFunctionCreator](#newfunctioncreator)
   - [MLPredictor](#mlpredictor)
   - [RealTimeMonitor](#realtimemonitor)
   - [FeedbackLearner](#feedbacklearner)
   - [DatabaseManager](#databasemanager)
3. [配置系统 API](#配置系统-api)
4. [Web UI REST API](#web-ui-rest-api)
5. [数据模型](#数据模型)
6. [错误处理](#错误处理)

## Python API 概览

### 导入方式

```python
# 方式1: 导入整个包
import qtassist_self_evolution as qta

# 方式2: 导入特定模块
from qtassist_self_evolution import (
    EvolutionController,
    UsagePatternTracker,
    DemandAnalyzer,
    AutoOptimizer,
    AutoSearchInstaller,
    NewFunctionCreator,
    get_ml_predictor,
    get_global_monitor,
    get_global_feedback_learner,
    db_manager,
    start_system
)

# 方式3: 从子模块导入
from qtassist_self_evolution.core import EvolutionController
from qtassist_self_evolution.webui import app
from qtassist_self_evolution.config import get_config
```

### 快速开始示例

```python
import qtassist_self_evolution as qta

# 启动系统
controller = qta.start_system()

# 记录使用
tracker = qta.get_global_tracker()
tracker.record_usage("stock_query", {"symbol": "000001.SZ"})

# 获取预测
predictor = qta.get_ml_predictor()
predictions = predictor.predict_function_usage()

# 获取系统状态
monitor = qta.get_global_monitor()
status = monitor.get_system_status()
```

## 核心模块 API

### EvolutionController

进化控制器，协调所有模块的工作。

#### 类定义

```python
class EvolutionController:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化进化控制器
        
        参数:
            config: 配置字典，可选
        """
        
    def start(self) -> bool:
        """
        启动自我进化系统
        
        返回:
            bool: 启动是否成功
        """
        
    def stop(self) -> bool:
        """
        停止自我进化系统
        
        返回:
            bool: 停止是否成功
        """
        
    def get_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        返回:
            Dict[str, Any]: 状态信息，包括:
                - phase: 当前进化阶段
                - modules: 模块状态
                - tasks: 活动任务
                - metrics: 性能指标
        """
        
    def trigger_evolution(self, module: str = "all") -> bool:
        """
        手动触发进化
        
        参数:
            module: 进化模块 (all, optimizer, search, creator)
            
        返回:
            bool: 触发是否成功
        """
        
    def get_evolution_report(self, days: int = 7) -> Dict[str, Any]:
        """
        获取进化报告
        
        参数:
            days: 报告天数
            
        返回:
            Dict[str, Any]: 进化报告，包括:
                - optimizations: 优化记录
                - new_functions: 新功能创建
                - installations: 安装记录
                - performance: 性能改进
        """
        
    def add_feedback(self, 
                    pattern_type: str,
                    pattern_data: Dict[str, Any],
                    correction: Optional[Dict[str, Any]] = None) -> bool:
        """
        添加用户反馈
        
        参数:
            pattern_type: 模式类型
            pattern_data: 模式数据
            correction: 纠正信息，可选
            
        返回:
            bool: 添加是否成功
        """
```

#### 使用示例

```python
from qtassist_self_evolution import EvolutionController

# 创建控制器
controller = EvolutionController()

# 启动系统
controller.start()

# 获取状态
status = controller.get_status()
print(f"当前阶段: {status['phase']}")
print(f"活跃任务: {len(status['tasks'])}")

# 触发进化
controller.trigger_evolution("optimizer")

# 添加反馈
controller.add_feedback(
    pattern_type="function_usage",
    pattern_data={"function": "stock_query", "time": "morning"},
    correction={"correct_function": "market_analysis"}
)

# 获取报告
report = controller.get_evolution_report(30)
print(f"过去30天优化次数: {len(report['optimizations'])}")

# 停止系统
controller.stop()
```

### UsagePatternTracker

使用模式跟踪器，记录和分析用户操作。

#### 类定义

```python
class UsagePatternTracker:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化使用模式跟踪器
        """
        
    def record_usage(self,
                    function_name: str,
                    parameters: Dict[str, Any],
                    execution_time: float,
                    success: bool = True,
                    error: Optional[str] = None,
                    timestamp: Optional[datetime] = None) -> bool:
        """
        记录使用
        
        参数:
            function_name: 功能名称
            parameters: 参数字典
            execution_time: 执行时间（秒）
            success: 是否成功
            error: 错误信息，可选
            timestamp: 时间戳，可选
            
        返回:
            bool: 记录是否成功
        """
        
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取使用统计
        
        返回:
            Dict[str, Any]: 统计信息，包括:
                - total_usage_count: 总使用次数
                - tracked_functions: 跟踪功能数
                - success_rate: 成功率
                - avg_execution_time: 平均执行时间
        """
        
    def get_top_functions(self, limit: int = 10, 
                         time_range: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取高频功能
        
        参数:
            limit: 返回数量限制
            time_range: 时间范围 (24h, 7d, 30d)，可选
            
        返回:
            List[Dict[str, Any]]: 功能列表，每个元素包含:
                - function_name: 功能名称
                - usage_count: 使用次数
                - avg_time: 平均时间
                - last_used: 最后使用时间
        """
        
    def get_usage_history(self, 
                         function_name: Optional[str] = None,
                         days: int = 7) -> List[Dict[str, Any]]:
        """
        获取使用历史
        
        参数:
            function_name: 功能名称，可选（为空则返回所有）
            days: 天数
            
        返回:
            List[Dict[str, Any]]: 使用记录列表
        """
        
    def get_function_stats(self, function_name: str) -> Dict[str, Any]:
        """
        获取功能统计
        
        参数:
            function_name: 功能名称
            
        返回:
            Dict[str, Any]: 功能统计信息
        """
        
    def get_time_patterns(self) -> Dict[str, Any]:
        """
        获取时间模式
        
        返回:
            Dict[str, Any]: 时间模式信息，包括:
                - hourly_distribution: 小时分布
                - daily_distribution: 日分布
                - weekly_distribution: 周分布
        """
```

#### 使用示例

```python
from qtassist_self_evolution import get_global_tracker
from datetime import datetime

# 获取跟踪器
tracker = get_global_tracker()

# 记录使用
tracker.record_usage(
    function_name="stock_query",
    parameters={"symbol": "000001.SZ", "market": "SZ"},
    execution_time=0.25,
    success=True
)

# 获取统计
stats = tracker.get_statistics()
print(f"总使用次数: {stats['total_usage_count']}")
print(f"跟踪功能数: {stats['tracked_functions']}")

# 获取高频功能
top_functions = tracker.get_top_functions(limit=5, time_range="7d")
for i, func in enumerate(top_functions, 1):
    print(f"{i}. {func['function_name']}: {func['usage_count']}次")

# 获取使用历史
history = tracker.get_usage_history(days=3)
for record in history[:5]:
    print(f"{record['function_name']} at {record['timestamp']}")

# 获取时间模式
patterns = tracker.get_time_patterns()
print(f"最活跃时段: {patterns['hourly_distribution']}")
```

### DemandAnalyzer

需求分析器，分析使用数据识别改进需求。

#### 类定义

```python
class DemandAnalyzer:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化需求分析器
        """
        
    def analyze_demand(self, 
                      days: int = 30,
                      min_frequency: int = 5) -> List[Dict[str, Any]]:
        """
        分析需求
        
        参数:
            days: 分析天数
            min_frequency: 最小频率阈值
            
        返回:
            List[Dict[str, Any]]: 需求列表，每个元素包含:
                - type: 需求类型 (optimization, new_feature, missing)
                - function: 相关功能
                - priority: 优先级 (1-10)
                - reason: 原因描述
                - evidence: 证据数据
        """
        
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """
        获取优化建议
        
        返回:
            List[Dict[str, Any]]: 优化建议列表
        """
        
    def get_missing_features(self) -> List[Dict[str, Any]]:
        """
        获取缺失功能
        
        返回:
            List[Dict[str, Any]]: 缺失功能列表
        """
        
    def calculate_priority(self, demand: Dict[str, Any]) -> int:
        """
        计算需求优先级
        
        参数:
            demand: 需求数据
            
        返回:
            int: 优先级分数 (1-10)
        """
```

#### 使用示例

```python
from qtassist_self_evolution.core import DemandAnalyzer

# 创建分析器
analyzer = DemandAnalyzer()

# 分析需求
demands = analyzer.analyze_demand(days=30, min_frequency=3)
for demand in demands:
    print(f"需求: {demand['type']} - {demand['function']}")
    print(f"优先级: {demand['priority']}/10")
    print(f"原因: {demand['reason']}")

# 获取优化建议
suggestions = analyzer.get_optimization_suggestions()
for suggestion in suggestions:
    print(f"优化: {suggestion['function']} - {suggestion['suggestion']}")

# 获取缺失功能
missing = analyzer.get_missing_features()
for feature in missing:
    print(f"缺失功能: {feature['name']} - {feature['description']}")
```

### AutoOptimizer

自动优化器，优化系统配置和性能。

#### 类定义

```python
class AutoOptimizer:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化自动优化器
        """
        
    def optimize(self, 
                target: Optional[str] = None,
                force: bool = False) -> Dict[str, Any]:
        """
        执行优化
        
        参数:
            target: 优化目标，可选
            force: 是否强制优化
            
        返回:
            Dict[str, Any]: 优化结果，包括:
                - success: 是否成功
                - optimizations: 优化项列表
                - performance_improvement: 性能改进
                - execution_time: 执行时间
        """
        
    def get_optimization_history(self, 
                               days: int = 30) -> List[Dict[str, Any]]:
        """
        获取优化历史
        
        参数:
            days: 天数
            
        返回:
            List[Dict[str, Any]]: 优化历史记录
        """
        
    def analyze_performance(self) -> Dict[str, Any]:
        """
        分析性能
        
        返回:
            Dict[str, Any]: 性能分析结果
        """
        
    def apply_configuration(self, config: Dict[str, Any]) -> bool:
        """
        应用配置
        
        参数:
            config: 配置字典
            
        返回:
            bool: 应用是否成功
        """
```

#### 使用示例

```python
from qtassist_self_evolution.core import AutoOptimizer

# 创建优化器
optimizer = AutoOptimizer()

# 执行优化
result = optimizer.optimize(target="database")
if result["success"]:
    print(f"优化成功，性能改进: {result['performance_improvement']}%")
    for opt in result["optimizations"]:
        print(f"  - {opt['description']}")

# 获取优化历史
history = optimizer.get_optimization_history(days=7)
for record in history:
    print(f"{record['timestamp']}: {record['type']} - {record['result']}")

# 分析性能
analysis = optimizer.analyze_performance()
print(f"当前性能评分: {analysis['score']}/100")
for issue in analysis["issues"]:
    print(f"问题: {issue['description']} - 建议: {issue['suggestion']}")
```

### AutoSearchInstaller

自动搜索安装器，搜索并安装缺失功能。

#### 类定义

```python
class AutoSearchInstaller:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化自动搜索安装器
        """
        
    def search_and_install(self, 
                          requirement: Dict[str, Any],
                          auto_install: bool = True) -> Dict[str, Any]:
        """
        搜索并安装
        
        参数:
            requirement: 需求描述
            auto_install: 是否自动安装
            
        返回:
            Dict[str, Any]: 安装结果，包括:
                - success: 是否成功
                - packages: 找到的包列表
                - installed: 已安装的包
                - errors: 错误信息
        """
        
    def search_packages(self, 
                       keywords: List[str],
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索包
        
        参数:
            keywords: 关键词列表
            limit: 结果限制
            
        返回:
            List[Dict[str, Any]]: 包信息列表
        """
        
    def install_package(self, 
                       package_name: str,
                       version: Optional[str] = None) -> bool:
        """
        安装包
        
        参数:
            package_name: 包名称
            version: 版本，可选
            
        返回:
            bool: 安装是否成功
        """
        
    def get_installation_history(self) -> List[Dict[str, Any]]:
        """
        获取安装历史
        
        返回:
            List[Dict[str, Any]]: 安装历史记录
        """
```

#### 使用示例

```python
from qtassist_self_evolution.core import AutoSearchInstaller

# 创建安装器
installer = AutoSearchInstaller()

# 搜索并安装
requirement = {
    "name": "技术指标计算",
    "description": "计算MACD、RSI等技术指标",
    "keywords": ["technical", "indicator", "trading"]
}

result = installer.search_and_install(requirement)
if result["success"]:
    print("安装成功!")
    for pkg in result["installed"]:
        print(f"  - 已安装: {pkg['name']} {pkg['version']}")

# 搜索包
packages = installer.search_packages(["quantitative", "analysis"], limit=5)
for pkg in packages:
    print(f"{pkg['name']}: {pkg['description']}")

# 安装特定包
success = installer.install_package("ta-lib", "0.4.0")
if success:
    print("TA-Lib安装成功")
```

### NewFunctionCreator

新功能创建器，基于需求自动生成代码。

#### 类定义

```python
class NewFunctionCreator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化新功能创建器
        """
        
    def create_function(self, 
                       requirement: Dict[str, Any],
                       template: Optional[str] = None) -> Dict[str, Any]:
        """
        创建新功能
        
        参数:
            requirement: 功能需求
            template: 模板名称，可选
            
        返回:
            Dict[str, Any]: 创建结果，包括:
                - success: 是否成功
                - function_name: 功能名称
                - code: 生成的代码
                - test_code: 测试代码
                - documentation: 文档
        """
        
    def generate_code(self, 
                     description: str,
                     language: str = "python") -> str:
        """
        生成代码
        
        参数:
            description: 功能描述
            language: 编程语言
            
        返回:
            str: 生成的代码
        """
        
    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        验证代码
        
        参数:
            code: 代码字符串
            
        返回:
            Dict[str, Any]: 验证结果
        """
        
    def get_creation_history(self) -> List[Dict[str, Any]]:
        """
        获取创建历史
        
        返回:
            List[Dict[str, Any]]: 创建历史记录
        """
```

#### 使用示例

```python
from qtassist_self_evolution.core import NewFunctionCreator

# 创建功能创建器
creator = NewFunctionCreator()

# 创建新功能
requirement = {
    "name": "calculate_portfolio_risk",
    "description": "计算投资组合风险",
    "inputs": ["returns", "weights", "covariance_matrix"],
    "outputs": ["portfolio_variance", "portfolio_std", "var"],
    "requirements": ["numpy", "pandas"]
}

result = creator.create_function(requirement)
if result["success"]:
    print(f"功能创建成功: {result['function_name']}")
    print("生成的代码:")
    print(result["code"])
    print("\n测试代码:")
    print(result["test_code"])

# 生成代码
code = creator.generate_code(
    description="计算移动平均线",
    language="python"
)
print("生成的移动平均线代码:")
print(code)
```

### MLPredictor

机器学习预测器，提供预测性分析。

#### 类定义

```python
class MLPredictor:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化机器学习预测器
        """
        
    def predict_function_usage(self, 
                              limit: int = 5) -> List[Dict[str, Any]]:
        """
        预测功能使用
        
        参数:
            limit: 预测数量限制
            
        返回:
            List[Dict[str, Any]]: 预测结果列表，每个元素包含:
                - predicted_value: 预测功能
                - confidence: 置信度 (0-1)
                - explanation: 解释
                - features: 特征数据
        """
        
    def predict_performance_trend(self) -> Dict[str, Any]:
        """
        预测性能趋势
        
        返回:
            Dict[str, Any]: 性能趋势预测
        """
        
    def detect_anomalies(self, 
                        data: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        检测异常
        
        参数:
            data: 检测数据，可选（为空则使用历史数据）
            
        返回:
            List[Dict[str, Any]]: 异常检测结果
        """
        
    def train_models(self, 
                    force: bool = False) -> Dict[str, Any]:
        """
        训练模型
        
        参数:
            force: 是否强制训练
            
        返回:
            Dict[str, Any]: 训练结果
        """
        
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        返回:
            Dict[str, Any]: 统计信息，包括:
                - total_predictions: 总预测数
                - accuracy: 准确率
                - model_trained: 模型是否已训练
                - training_sessions: 训练次数
                - fallback_predictions: 备用预测数
        """
        
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        返回:
            Dict[str, Any]: 模型信息
        """
```

#### 使用示例

```python
from qtassist_self_evolution import get_ml_predictor

# 获取预测器
predictor = get_ml_predictor()

# 预测功能使用
predictions = predictor.predict_function_usage(limit=3)
print("功能使用预测:")
for i, pred in enumerate(predictions, 1):
    print(f"{i}. {pred['predicted_value']} ({pred['confidence']*100:.1f}%)")
    print(f"   原因: {pred['explanation']}")

# 预测性能趋势
trend = predictor.predict_performance_trend()
print(f"性能趋势: {trend['trend']}")
print(f"预测值: {trend['predicted_value']}")
print(f"置信区间: {trend['confidence_interval']}")

# 检测异常
anomalies = predictor.detect_anomalies()
if anomalies:
    print("检测到异常:")
    for anomaly in anomalies:
        print(f"  - {anomaly['description']} (分数: {anomaly['score']})")

# 训练模型
result = predictor.train_models()
if result["success"]:
    print(f"模型训练成功，耗时: {result['training_time']:.2f}秒")

# 获取统计
stats = predictor.get_stats()
print(f"总预测数: {stats['total_predictions']}")
print(f"准确率: {stats['accuracy']}")
print(f"模型状态: {'已训练' if stats['model_trained'] else '未训练'}")
```

### RealTimeMonitor

实时监控器，监控系统资源和性能。

#### 类定义

```python
class RealTimeMonitor:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化实时监控器
        """
        
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        获取当前指标
        
        返回:
            Dict[str, Any]: 当前指标，包括:
                - cpu_usage: CPU使用率
                - memory_usage: 内存使用率
                - disk_usage: 磁盘使用率
                - network_io: 网络IO
                - function_execution: 函数执行时间
                - active_alerts: 活跃警报数
        """
        
    def get_metric_history(self,
                          metric_type: str,
                          time_range: str = "1h") -> List[Dict[str, Any]]:
        """
        获取指标历史
        
        参数:
            metric_type: 指标类型
            time_range: 时间范围 (1h, 24h, 7d, 30d)
            
        返回:
            List[Dict[str, Any]]: 指标历史数据
        """
        
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        返回:
            Dict[str, Any]: 系统状态，包括:
                - overall: 整体状态 (healthy, warning, critical)
                - components: 组件状态
                - recommendations: 建议
        """
        
    def get_active_alerts(self,
                         severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取活跃警报
        
        参数:
            severity: 严重级别 (info, warning, critical)，可选
            
        返回:
            List[Dict[str, Any]]: 警报列表
        """
        
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        确认警报
        
        参数:
            alert_id: 警报ID
            
        返回:
            bool: 确认是否成功
        """
        
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        返回:
            Dict[str, Any]: 统计信息
        """
```

#### 使用示例

```python
from qtassist_self_evolution import get_global_monitor

# 获取监控器
monitor = get_global_monitor()

# 获取当前指标
metrics = monitor.get_current_metrics()
print(f"CPU使用率: {metrics['cpu_usage']['current']}%")
print(f"内存使用率: {metrics['memory_usage']['current']}%")
print(f"磁盘使用率: {metrics['disk_usage']['current']}%")

# 获取指标历史
history = monitor.get_metric_history("cpu_usage", "24h")
print(f"过去24小时CPU使用率数据点: {len(history)}")
if history:
    print(f"最高值: {max(h['value'] for h in history)}%")
    print(f"平均值: {sum(h['value'] for h in history)/len(history):.1f}%")

# 获取系统状态
status = monitor.get_system_status()
print(f"系统状态: {status['overall']}")
for component, comp_status in status['components'].items():
    print(f"  {component}: {comp_status['status']}")

# 获取警报
alerts = monitor.get_active_alerts()
if alerts:
    print("活跃警报:")
    for alert in alerts:
        print(f"  [{alert['severity']}] {alert['message']}")
        if not alert['acknowledged']:
            monitor.acknowledge_alert(alert['id'])
            print(f"    警报已确认")
```

### FeedbackLearner

反馈学习器，从用户反馈中学习。

#### 类定义

```python
class FeedbackLearner:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化反馈学习器
        """
        
    def add_feedback(self,
                    pattern_type: str,
                    pattern_data: Dict[str, Any],
                    correction: Optional[Dict[str, Any]] = None,
                    namespace: str = "default") -> bool:
        """
        添加反馈
        
        参数:
            pattern_type: 模式类型
            pattern_data: 模式数据
            correction: 纠正信息，可选
            namespace: 命名空间
            
        返回:
            bool: 添加是否成功
        """
        
    def get_patterns(self,
                    namespace: str = "default",
                    status: str = "confirmed") -> List[Dict[str, Any]]:
        """
        获取模式
        
        参数:
            namespace: 命名空间
            status: 模式状态 (tentative, emerging, pending, confirmed, archived)
            
        返回:
            List[Dict[str, Any]]: 模式列表
        """
        
    def confirm_pattern(self,
                       pattern_id: str,
                       namespace: str = "default") -> bool:
        """
        确认模式
        
        参数:
            pattern_id: 模式ID
            namespace: 命名空间
            
        返回:
            bool: 确认是否成功
        """
        
    def archive_pattern(self,
                       pattern_id: str,
                       namespace: str = "default") -> bool:
        """
        归档模式
        
        参数:
            pattern_id: 模式ID
            namespace: 命名空间
            
        返回:
            bool: 归档是否成功
        """
        
    def get_learning_stats(self) -> Dict[str, Any]:
        """
        获取学习统计
        
        返回:
            Dict[str, Any]: 学习统计
        """
```

#### 使用示例

```python
from qtassist_self_evolution import get_global_feedback_learner

# 获取学习器
learner = get_global_feedback_learner()

# 添加反馈
success = learner.add_feedback(
    pattern_type="function_sequence",
    pattern_data={
        "sequence": ["stock_query", "technical_analysis"],
        "context": {"time_of_day": "morning"}
    },
    correction={
        "correct_sequence": ["stock_query", "fundamental_analysis"],
        "reason": "早晨更适合基本面分析"
    },
    namespace="trading_patterns"
)

if success:
    print("反馈添加成功")

# 获取模式
patterns = learner.get_patterns(
    namespace="trading_patterns",
    status="confirmed"
)

print("确认的模式:")
for pattern in patterns:
    print(f"类型: {pattern['type']}")
    print(f"数据: {pattern['data']}")
    print(f"置信度: {pattern['confidence']}")
    print(f"使用次数: {pattern['usage_count']}")

# 获取统计
stats = learner.get_learning_stats()
print(f"总模式数: {stats['total_patterns']}")
print(f"确认模式: {stats['confirmed_patterns']}")
print(f"待定模式: {stats['pending_patterns']}")
```

### DatabaseManager

数据库管理器，提供数据库操作接口。

#### 类定义

```python
class DatabaseManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据库管理器
        """
        
    def execute_query(self,
                     query: str,
                     params: Tuple[Any, ...] = (),
                     fetch: bool = True) -> Union[List[Dict[str, Any]], int]:
        """
        执行查询
        
        参数:
            query: SQL查询语句
            params: 查询参数
            fetch: 是否获取结果
            
        返回:
            Union[List[Dict[str, Any]], int]: 查询结果或影响行数
        """
        
    def batch_insert(self,
                    table: str,
                    records: List[Dict[str, Any]]) -> bool:
        """
        批量插入
        
        参数:
            table: 表名
            records: 记录列表
            
        返回:
            bool: 插入是否成功
        """
        
    def get_table_info(self, table: str) -> Dict[str, Any]:
        """
        获取表信息
        
        参数:
            table: 表名
            
        返回:
            Dict[str, Any]: 表信息
        """
        
    def backup_database(self, backup_path: str) -> bool:
        """
        备份数据库
        
        参数:
            backup_path: 备份路径
            
        返回:
            bool: 备份是否成功
        """
        
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        返回:
            Dict[str, Any]: 统计信息
        """
```

#### 使用示例

```python
from qtassist_self_evolution import db_manager

# 执行查询
results = db_manager.execute_query(
    "SELECT * FROM usage_records WHERE date >= ? ORDER BY timestamp DESC LIMIT 10",
    ("2024-01-01",)
)

print("最近10条使用记录:")
for row in results:
    print(f"{row['timestamp']}: {row['function_name']} ({row['execution_time']}秒)")

# 批量插入
new_records = [
    {
        "function_name": "portfolio_analysis",
        "parameters": json.dumps({"portfolio_id": 1}),
        "execution_time": 1.25,
        "success": True,
        "timestamp": datetime.now().isoformat()
    },
    # ... 更多记录
]

success = db_manager.batch_insert("usage_records", new_records)
if success:
    print(f"批量插入成功: {len(new_records)} 条记录")

# 获取表信息
table_info = db_manager.get_table_info("usage_records")
print(f"表: {table_info['name']}")
print(f"列数: {len(table_info['columns'])}")
print(f"行数: {table_info['row_count']}")

# 备份数据库
backup_success = db_manager.backup_database("backups/evolution_backup.db")
if backup_success:
    print("数据库备份成功")

# 获取统计
stats = db_manager.get_stats()
print(f"连接池大小: {stats['pool_size']}")
print(f"批量写入次数: {stats['batch_writes']}")
print(f"查询缓存命中率: {stats['cache_hit_rate']}")
```

## 配置系统 API

配置系统提供统一的配置管理接口。

### 主要函数

```python
from qtassist_self_evolution.config import get_config, config_manager

# 获取配置
config = get_config()  # 使用默认配置
config = get_config("config/my_config.yaml")  # 从文件加载

# 通过管理器获取
config = config_manager.get()

# 保存配置
config_manager.save(config, "config/custom_config.yaml")

# 获取配置路径
paths = config_manager.get_config_paths()
```

### 配置类

```python
from qtassist_self_evolution.config import SystemConfig

# 创建配置
config = SystemConfig()

# 修改配置
config.database.path = "data/custom.db"
config.monitoring.collection_interval = 30
config.webui.port = 8080

# 转换为字典
config_dict = config.to_dict()

# 从字典创建
new_config = SystemConfig.from_dict(config_dict)
```

## Web UI REST API

Web控制面板提供以下REST API端点：

### 基础URL
```
http://localhost:5001/api
```

### 认证
目前API不需要认证，但生产环境建议添加认证。

### 响应格式
所有API返回JSON格式响应：

```json
{
  "status": "success" | "error",
  "message": "操作描述",
  "data": { ... },  // 实际数据
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### API端点列表

#### 1. 系统状态

**GET /api/status**
获取系统状态信息。

响应示例:
```json
{
  "status": "success",
  "data": {
    "phase": "监控中",
    "uptime": "3天2小时15分",
    "modules": {
      "tracker": "运行中",
      "monitor": "运行中",
      "predictor": "运行中"
    },
    "metrics": {
      "cpu_usage": 15.5,
      "memory_usage": 48.7,
      "disk_usage": 32.1
    }
  }
}
```

**GET /api/metrics**
获取性能指标。

查询参数:
- `type`: 指标类型 (cpu, memory, disk, network)
- `range`: 时间范围 (1h, 24h, 7d, 30d)

**GET /api/alerts**
获取警报列表。

查询参数:
- `severity`: 严重级别 (info, warning, critical)
- `acknowledged`: 是否已确认 (true/false)

#### 2. 使用数据

**GET /api/usage/stats**
获取使用统计。

**GET /api/usage/top**
获取高频功能。

查询参数:
- `limit`: 数量限制
- `range`: 时间范围

**GET /api/usage/history**
获取使用历史。

查询参数:
- `function`: 功能名称
- `days`: 天数

#### 3. 机器学习

**GET /api/ml/predictions**
获取预测结果。

**GET /api/ml/stats**
获取模型统计。

**POST /api/ml/train**
手动训练模型。

#### 4. 进化控制

**POST /api/evolution/start**
启动进化。

**POST /api/evolution/stop**
停止进化。

**GET /api/evolution/report**
获取进化报告。

查询参数:
- `days`: 报告天数

#### 5. 反馈学习

**POST /api/feedback**
提交反馈。

请求体:
```json
{
  "type": "pattern_type",
  "data": { ... },
  "correction": { ... }
}
```

**GET /api/feedback/patterns**
获取学习模式。

查询参数:
- `namespace`: 命名空间
- `status`: 模式状态

### 使用示例

```python
import requests
import json

# 基础URL
BASE_URL = "http://localhost:5001/api"

# 获取系统状态
response = requests.get(f"{BASE_URL}/status")
status = response.json()
print(f"系统状态: {status['data']['phase']}")

# 获取性能指标
response = requests.get(f"{BASE_URL}/metrics?type=cpu&range=24h")
metrics = response.json()
print(f"CPU指标数据点: {len(metrics['data'])}")

# 获取高频功能
response = requests.get(f"{BASE_URL}/usage/top?limit=5&range=7d")
top_functions = response.json()
print("高频功能:")
for func in top_functions['data']:
    print(f"  {func['function_name']}: {func['usage_count']}次")

# 提交反馈
feedback = {
    "type": "function_usage",
    "data": {
        "function": "stock_query",
        "context": {"time": "morning"}
    },
    "correction": {
        "suggestion": "添加更多技术指标"
    }
}

response = requests.post(
    f"{BASE_URL}/feedback",
    json=feedback,
    headers={"Content-Type": "application/json"}
)

if response.json()['status'] == 'success':
    print("反馈提交成功")

# 启动进化
response = requests.post(f"{BASE_URL}/evolution/start")
if response.json()['status'] == 'success':
    print("进化已启动")
```

## 数据模型

### 核心数据类

系统使用以下数据类：

#### UsageRecord
使用记录

```python
@dataclass
class UsageRecord:
    id: Optional[int] = None
    function_name: str = ""
    parameters: Dict[str, Any] = None
    execution_time: float = 0.0
    success: bool = True
    error: Optional[str] = None
    timestamp: datetime = None
```

#### FunctionStats
功能统计

```python
@dataclass
class FunctionStats:
    function_name: str = ""
    usage_count: int = 0
    avg_execution_time: float = 0.0
    success_count: int = 0
    error_count: int = 0
    last_used: datetime = None
    category: str = ""
```

#### EvolutionTask
进化任务

```python
@dataclass
class EvolutionTask:
    id: Optional[int] = None
    task_type: str = ""
    description: str = ""
    priority: str = ""
    target_module: str = ""
    parameters: Dict[str, Any] = None
    status: str = "pending"
    scheduled_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    result: Optional[Dict[str, Any]] = None
```

#### PredictionResult
预测结果

```python
@dataclass
class PredictionResult:
    prediction_type: str = ""
    target: str = ""
    confidence: float = 0.0
    predicted_value: Any = None
    timestamp: datetime = None
    features: Dict[str, Any] = None
    explanation: str = ""
```

#### SystemMetric
系统指标

```python
@dataclass
class SystemMetric:
    id: Optional[int] = None
    metric_type: str = ""
    value: float = 0.0
    timestamp: datetime = None
    tags: Dict[str, Any] = None
```

#### Alert
警报

```python
@dataclass
class Alert:
    id: Optional[int] = None
    alert_type: str = ""
    severity: str = "info"
    message: str = ""
    acknowledged: bool = False
    created_at: datetime = None
    acknowledged_at: Optional[datetime] = None
```

#### LearningPattern
学习模式

```python
@dataclass
class LearningPattern:
    id: Optional[str] = None
    pattern_type: str = ""
    pattern_data: Dict[str, Any] = None
    correction: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    status: str = "tentative"
    usage_count: int = 0
    namespace: str = "default"
    created_at: datetime = None
    updated_at: datetime = None
```

## 错误处理

### 异常类

系统定义以下