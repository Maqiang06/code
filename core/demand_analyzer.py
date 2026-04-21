"""
需求分析模块

功能：分析用户未满足的需求，识别功能缺口，预测未来需求趋势，量化需求优先级

主要功能：
1. 显性需求分析：直接从用户请求中提取需求
2. 隐性需求分析：从使用模式中推断未满足的需求
3. 功能缺口识别：识别系统当前不具备的功能
4. 需求趋势预测：基于历史数据预测未来需求
5. 优先级计算：基于频率、重要性、实现难度计算优先级
"""

import json
import re
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
import os
from collections import defaultdict
from enum import Enum
import statistics


class DemandType(Enum):
    """需求类型枚举"""
    PERFORMANCE_OPTIMIZATION = "性能优化"
    NEW_FEATURE = "新功能"
    BUG_FIX = "错误修复"
    UX_IMPROVEMENT = "用户体验改进"
    INTEGRATION = "系统集成"
    DATA_ACCESS = "数据访问"
    TOOL_REQUEST = "工具请求"
    SKILL_REQUEST = "技能请求"
    OTHER = "其他"


class PriorityLevel(Enum):
    """优先级级别枚举"""
    CRITICAL = "关键"     # 必须立即处理
    HIGH = "高"          # 需要尽快处理
    MEDIUM = "中"        # 应该处理
    LOW = "低"           # 可以处理


@dataclass
class UserDemand:
    """用户需求数据类"""
    id: Optional[int] = None
    demand_type: str = DemandType.OTHER.value
    description: str = ""
    source: str = ""  # 需求来源：explicit（显性）、implicit（隐性）、pattern（模式分析）
    confidence: float = 0.0  # 需求置信度（0-1）
    frequency: int = 1  # 出现频率
    first_detected: datetime = None
    last_detected: datetime = None
    user_feedback: str = ""
    context: Dict[str, Any] = None
    related_functions: List[str] = None
    
    def __post_init__(self):
        if self.first_detected is None:
            self.first_detected = datetime.now()
        if self.last_detected is None:
            self.last_detected = datetime.now()
        if self.context is None:
            self.context = {}
        if self.related_functions is None:
            self.related_functions = []


@dataclass
class FeatureGap:
    """功能缺口数据类"""
    id: Optional[int] = None
    gap_name: str = ""
    description: str = ""
    detected_from: str = ""  # 检测来源：comparison（对比）、request（请求）、pattern（模式）
    severity: str = "中"     # 严重程度：高、中、低
    priority: str = PriorityLevel.MEDIUM.value
    estimated_effort: int = 0  # 预估工作量（小时）
    potential_impact: float = 0.0  # 潜在影响（0-1）
    related_demands: List[int] = None  # 相关需求ID列表
    suggested_solutions: List[str] = None
    
    def __post_init__(self):
        if self.related_demands is None:
            self.related_demands = []
        if self.suggested_solutions is None:
            self.suggested_solutions = []


@dataclass
class TrendPrediction:
    """趋势预测数据类"""
    id: Optional[int] = None
    trend_name: str = ""
    description: str = ""
    category: str = ""
    confidence: float = 0.0
    timeframe: str = ""  # 时间范围：short（短期）、medium（中期）、long（长期）
    expected_impact: str = ""
    supporting_evidence: List[str] = None
    recommended_actions: List[str] = None
    
    def __post_init__(self):
        if self.supporting_evidence is None:
            self.supporting_evidence = []
        if self.recommended_actions is None:
            self.recommended_actions = []


class DemandAnalyzer:
    """需求分析器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化需求分析器
        
        Args:
            db_path: SQLite数据库路径，如果为None则使用默认路径
        """
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "data", "demand_analysis.db")
        
        self.db_path = db_path
        self._init_database()
        
        # 关键词映射
        self._performance_keywords = ["慢", "卡顿", "优化", "加速", "性能", "响应", "速度"]
        self._feature_keywords = ["需要", "想要", "希望", "应该", "可以", "功能", "特性"]
        self._bug_keywords = ["错误", "故障", "问题", "bug", "异常", "失败", "崩溃"]
        self._ux_keywords = ["体验", "界面", "UI", "UX", "设计", "美观", "易用"]
        self._integration_keywords = ["集成", "连接", "对接", "接口", "API", "同步"]
        self._data_keywords = ["数据", "获取", "查询", "存储", "分析", "处理"]
        self._tool_keywords = ["工具", "软件", "应用", "程序", "脚本", "自动化"]
        self._skill_keywords = ["技能", "能力", "知识", "技巧", "经验", "专业"]
        
        # 需求模式识别器
        self._demand_patterns = [
            (r"能不能.*(实现|添加|创建).*功能", DemandType.NEW_FEATURE.value),
            (r"希望.*(更快|加速|优化).*", DemandType.PERFORMANCE_OPTIMIZATION.value),
            (r"(错误|问题|bug).*(修复|解决)", DemandType.BUG_FIX.value),
            (r"体验.*(改进|提升|优化)", DemandType.UX_IMPROVEMENT.value),
            (r"(集成|连接|对接).*系统", DemandType.INTEGRATION.value),
            (r"(数据|信息).*(获取|查询|分析)", DemandType.DATA_ACCESS.value),
            (r"需要.*(工具|软件|应用)", DemandType.TOOL_REQUEST.value),
            (r"学习.*(技能|能力|知识)", DemandType.SKILL_REQUEST.value),
        ]
    
    def _init_database(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建需求表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_demands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                demand_type TEXT NOT NULL,
                description TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                frequency INTEGER DEFAULT 1,
                first_detected DATETIME,
                last_detected DATETIME,
                user_feedback TEXT,
                context TEXT,
                related_functions TEXT
            )
        """)
        
        # 创建功能缺口表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gap_name TEXT NOT NULL,
                description TEXT NOT NULL,
                detected_from TEXT NOT NULL,
                severity TEXT NOT NULL,
                priority TEXT NOT NULL,
                estimated_effort INTEGER DEFAULT 0,
                potential_impact REAL DEFAULT 0.0,
                related_demands TEXT,
                suggested_solutions TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建趋势预测表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trend_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trend_name TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                timeframe TEXT NOT NULL,
                expected_impact TEXT,
                supporting_evidence TEXT,
                recommended_actions TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建需求来源表（记录用户请求）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS demand_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_text TEXT NOT NULL,
                request_type TEXT NOT NULL,
                timestamp DATETIME,
                context TEXT,
                processed BOOLEAN DEFAULT FALSE
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_demands_type ON user_demands(demand_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_demands_source ON user_demands(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gaps_priority ON feature_gaps(priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_timeframe ON trend_predictions(timeframe)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_timestamp ON demand_sources(timestamp)")
        
        conn.commit()
        conn.close()
    
    def analyze_explicit_demand(self, request_text: str, context: Dict[str, Any] = None) -> List[UserDemand]:
        """
        分析显性需求（直接从用户请求中提取）
        
        Args:
            request_text: 用户请求文本
            context: 请求上下文
            
        Returns:
            识别出的需求列表
        """
        if context is None:
            context = {}
        
        # 保存需求来源
        self._save_demand_source(request_text, "explicit", context)
        
        demands = []
        
        # 使用正则表达式匹配需求模式
        for pattern, demand_type in self._demand_patterns:
            if re.search(pattern, request_text, re.IGNORECASE):
                description = self._extract_demand_description(request_text, pattern)
                demand = UserDemand(
                    demand_type=demand_type,
                    description=description,
                    source="explicit",
                    confidence=0.8,  # 显性需求置信度较高
                    context=context
                )
                demands.append(demand)
        
        # 关键词匹配
        demand_type = self._classify_by_keywords(request_text)
        if demand_type != DemandType.OTHER.value:
            description = self._extract_keyword_description(request_text)
            demand = UserDemand(
                demand_type=demand_type,
                description=description,
                source="explicit_keyword",
                confidence=0.7,
                context=context
            )
            demands.append(demand)
        
        # 保存到数据库
        for demand in demands:
            self._save_demand(demand)
        
        return demands
    
    def _classify_by_keywords(self, text: str) -> str:
        """通过关键词分类需求类型"""
        text_lower = text.lower()
        
        # 检查性能相关关键词
        if any(keyword in text_lower for keyword in self._performance_keywords):
            return DemandType.PERFORMANCE_OPTIMIZATION.value
        
        # 检查功能相关关键词
        if any(keyword in text_lower for keyword in self._feature_keywords):
            return DemandType.NEW_FEATURE.value
        
        # 检查错误相关关键词
        if any(keyword in text_lower for keyword in self._bug_keywords):
            return DemandType.BUG_FIX.value
        
        # 检查用户体验相关关键词
        if any(keyword in text_lower for keyword in self._ux_keywords):
            return DemandType.UX_IMPROVEMENT.value
        
        # 检查集成相关关键词
        if any(keyword in text_lower for keyword in self._integration_keywords):
            return DemandType.INTEGRATION.value
        
        # 检查数据相关关键词
        if any(keyword in text_lower for keyword in self._data_keywords):
            return DemandType.DATA_ACCESS.value
        
        # 检查工具相关关键词
        if any(keyword in text_lower for keyword in self._tool_keywords):
            return DemandType.TOOL_REQUEST.value
        
        # 检查技能相关关键词
        if any(keyword in text_lower for keyword in self._skill_keywords):
            return DemandType.SKILL_REQUEST.value
        
        return DemandType.OTHER.value
    
    def _extract_demand_description(self, text: str, pattern: str) -> str:
        """从文本中提取需求描述"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
        
        # 如果无法匹配，返回前50个字符
        return text[:50] + ("..." if len(text) > 50 else "")
    
    def _extract_keyword_description(self, text: str) -> str:
        """从关键词匹配中提取描述"""
        # 尝试提取包含关键词的句子
        sentences = re.split(r'[.!?。！？]', text)
        for sentence in sentences:
            if len(sentence.strip()) > 10:
                return sentence.strip()
        
        # 返回前60个字符
        return text[:60] + ("..." if len(text) > 60 else "")
    
    def analyze_implicit_demand(self, usage_stats: List[Dict], user_patterns: List[Any]) -> List[UserDemand]:
        """
        分析隐性需求（从使用模式中推断）
        
        Args:
            usage_stats: 使用统计数据
            user_patterns: 用户使用模式
            
        Returns:
            识别出的需求列表
        """
        demands = []
        
        # 从使用统计数据中推断需求
        demands.extend(self._analyze_usage_stats(usage_stats))
        
        # 从用户模式中推断需求
        demands.extend(self._analyze_user_patterns(user_patterns))
        
        # 保存到数据库
        for demand in demands:
            demand.source = "implicit"
            self._save_demand(demand)
        
        return demands
    
    def _analyze_usage_stats(self, usage_stats: List[Dict]) -> List[UserDemand]:
        """从使用统计数据中分析需求"""
        demands = []
        
        for stat in usage_stats:
            function_name = stat.get("function_name", "")
            avg_time = stat.get("avg_execution_time", 0.0)
            success_rate = stat.get("success_rate", 1.0)
            call_count = stat.get("call_count", 0)
            
            # 性能优化需求：执行时间过长
            if avg_time > 2.0 and call_count > 10:
                demands.append(UserDemand(
                    demand_type=DemandType.PERFORMANCE_OPTIMIZATION.value,
                    description=f"功能'{function_name}'执行时间过长（平均{avg_time:.2f}秒）",
                    confidence=min(0.9, avg_time / 5.0),  # 执行时间越长，置信度越高
                    frequency=call_count,
                    related_functions=[function_name]
                ))
            
            # 错误修复需求：成功率过低
            if success_rate < 0.7 and call_count > 5:
                demands.append(UserDemand(
                    demand_type=DemandType.BUG_FIX.value,
                    description=f"功能'{function_name}'成功率过低（{success_rate*100:.1f}%）",
                    confidence=min(0.9, (1.0 - success_rate) * 2),  # 成功率越低，置信度越高
                    frequency=call_count,
                    related_functions=[function_name]
                ))
            
            # 功能增强需求：高频使用但功能单一
            if call_count > 50 and function_name:
                # 检查是否可能有相关功能需求
                demands.append(UserDemand(
                    demand_type=DemandType.NEW_FEATURE.value,
                    description=f"高频使用功能'{function_name}'可能需要增强或相关功能",
                    confidence=0.6,
                    frequency=call_count,
                    related_functions=[function_name]
                ))
        
        return demands
    
    def _analyze_user_patterns(self, user_patterns: List[Any]) -> List[UserDemand]:
        """从用户模式中分析需求"""
        demands = []
        
        for pattern in user_patterns:
            pattern_name = getattr(pattern, 'pattern_name', '')
            description = getattr(pattern, 'description', '')
            confidence = getattr(pattern, 'confidence', 0.0)
            functions = getattr(pattern, 'functions', [])
            
            # 高置信度的模式可能表示自动化需求
            if confidence > 0.7 and functions:
                demands.append(UserDemand(
                    demand_type=DemandType.INTEGRATION.value,
                    description=f"检测到稳定模式：{description}，可能需要自动化集成",
                    confidence=confidence * 0.8,  # 模式置信度转换为需求置信度
                    frequency=1,
                    related_functions=functions
                ))
        
        return demands
    
    def identify_feature_gaps(self, 
                             existing_features: List[str],
                             user_demands: List[UserDemand],
                             external_comparison: Dict[str, Any] = None) -> List[FeatureGap]:
        """
        识别功能缺口
        
        Args:
            existing_features: 现有功能列表
            user_demands: 用户需求列表
            external_comparison: 外部系统对比数据
            
        Returns:
            功能缺口列表
        """
        gaps = []
        
        # 从用户需求中识别功能缺口
        gaps.extend(self._identify_gaps_from_demands(existing_features, user_demands))
        
        # 从外部对比中识别功能缺口
        if external_comparison:
            gaps.extend(self._identify_gaps_from_comparison(existing_features, external_comparison))
        
        # 保存到数据库
        for gap in gaps:
            self._save_feature_gap(gap)
        
        return gaps
    
    def _identify_gaps_from_demands(self, existing_features: List[str], user_demands: List[UserDemand]) -> List[FeatureGap]:
        """从用户需求中识别功能缺口"""
        gaps = []
        
        # 将现有功能转换为小写以便比较
        existing_lower = [f.lower() for f in existing_features]
        
        for demand in user_demands:
            demand_desc = demand.description.lower()
            
            # 检查需求是否与现有功能相关
            is_related = any(feature in demand_desc for feature in existing_lower)
            
            # 如果不相关，可能是一个功能缺口
            if not is_related and demand.demand_type == DemandType.NEW_FEATURE.value:
                # 提取可能的功能名称
                function_name = self._extract_potential_function_name(demand.description)
                
                gap = FeatureGap(
                    gap_name=f"缺失功能：{function_name}",
                    description=demand.description,
                    detected_from="demand_analysis",
                    severity="中",
                    priority=self._calculate_gap_priority(demand),
                    estimated_effort=self._estimate_effort(demand),
                    potential_impact=demand.confidence,
                    related_demands=[demand.id] if demand.id else [],
                    suggested_solutions=[f"实现{function_name}功能", f"集成现有解决方案"]
                )
                gaps.append(gap)
        
        return gaps
    
    def _identify_gaps_from_comparison(self, existing_features: List[str], comparison: Dict[str, Any]) -> List[FeatureGap]:
        """从外部对比中识别功能缺口"""
        gaps = []
        
        # 假设comparison包含其他系统的功能列表
        other_systems = comparison.get("other_systems", {})
        
        for system_name, features in other_systems.items():
            if isinstance(features, list):
                for feature in features:
                    # 检查该功能是否在现有功能中
                    if feature not in existing_features:
                        gap = FeatureGap(
                            gap_name=f"与{system_name}对比缺失：{feature}",
                            description=f"其他系统{system_name}具有{feature}功能，但本系统缺失",
                            detected_from="external_comparison",
                            severity="低",
                            priority=PriorityLevel.MEDIUM.value,
                            estimated_effort=8,  # 默认8小时
                            potential_impact=0.5,
                            suggested_solutions=[f"参考{system_name}实现{feature}", "寻找替代方案"]
                        )
                        gaps.append(gap)
        
        return gaps
    
    def _extract_potential_function_name(self, description: str) -> str:
        """从描述中提取可能的功能名称"""
        # 简单提取：取前几个词
        words = description.split()
        if len(words) >= 2:
            return " ".join(words[:2])
        return description[:20]
    
    def _calculate_gap_priority(self, demand: UserDemand) -> str:
        """计算功能缺口优先级"""
        # 基于需求频率和置信度计算优先级
        score = demand.confidence * 0.7 + min(demand.frequency / 100.0, 0.3)
        
        if score > 0.8:
            return PriorityLevel.HIGH.value
        elif score > 0.5:
            return PriorityLevel.MEDIUM.value
        else:
            return PriorityLevel.LOW.value
    
    def _estimate_effort(self, demand: UserDemand) -> int:
        """预估实现工作量（小时）"""
        # 基于需求类型和描述长度简单预估
        base_effort = {
            DemandType.NEW_FEATURE.value: 16,
            DemandType.PERFORMANCE_OPTIMIZATION.value: 8,
            DemandType.BUG_FIX.value: 4,
            DemandType.UX_IMPROVEMENT.value: 12,
            DemandType.INTEGRATION.value: 24,
            DemandType.DATA_ACCESS.value: 12,
            DemandType.TOOL_REQUEST.value: 20,
            DemandType.SKILL_REQUEST.value: 40,
            DemandType.OTHER.value: 8
        }
        
        effort = base_effort.get(demand.demand_type, 8)
        
        # 根据描述长度调整
        desc_len = len(demand.description)
        if desc_len > 100:
            effort *= 1.5
        elif desc_len > 200:
            effort *= 2.0
        
        return int(effort)
    
    def predict_demand_trends(self, 
                             historical_demands: List[UserDemand],
                             usage_trends: Dict[str, Any]) -> List[TrendPrediction]:
        """
        预测需求趋势
        
        Args:
            historical_demands: 历史需求数据
            usage_trends: 使用趋势数据
            
        Returns:
            趋势预测列表
        """
        trends = []
        
        # 分析需求类型趋势
        trends.extend(self._analyze_demand_type_trends(historical_demands))
        
        # 分析功能使用趋势
        trends.extend(self._analyze_usage_trends(usage_trends))
        
        # 保存到数据库
        for trend in trends:
            self._save_trend_prediction(trend)
        
        return trends
    
    def _analyze_demand_type_trends(self, demands: List[UserDemand]) -> List[TrendPrediction]:
        """分析需求类型趋势"""
        trends = []
        
        if not demands:
            return trends
        
        # 按需求类型分组
        type_counts = defaultdict(int)
        for demand in demands:
            type_counts[demand.demand_type] += demand.frequency
        
        # 找出增长最快的需求类型
        total_demands = sum(type_counts.values())
        if total_demands == 0:
            return trends
        
        # 计算比例
        for demand_type, count in type_counts.items():
            proportion = count / total_demands
            
            if proportion > 0.3:  # 占比超过30%
                trend = TrendPrediction(
                    trend_name=f"{demand_type}需求增长",
                    description=f"{demand_type}类需求占比{proportion*100:.1f}%，呈现增长趋势",
                    category="需求类型",
                    confidence=min(0.9, proportion),
                    timeframe="short",  # 短期趋势
                    expected_impact=f"需要加强{demand_type}相关能力建设",
                    supporting_evidence=[f"近期{demand_type}需求共{count}次"],
                    recommended_actions=[
                        f"优先处理{demand_type}相关需求",
                        f"储备{demand_type}相关技能和工具"
                    ]
                )
                trends.append(trend)
        
        return trends
    
    def _analyze_usage_trends(self, usage_trends: Dict[str, Any]) -> List[TrendPrediction]:
        """分析使用趋势"""
        trends = []
        
        # 检查是否有高频功能增长趋势
        top_functions = usage_trends.get("top_functions", [])
        
        for i, func_data in enumerate(top_functions[:3]):
            func_name = func_data.get("function_name", "")
            call_count = func_data.get("call_count", 0)
            
            if call_count > 100:
                trend = TrendPrediction(
                    trend_name=f"高频功能{func_name}持续使用",
                    description=f"功能'{func_name}'被高频使用（{call_count}次），用户依赖度高",
                    category="功能使用",
                    confidence=min(0.8, call_count / 200.0),
                    timeframe="medium",  # 中期趋势
                    expected_impact="需要确保该功能的稳定性和性能",
                    supporting_evidence=[f"近期调用{call_count}次"],
                    recommended_actions=[
                        f"优化{func_name}性能",
                        f"为{func_name}添加更多特性",
                        f"确保{func_name}高可用性"
                    ]
                )
                trends.append(trend)
        
        return trends
    
    def calculate_demand_priority(self, demands: List[UserDemand]) -> List[Tuple[UserDemand, str]]:
        """
        计算需求优先级
        
        Args:
            demands: 需求列表
            
        Returns:
            (需求, 优先级) 元组列表
        """
        prioritized = []
        
        for demand in demands:
            priority = self._calculate_individual_priority(demand)
            prioritized.append((demand, priority))
        
        # 按优先级排序
        priority_order = {
            PriorityLevel.CRITICAL.value: 0,
            PriorityLevel.HIGH.value: 1,
            PriorityLevel.MEDIUM.value: 2,
            PriorityLevel.LOW.value: 3
        }
        
        prioritized.sort(key=lambda x: priority_order.get(x[1], 4))
        
        return prioritized
    
    def _calculate_individual_priority(self, demand: UserDemand) -> str:
        """计算单个需求的优先级"""
        # 基于多个因素计算分数
        factors = []
        
        # 1. 置信度（权重0.3）
        factors.append(demand.confidence * 0.3)
        
        # 2. 频率（权重0.2）
        freq_score = min(demand.frequency / 50.0, 1.0)
        factors.append(freq_score * 0.2)
        
        # 3. 需求类型权重（权重0.3）
        type_weights = {
            DemandType.BUG_FIX.value: 1.0,
            DemandType.PERFORMANCE_OPTIMIZATION.value: 0.8,
            DemandType.NEW_FEATURE.value: 0.6,
            DemandType.UX_IMPROVEMENT.value: 0.5,
            DemandType.INTEGRATION.value: 0.7,
            DemandType.DATA_ACCESS.value: 0.6,
            DemandType.TOOL_REQUEST.value: 0.5,
            DemandType.SKILL_REQUEST.value: 0.4,
            DemandType.OTHER.value: 0.3
        }
        type_score = type_weights.get(demand.demand_type, 0.3)
        factors.append(type_score * 0.3)
        
        # 4. 时效性（权重0.2）
        if demand.last_detected:
            days_ago = (datetime.now() - demand.last_detected).days
            recency_score = max(0, 1.0 - days_ago / 30.0)  # 30天内线性衰减
            factors.append(recency_score * 0.2)
        else:
            factors.append(0.1)  # 默认值
        
        # 计算总分
        total_score = sum(factors)
        
        # 转换为优先级级别
        if total_score > 0.8:
            return PriorityLevel.CRITICAL.value
        elif total_score > 0.6:
            return PriorityLevel.HIGH.value
        elif total_score > 0.4:
            return PriorityLevel.MEDIUM.value
        else:
            return PriorityLevel.LOW.value
    
    def get_recommendations(self, 
                           demands: List[UserDemand],
                           gaps: List[FeatureGap],
                           trends: List[TrendPrediction]) -> Dict[str, Any]:
        """
        生成综合推荐
        
        Args:
            demands: 需求列表
            gaps: 功能缺口列表
            trends: 趋势预测列表
            
        Returns:
            推荐报告
        """
        recommendations = {
            "timestamp": datetime.now().isoformat(),
            "high_priority_demands": [],
            "critical_gaps": [],
            "immediate_actions": [],
            "strategic_recommendations": []
        }
        
        # 高优先级需求
        prioritized = self.calculate_demand_priority(demands)
        for demand, priority in prioritized[:5]:  # 前5个高优先级
            if priority in [PriorityLevel.CRITICAL.value, PriorityLevel.HIGH.value]:
                recommendations["high_priority_demands"].append({
                    "description": demand.description,
                    "type": demand.demand_type,
                    "priority": priority,
                    "confidence": demand.confidence
                })
        
        # 关键功能缺口
        for gap in gaps:
            if gap.priority in [PriorityLevel.CRITICAL.value, PriorityLevel.HIGH.value]:
                recommendations["critical_gaps"].append({
                    "name": gap.gap_name,
                    "description": gap.description,
                    "priority": gap.priority,
                    "impact": gap.potential_impact
                })
        
        # 立即行动
        if recommendations["high_priority_demands"]:
            for demand in recommendations["high_priority_demands"][:3]:
                recommendations["immediate_actions"].append(
                    f"处理{demand['type']}：{demand['description']}"
                )
        
        # 战略推荐
        for trend in trends[:3]:
            if trend.confidence > 0.7:
                recommendations["strategic_recommendations"].append({
                    "trend": trend.trend_name,
                    "description": trend.description,
                    "timeframe": trend.timeframe,
                    "actions": trend.recommended_actions
                })
        
        # 技能和工具推荐
        skill_demands = [d for d in demands if d.demand_type == DemandType.SKILL_REQUEST.value]
        tool_demands = [d for d in demands if d.demand_type == DemandType.TOOL_REQUEST.value]
        
        if skill_demands or tool_demands:
            recommendations["skill_tool_recommendations"] = {
                "skills_needed": [d.description for d in skill_demands[:3]],
                "tools_needed": [d.description for d in tool_demands[:3]],
                "recommendation": "建议搜索并集成相关技能和工具"
            }
        
        return recommendations
    
    def _save_demand_source(self, request_text: str, request_type: str, context: Dict[str, Any]):
        """保存需求来源"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO demand_sources 
            (request_text, request_type, timestamp, context, processed)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request_text,
            request_type,
            datetime.now().isoformat(),
            json.dumps(context, ensure_ascii=False),
            True
        ))
        
        conn.commit()
        conn.close()
    
    def _save_demand(self, demand: UserDemand) -> int:
        """保存需求到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查是否已存在类似需求
        cursor.execute("""
            SELECT id, frequency FROM user_demands 
            WHERE description LIKE ? AND demand_type = ?
        """, (f"%{demand.description[:30]}%", demand.demand_type))
        
        existing = cursor.fetchone()
        
        if existing:
            # 更新现有需求
            demand_id, current_freq = existing
            new_freq = current_freq + demand.frequency
            
            cursor.execute("""
                UPDATE user_demands SET
                frequency = ?,
                last_detected = ?,
                confidence = MAX(confidence, ?),
                context = ?
                WHERE id = ?
            """, (
                new_freq,
                demand.last_detected.isoformat(),
                demand.confidence,
                json.dumps(demand.context, ensure_ascii=False),
                demand_id
            ))
            
            demand.id = demand_id
        else:
            # 插入新需求
            cursor.execute("""
                INSERT INTO user_demands 
                (demand_type, description, source, confidence, frequency, 
                 first_detected, last_detected, user_feedback, context, related_functions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                demand.demand_type,
                demand.description,
                demand.source,
                demand.confidence,
                demand.frequency,
                demand.first_detected.isoformat(),
                demand.last_detected.isoformat(),
                demand.user_feedback,
                json.dumps(demand.context, ensure_ascii=False),
                json.dumps(demand.related_functions, ensure_ascii=False)
            ))
            
            demand.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return demand.id
    
    def _save_feature_gap(self, gap: FeatureGap) -> int:
        """保存功能缺口到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feature_gaps 
            (gap_name, description, detected_from, severity, priority,
             estimated_effort, potential_impact, related_demands, suggested_solutions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            gap.gap_name,
            gap.description,
            gap.detected_from,
            gap.severity,
            gap.priority,
            gap.estimated_effort,
            gap.potential_impact,
            json.dumps(gap.related_demands, ensure_ascii=False),
            json.dumps(gap.suggested_solutions, ensure_ascii=False)
        ))
        
        gap.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return gap.id
    
    def _save_trend_prediction(self, trend: TrendPrediction) -> int:
        """保存趋势预测到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trend_predictions 
            (trend_name, description, category, confidence, timeframe,
             expected_impact, supporting_evidence, recommended_actions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trend.trend_name,
            trend.description,
            trend.category,
            trend.confidence,
            trend.timeframe,
            trend.expected_impact,
            json.dumps(trend.supporting_evidence, ensure_ascii=False),
            json.dumps(trend.recommended_actions, ensure_ascii=False)
        ))
        
        trend.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return trend.id
    
    def get_analysis_report(self) -> Dict[str, Any]:
        """获取需求分析报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取需求统计
        cursor.execute("""
            SELECT demand_type, COUNT(*) as count, SUM(frequency) as total_freq
            FROM user_demands
            GROUP BY demand_type
            ORDER BY total_freq DESC
        """)
        demand_stats = cursor.fetchall()
        
        # 获取功能缺口统计
        cursor.execute("""
            SELECT priority, COUNT(*) as count
            FROM feature_gaps
            GROUP BY priority
            ORDER BY 
                CASE priority
                    WHEN '关键' THEN 0
                    WHEN '高' THEN 1
                    WHEN '中' THEN 2
                    WHEN '低' THEN 3
                    ELSE 4
                END
        """)
        gap_stats = cursor.fetchall()
        
        # 获取趋势预测
        cursor.execute("""
            SELECT trend_name, description, confidence, timeframe
            FROM trend_predictions
            WHERE confidence > 0.6
            ORDER BY confidence DESC
            LIMIT 5
        """)
        top_trends = cursor.fetchall()
        
        # 获取最新需求
        cursor.execute("""
            SELECT description, demand_type, confidence, last_detected
            FROM user_demands
            ORDER BY last_detected DESC
            LIMIT 10
        """)
        recent_demands = cursor.fetchall()
        
        conn.close()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "demand_statistics": [
                {
                    "type": demand_type,
                    "count": count,
                    "total_frequency": total_freq
                }
                for demand_type, count, total_freq in demand_stats
            ],
            "gap_statistics": [
                {
                    "priority": priority,
                    "count": count
                }
                for priority, count in gap_stats
            ],
            "top_trends": [
                {
                    "name": name,
                    "description": desc,
                    "confidence": confidence,
                    "timeframe": timeframe
                }
                for name, desc, confidence, timeframe in top_trends
            ],
            "recent_demands": [
                {
                    "description": desc,
                    "type": demand_type,
                    "confidence": confidence,
                    "last_detected": last_detected
                }
                for desc, demand_type, confidence, last_detected in recent_demands
            ]
        }