"""
自动搜索安装模块

功能：自动搜索需要的skills、MCP、工具、库和其他模块，安装配置它们

主要功能：
1. 需求分析：分析系统缺失的功能和能力
2. 智能搜索：在多个来源搜索合适的工具和模块
3. 兼容性检查：检查与当前系统的兼容性
4. 自动安装：自动安装和配置发现的项目
5. 验证测试：验证安装结果和功能可用性
6. 文档记录：记录安装过程和配置信息

搜索来源：
1. Python包索引 (PyPI)
2. GitHub开源项目
3. MCP官方仓库
4. 技能市场
5. 工具社区
6. 其他模块仓库
"""

import json
import sqlite3
import time
import subprocess
import os
import sys
import re
import requests
import tempfile
import shutil
import importlib
import importlib.util
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from urllib.parse import urlparse, quote


class SearchSource(Enum):
    """搜索来源枚举"""
    PYPI = "PyPI"
    GITHUB = "GitHub"
    MCP = "MCP"
    SKILL = "Skill"
    TOOL = "Tool"
    OTHER = "其他"
    LOCAL = "本地"


class InstallationStatus(Enum):
    """安装状态枚举"""
    NOT_FOUND = "未找到"
    FOUND = "已找到"
    COMPATIBLE = "兼容"
    INCOMPATIBLE = "不兼容"
    INSTALLING = "安装中"
    INSTALLED = "已安装"
    FAILED = "安装失败"
    TESTED = "已测试"
    CONFIGURED = "已配置"


@dataclass
class SearchRequest:
    """搜索请求数据类"""
    id: Optional[int] = None
    request_text: str = ""
    search_terms: List[str] = None
    search_source: str = SearchSource.PYPI.value
    requested_at: datetime = None
    priority: int = 5  # 1-10，10为最高优先级
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.now()
        if self.search_terms is None:
            self.search_terms = []
        if self.context is None:
            self.context = {}


@dataclass
class SearchResult:
    """搜索结果数据类"""
    id: Optional[int] = None
    request_id: int = 0
    item_name: str = ""
    item_type: str = ""
    description: str = ""
    source: str = SearchSource.PYPI.value
    source_url: str = ""
    version: str = ""
    compatibility_score: float = 0.0  # 兼容性分数（0-1）
    popularity_score: float = 0.0  # 流行度分数（0-1）
    quality_score: float = 0.0  # 质量分数（0-1）
    found_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.found_at is None:
            self.found_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class InstallationPlan:
    """安装计划数据类"""
    id: Optional[int] = None
    result_id: int = 0
    item_name: str = ""
    item_type: str = ""
    installation_method: str = ""
    target_location: str = ""
    dependencies: List[str] = None
    prerequisites: List[str] = None
    estimated_time: int = 0  # 预估安装时间（秒）
    risk_level: str = "低"  # 风险级别：高、中、低
    rollback_plan: str = ""
    created_at: datetime = None
    status: str = InstallationStatus.FOUND.value
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []
        if self.prerequisites is None:
            self.prerequisites = []


@dataclass
class InstallationResult:
    """安装结果数据类"""
    id: Optional[int] = None
    plan_id: int = 0
    installation_time: datetime = None
    duration: float = 0.0  # 安装耗时（秒）
    status: str = InstallationStatus.INSTALLED.value
    log_output: str = ""
    error_messages: List[str] = None
    test_results: Dict[str, Any] = None
    configuration_details: Dict[str, Any] = None
    user_feedback: str = ""
    
    def __post_init__(self):
        if self.installation_time is None:
            self.installation_time = datetime.now()
        if self.error_messages is None:
            self.error_messages = []
        if self.test_results is None:
            self.test_results = {}
        if self.configuration_details is None:
            self.configuration_details = {}


class AutoSearchInstaller:
    """自动搜索安装器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化自动搜索安装器
        
        Args:
            db_path: SQLite数据库路径，如果为None则使用默认路径
        """
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "data", "auto_installation.db")
        
        self.db_path = db_path
        self._init_database()
        
        # 关键词映射表
        self._tool_keywords = {
            "数据分析": ["pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly"],
            "机器学习": ["scikit-learn", "tensorflow", "pytorch", "keras", "xgboost", "lightgbm"],
            "网络请求": ["requests", "httpx", "aiohttp", "urllib3"],
            "数据库": ["sqlalchemy", "sqlite3", "psycopg2", "pymysql", "redis", "mongodb"],
            "爬虫": ["scrapy", "beautifulsoup4", "selenium", "playwright"],
            "自动化": ["selenium", "playwright", "pyautogui", "robotframework"],
            "文档处理": ["pypdf2", "pdfminer", "docx", "openpyxl", "xlrd"],
            "图像处理": ["pillow", "opencv-python", "scikit-image"],
            "自然语言处理": ["nltk", "spacy", "transformers", "gensim"],
            "Web开发": ["flask", "django", "fastapi", "streamlit", "dash"],
            "金融分析": ["yfinance", "zipline", "backtrader", "quantlib", "ta-lib"],
            "任务调度": ["celery", "apscheduler", "schedule", "airflow"],
            "日志管理": ["loguru", "structlog", "logging"],
            "测试框架": ["pytest", "unittest", "nose2", "tox"],
            "部署工具": ["docker", "kubernetes", "ansible", "fabric"],
        }
        
        # 搜索API端点
        self._search_apis = {
            SearchSource.PYPI.value: "https://pypi.org/pypi/{package}/json",
            SearchSource.GITHUB.value: "https://api.github.com/search/repositories",
            SearchSource.MCP.value: "https://mcp-registry.example.com/search",  # 示例
            SearchSource.SKILL.value: "https://skills-marketplace.example.com/search",  # 示例
        }
        
        # 安装命令模板
        self._install_commands = {
            "pip": "pip install {package}",
            "pip_with_version": "pip install {package}=={version}",
            "git": "pip install git+{url}",
            "local": "pip install -e {path}",
            "apt": "sudo apt-get install {package}",
            "brew": "brew install {package}",
            "conda": "conda install {package}",
        }
        
        # 临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="auto_install_")
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def _init_database(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建搜索请求表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_text TEXT NOT NULL,
                search_terms TEXT NOT NULL,
                search_source TEXT NOT NULL,
                requested_at DATETIME,
                priority INTEGER,
                context TEXT
            )
        """)
        
        # 创建搜索结果表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                item_type TEXT NOT NULL,
                description TEXT,
                source TEXT NOT NULL,
                source_url TEXT,
                version TEXT,
                compatibility_score REAL,
                popularity_score REAL,
                quality_score REAL,
                found_at DATETIME,
                metadata TEXT,
                FOREIGN KEY (request_id) REFERENCES search_requests (id)
            )
        """)
        
        # 创建安装计划表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS installation_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                item_type TEXT NOT NULL,
                installation_method TEXT NOT NULL,
                target_location TEXT,
                dependencies TEXT,
                prerequisites TEXT,
                estimated_time INTEGER,
                risk_level TEXT NOT NULL,
                rollback_plan TEXT,
                created_at DATETIME,
                status TEXT NOT NULL,
                FOREIGN KEY (result_id) REFERENCES search_results (id)
            )
        """)
        
        # 创建安装结果表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS installation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                installation_time DATETIME,
                duration REAL,
                status TEXT NOT NULL,
                log_output TEXT,
                error_messages TEXT,
                test_results TEXT,
                configuration_details TEXT,
                user_feedback TEXT,
                FOREIGN KEY (plan_id) REFERENCES installation_plans (id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_priority ON search_requests(priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_requested ON search_requests(requested_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_request ON search_results(request_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_compatibility ON search_results(compatibility_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plans_status ON installation_plans(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_plan ON installation_results(plan_id)")
        
        conn.commit()
        conn.close()
    
    def analyze_demand(self, demand_text: str, context: Dict[str, Any] = None) -> SearchRequest:
        """
        分析需求，生成搜索请求
        
        Args:
            demand_text: 需求文本
            context: 上下文信息
            
        Returns:
            搜索请求
        """
        if context is None:
            context = {}
        
        # 提取关键词
        search_terms = self._extract_search_terms(demand_text)
        
        # 确定搜索来源
        search_source = self._determine_search_source(demand_text, context)
        
        # 确定优先级
        priority = self._determine_priority(demand_text, context)
        
        request = SearchRequest(
            request_text=demand_text,
            search_terms=search_terms,
            search_source=search_source,
            priority=priority,
            context=context
        )
        
        # 保存到数据库
        request_id = self._save_search_request(request)
        request.id = request_id
        
        return request
    
    def _extract_search_terms(self, text: str) -> List[str]:
        """从文本中提取搜索关键词"""
        terms = []
        
        # 转换为小写
        text_lower = text.lower()
        
        # 检查关键词映射
        for category, keywords in self._tool_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    terms.append(keyword)
                    break  # 每个类别只添加一个关键词
        
        # 如果没有找到映射关键词，使用文本中的名词
        if not terms:
            # 简单分词
            words = re.findall(r'\b\w+\b', text)
            # 过滤停用词和短词
            stop_words = {"的", "了", "和", "在", "是", "有", "我", "你", "他", "她", "它"}
            terms = [word for word in words if len(word) > 2 and word not in stop_words]
            terms = list(set(terms))[:5]  # 最多取5个
        
        return terms
    
    def _determine_search_source(self, text: str, context: Dict[str, Any]) -> str:
        """确定搜索来源"""
        text_lower = text.lower()
        
        # 根据关键词确定来源
        if any(word in text_lower for word in ["python", "pip", "pypi", "库", "包"]):
            return SearchSource.PYPI.value
        elif any(word in text_lower for word in ["github", "开源", "仓库", "代码"]):
            return SearchSource.GITHUB.value
        elif any(word in text_lower for word in ["mcp", "模型", "协议"]):
            return SearchSource.MCP.value
        elif any(word in text_lower for word in ["skill", "技能", "能力", "功能"]):
            return SearchSource.SKILL.value
        elif any(word in text_lower for word in ["工具", "软件", "应用", "程序"]):
            return SearchSource.TOOL.value
        else:
            return SearchSource.PYPI.value  # 默认
    
    def _determine_priority(self, text: str, context: Dict[str, Any]) -> int:
        """确定优先级"""
        # 基于文本和上下文确定优先级
        priority = 5  # 默认中等优先级
        
        text_lower = text.lower()
        
        # 根据关键词提高优先级
        urgency_words = ["紧急", "立即", "马上", "尽快", "重要", "必须", "需要", "必要"]
        for word in urgency_words:
            if word in text_lower:
                priority = min(10, priority + 3)
                break
        
        # 根据上下文调整优先级
        if context.get("is_critical", False):
            priority = 10
        elif context.get("is_important", False):
            priority = 8
        elif context.get("is_optional", False):
            priority = 3
        
        return priority
    
    def search_for_items(self, request: SearchRequest) -> List[SearchResult]:
        """
        搜索项目
        
        Args:
            request: 搜索请求
            
        Returns:
            搜索结果列表
        """
        results = []
        
        # 根据搜索来源执行搜索
        if request.search_source == SearchSource.PYPI.value:
            results.extend(self._search_pypi(request))
        elif request.search_source == SearchSource.GITHUB.value:
            results.extend(self._search_github(request))
        elif request.search_source == SearchSource.MCP.value:
            results.extend(self._search_mcp(request))
        elif request.search_source == SearchSource.SKILL.value:
            results.extend(self._search_skills(request))
        elif request.search_source == SearchSource.TOOL.value:
            results.extend(self._search_tools(request))
        elif request.search_source == SearchSource.LOCAL.value:
            results.extend(self._search_local(request))
        else:
            results.extend(self._search_general(request))
        
        # 保存结果到数据库
        for result in results:
            result.request_id = request.id
            result_id = self._save_search_result(result)
            result.id = result_id
        
        return results
    
    def _search_pypi(self, request: SearchRequest) -> List[SearchResult]:
        """搜索PyPI包"""
        results = []
        
        for term in request.search_terms:
            try:
                # 调用PyPI API
                url = f"https://pypi.org/pypi/{term}/json"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    result = SearchResult(
                        item_name=data.get("info", {}).get("name", term),
                        item_type="Python包",
                        description=data.get("info", {}).get("summary", ""),
                        source=SearchSource.PYPI.value,
                        source_url=data.get("info", {}).get("package_url", ""),
                        version=data.get("info", {}).get("version", ""),
                        compatibility_score=self._calculate_compatibility_score(data, "pypi"),
                        popularity_score=self._calculate_popularity_score(data, "pypi"),
                        quality_score=self._calculate_quality_score(data, "pypi"),
                        metadata={
                            "author": data.get("info", {}).get("author", ""),
                            "license": data.get("info", {}).get("license", ""),
                            "requires_python": data.get("info", {}).get("requires_python", ""),
                            "requires_dist": data.get("info", {}).get("requires_dist", []),
                            "project_urls": data.get("info", {}).get("project_urls", {}),
                        }
                    )
                    results.append(result)
                    
                else:
                    # 如果精确搜索失败，尝试搜索建议
                    search_url = f"https://pypi.org/search/?q={term}"
                    result = SearchResult(
                        item_name=term,
                        item_type="Python包",
                        description=f"搜索建议: {term}",
                        source=SearchSource.PYPI.value,
                        source_url=search_url,
                        compatibility_score=0.5,
                        popularity_score=0.3,
                        quality_score=0.4,
                        metadata={"search_suggestion": True}
                    )
                    results.append(result)
                    
            except Exception as e:
                # 创建错误结果
                result = SearchResult(
                    item_name=term,
                    item_type="Python包",
                    description=f"搜索失败: {str(e)[:100]}",
                    source=SearchSource.PYPI.value,
                    compatibility_score=0.0,
                    popularity_score=0.0,
                    quality_score=0.0,
                    metadata={"error": str(e)}
                )
                results.append(result)
        
        return results
    
    def _search_github(self, request: SearchRequest) -> List[SearchResult]:
        """搜索GitHub项目"""
        results = []
        
        for term in request.search_terms:
            try:
                # GitHub搜索API
                headers = {"Accept": "application/vnd.github.v3+json"}
                search_url = f"https://api.github.com/search/repositories?q={term}+language:python"
                response = requests.get(search_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("items"):
                        for item in data.get("items", [])[:3]:  # 取前3个结果
                            result = SearchResult(
                                item_name=item.get("name", term),
                                item_type="GitHub项目",
                                description=item.get("description", ""),
                                source=SearchSource.GITHUB.value,
                                source_url=item.get("html_url", ""),
                                version="latest",
                                compatibility_score=self._calculate_compatibility_score(item, "github"),
                                popularity_score=self._calculate_popularity_score(item, "github"),
                                quality_score=self._calculate_quality_score(item, "github"),
                                metadata={
                                    "owner": item.get("owner", {}).get("login", ""),
                                    "stars": item.get("stargazers_count", 0),
                                    "forks": item.get("forks_count", 0),
                                    "language": item.get("language", ""),
                                    "updated_at": item.get("updated_at", ""),
                                }
                            )
                            results.append(result)
                
            except Exception as e:
                # 创建错误结果
                result = SearchResult(
                    item_name=term,
                    item_type="GitHub项目",
                    description=f"搜索失败: {str(e)[:100]}",
                    source=SearchSource.GITHUB.value,
                    compatibility_score=0.0,
                    popularity_score=0.0,
                    quality_score=0.0,
                    metadata={"error": str(e)}
                )
                results.append(result)
        
        return results
    
    def _search_mcp(self, request: SearchRequest) -> List[SearchResult]:
        """搜索MCP项目"""
        results = []
        
        for term in request.search_terms:
            # 模拟MCP搜索
            result = SearchResult(
                item_name=f"mcp-{term}",
                item_type="MCP协议",
                description=f"与{term}相关的MCP协议",
                source=SearchSource.MCP.value,
                source_url=f"https://mcp-registry.example.com/{term}",
                version="1.0.0",
                compatibility_score=0.7,
                popularity_score=0.5,
                quality_score=0.6,
                metadata={
                    "protocol_type": "REST",
                    "version": "1.0.0",
                    "category": "general"
                }
            )
            results.append(result)
        
        return results
    
    def _search_skills(self, request: SearchRequest) -> List[SearchResult]:
        """搜索技能"""
        results = []
        
        for term in request.search_terms:
            # 模拟技能搜索
            result = SearchResult(
                item_name=f"skill-{term}",
                item_type="技能",
                description=f"实现{term}功能的技能",
                source=SearchSource.SKILL.value,
                source_url=f"https://skills-marketplace.example.com/{term}",
                version="1.0.0",
                compatibility_score=0.8,
                popularity_score=0.6,
                quality_score=0.7,
                metadata={
                    "skill_type": "general",
                    "compatibility": ["python>=3.8"],
                    "category": "utility"
                }
            )
            results.append(result)
        
        return results
    
    def _search_tools(self, request: SearchRequest) -> List[SearchResult]:
        """搜索工具"""
        results = []
        
        for term in request.search_terms:
            # 工具搜索
            result = SearchResult(
                item_name=f"tool-{term}",
                item_type="工具",
                description=f"用于{term}的工具",
                source=SearchSource.TOOL.value,
                source_url=f"https://tools-community.example.com/{term}",
                version="1.0.0",
                compatibility_score=0.6,
                popularity_score=0.4,
                quality_score=0.5,
                metadata={
                    "tool_type": "utility",
                    "platform": ["macos", "linux", "windows"],
                    "category": "general"
                }
            )
            results.append(result)
        
        return results
    
    def _search_local(self, request: SearchRequest) -> List[SearchResult]:
        """搜索本地项目"""
        results = []
        
        # 搜索本地Python包
        for term in request.search_terms:
            # 检查是否已安装
            try:
                spec = importlib.util.find_spec(term)
                if spec is not None:
                    result = SearchResult(
                        item_name=term,
                        item_type="本地Python包",
                        description=f"已安装的Python包: {term}",
                        source=SearchSource.LOCAL.value,
                        compatibility_score=1.0,
                        popularity_score=0.8,
                        quality_score=0.9,
                        metadata={
                            "location": spec.origin,
                            "is_installed": True
                        }
                    )
                    results.append(result)
            except Exception:
                pass
        
        return results
    
    def _search_general(self, request: SearchRequest) -> List[SearchResult]:
        """通用搜索"""
        results = []
        
        # 尝试多个来源
        pypi_results = self._search_pypi(request)
        github_results = self._search_github(request)
        
        results.extend(pypi_results)
        results.extend(github_results)
        
        return results
    
    def _calculate_compatibility_score(self, item_data: Dict[str, Any], source: str) -> float:
        """计算兼容性分数"""
        score = 0.5  # 基础分数
        
        if source == "pypi":
            # 检查Python版本要求
            requires_python = item_data.get("info", {}).get("requires_python", "")
            if requires_python:
                # 简化版本检查
                current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
                if ">=" in requires_python or "==" in requires_python:
                    score = min(1.0, score + 0.3)
            
            # 检查依赖兼容性
            requires_dist = item_data.get("info", {}).get("requires_dist", [])
            if requires_dist:
                # 简化检查：依赖越多，兼容性风险越高
                dependency_count = len(requires_dist)
                dependency_penalty = min(0.3, dependency_count * 0.01)
                score = max(0.0, score - dependency_penalty)
        
        elif source == "github":
            # 检查主要语言
            language = item_data.get("language", "")
            if language and language.lower() == "python":
                score = min(1.0, score + 0.3)
            
            # 检查最近更新
            updated_at = item_data.get("updated_at", "")
            if updated_at:
                try:
                    from dateutil.parser import parse
                    last_update = parse(updated_at)
                    days_since_update = (datetime.now() - last_update).days
                    if days_since_update < 365:  # 一年内有更新
                        score = min(1.0, score + 0.2)
                except Exception:
                    pass
        
        return score
    
    def _calculate_popularity_score(self, item_data: Dict[str, Any], source: str) -> float:
        """计算流行度分数"""
        score = 0.3  # 基础分数
        
        if source == "pypi":
            # PyPI的下载量等信息通常不可直接获取
            # 使用项目URL数量作为代理指标
            project_urls = item_data.get("info", {}).get("project_urls", {})
            url_count = len(project_urls) if project_urls else 0
            score = min(1.0, score + (url_count * 0.05))
        
        elif source == "github":
            # GitHub的star和fork数
            stars = item_data.get("stargazers_count", 0)
            forks = item_data.get("forks_count", 0)
            
            # 归一化处理
            star_score = min(1.0, stars / 10000) * 0.5
            fork_score = min(1.0, forks / 2000) * 0.3
            
            score = min(1.0, score + star_score + fork_score)
        
        return score
    
    def _calculate_quality_score(self, item_data: Dict[str, Any], source: str) -> float:
        """计算质量分数"""
        score = 0.4  # 基础分数
        
        if source == "pypi":
            # 检查是否有文档、许可证等
            has_docs = bool(item_data.get("info", {}).get("docs_url", ""))
            has_bug_tracker = bool(item_data.get("info", {}).get("bugtrack_url", ""))
            has_homepage = bool(item_data.get("info", {}).get("home_page", ""))
            has_license = bool(item_data.get("info", {}).get("license", ""))
            
            quality_indicators = [has_docs, has_bug_tracker, has_homepage, has_license]
            indicator_count = sum(quality_indicators)
            score = min(1.0, score + (indicator_count * 0.15))
        
        elif source == "github":
            # 检查是否有描述、README等
            has_description = bool(item_data.get("description", ""))
            has_homepage = bool(item_data.get("homepage", ""))
            has_license = bool(item_data.get("license", {}).get("name", ""))
            is_fork = item_data.get("fork", False)
            
            if has_description:
                score += 0.2
            if has_homepage:
                score += 0.1
            if has_license:
                score += 0.15
            if not is_fork:
                score += 0.1
            
            score = min(1.0, score)
        
        return score
    
    def create_installation_plans(self, results: List[SearchResult]) -> List[InstallationPlan]:
        """
        创建安装计划
        
        Args:
            results: 搜索结果列表
            
        Returns:
            安装计划列表
        """
        plans = []
        
        for result in results:
            # 过滤低质量结果
            if result.compatibility_score < 0.3 or result.quality_score < 0.3:
                continue
            
            plan = self._create_plan_for_result(result)
            if plan:
                plans.append(plan)
        
        # 保存计划到数据库
        for plan in plans:
            plan_id = self._save_installation_plan(plan)
            plan.id = plan_id
        
        return plans
    
    def _create_plan_for_result(self, result: SearchResult) -> Optional[InstallationPlan]:
        """为搜索结果创建安装计划"""
        if result.source == SearchSource.PYPI.value:
            return self._create_pypi_installation_plan(result)
        elif result.source == SearchSource.GITHUB.value:
            return self._create_github_installation_plan(result)
        elif result.source == SearchSource.MCP.value:
            return self._create_mcp_installation_plan(result)
        elif result.source == SearchSource.SKILL.value:
            return self._create_skill_installation_plan(result)
        elif result.source == SearchSource.TOOL.value:
            return self._create_tool_installation_plan(result)
        elif result.source == SearchSource.LOCAL.value:
            return self._create_local_installation_plan(result)
        
        return None
    
    def _create_pypi_installation_plan(self, result: SearchResult) -> InstallationPlan:
        """创建PyPI包安装计划"""
        return InstallationPlan(
            result_id=result.id,
            item_name=result.item_name,
            item_type=result.item_type,
            installation_method="pip",
            target_location=f"Python包: {result.item_name}",
            dependencies=result.metadata.get("requires_dist", []) if isinstance(result.metadata.get("requires_dist"), list) else [],
            prerequisites=["Python环境", "pip工具"],
            estimated_time=30,  # 30秒
            risk_level="低",
            rollback_plan=f"pip uninstall {result.item_name} -y",
            status=InstallationStatus.FOUND.value
        )
    
    def _create_github_installation_plan(self, result: SearchResult) -> InstallationPlan:
        """创建GitHub项目安装计划"""
        return InstallationPlan(
            result_id=result.id,
            item_name=result.item_name,
            item_type=result.item_type,
            installation_method="git",
            target_location=self.temp_dir,
            dependencies=[],
            prerequisites=["Git工具", "Python环境"],
            estimated_time=120,  # 2分钟
            risk_level="中",
            rollback_plan=f"rm -rf {os.path.join(self.temp_dir, result.item_name)}",
            status=InstallationStatus.FOUND.value
        )
    
    def _create_mcp_installation_plan(self, result: SearchResult) -> InstallationPlan:
        """创建MCP安装计划"""
        return InstallationPlan(
            result_id=result.id,
            item_name=result.item_name,
            item_type=result.item_type,
            installation_method="custom",
            target_location=f"MCP协议: {result.item_name}",
            dependencies=[],
            prerequisites=["MCP客户端"],
            estimated_time=60,  # 1分钟
            risk_level="中",
            rollback_plan="移除MCP配置",
            status=InstallationStatus.FOUND.value
        )
    
    def _create_skill_installation_plan(self, result: SearchResult) -> InstallationPlan:
        """创建技能安装计划"""
        return InstallationPlan(
            result_id=result.id,
            item_name=result.item_name,
            item_type=result.item_type,
            installation_method="custom",
            target_location=f"技能: {result.item_name}",
            dependencies=[],
            prerequisites=["技能执行环境"],
            estimated_time=45,  # 45秒
            risk_level="低",
            rollback_plan="移除技能配置",
            status=InstallationStatus.FOUND.value
        )
    
    def _create_tool_installation_plan(self, result: SearchResult) -> InstallationPlan:
        """创建工具安装计划"""
        return InstallationPlan(
            result_id=result.id,
            item_name=result.item_name,
            item_type=result.item_type,
            installation_method="system",
            target_location=f"系统工具: {result.item_name}",
            dependencies=[],
            prerequisites=["系统包管理器"],
            estimated_time=90,  # 1.5分钟
            risk_level="中",
            rollback_plan="系统包管理器卸载",
            status=InstallationStatus.FOUND.value
        )
    
    def _create_local_installation_plan(self, result: SearchResult) -> InstallationPlan:
        """创建本地安装计划"""
        return InstallationPlan(
            result_id=result.id,
            item_name=result.item_name,
            item_type=result.item_type,
            installation_method="local",
            target_location=result.metadata.get("location", ""),
            dependencies=[],
            prerequisites=[],
            estimated_time=0,  # 已安装
            risk_level="低",
            rollback_plan="无需回滚，已安装",
            status=InstallationStatus.INSTALLED.value
        )
    
    def execute_installation(self, plan: InstallationPlan) -> InstallationResult:
        """
        执行安装
        
        Args:
            plan: 安装计划
            
        Returns:
            安装结果
        """
        start_time = time.time()
        logs = []
        errors = []
        
        try:
            # 更新计划状态
            plan.status = InstallationStatus.INSTALLING.value
            self._update_plan_status(plan.id, plan.status)
            
            logs.append(f"开始安装: {plan.item_name}")
            logs.append(f"安装类型: {plan.item_type}")
            logs.append(f"安装方法: {plan.installation_method}")
            
            # 执行安装
            if plan.installation_method == "pip":
                result = self._install_pip_package(plan, logs, errors)
            elif plan.installation_method == "git":
                result = self._install_git_repository(plan, logs, errors)
            elif plan.installation_method == "local":
                result = self._install_local_package(plan, logs, errors)
            elif plan.installation_method == "system":
                result = self._install_system_package(plan, logs, errors)
            elif plan.installation_method == "custom":
                result = self._install_custom_item(plan, logs, errors)
            else:
                result = self._install_general_item(plan, logs, errors)
            
            # 测试安装结果
            test_results = self._test_installation(plan)
            
            # 记录配置详情
            config_details = self._record_configuration(plan)
            
            # 计算安装耗时
            installation_time = time.time() - start_time
            
            # 创建结果对象
            result = InstallationResult(
                plan_id=plan.id,
                duration=installation_time,
                status=InstallationStatus.INSTALLED.value if not errors else InstallationStatus.FAILED.value,
                log_output="\n".join(logs),
                error_messages=errors,
                test_results=test_results,
                configuration_details=config_details
            )
            
            # 更新计划状态
            plan.status = result.status
            self._update_plan_status(plan.id, plan.status)
            
            logs.append(f"安装完成，耗时{installation_time:.2f}秒")
            
        except Exception as e:
            # 安装失败
            installation_time = time.time() - start_time
            logs.append(f"安装失败: {str(e)}")
            errors.append(str(e))
            
            result = InstallationResult(
                plan_id=plan.id,
                duration=installation_time,
                status=InstallationStatus.FAILED.value,
                log_output="\n".join(logs),
                error_messages=errors
            )
            
            # 更新计划状态
            plan.status = InstallationStatus.FAILED.value
            self._update_plan_status(plan.id, plan.status)
            
            # 尝试回滚
            try:
                self._rollback_installation(plan, logs)
            except Exception as rollback_error:
                logs.append(f"回滚失败: {str(rollback_error)}")
        
        # 保存结果
        result_id = self._save_installation_result(result)
        result.id = result_id
        
        return result
    
    def _install_pip_package(self, plan: InstallationPlan, logs: List[str], errors: List[str]) -> bool:
        """安装PyPI包"""
        try:
            command = f"pip install {plan.item_name}"
            logs.append(f"执行命令: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            logs.append(f"标准输出: {result.stdout[:500]}")
            if result.stderr:
                logs.append(f"标准错误: {result.stderr[:500]}")
            
            if result.returncode == 0:
                logs.append(f"包 {plan.item_name} 安装成功")
                return True
            else:
                errors.append(f"包安装失败，返回码: {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            errors.append(f"安装超时: {plan.item_name}")
            return False
        except Exception as e:
            errors.append(f"安装异常: {str(e)}")
            return False
    
    def _install_git_repository(self, plan: InstallationPlan, logs: List[str], errors: List[str]) -> bool:
        """安装Git仓库"""
        try:
            # 这里需要实际的Git仓库URL，简化版本
            repo_url = f"https://github.com/example/{plan.item_name}.git"
            target_dir = os.path.join(self.temp_dir, plan.item_name)
            
            # 克隆仓库
            clone_cmd = f"git clone {repo_url} {target_dir}"
            logs.append(f"执行命令: {clone_cmd}")
            
            result = subprocess.run(
                clone_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0:
                logs.append(f"仓库克隆成功: {plan.item_name}")
                
                # 尝试安装
                install_cmd = f"pip install -e {target_dir}"
                logs.append(f"执行命令: {install_cmd}")
                
                install_result = subprocess.run(
                    install_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if install_result.returncode == 0:
                    logs.append(f"Git仓库安装成功: {plan.item_name}")
                    return True
                else:
                    errors.append(f"Git仓库安装失败: {install_result.stderr[:500]}")
                    return False
            else:
                errors.append(f"仓库克隆失败: {result.stderr[:500]}")
                return False
                
        except Exception as e:
            errors.append(f"Git仓库安装异常: {str(e)}")
            return False
    
    def _install_local_package(self, plan: InstallationPlan, logs: List[str], errors: List[str]) -> bool:
        """安装本地包"""
        logs.append(f"本地包已安装: {plan.item_name}")
        return True  # 本地包视为已安装
    
    def _install_system_package(self, plan: InstallationPlan, logs: List[str], errors: List[str]) -> bool:
        """安装系统包"""
        try:
            # 根据系统选择包管理器
            if sys.platform.startswith("linux"):
                command = f"sudo apt-get install -y {plan.item_name}"
            elif sys.platform == "darwin":  # macOS
                command = f"brew install {plan.item_name}"
            else:
                command = f"echo '不支持的系统: {sys.platform}'"
                errors.append(f"不支持的系统: {sys.platform}")
                return False
            
            logs.append(f"执行命令: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logs.append(f"系统包安装成功: {plan.item_name}")
                return True
            else:
                errors.append(f"系统包安装失败: {result.stderr[:500]}")
                return False
                
        except Exception as e:
            errors.append(f"系统包安装异常: {str(e)}")
            return False
    
    def _install_custom_item(self, plan: InstallationPlan, logs: List[str], errors: List[str]) -> bool:
        """安装自定义项目"""
        logs.append(f"自定义安装: {plan.item_name}")
        logs.append("执行自定义安装逻辑...")
        
        # 模拟安装成功
        logs.append("自定义项目安装完成")
        return True
    
    def _install_general_item(self, plan: InstallationPlan, logs: List[str], errors: List[str]) -> bool:
        """通用安装"""
        logs.append(f"通用安装: {plan.item_name}")
        
        # 尝试使用pip安装
        return self._install_pip_package(plan, logs, errors)
    
    def _test_installation(self, plan: InstallationPlan) -> Dict[str, Any]:
        """测试安装结果"""
        test_results = {}
        
        try:
            # 尝试导入包
            if plan.installation_method in ["pip", "git", "local"]:
                spec = importlib.util.find_spec(plan.item_name)
                if spec is not None:
                    test_results["import_test"] = "通过"
                    test_results["location"] = spec.origin
                else:
                    test_results["import_test"] = "失败"
            
            # 检查版本
            test_results["version_check"] = "待实现"
            
            # 功能测试
            test_results["function_test"] = "待实现"
            
        except Exception as e:
            test_results["error"] = str(e)
        
        return test_results
    
    def _record_configuration(self, plan: InstallationPlan) -> Dict[str, Any]:
        """记录配置详情"""
        config_details = {
            "item_name": plan.item_name,
            "item_type": plan.item_type,
            "installation_method": plan.installation_method,
            "target_location": plan.target_location,
            "installed_at": datetime.now().isoformat(),
            "system_info": {
                "platform": sys.platform,
                "python_version": sys.version,
                "python_executable": sys.executable
            }
        }
        
        return config_details
    
    def _rollback_installation(self, plan: InstallationPlan, logs: List[str]):
        """回滚安装"""
        logs.append(f"开始回滚安装: {plan.item_name}")
        
        try:
            if plan.installation_method == "pip":
                command = f"pip uninstall {plan.item_name} -y"
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    logs.append(f"包卸载成功: {plan.item_name}")
                else:
                    logs.append(f"包卸载失败: {result.stderr[:500]}")
            
            elif plan.installation_method == "git":
                target_dir = os.path.join(self.temp_dir, plan.item_name)
                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                    logs.append(f"删除Git仓库: {target_dir}")
            
            logs.append("回滚完成")
            
        except Exception as e:
            logs.append(f"回滚异常: {str(e)}")
    
    def _save_search_request(self, request: SearchRequest) -> int:
        """保存搜索请求到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO search_requests 
            (request_text, search_terms, search_source, requested_at, priority, context)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.request_text,
            json.dumps(request.search_terms, ensure_ascii=False),
            request.search_source,
            request.requested_at.isoformat(),
            request.priority,
            json.dumps(request.context, ensure_ascii=False)
        ))
        
        request_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return request_id
    
    def _save_search_result(self, result: SearchResult) -> int:
        """保存搜索结果到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO search_results 
            (request_id, item_name, item_type, description, source, source_url,
             version, compatibility_score, popularity_score, quality_score,
             found_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.request_id,
            result.item_name,
            result.item_type,
            result.description,
            result.source,
            result.source_url,
            result.version,
            result.compatibility_score,
            result.popularity_score,
            result.quality_score,
            result.found_at.isoformat(),
            json.dumps(result.metadata, ensure_ascii=False)
        ))
        
        result_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return result_id
    
    def _save_installation_plan(self, plan: InstallationPlan) -> int:
        """保存安装计划到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO installation_plans 
            (result_id, item_name, item_type, installation_method, target_location,
             dependencies, prerequisites, estimated_time, risk_level, rollback_plan,
             created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan.result_id,
            plan.item_name,
            plan.item_type,
            plan.installation_method,
            plan.target_location,
            json.dumps(plan.dependencies, ensure_ascii=False),
            json.dumps(plan.prerequisites, ensure_ascii=False),
            plan.estimated_time,
            plan.risk_level,
            plan.rollback_plan,
            plan.created_at.isoformat(),
            plan.status
        ))
        
        plan_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return plan_id
    
    def _update_plan_status(self, plan_id: int, status: str):
        """更新安装计划状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE installation_plans SET status = ? WHERE id = ?
        """, (status, plan_id))
        
        conn.commit()
        conn.close()
    
    def _save_installation_result(self, result: InstallationResult) -> int:
        """保存安装结果到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO installation_results 
            (plan_id, installation_time, duration, status, log_output,
             error_messages, test_results, configuration_details, user_feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.plan_id,
            result.installation_time.isoformat(),
            result.duration,
            result.status,
            result.log_output,
            json.dumps(result.error_messages, ensure_ascii=False),
            json.dumps(result.test_results, ensure_ascii=False),
            json.dumps(result.configuration_details, ensure_ascii=False),
            result.user_feedback
        ))
        
        result_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return result_id
    
    def get_installation_summary(self) -> Dict[str, Any]:
        """获取安装汇总信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取搜索请求统计
        cursor.execute("""
            SELECT COUNT(*) as total_requests
            FROM search_requests
        """)
        request_stats = cursor.fetchone()
        
        # 获取搜索结果统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total_results,
                AVG(compatibility_score) as avg_compatibility,
                AVG(quality_score) as avg_quality
            FROM search_results
        """)
        result_stats = cursor.fetchone()
        
        # 获取安装计划统计
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM installation_plans
            GROUP BY status
        """)
        plan_stats = cursor.fetchall()
        
        # 获取安装结果统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total_installations,
                SUM(CASE WHEN status = '已安装' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = '安装失败' THEN 1 ELSE 0 END) as failed,
                AVG(duration) as avg_duration
            FROM installation_results
        """)
        installation_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "search_statistics": {
                "total_requests": request_stats[0] if request_stats else 0,
                "total_results": result_stats[0] if result_stats else 0,
                "avg_compatibility": result_stats[1] if result_stats else 0.0,
                "avg_quality": result_stats[2] if result_stats else 0.0
            },
            "plan_statistics": [
                {"status": status, "count": count}
                for status, count in plan_stats
            ],
            "installation_statistics": {
                "total_installations": installation_stats[0] if installation_stats else 0,
                "successful": installation_stats[1] if installation_stats else 0,
                "failed": installation_stats[2] if installation_stats else 0,
                "avg_duration": installation_stats[3] if installation_stats else 0.0
            }
        }
    
    def process_demand(self, demand_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理需求：分析、搜索、安装
        
        Args:
            demand_text: 需求文本
            context: 上下文信息
            
        Returns:
            处理结果
        """
        if context is None:
            context = {}
        
        result = {
            "demand_text": demand_text,
            "context": context,
            "steps": [],
            "success": False
        }
        
        try:
            # 步骤1: 分析需求
            result["steps"].append("分析需求")
            search_request = self.analyze_demand(demand_text, context)
            result["search_request"] = asdict(search_request)
            
            # 步骤2: 搜索项目
            result["steps"].append("搜索项目")
            search_results = self.search_for_items(search_request)
            result["search_results"] = [asdict(r) for r in search_results]
            
            if not search_results:
                result["steps"].append("未找到合适项目")
                return result
            
            # 步骤3: 创建安装计划
            result["steps"].append("创建安装计划")
            installation_plans = self.create_installation_plans(search_results)
            result["installation_plans"] = [asdict(p) for p in installation_plans]
            
            if not installation_plans:
                result["steps"].append("无合适的安装计划")
                return result
            
            # 步骤4: 执行安装
            result["steps"].append("执行安装")
            installation_results = []
            
            for plan in installation_plans:
                if plan.status == InstallationStatus.FOUND.value:
                    installation_result = self.execute_installation(plan)
                    installation_results.append(installation_result)
            
            result["installation_results"] = [asdict(r) for r in installation_results]
            
            # 检查是否至少有一个安装成功
            successful_installations = [
                r for r in installation_results 
                if r.status == InstallationStatus.INSTALLED.value
            ]
            
            if successful_installations:
                result["success"] = True
                result["steps"].append("安装完成")
            else:
                result["steps"].append("安装失败")
            
        except Exception as e:
            result["steps"].append(f"处理异常: {str(e)}")
            result["error"] = str(e)
        
        return result
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                return True
        except Exception as e:
            return False
        
        return True
    
    def __del__(self):
        """析构函数：清理资源"""
        self.cleanup_temp_files()