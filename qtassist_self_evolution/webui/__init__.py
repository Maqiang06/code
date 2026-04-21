"""
自我进化系统Web界面模块

提供基于Flask的Web控制面板，用于可视化监控和控制自我进化系统。
"""

from .app import app, get_controller

__all__ = ["app", "get_controller"]