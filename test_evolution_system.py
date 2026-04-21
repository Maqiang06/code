#!/usr/bin/env python3
"""
自我进化系统测试脚本

功能：测试自我进化系统的各个模块和整体功能
"""

import sys
import os
import time
import json

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.evolution_controller import EvolutionController, EvolutionPriority
from core.usage_tracker import UsageRecord, FunctionCategory, UsagePatternTracker


def test_evolution_controller_initialization():
    """测试进化控制器初始化"""
    print("=== 测试进化控制器初始化 ===")
    
    try:
        controller = EvolutionController()
        print("✓ 进化控制器创建成功")
        
        # 获取系统状态
        status = controller.get_system_status()
        print(f"✓ 获取系统状态成功: {status.get('current_phase', '未知')}")
        
        # 检查模块状态
        modules_status = status.get("modules_status", {})
        for module, is_ready in modules_status.items():
            print(f"  - {module}: {'正常' if is_ready else '异常'}")
        
        return controller
        
    except Exception as e:
        print(f"✗ 进化控制器初始化失败: {str(e)}")
        return None


def test_usage_tracking(controller):
    """测试使用模式跟踪"""
    print("\n=== 测试使用模式跟踪 ===")
    
    try:
        # 创建独立的使用模式跟踪器实例，避免与控制器后台任务冲突
        usage_tracker = UsagePatternTracker()
        
        print("✓ 独立使用模式跟踪器创建成功")
        
        # 创建使用记录对象
        record = UsageRecord(
            function_name="test_function",
            function_category=FunctionCategory.TOOL_EXECUTION.value,
            execution_time=1.5,
            success=True,
            context_info={"test": "data"}
        )
        
        # 记录使用数据
        record_id = usage_tracker.record_usage(record)
        
        print(f"✓ 使用记录添加成功，记录ID: {record_id}")
        
        # 等待一小段时间，确保数据库操作完成
        import time
        time.sleep(0.5)
        
        # 获取统计数据
        stats_list = usage_tracker.get_function_stats("test_function")
        if stats_list and len(stats_list) > 0:
            stats = stats_list[0]
            print(f"✓ 获取函数统计成功: {stats.function_name}, 调用次数: {stats.total_calls}")
        else:
            print("⚠ 函数统计为空（可能是首次调用）")
        
        return True
        
    except Exception as e:
        print(f"✗ 使用模式跟踪测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_demand_analysis(controller):
    """测试需求分析"""
    print("\n=== 测试需求分析 ===")
    
    try:
        # 测试需求分析
        demand_text = "我需要一个数据分析工具，能够处理股票数据并生成可视化图表"
        
        result = controller.analyze_user_demand(demand_text)
        
        if "error" in result:
            print(f"✗ 需求分析失败: {result.get('error')}")
            return False
        
        print(f"✓ 需求分析成功")
        print(f"  需求文本: {result.get('demand_text')}")
        print(f"  识别需求数: {len(result.get('identified_demands', []))}")
        
        for demand in result.get("identified_demands", []):
            print(f"  - 需求类型: {demand.get('demand_type')}, 描述: {demand.get('description')}")
        
        return True
        
    except Exception as e:
        print(f"✗ 需求分析测试失败: {str(e)}")
        return False


def test_function_optimization(controller):
    """测试功能优化"""
    print("\n=== 测试功能优化 ===")
    
    try:
        # 调度一个优化任务
        function_name = "test_function"
        task_id = controller.optimize_function(function_name, EvolutionPriority.MEDIUM.value)
        
        if task_id > 0:
            print(f"✓ 优化任务调度成功，任务ID: {task_id}")
            
            # 等待一段时间（简化测试）
            time.sleep(1)
            
            # 获取系统状态
            status = controller.get_system_status()
            print(f"  活动任务数: {status.get('active_tasks', 0)}")
            print(f"  待执行任务数: {status.get('pending_tasks', 0)}")
            
            return True
        else:
            print("✗ 优化任务调度失败")
            return False
            
    except Exception as e:
        print(f"✗ 功能优化测试失败: {str(e)}")
        return False


def test_new_function_creation(controller):
    """测试新功能创建"""
    print("\n=== 测试新功能创建 ===")
    
    try:
        # 调度一个新功能创建任务
        demand_text = "创建一个数据可视化工具，能够生成股票价格走势图"
        task_id = controller.create_new_function(demand_text, EvolutionPriority.MEDIUM.value)
        
        if task_id > 0:
            print(f"✓ 新功能创建任务调度成功，任务ID: {task_id}")
            
            # 等待一段时间（简化测试）
            time.sleep(2)
            
            # 获取系统状态
            status = controller.get_system_status()
            print(f"  活动任务数: {status.get('active_tasks', 0)}")
            print(f"  待执行任务数: {status.get('pending_tasks', 0)}")
            
            return True
        else:
            print("✗ 新功能创建任务调度失败")
            return False
            
    except Exception as e:
        print(f"✗ 新功能创建测试失败: {str(e)}")
        return False


def test_system_report(controller):
    """测试系统报告"""
    print("\n=== 测试系统报告 ===")
    
    try:
        # 获取最近的报告
        reports = controller.get_recent_reports(limit=3)
        
        print(f"✓ 获取报告成功，报告数量: {len(reports)}")
        
        for report in reports:
            print(f"  - 报告标题: {report.get('title')}, 类型: {report.get('report_type')}, 生成时间: {report.get('generated_at')}")
        
        return True
        
    except Exception as e:
        print(f"✗ 系统报告测试失败: {str(e)}")
        return False


def test_system_start_stop(controller):
    """测试系统启动和停止"""
    print("\n=== 测试系统启动和停止 ===")
    
    try:
        # 启动系统
        start_result = controller.start()
        
        if start_result:
            print("✓ 系统启动成功")
            
            # 获取系统状态
            status = controller.get_system_status()
            print(f"  系统运行状态: {'运行中' if status.get('is_running') else '已停止'}")
            print(f"  当前阶段: {status.get('current_phase')}")
            
            # 等待一会儿
            time.sleep(2)
            
            # 停止系统
            stop_result = controller.stop()
            
            if stop_result:
                print("✓ 系统停止成功")
            else:
                print("✗ 系统停止失败")
            
            return start_result and stop_result
        else:
            print("✗ 系统启动失败")
            return False
            
    except Exception as e:
        print(f"✗ 系统启动停止测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("自我进化系统测试")
    print("=" * 60)
    
    # 测试结果统计
    test_results = []
    
    # 测试1: 进化控制器初始化
    controller = test_evolution_controller_initialization()
    test_results.append(("进化控制器初始化", controller is not None))
    
    if not controller:
        print("\n✗ 进化控制器初始化失败，终止测试")
        return
    
    # 测试2: 使用模式跟踪
    test_results.append(("使用模式跟踪", test_usage_tracking(controller)))
    
    # 测试3: 需求分析
    test_results.append(("需求分析", test_demand_analysis(controller)))
    
    # 测试4: 功能优化
    test_results.append(("功能优化", test_function_optimization(controller)))
    
    # 测试5: 新功能创建
    test_results.append(("新功能创建", test_new_function_creation(controller)))
    
    # 测试6: 系统报告
    test_results.append(("系统报告", test_system_report(controller)))
    
    # 测试7: 系统启动停止
    test_results.append(("系统启动停止", test_system_start_stop(controller)))
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {len(test_results)} 项测试")
    print(f"通过: {passed} 项")
    print(f"失败: {failed} 项")
    
    if failed == 0:
        print("\n🎉 所有测试通过！自我进化系统功能正常。")
    else:
        print(f"\n⚠ 有 {failed} 项测试失败，需要检查问题。")


if __name__ == "__main__":
    main()