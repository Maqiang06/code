#!/usr/bin/env python3
"""
量化交易助手自我进化系统 - 命令行接口

提供系统启动、监控、控制和配置功能。
"""

import argparse
import sys
import os
import json
import time
import signal
from typing import Optional, Dict, Any

def main():
    """主命令行入口点"""
    parser = argparse.ArgumentParser(
        description="量化交易助手自我进化系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动Web控制面板
  qtassist-evolution web --port 5001
  
  # 启动后台服务
  qtassist-evolution start
  
  # 查看系统状态
  qtassist-evolution status
  
  # 手动触发进化
  qtassist-evolution evolve
  
  # 查看使用统计数据
  qtassist-evolution stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 启动Web控制面板
    web_parser = subparsers.add_parser('web', help='启动Web控制面板')
    web_parser.add_argument('--host', default='127.0.0.1', help='监听主机地址')
    web_parser.add_argument('--port', type=int, default=5001, help='监听端口')
    web_parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    # 启动后台服务
    start_parser = subparsers.add_parser('start', help='启动后台服务')
    start_parser.add_argument('--config', help='配置文件路径')
    start_parser.add_argument('--daemon', action='store_true', help='以守护进程方式运行')
    
    # 停止服务
    stop_parser = subparsers.add_parser('stop', help='停止后台服务')
    
    # 查看状态
    status_parser = subparsers.add_parser('status', help='查看系统状态')
    
    # 手动触发进化
    evolve_parser = subparsers.add_parser('evolve', help='手动触发进化')
    evolve_parser.add_argument('--module', choices=['all', 'optimizer', 'search', 'creator'], 
                              default='all', help='指定进化模块')
    
    # 查看统计数据
    stats_parser = subparsers.add_parser('stats', help='查看使用统计数据')
    
    # 查看配置
    config_parser = subparsers.add_parser('config', help='查看和修改配置')
    config_parser.add_argument('--show', action='store_true', help='显示当前配置')
    config_parser.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'), 
                              help='设置配置项')
    
    # 初始化系统
    init_parser = subparsers.add_parser('init', help='初始化系统')
    init_parser.add_argument('--reset', action='store_true', help='重置系统数据')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 根据命令执行相应操作
    try:
        if args.command == 'web':
            start_web_ui(args.host, args.port, args.debug)
        elif args.command == 'start':
            start_background_service(args.config, args.daemon)
        elif args.command == 'stop':
            stop_background_service()
        elif args.command == 'status':
            show_system_status()
        elif args.command == 'evolve':
            trigger_evolution(args.module)
        elif args.command == 'stats':
            show_statistics()
        elif args.command == 'config':
            handle_config(args.show, args.set)
        elif args.command == 'init':
            initialize_system(args.reset)
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)

def start_web_ui(host: str, port: int, debug: bool):
    """启动Web控制面板"""
    print(f"启动Web控制面板: http://{host}:{port}")
    print("按Ctrl+C停止服务器")
    
    try:
        from .webui.app import app
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    except ImportError as e:
        print(f"错误: 无法导入Web应用 - {str(e)}")
        print("请确保已安装Flask: pip install Flask")
        sys.exit(1)

def start_background_service(config_path: Optional[str], daemon: bool):
    """启动后台服务"""
    print("启动自我进化系统后台服务...")
    
    try:
        from . import start_system
        import threading
        
        # 加载配置
        config = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        # 启动系统
        controller = start_system(config)
        
        print("系统已启动")
        print(f"Web控制面板: http://127.0.0.1:5001")
        print("按Ctrl+C停止系统")
        
        if daemon:
            print("以守护进程方式运行...")
            # 在主线程中保持运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n正在停止系统...")
                controller.stop()
        else:
            # 等待用户中断
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n正在停止系统...")
                controller.stop()
                
    except ImportError as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

def stop_background_service():
    """停止后台服务"""
    print("停止后台服务...")
    # TODO: 实现PID文件检查和进程停止
    print("功能待实现")

def show_system_status():
    """显示系统状态"""
    try:
        from .core.real_time_monitor import get_global_monitor, _global_monitor
        
        # 重置全局监控器实例，确保使用最新代码
        global _global_monitor_reset
        if '_global_monitor_reset' not in globals():
            globals()['_global_monitor_reset'] = True
            import importlib
            import sys
            # 重新加载real_time_monitor模块
            if 'qtassist_self_evolution.core.real_time_monitor' in sys.modules:
                importlib.reload(sys.modules['qtassist_self_evolution.core.real_time_monitor'])
        
        # 强制重新创建监控器实例
        import sys
        if 'qtassist_self_evolution.core.real_time_monitor' in sys.modules:
            module = sys.modules['qtassist_self_evolution.core.real_time_monitor']
            module._global_monitor = None
        
        monitor = get_global_monitor()
        if monitor:
            # 检查是否有get_stats方法，如果没有则使用默认值
            if hasattr(monitor, 'get_stats'):
                stats = monitor.get_stats()
            else:
                # 使用默认值
                stats = {
                    "uptime": "未知",
                    "cpu_usage": {"current": 0, "avg": 0},
                    "memory_usage": {"current": 0, "avg": 0},
                    "disk_usage": {"current": 0, "avg": 0},
                    "active_alerts": 0
                }
            
            print("系统状态概览:")
            print(f"  运行时间: {stats.get('uptime', '未知')}")
            print(f"  CPU使用率: {stats.get('cpu_usage', {}).get('current', '未知')}%")
            print(f"  内存使用率: {stats.get('memory_usage', {}).get('current', '未知')}%")
            print(f"  磁盘使用率: {stats.get('disk_usage', {}).get('current', '未知')}%")
            print(f"  活跃警报: {stats.get('active_alerts', 0)}")
        else:
            print("监控模块未初始化")
    except Exception as e:
        print(f"无法获取系统状态: {str(e)}")

def trigger_evolution(module: str):
    """手动触发进化"""
    print(f"触发进化: {module}")
    # TODO: 实现进化触发
    print("功能待实现")

def show_statistics():
    """显示使用统计数据"""
    try:
        from .core.usage_tracker import get_global_tracker
        
        tracker = get_global_tracker()
        if tracker:
            stats = tracker.get_statistics()
            print("使用统计数据:")
            print(f"  总使用次数: {stats.get('total_usage_count', 0)}")
            print(f"  跟踪功能数: {stats.get('tracked_functions', 0)}")
            print(f"  高频功能: {stats.get('top_functions', [])}")
        else:
            print("使用跟踪器未初始化")
    except Exception as e:
        print(f"无法获取统计数据: {str(e)}")

def handle_config(show: bool, set_item: Optional[tuple]):
    """处理配置"""
    if show:
        print("当前配置:")
        # TODO: 显示配置
        print("功能待实现")
    
    if set_item:
        key, value = set_item
        print(f"设置配置项 {key}={value}")
        # TODO: 保存配置
        print("功能待实现")

def initialize_system(reset: bool):
    """初始化系统"""
    print("初始化自我进化系统...")
    if reset:
        print("警告: 将重置所有系统数据!")
        # TODO: 确认和重置
        print("功能待实现")
    else:
        # TODO: 初始化数据库和目录
        print("功能待实现")

if __name__ == '__main__':
    main()