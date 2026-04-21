#!/usr/bin/env python3
"""
量化交易助手自我进化系统 - 安装测试脚本

测试包安装是否成功，基本功能是否正常。
"""

import sys
import os

def test_imports():
    """测试所有模块导入"""
    print("测试模块导入...")
    
    modules_to_test = [
        "qtassist_self_evolution",
        "qtassist_self_evolution.core",
        "qtassist_self_evolution.core.evolution_controller",
        "qtassist_self_evolution.core.usage_tracker",
        "qtassist_self_evolution.core.database_manager",
        "qtassist_self_evolution.core.demand_analyzer",
        "qtassist_self_evolution.core.auto_optimizer",
        "qtassist_self_evolution.core.auto_search_installer",
        "qtassist_self_evolution.core.new_function_creator",
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module}: {e}")
            return False
    
    # 测试可选模块
    optional_modules = [
        "qtassist_self_evolution.core.ml_predictor",
        "qtassist_self_evolution.core.real_time_monitor",
        "qtassist_self_evolution.core.feedback_learner",
        "qtassist_self_evolution.webui",
    ]
    
    print("\n测试可选模块导入...")
    for module in optional_modules:
        try:
            __import__(module)
            print(f"  ✓ {module} (可选)")
        except ImportError as e:
            print(f"  ✗ {module}: {e} (可选，可忽略)")
    
    return True

def test_cli():
    """测试命令行接口"""
    print("\n测试命令行接口...")
    
    try:
        from qtassist_self_evolution.cli import main
        print("  ✓ CLI模块导入成功")
        
        # 测试帮助命令
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            # 模拟--help参数
            sys.argv = ["qtassist-evolution", "--help"]
            try:
                main()
                output = f.getvalue()
                if "量化交易助手自我进化系统" in output:
                    print("  ✓ CLI帮助信息正常")
                else:
                    print("  ⚠ CLI帮助信息可能有问题")
            except SystemExit:
                # 预期行为，argparse会调用sys.exit()
                output = f.getvalue()
                if "量化交易助手自我进化系统" in output:
                    print("  ✓ CLI帮助信息正常")
                else:
                    print("  ⚠ CLI帮助信息可能有问题")
    except Exception as e:
        print(f"  ✗ CLI测试失败: {e}")
        return False
    
    return True

def test_config():
    """测试配置系统"""
    print("\n测试配置系统...")
    
    try:
        from qtassist_self_evolution.config import SystemConfig, DatabaseConfig
        
        # 测试默认配置
        config = SystemConfig()
        print(f"  ✓ 默认配置创建成功")
        
        # 测试数据库配置
        db_config = DatabaseConfig()
        print(f"  ✓ 数据库配置创建成功")
        
        # 测试配置转字典
        config_dict = config.to_dict()
        if isinstance(config_dict, dict):
            print(f"  ✓ 配置转字典成功")
        else:
            print(f"  ✗ 配置转字典失败")
            return False
            
    except Exception as e:
        print(f"  ✗ 配置测试失败: {e}")
        return False
    
    return True

def test_core_classes():
    """测试核心类实例化"""
    print("\n测试核心类实例化...")
    
    try:
        from qtassist_self_evolution.core.database_manager import DatabaseManager
        from qtassist_self_evolution.core.usage_tracker import UsagePatternTracker
        
        # 测试数据库管理器
        db_manager = DatabaseManager()
        print(f"  ✓ 数据库管理器实例化成功")
        
        # 测试使用跟踪器
        tracker = UsagePatternTracker()
        print(f"  ✓ 使用跟踪器实例化成功")
        
    except Exception as e:
        print(f"  ✗ 核心类测试失败: {e}")
        return False
    
    return True

def create_test_directories():
    """创建测试目录"""
    print("\n创建测试目录...")
    
    directories = ["data", "logs", "models"]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"  ✓ 创建目录: {directory}")
        except Exception as e:
            print(f"  ⚠ 无法创建目录 {directory}: {e}")
    
    return True

def main():
    """主测试函数"""
    print("=" * 60)
    print("量化交易助手自我进化系统 - 安装测试")
    print("版本: 1.0.0")
    print("=" * 60)
    
    tests = [
        ("模块导入测试", test_imports),
        ("配置系统测试", test_config),
        ("核心类测试", test_core_classes),
        ("命令行接口测试", test_cli),
        ("目录创建测试", create_test_directories),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                print(f"  ✓ {test_name} 通过")
                passed += 1
            else:
                print(f"  ✗ {test_name} 失败")
        except Exception as e:
            print(f"  ✗ {test_name} 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✅ 所有测试通过！安装成功。")
        print("\n下一步:")
        print("1. 初始化系统: qtassist-evolution init")
        print("2. 启动Web控制面板: qtassist-evolution web")
        print("3. 查看完整文档: docs/USAGE.md")
        return 0
    elif passed >= total * 0.7:
        print("⚠ 部分测试通过，基本功能可用。")
        print("某些可选功能可能未安装或存在问题。")
        return 1
    else:
        print("❌ 测试失败较多，请检查安装。")
        return 1

if __name__ == "__main__":
    sys.exit(main())