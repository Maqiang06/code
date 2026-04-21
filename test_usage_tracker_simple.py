#!/usr/bin/env python3
"""
单独测试使用模式跟踪模块
"""

import sys
import os
import time

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.usage_tracker import UsagePatternTracker, UsageRecord, FunctionCategory

def test_simple_usage_tracking():
    """简单测试使用模式跟踪"""
    print("=== 简单测试使用模式跟踪 ===")
    
    try:
        # 创建使用模式跟踪器
        tracker = UsagePatternTracker()
        
        print("✓ 使用模式跟踪器创建成功")
        
        # 创建测试记录
        record = UsageRecord(
            function_name="test_simple_function",
            function_category=FunctionCategory.TOOL_EXECUTION.value,
            execution_time=0.5,
            success=True,
            context_info={"test": "simple_test"}
        )
        
        # 记录使用数据
        record_id = tracker.record_usage(record)
        print(f"✓ 使用记录添加成功，记录ID: {record_id}")
        
        # 获取统计数据
        stats = tracker.get_function_stats("test_simple_function")
        if stats:
            print(f"✓ 获取函数统计成功: {stats[0].function_name}, 调用次数: {stats[0].total_calls}")
        else:
            print("⚠ 函数统计为空")
            
        return True
        
    except Exception as e:
        print(f"✗ 使用模式跟踪测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_records():
    """测试多个记录"""
    print("\n=== 测试多个记录 ===")
    
    try:
        tracker = UsagePatternTracker()
        
        # 添加多个记录
        for i in range(3):
            record = UsageRecord(
                function_name=f"multi_test_function_{i}",
                function_category=FunctionCategory.DATA_ANALYSIS.value,
                execution_time=0.1 + i * 0.1,
                success=True,
                context_info={"iteration": i}
            )
            record_id = tracker.record_usage(record)
            print(f"  记录{i+1}添加成功，ID: {record_id}")
        
        print("✓ 多个记录添加成功")
        
        # 获取所有统计
        all_stats = tracker.get_function_stats()
        print(f"✓ 获取所有统计成功，共{len(all_stats)}个函数")
        
        for stat in all_stats:
            print(f"  - {stat.function_name}: {stat.total_calls}次调用")
            
        return True
        
    except Exception as e:
        print(f"✗ 多个记录测试失败: {str(e)}")
        return False

def test_concurrent_access():
    """测试并发访问（模拟）"""
    print("\n=== 测试并发访问 ===")
    
    try:
        tracker = UsagePatternTracker()
        
        import threading
        
        results = []
        lock = threading.Lock()
        
        def worker(worker_id):
            try:
                record = UsageRecord(
                    function_name=f"concurrent_function_{worker_id}",
                    function_category=FunctionCategory.SYSTEM_CONFIG.value,
                    execution_time=0.05,
                    success=True,
                    context_info={"worker": worker_id}
                )
                record_id = tracker.record_usage(record)
                with lock:
                    results.append((worker_id, record_id))
            except Exception as e:
                with lock:
                    results.append((worker_id, str(e)))
        
        # 创建并启动线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查结果
        success_count = 0
        error_count = 0
        
        for worker_id, result in results:
            if isinstance(result, int):
                print(f"  工作线程{worker_id}: 成功，记录ID: {result}")
                success_count += 1
            else:
                print(f"  工作线程{worker_id}: 失败，错误: {result}")
                error_count += 1
        
        print(f"✓ 并发测试完成: {success_count}成功, {error_count}失败")
        
        return error_count == 0
        
    except Exception as e:
        print(f"✗ 并发访问测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("使用模式跟踪模块单独测试")
    print("=" * 60)
    
    test_results = []
    
    # 测试1: 简单使用跟踪
    test_results.append(("简单使用跟踪", test_simple_usage_tracking()))
    
    # 测试2: 多个记录
    test_results.append(("多个记录", test_multiple_records()))
    
    # 测试3: 并发访问
    test_results.append(("并发访问", test_concurrent_access()))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for test_name, passed in test_results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, passed in test_results if passed)
    
    print(f"\n总计: {total_tests} 项测试")
    print(f"通过: {passed_tests} 项")
    print(f"失败: {total_tests - passed_tests} 项")
    
    if passed_tests < total_tests:
        print("\n⚠ 有测试失败，需要检查问题。")

if __name__ == "__main__":
    main()