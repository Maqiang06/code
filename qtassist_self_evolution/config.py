"""
自我进化系统配置文件

提供系统配置管理功能，支持：
1. 默认配置
2. 环境变量覆盖
3. 配置文件加载
4. 运行时配置修改
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class DatabaseConfig:
    """数据库配置"""
    path: str = "data/evolution.db"
    pool_size: int = 5
    wal_mode: bool = True
    batch_size: int = 100
    flush_interval: int = 60  # 秒


@dataclass
class MonitoringConfig:
    """监控配置"""
    enabled: bool = True
    collection_interval: int = 60  # 秒
    metrics_retention_days: int = 30
    alert_enabled: bool = True
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    disk_threshold: float = 90.0


@dataclass
class MLConfig:
    """机器学习配置"""
    enabled: bool = True
    prediction_enabled: bool = True
    anomaly_detection_enabled: bool = True
    model_save_path: str = "models/"
    training_interval_hours: int = 24
    min_training_samples: int = 100


@dataclass
class WebUIConfig:
    """Web界面配置"""
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 5001
    debug: bool = False


@dataclass
class EvolutionConfig:
    """进化系统配置"""
    auto_optimize_enabled: bool = True
    auto_search_enabled: bool = True
    auto_create_enabled: bool = True
    optimization_interval_hours: int = 24
    search_interval_hours: int = 168  # 一周
    creation_interval_hours: int = 336  # 两周


@dataclass
class SystemConfig:
    """系统主配置"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    webui: WebUIConfig = field(default_factory=WebUIConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    
    # 系统全局设置
    log_level: str = "INFO"
    data_dir: str = "data/"
    logs_dir: str = "logs/"
    pid_file: str = "evolution.pid"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfig':
        """从字典创建配置"""
        # 处理嵌套配置
        db_data = data.get('database', {})
        monitoring_data = data.get('monitoring', {})
        ml_data = data.get('ml', {})
        webui_data = data.get('webui', {})
        evolution_data = data.get('evolution', {})
        
        return cls(
            database=DatabaseConfig(**db_data),
            monitoring=MonitoringConfig(**monitoring_data),
            ml=MLConfig(**ml_data),
            webui=WebUIConfig(**webui_data),
            evolution=EvolutionConfig(**evolution_data),
            log_level=data.get('log_level', 'INFO'),
            data_dir=data.get('data_dir', 'data/'),
            logs_dir=data.get('logs_dir', 'logs/'),
            pid_file=data.get('pid_file', 'evolution.pid')
        )


class ConfigManager:
    """配置管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = None
            cls._instance._config_paths = []
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._config = None
            self._config_paths = []
    
    def load(self, config_path: Optional[str] = None) -> SystemConfig:
        """加载配置"""
        # 默认配置
        default_config = SystemConfig()
        
        # 从环境变量加载
        env_config = self._load_from_env()
        
        # 从配置文件加载
        file_config = {}
        if config_path and os.path.exists(config_path):
            file_config = self._load_from_file(config_path)
        else:
            # 尝试默认配置文件路径
            default_paths = [
                "config.yaml",
                "config.yml", 
                "config.json",
                os.path.expanduser("~/.qtassist-evolution/config.yaml"),
                os.path.expanduser("~/.qtassist-evolution/config.json")
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    file_config = self._load_from_file(path)
                    self._config_paths.append(path)
                    break
        
        # 合并配置（优先级：文件 > 环境变量 > 默认）
        merged = default_config.to_dict()
        
        # 更新环境变量配置
        for key, value in env_config.items():
            self._update_nested(merged, key, value)
        
        # 更新文件配置
        for key, value in file_config.items():
            self._update_nested(merged, key, value)
        
        self._config = SystemConfig.from_dict(merged)
        return self._config
    
    def _load_from_env(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        env_config = {}
        
        # 数据库配置
        if os.getenv('EVOLUTION_DB_PATH'):
            env_config['database.path'] = os.getenv('EVOLUTION_DB_PATH')
        
        # WebUI配置
        if os.getenv('EVOLUTION_WEBUI_HOST'):
            env_config['webui.host'] = os.getenv('EVOLUTION_WEBUI_HOST')
        if os.getenv('EVOLUTION_WEBUI_PORT'):
            env_config['webui.port'] = int(os.getenv('EVOLUTION_WEBUI_PORT'))
        
        # 日志级别
        if os.getenv('EVOLUTION_LOG_LEVEL'):
            env_config['log_level'] = os.getenv('EVOLUTION_LOG_LEVEL')
        
        return env_config
    
    def _load_from_file(self, path: str) -> Dict[str, Any]:
        """从文件加载配置"""
        try:
            with open(path, 'r') as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    if HAS_YAML:
                        return yaml.safe_load(f) or {}
                    else:
                        print("警告: PyYAML未安装，无法加载YAML配置文件")
                        return {}
                elif path.endswith('.json'):
                    return json.load(f) or {}
                else:
                    # 尝试JSON，然后YAML
                    content = f.read()
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        if HAS_YAML:
                            return yaml.safe_load(content) or {}
                        else:
                            return {}
        except Exception as e:
            print(f"加载配置文件 {path} 失败: {str(e)}")
            return {}
    
    def _update_nested(self, config_dict: Dict[str, Any], key: str, value: Any):
        """更新嵌套字典配置"""
        keys = key.split('.')
        current = config_dict
        
        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get(self) -> SystemConfig:
        """获取当前配置"""
        if self._config is None:
            return self.load()
        return self._config
    
    def save(self, config: SystemConfig, path: str):
        """保存配置到文件"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        config_dict = config.to_dict()
        
        if path.endswith('.yaml') or path.endswith('.yml'):
            if HAS_YAML:
                with open(path, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False)
            else:
                raise RuntimeError("PyYAML未安装，无法保存YAML配置文件")
        elif path.endswith('.json'):
            with open(path, 'w') as f:
                json.dump(config_dict, f, indent=2)
        else:
            # 默认保存为JSON
            with open(path, 'w') as f:
                json.dump(config_dict, f, indent=2)
    
    def get_config_paths(self) -> List[str]:
        """获取已加载的配置文件路径"""
        return self._config_paths


# 全局配置管理器实例
config_manager = ConfigManager()

def get_config(config_path: Optional[str] = None) -> SystemConfig:
    """获取配置（简化接口）"""
    return config_manager.load(config_path)