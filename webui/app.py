"""
自我进化系统可视化控制面板

基于Flask的Web界面，提供系统监控、性能分析和控制功能。

主要功能：
1. 系统状态监控：实时显示CPU、内存、磁盘使用率
2. 性能指标图表：可视化展示性能趋势
3. 警报管理：查看和确认系统警报
4. 进化控制：启动/停止进化任务
5. 数据报告：生成和查看性能报告

依赖：
- Flask: Web框架
- psutil: 系统监控（已在实时监控模块中使用）
- 可选：Chart.js用于前端图表
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from flask import Flask, render_template, jsonify, request, send_from_directory
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("错误: Flask未安装。请运行: pip install flask")
    sys.exit(1)

try:
    from core.evolution_controller import EvolutionController
    HAS_EVOLUTION = True
except ImportError as e:
    HAS_EVOLUTION = False
    print(f"错误: 无法导入进化控制器: {str(e)}")
    sys.exit(1)

# 创建Flask应用
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

# 全局控制器实例
_controller = None


def get_controller():
    """获取进化控制器实例"""
    global _controller
    if _controller is None:
        try:
            _controller = EvolutionController()
            # 尝试启动系统
            _controller.start()
        except Exception as e:
            print(f"警告: 无法初始化进化控制器: {str(e)}")
            _controller = None
    return _controller


@app.route('/')
def index():
    """主页面"""
    controller = get_controller()
    system_status = {
        "has_evolution": HAS_EVOLUTION,
        "controller_available": controller is not None,
        "is_running": controller.is_running if controller else False,
        "current_phase": controller.current_phase if controller else "未知",
        "timestamp": datetime.now().isoformat()
    }
    return render_template('index.html', system_status=system_status)


@app.route('/api/system/status')
def get_system_status():
    """获取系统状态API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        # 获取系统状态
        status = {
            "status": "成功",
            "is_running": controller.is_running,
            "current_phase": controller.current_phase,
            "last_heartbeat": controller.last_heartbeat.isoformat() if controller.last_heartbeat else None,
            "active_tasks": len(controller.task_queue),
            "completed_tasks": len(controller.completed_tasks),
            "timestamp": datetime.now().isoformat()
        }
        
        # 获取模块状态
        module_status = {
            "usage_tracker": controller.usage_tracker is not None,
            "demand_analyzer": controller.demand_analyzer is not None,
            "auto_optimizer": controller.auto_optimizer is not None,
            "auto_installer": controller.auto_installer is not None,
            "new_function_creator": controller.new_function_creator is not None,
            "ml_predictor": controller.ml_predictor is not None,
            "real_time_monitor": controller.real_time_monitor is not None
        }
        status["module_status"] = module_status
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取系统状态失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/monitoring/status')
def get_monitoring_status():
    """获取监控状态API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        if controller.real_time_monitor:
            status = controller.get_monitoring_status()
            return jsonify(status)
        else:
            return jsonify({
                "status": "成功",
                "monitoring_available": False,
                "message": "实时监控模块不可用",
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取监控状态失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/monitoring/current-metrics')
def get_current_metrics():
    """获取当前指标API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        metrics = controller.get_current_metrics()
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取当前指标失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/monitoring/performance-summary')
def get_performance_summary():
    """获取性能总结API"""
    minutes = request.args.get('minutes', default=5, type=int)
    
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        summary = controller.get_performance_summary(minutes)
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取性能总结失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/monitoring/alerts')
def get_alerts():
    """获取警报API"""
    severity = request.args.get('severity', default=None, type=str)
    acknowledged = request.args.get('acknowledged', default=None, type=str)
    hours = request.args.get('hours', default=24, type=int)
    
    # 转换acknowledged参数
    if acknowledged is not None:
        acknowledged = acknowledged.lower() == 'true'
    
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        alerts = controller.get_alerts(severity, acknowledged, hours)
        return jsonify(alerts)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取警报失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/monitoring/acknowledge-alert', methods=['POST'])
def acknowledge_alert():
    """确认警报API"""
    data = request.get_json()
    if not data or 'alert_id' not in data:
        return jsonify({
            "status": "错误",
            "message": "缺少alert_id参数",
            "timestamp": datetime.now().isoformat()
        })
    
    alert_id = data['alert_id']
    acknowledged_by = data.get('acknowledged_by', 'webui')
    
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        result = controller.acknowledge_alert(alert_id, acknowledged_by)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"确认警报失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/monitoring/metrics-report')
def get_metrics_report():
    """获取指标报告API"""
    metric_type = request.args.get('metric_type', default=None, type=str)
    hours = request.args.get('hours', default=1, type=int)
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        report = controller.get_metrics_report(metric_type, start_time, end_time)
        return jsonify(report)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取指标报告失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/ml/predictions')
def get_ml_predictions():
    """获取机器学习预测API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        user_id = request.args.get('user_id', default=None, type=str)
        context_str = request.args.get('context', default='{}', type=str)
        
        try:
            context = json.loads(context_str)
        except:
            context = {}
        
        top_n = request.args.get('top_n', default=5, type=int)
        
        predictions = controller.predict_next_function(user_id, context, top_n)
        return jsonify(predictions)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取预测失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/ml/stats')
def get_ml_stats():
    """获取机器学习统计API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        stats = controller.get_ml_stats()
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取机器学习统计失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/system/control/start', methods=['POST'])
def start_system():
    """启动系统API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        if controller.is_running:
            return jsonify({
                "status": "成功",
                "message": "系统已经在运行中",
                "is_running": True,
                "timestamp": datetime.now().isoformat()
            })
        
        success = controller.start()
        return jsonify({
            "status": "成功" if success else "错误",
            "message": "系统启动成功" if success else "系统启动失败",
            "is_running": success,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"系统启动失败: {str(e)}",
            "is_running": False,
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/system/control/stop', methods=['POST'])
def stop_system():
    """停止系统API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        if not controller.is_running:
            return jsonify({
                "status": "成功",
                "message": "系统已经停止",
                "is_running": False,
                "timestamp": datetime.now().isoformat()
            })
        
        success = controller.stop()
        return jsonify({
            "status": "成功" if success else "错误",
            "message": "系统停止成功" if success else "系统停止失败",
            "is_running": not success,  # 如果成功停止，则is_running为False
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"系统停止失败: {str(e)}",
            "is_running": controller.is_running if controller else False,
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/system/tasks')
def get_tasks():
    """获取任务列表API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        # 这里应该从数据库获取任务列表
        # 为简化，返回示例数据
        tasks = []
        return jsonify({
            "status": "成功",
            "tasks": tasks,
            "count": len(tasks),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取任务列表失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/static/<path:filename>')
def static_files(filename):
    """静态文件服务"""
    return send_from_directory(app.static_folder, filename)


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        "status": "错误",
        "message": "请求的资源不存在",
        "timestamp": datetime.now().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        "status": "错误",
        "message": "服务器内部错误",
        "timestamp": datetime.now().isoformat()
    }), 500


def main():
    """主函数"""
    print("=" * 60)
    print("自我进化系统可视化控制面板")
    print("=" * 60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Flask可用: {HAS_FLASK}")
    print(f"进化系统可用: {HAS_EVOLUTION}")
    
    if not HAS_FLASK:
        print("错误: Flask未安装。请运行: pip install flask")
        return 1
    
    if not HAS_EVOLUTION:
        print("警告: 进化系统模块不可用，部分功能受限")
    
    try:
        # 初始化控制器
        controller = get_controller()
        if controller:
            print(f"进化控制器初始化: {'成功' if controller else '失败'}")
            if controller.is_running:
                print("系统状态: 运行中")
            else:
                print("系统状态: 已停止")
        else:
            print("进化控制器初始化失败")
        
        # 启动Flask应用
        print("\n启动Web服务器...")
        print("控制面板地址: http://127.0.0.1:5001")
        print("按 Ctrl+C 停止服务器")
        
        # 在生产环境中应该使用更安全的设置
        app.run(host='127.0.0.1', port=5001, debug=True, threaded=True)
        
    except KeyboardInterrupt:
        print("\n接收到中断信号，正在停止服务器...")
        if controller and controller.is_running:
            controller.stop()
        print("服务器已停止")
        return 0
    except Exception as e:
        print(f"服务器启动失败: {str(e)}")
        return 1


# ==================== 反馈学习API端点 ====================

@app.route('/api/learning/feedback', methods=['POST'])
def record_learning_feedback():
    """记录学习反馈API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "错误",
                "message": "请求数据为空",
                "timestamp": datetime.now().isoformat()
            })
        
        trigger = data.get('trigger', 'user_correction')
        context = data.get('context', 'general')
        incorrect = data.get('incorrect', '')
        correct = data.get('correct', '')
        pattern_type = data.get('pattern_type', 'general')
        namespace = data.get('namespace', 'global')
        
        if not correct:
            return jsonify({
                "status": "错误",
                "message": "正确的行为描述不能为空",
                "timestamp": datetime.now().isoformat()
            })
        
        result = controller.record_user_feedback(
            trigger, context, incorrect, correct, pattern_type, namespace
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"记录反馈失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/learning/patterns')
def get_learning_patterns():
    """获取学习模式API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        namespace = request.args.get('namespace')
        stage = request.args.get('stage')
        limit = request.args.get('limit', 50, type=int)
        
        result = controller.get_learned_patterns(namespace, stage, limit)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取学习模式失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/learning/confirm-pattern', methods=['POST'])
def confirm_learning_pattern():
    """确认学习模式API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "错误",
                "message": "请求数据为空",
                "timestamp": datetime.now().isoformat()
            })
        
        pattern_key = data.get('pattern_key')
        namespace = data.get('namespace', 'global')
        always = data.get('always', True)
        context = data.get('context')
        
        if not pattern_key:
            return jsonify({
                "status": "错误",
                "message": "模式键不能为空",
                "timestamp": datetime.now().isoformat()
            })
        
        result = controller.confirm_pattern(pattern_key, namespace, always, context)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"确认模式失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/learning/recommendations')
def get_learning_recommendations():
    """获取学习推荐API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        context = request.args.get('context', '')
        namespace = request.args.get('namespace', 'global')
        
        result = controller.get_recommendations(context, namespace)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取推荐失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/learning/stats')
def get_learning_stats():
    """获取学习统计API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        result = controller.get_learning_stats()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"获取学习统计失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.route('/api/learning/export')
def export_learning_memory():
    """导出学习内存API"""
    controller = get_controller()
    if not controller:
        return jsonify({
            "status": "错误",
            "message": "进化控制器不可用",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        output_path = request.args.get('output_path')
        
        result = controller.export_learning_memory(output_path)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "错误",
            "message": f"导出学习内存失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


if __name__ == '__main__':
    sys.exit(main())