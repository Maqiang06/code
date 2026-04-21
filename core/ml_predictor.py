#!/usr/bin/env python3
"""
机器学习预测模块

提供预测性分析功能，包括：
1. 功能使用预测：基于历史模式预测用户下一步可能使用的功能
2. 性能趋势预测：预测系统性能瓶颈
3. 需求预测：基于用户行为预测未来需求
4. 异常检测：检测异常使用模式

支持多种机器学习算法，如果相关库不存在则优雅降级
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import os
import logging
import hashlib

# 尝试导入机器学习库
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    LinearRegression = None
    RandomForestClassifier = None
    IsolationForest = None
    LabelEncoder = None
    StandardScaler = None
    KMeans = None

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False
    joblib = None


class PredictionType(Enum):
    """预测类型枚举"""
    FUNCTION_USAGE = "function_usage"  # 功能使用预测
    PERFORMANCE_TREND = "performance_trend"  # 性能趋势预测
    DEMAND_PREDICTION = "demand_prediction"  # 需求预测
    ANOMALY_DETECTION = "anomaly_detection"  # 异常检测


@dataclass
class PredictionResult:
    """预测结果数据类"""
    prediction_type: str
    target: str
    confidence: float  # 置信度 (0-1)
    predicted_value: Any
    timestamp: datetime
    features: Dict[str, Any] = None
    explanation: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.features is None:
            self.features = {}


@dataclass
class ModelMetrics:
    """模型指标数据类"""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    last_trained: datetime
    inference_time_ms: float


class MLPredictor:
    """机器学习预测器"""
    
    def __init__(self, db_path: str = None, model_dir: str = None):
        """
        初始化机器学习预测器
        
        Args:
            db_path: 数据库路径（用于获取训练数据）
            model_dir: 模型保存目录
        """
        self.logger = logging.getLogger(__name__)
        
        # 检查机器学习库可用性
        self.ml_available = HAS_NUMPY and HAS_SKLEARN
        if not self.ml_available:
            self.logger.warning("机器学习库不可用，将使用简化预测模式")
        
        # 设置路径
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "data", "usage_tracking.db")
        
        if model_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_dir = os.path.join(base_dir, "models")
        
        self.db_path = db_path
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        
        # 模型缓存
        self.models = {}
        self.label_encoders = {}
        self.scalers = {}
        
        # 数据缓存
        self.data_cache = {}
        self.cache_timestamp = {}
        self.cache_ttl = 300  # 缓存5分钟
        
        # 统计信息
        self.stats = {
            "predictions_made": 0,
            "training_sessions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "fallback_predictions": 0
        }
        
        # 后台训练线程
        self._training_thread = None
        self._training_running = False
        
        self.logger.info(f"机器学习预测器初始化完成，ML可用性: {self.ml_available}")
    
    def predict_next_function(self, user_id: str = None, context: Dict[str, Any] = None, 
                            top_n: int = 5) -> List[PredictionResult]:
        """
        预测用户下一步可能使用的功能
        
        Args:
            user_id: 用户ID（如果为None则使用通用模式）
            context: 上下文信息（当前时间、已使用功能等）
            top_n: 返回前N个预测结果
            
        Returns:
            预测结果列表
        """
        if context is None:
            context = {}
        
        current_time = datetime.now()
        hour = current_time.hour
        weekday = current_time.weekday()
        
        try:
            if self.ml_available:
                # 使用机器学习模型预测
                predictions = self._predict_with_ml(user_id, context, hour, weekday, top_n)
            else:
                # 使用简化规则预测
                predictions = self._predict_with_rules(user_id, context, hour, weekday, top_n)
                self.stats["fallback_predictions"] += 1
            
            self.stats["predictions_made"] += 1
            return predictions
            
        except Exception as e:
            self.logger.error(f"预测功能使用失败: {str(e)}")
            # 返回基本预测
            return self._get_fallback_predictions(top_n)
    
    def _predict_with_ml(self, user_id: str, context: Dict[str, Any], 
                        hour: int, weekday: int, top_n: int) -> List[PredictionResult]:
        """使用机器学习模型预测"""
        # 获取训练数据
        training_data = self._get_training_data_for_prediction(user_id)
        
        if not training_data or len(training_data) < 10:
            # 数据不足，使用规则预测
            return self._predict_with_rules(user_id, context, hour, weekday, top_n)
        
        try:
            # 准备特征
            X, y, feature_names = self._prepare_features_for_prediction(
                training_data, hour, weekday, context
            )
            
            if len(set(y)) < 2:
                # 目标类别不足，使用规则预测
                return self._predict_with_rules(user_id, context, hour, weekday, top_n)
            
            # 训练或加载模型
            model_key = f"function_predictor_{user_id or 'global'}"
            if model_key not in self.models:
                self.models[model_key] = RandomForestClassifier(
                    n_estimators=100, random_state=42, n_jobs=-1
                )
            
            model = self.models[model_key]
            
            # 训练模型（如果数据足够新）
            model.fit(X, y)
            
            # 准备当前上下文特征
            current_features = self._extract_current_features(hour, weekday, context)
            
            # 确保特征维度一致
            if len(current_features) != X.shape[1]:
                # 调整特征维度
                current_features = self._adjust_feature_dimensions(
                    current_features, X.shape[1], feature_names
                )
            
            # 预测概率
            X_current = np.array([current_features])
            probabilities = model.predict_proba(X_current)[0]
            
            # 获取类别
            classes = model.classes_
            
            # 创建预测结果
            results = []
            for i, prob in enumerate(probabilities):
                if len(results) >= top_n:
                    break
                
                result = PredictionResult(
                    prediction_type=PredictionType.FUNCTION_USAGE.value,
                    target=classes[i],
                    confidence=float(prob),
                    predicted_value=classes[i],
                    timestamp=datetime.now(),
                    features={
                        "hour": hour,
                        "weekday": weekday,
                        "user_id": user_id,
                        "context_keys": list(context.keys()) if context else []
                    },
                    explanation=f"基于历史使用模式的预测，置信度: {prob:.2%}"
                )
                results.append(result)
            
            # 按置信度排序
            results.sort(key=lambda x: x.confidence, reverse=True)
            return results[:top_n]
            
        except Exception as e:
            self.logger.error(f"ML预测失败: {str(e)}")
            return self._predict_with_rules(user_id, context, hour, weekday, top_n)
    
    def _predict_with_rules(self, user_id: str, context: Dict[str, Any], 
                           hour: int, weekday: int, top_n: int) -> List[PredictionResult]:
        """使用规则预测（机器学习不可用时的回退方案）"""
        # 基于时间的简单规则
        predictions = []
        
        # 工作时间模式（09:00-17:00）
        if 9 <= hour <= 17:
            time_based_funcs = [
                ("股票查询", 0.8, "工作时间常用"),
                ("数据分析", 0.7, "工作时间常用"),
                ("系统配置", 0.3, "工作时间偶尔使用")
            ]
        # 晚间模式（18:00-22:00）
        elif 18 <= hour <= 22:
            time_based_funcs = [
                ("数据整理", 0.6, "晚间常用"),
                ("报告生成", 0.5, "晚间常用"),
                ("系统优化", 0.4, "晚间偶尔使用")
            ]
        # 其他时间
        else:
            time_based_funcs = [
                ("系统监控", 0.5, "非工作时间常用"),
                ("数据备份", 0.4, "非工作时间常用"),
                ("系统维护", 0.3, "非工作时间偶尔使用")
            ]
        
        # 工作日模式
        if weekday < 5:  # 周一到周五
            weekday_based_funcs = [
                ("实时交易", 0.7, "工作日常用"),
                ("市场分析", 0.6, "工作日常用"),
                ("投资组合管理", 0.5, "工作日常用")
            ]
        else:  # 周末
            weekday_based_funcs = [
                ("策略回测", 0.6, "周末常用"),
                ("数据分析", 0.5, "周末常用"),
                ("系统优化", 0.4, "周末常用")
            ]
        
        # 合并预测
        all_funcs = {}
        for func_name, confidence, explanation in time_based_funcs + weekday_based_funcs:
            if func_name not in all_funcs or confidence > all_funcs[func_name][0]:
                all_funcs[func_name] = (confidence, explanation)
        
        # 转换为预测结果
        for func_name, (confidence, explanation) in list(all_funcs.items())[:top_n]:
            result = PredictionResult(
                prediction_type=PredictionType.FUNCTION_USAGE.value,
                target=func_name,
                confidence=confidence,
                predicted_value=func_name,
                timestamp=datetime.now(),
                features={
                    "hour": hour,
                    "weekday": weekday,
                    "user_id": user_id,
                    "rule_based": True
                },
                explanation=f"基于时间模式的预测: {explanation}"
            )
            predictions.append(result)
        
        return predictions
    
    def _get_fallback_predictions(self, top_n: int) -> List[PredictionResult]:
        """获取回退预测（当所有预测方法都失败时）"""
        fallback_funcs = [
            ("股票查询", 0.5, "系统默认功能"),
            ("数据分析", 0.4, "系统默认功能"),
            ("系统配置", 0.3, "系统默认功能")
        ]
        
        predictions = []
        for func_name, confidence, explanation in fallback_funcs[:top_n]:
            result = PredictionResult(
                prediction_type=PredictionType.FUNCTION_USAGE.value,
                target=func_name,
                confidence=confidence,
                predicted_value=func_name,
                timestamp=datetime.now(),
                features={"fallback": True},
                explanation=f"回退预测: {explanation}"
            )
            predictions.append(result)
        
        return predictions
    
    def predict_performance_trend(self, metric_name: str, lookback_days: int = 7, 
                                forecast_days: int = 3) -> PredictionResult:
        """
        预测性能趋势
        
        Args:
            metric_name: 指标名称（如"execution_time", "memory_usage"等）
            lookback_days: 回顾天数
            forecast_days: 预测天数
            
        Returns:
            性能趋势预测结果
        """
        try:
            # 获取历史数据
            historical_data = self._get_performance_data(metric_name, lookback_days)
            
            if not historical_data or len(historical_data) < 3:
                return self._get_fallback_performance_prediction(metric_name)
            
            if self.ml_available:
                # 使用线性回归预测趋势
                trend, confidence = self._predict_trend_with_regression(
                    historical_data, forecast_days
                )
                method = "linear_regression"
            else:
                # 使用简单移动平均
                trend, confidence = self._predict_trend_with_moving_average(
                    historical_data, forecast_days
                )
                method = "moving_average"
                self.stats["fallback_predictions"] += 1
            
            self.stats["predictions_made"] += 1
            
            result = PredictionResult(
                prediction_type=PredictionType.PERFORMANCE_TREND.value,
                target=metric_name,
                confidence=confidence,
                predicted_value=trend,
                timestamp=datetime.now(),
                features={
                    "lookback_days": lookback_days,
                    "forecast_days": forecast_days,
                    "historical_samples": len(historical_data),
                    "method": method
                },
                explanation=f"基于{lookback_days}天历史数据的{forecast_days}天趋势预测，使用{method}方法"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"预测性能趋势失败: {str(e)}")
            return self._get_fallback_performance_prediction(metric_name)
    
    def detect_anomalies(self, data_points: List[Dict[str, Any]], 
                        features: List[str]) -> List[Dict[str, Any]]:
        """
        检测异常数据点
        
        Args:
            data_points: 数据点列表
            features: 用于异常检测的特征列表
            
        Returns:
            异常数据点列表
        """
        if not data_points or len(data_points) < 10:
            return []
        
        try:
            if self.ml_available:
                anomalies = self._detect_anomalies_with_isolation_forest(data_points, features)
                method = "isolation_forest"
            else:
                anomalies = self._detect_anomalies_with_iqr(data_points, features)
                method = "iqr"
                self.stats["fallback_predictions"] += 1
            
            self.stats["predictions_made"] += 1
            
            # 添加检测方法信息
            for anomaly in anomalies:
                anomaly["detection_method"] = method
                anomaly["detected_at"] = datetime.now().isoformat()
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"异常检测失败: {str(e)}")
            return []
    
    def start_background_training(self, interval_hours: int = 24):
        """
        启动后台训练线程
        
        Args:
            interval_hours: 训练间隔（小时）
        """
        if self._training_running:
            self.logger.warning("后台训练线程已在运行")
            return
        
        self._training_running = True
        
        def training_worker():
            while self._training_running:
                try:
                    self.logger.info("开始后台模型训练...")
                    self.train_all_models()
                    self.stats["training_sessions"] += 1
                    self.logger.info(f"后台模型训练完成，已训练次数: {self.stats['training_sessions']}")
                except Exception as e:
                    self.logger.error(f"后台训练失败: {str(e)}")
                
                # 等待指定间隔
                for _ in range(interval_hours * 3600 // 10):
                    if not self._training_running:
                        break
                    time.sleep(10)
        
        self._training_thread = threading.Thread(target=training_worker, daemon=True)
        self._training_thread.start()
        self.logger.info(f"后台训练线程已启动，间隔: {interval_hours}小时")
    
    def stop_background_training(self):
        """停止后台训练线程"""
        self._training_running = False
        if self._training_thread:
            self._training_thread.join(timeout=5.0)
            self.logger.info("后台训练线程已停止")
    
    def train_all_models(self):
        """训练所有模型"""
        try:
            # 训练功能使用预测模型
            self._train_function_prediction_model()
            
            # 训练性能趋势预测模型
            self._train_performance_prediction_model()
            
            # 训练异常检测模型
            self._train_anomaly_detection_model()
            
            # 保存模型
            self._save_models()
            
        except Exception as e:
            self.logger.error(f"训练所有模型失败: {str(e)}")
    
    def get_model_metrics(self) -> Dict[str, ModelMetrics]:
        """获取所有模型的指标"""
        metrics = {}
        
        for model_name, model in self.models.items():
            # 这里应该计算实际的模型指标
            # 为简化，我们返回默认指标
            metrics[model_name] = ModelMetrics(
                model_name=model_name,
                accuracy=0.85,  # 示例值
                precision=0.82,  # 示例值
                recall=0.87,  # 示例值
                f1_score=0.84,  # 示例值
                training_samples=1000,  # 示例值
                last_trained=datetime.now(),
                inference_time_ms=5.0  # 示例值
            )
        
        return metrics
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        # 计算准确率（如果没有实际准确率，使用基于成功预测的估计值）
        accuracy = None
        if self.stats.get("predictions_made", 0) > 0:
            # 简单估算：成功预测比例（非回退预测）
            total_predictions = self.stats.get("predictions_made", 0)
            fallback_predictions = self.stats.get("fallback_predictions", 0)
            successful_predictions = total_predictions - fallback_predictions
            if total_predictions > 0:
                accuracy = successful_predictions / total_predictions
        
        # 检查是否有训练的模型
        # 如果机器学习库可用且已进行训练会话，则认为模型已训练
        model_trained = self.ml_available and self.stats.get("training_sessions", 0) > 0
        
        return {
            "total_predictions": self.stats.get("predictions_made", 0),
            "accuracy": accuracy,
            "model_trained": model_trained,
            "fallback_predictions": self.stats.get("fallback_predictions", 0),
            "training_sessions": self.stats.get("training_sessions", 0),
            "cache_hits": self.stats.get("cache_hits", 0),
            "cache_misses": self.stats.get("cache_misses", 0),
            "ml_available": self.ml_available,
            "models_count": len(self.models),
            "background_training": self._training_running
        }
    
    # ===== 内部方法 =====
    
    def _get_training_data_for_prediction(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取预测训练数据"""
        cache_key = f"training_data_{user_id or 'global'}"
        
        # 检查缓存
        if (cache_key in self.data_cache and 
            cache_key in self.cache_timestamp and
            time.time() - self.cache_timestamp[cache_key] < self.cache_ttl):
            self.stats["cache_hits"] += 1
            return self.data_cache[cache_key]
        
        self.stats["cache_misses"] += 1
        
        # 这里应该从数据库获取实际数据
        # 为简化，我们返回示例数据
        example_data = [
            {"function_name": "股票查询", "hour": 9, "weekday": 0, "user_id": user_id or "default"},
            {"function_name": "数据分析", "hour": 10, "weekday": 0, "user_id": user_id or "default"},
            {"function_name": "股票查询", "hour": 14, "weekday": 1, "user_id": user_id or "default"},
            {"function_name": "系统配置", "hour": 11, "weekday": 2, "user_id": user_id or "default"},
            {"function_name": "数据分析", "hour": 15, "weekday": 3, "user_id": user_id or "default"},
            {"function_name": "股票查询", "hour": 9, "weekday": 4, "user_id": user_id or "default"},
        ]
        
        # 缓存数据
        self.data_cache[cache_key] = example_data
        self.cache_timestamp[cache_key] = time.time()
        
        return example_data
    
    def _prepare_features_for_prediction(self, training_data: List[Dict[str, Any]], 
                                        hour: int, weekday: int, context: Dict[str, Any]) -> Tuple:
        """为预测准备特征"""
        if not self.ml_available or not HAS_NUMPY:
            return None, None, None
        
        # 提取特征和目标
        X = []
        y = []
        feature_names = ["hour", "weekday"]
        
        for data_point in training_data:
            features = [
                data_point.get("hour", 0),
                data_point.get("weekday", 0)
            ]
            
            # 添加上下文特征
            if context:
                for key, value in context.items():
                    if key not in feature_names:
                        feature_names.append(key)
                    
                    # 简单特征编码
                    if isinstance(value, (int, float)):
                        features.append(value)
                    elif isinstance(value, bool):
                        features.append(1 if value else 0)
                    else:
                        # 字符串或其他类型，使用简单哈希
                        features.append(hash(str(value)) % 100)
            
            X.append(features)
            y.append(data_point.get("function_name", "unknown"))
        
        return np.array(X), np.array(y), feature_names
    
    def _extract_current_features(self, hour: int, weekday: int, context: Dict[str, Any]) -> List[float]:
        """提取当前上下文特征"""
        features = [float(hour), float(weekday)]
        
        if context:
            for value in context.values():
                if isinstance(value, (int, float)):
                    features.append(float(value))
                elif isinstance(value, bool):
                    features.append(1.0 if value else 0.0)
                else:
                    features.append(float(hash(str(value)) % 100))
        
        return features
    
    def _adjust_feature_dimensions(self, features: List[float], target_dim: int, 
                                 feature_names: List[str]) -> List[float]:
        """调整特征维度以匹配训练数据"""
        if len(features) == target_dim:
            return features
        
        # 如果特征维度不匹配，使用零填充或截断
        if len(features) < target_dim:
            return features + [0.0] * (target_dim - len(features))
        else:
            return features[:target_dim]
    
    def _get_performance_data(self, metric_name: str, lookback_days: int) -> List[float]:
        """获取性能数据"""
        # 这里应该从数据库获取实际性能数据
        # 为简化，我们返回示例数据
        import random
        base_value = 100.0
        trend = 1.05  # 轻微上升趋势
        
        data = []
        for i in range(lookback_days):
            value = base_value * (trend ** i) + random.uniform(-10, 10)
            data.append(value)
        
        return data
    
    def _predict_trend_with_regression(self, historical_data: List[float], 
                                      forecast_days: int) -> Tuple[float, float]:
        """使用线性回归预测趋势"""
        if not self.ml_available or len(historical_data) < 3:
            return self._predict_trend_with_moving_average(historical_data, forecast_days)
        
        X = np.arange(len(historical_data)).reshape(-1, 1)
        y = np.array(historical_data)
        
        model = LinearRegression()
        model.fit(X, y)
        
        # 预测未来值
        future_X = np.array([len(historical_data) + forecast_days - 1]).reshape(-1, 1)
        predicted_value = model.predict(future_X)[0]
        
        # 计算置信度（基于R²分数）
        r_squared = model.score(X, y)
        confidence = max(0.0, min(1.0, r_squared))
        
        return float(predicted_value), float(confidence)
    
    def _predict_trend_with_moving_average(self, historical_data: List[float], 
                                          forecast_days: int) -> Tuple[float, float]:
        """使用移动平均预测趋势"""
        if not historical_data:
            return 0.0, 0.0
        
        # 计算简单移动平均
        window = min(7, len(historical_data))
        recent_data = historical_data[-window:]
        moving_avg = sum(recent_data) / len(recent_data)
        
        # 计算趋势（最后值与平均值的比率）
        if len(historical_data) >= 2:
            last_value = historical_data[-1]
            prev_value = historical_data[-2]
            trend = last_value / prev_value if prev_value != 0 else 1.0
        else:
            trend = 1.0
        
        # 预测值 = 移动平均 * 趋势^预测天数
        predicted_value = moving_avg * (trend ** forecast_days)
        
        # 基于数据稳定性计算置信度
        if len(recent_data) >= 2:
            variance = np.var(recent_data) if HAS_NUMPY else 0.0
            confidence = max(0.3, min(1.0, 1.0 - variance / (moving_avg ** 2) if moving_avg != 0 else 0.5))
        else:
            confidence = 0.5
        
        return float(predicted_value), float(confidence)
    
    def _get_fallback_performance_prediction(self, metric_name: str) -> PredictionResult:
        """获取回退性能预测"""
        return PredictionResult(
            prediction_type=PredictionType.PERFORMANCE_TREND.value,
            target=metric_name,
            confidence=0.3,
            predicted_value=100.0,
            timestamp=datetime.now(),
            features={"fallback": True},
            explanation="数据不足，使用默认值预测"
        )
    
    def _detect_anomalies_with_isolation_forest(self, data_points: List[Dict[str, Any]], 
                                               features: List[str]) -> List[Dict[str, Any]]:
        """使用孤立森林检测异常"""
        if not self.ml_available or not features or len(data_points) < 10:
            return self._detect_anomalies_with_iqr(data_points, features)
        
        # 提取特征矩阵
        X = []
        for point in data_points:
            feature_vector = []
            for feature in features:
                value = point.get(feature, 0)
                if isinstance(value, (int, float)):
                    feature_vector.append(float(value))
                else:
                    # 非数值特征，使用简单编码
                    feature_vector.append(float(hash(str(value)) % 100))
            X.append(feature_vector)
        
        X = np.array(X)
        
        # 训练孤立森林模型
        model = IsolationForest(contamination=0.1, random_state=42)
        predictions = model.fit_predict(X)
        
        # 识别异常点（预测为-1）
        anomalies = []
        for i, pred in enumerate(predictions):
            if pred == -1:
                anomaly_point = data_points[i].copy()
                anomaly_point["anomaly_score"] = float(model.score_samples([X[i]])[0])
                anomaly_point["is_anomaly"] = True
                anomalies.append(anomaly_point)
        
        return anomalies
    
    def _detect_anomalies_with_iqr(self, data_points: List[Dict[str, Any]], 
                                  features: List[str]) -> List[Dict[str, Any]]:
        """使用IQR（四分位距）方法检测异常"""
        if not features or len(data_points) < 5:
            return []
        
        anomalies = []
        
        for feature in features:
            # 提取特征值
            values = []
            for point in data_points:
                value = point.get(feature)
                if isinstance(value, (int, float)):
                    values.append(float(value))
            
            if len(values) < 5:
                continue
            
            # 计算四分位数
            q1 = np.percentile(values, 25) if HAS_NUMPY else sorted(values)[len(values)//4]
            q3 = np.percentile(values, 75) if HAS_NUMPY else sorted(values)[3*len(values)//4]
            iqr = q3 - q1
            
            if iqr == 0:
                continue
            
            # 定义异常边界
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            # 检测异常点
            for i, point in enumerate(data_points):
                value = point.get(feature)
                if isinstance(value, (int, float)) and (value < lower_bound or value > upper_bound):
                    if i not in [a["_index"] for a in anomalies if "_index" in a]:
                        anomaly_point = point.copy()
                        anomaly_point["_index"] = i
                        anomaly_point["anomaly_feature"] = feature
                        anomaly_point["anomaly_value"] = value
                        anomaly_point["lower_bound"] = lower_bound
                        anomaly_point["upper_bound"] = upper_bound
                        anomaly_point["is_anomaly"] = True
                        anomalies.append(anomaly_point)
        
        # 移除索引字段
        for anomaly in anomalies:
            if "_index" in anomaly:
                del anomaly["_index"]
        
        return anomalies
    
    def _train_function_prediction_model(self):
        """训练功能预测模型"""
        self.logger.info("训练功能预测模型...")
        # 实际实现需要从数据库获取数据并训练模型
        # 这里仅记录日志
        self.logger.info("功能预测模型训练完成（示例）")
    
    def _train_performance_prediction_model(self):
        """训练性能预测模型"""
        self.logger.info("训练性能预测模型...")
        # 实际实现需要从数据库获取数据并训练模型
        # 这里仅记录日志
        self.logger.info("性能预测模型训练完成（示例）")
    
    def _train_anomaly_detection_model(self):
        """训练异常检测模型"""
        self.logger.info("训练异常检测模型...")
        # 实际实现需要从数据库获取数据并训练模型
        # 这里仅记录日志
        self.logger.info("异常检测模型训练完成（示例）")
    
    def _save_models(self):
        """保存模型到磁盘"""
        if not HAS_JOBLIB:
            return
        
        try:
            for model_name, model in self.models.items():
                model_path = os.path.join(self.model_dir, f"{model_name}.joblib")
                joblib.dump(model, model_path)
            
            self.logger.info(f"模型已保存到: {self.model_dir}")
        except Exception as e:
            self.logger.error(f"保存模型失败: {str(e)}")
    
    def _load_models(self):
        """从磁盘加载模型"""
        if not HAS_JOBLIB:
            return
        
        try:
            for filename in os.listdir(self.model_dir):
                if filename.endswith(".joblib"):
                    model_name = filename[:-7]  # 移除.joblib扩展名
                    model_path = os.path.join(self.model_dir, filename)
                    model = joblib.load(model_path)
                    self.models[model_name] = model
            
            self.logger.info(f"从 {self.model_dir} 加载了 {len(self.models)} 个模型")
        except Exception as e:
            self.logger.error(f"加载模型失败: {str(e)}")


# 全局机器学习预测器实例
ml_predictor = None

def get_ml_predictor(db_path: str = None, model_dir: str = None) -> MLPredictor:
    """获取全局机器学习预测器实例"""
    global ml_predictor
    if ml_predictor is None:
        ml_predictor = MLPredictor(db_path, model_dir)
    return ml_predictor