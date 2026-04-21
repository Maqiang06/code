# 贡献指南

感谢您有兴趣为"量化交易助手自我进化系统"项目做出贡献！本指南将帮助您了解如何参与贡献。

## 行为准则

参与本项目贡献，请遵守以下行为准则：

- 保持尊重和友好的沟通态度
- 欢迎不同经验和背景的贡献者
- 建设性地接受批评和建议
- 关注社区成员的最佳利益

## 如何贡献

### 报告问题

如果您发现了bug或有问题要反馈：

1. 在[GitHub Issues](https://github.com/ptrade-code/qtassist-self-evolution/issues)中搜索是否已有类似问题
2. 如果没有，请创建新issue，包含：
   - 清晰的标题
   - 详细的问题描述
   - 复现步骤
   - 期望的行为
   - 实际的行为
   - 环境信息（Python版本、操作系统等）
   - 相关日志或截图

### 功能建议

如果您有新的功能想法：

1. 先在Issues中搜索是否已有类似建议
2. 创建新issue，描述：
   - 功能的具体用途
   - 为什么这个功能重要
   - 可能的实现方案
   - 是否有相关参考

### 代码贡献

#### 开发环境设置

1. Fork本项目
2. 克隆您的fork：
   ```bash
   git clone https://github.com/YOUR_USERNAME/qtassist-self-evolution.git
   cd qtassist-self-evolution
   ```
3. 创建虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   .\venv\Scripts\activate   # Windows
   ```
4. 安装开发依赖：
   ```bash
   pip install -e .[all,dev]
   ```

#### 代码规范

1. **代码风格**：
   - 遵循PEP 8规范
   - 使用Black进行代码格式化
   - 使用isort进行导入排序
   - 行长度限制在88个字符

2. **类型注解**：
   - 所有函数和方法都应包含类型注解
   - 使用mypy进行类型检查

3. **文档**：
   - 所有公共API都应包含docstring
   - 使用Google风格的docstring格式
   - 更新相关文档（README、API文档等）

4. **测试**：
   - 新功能应包含测试用例
   - 修复bug时添加回归测试
   - 确保所有测试通过
   - 测试覆盖率不应降低

#### 开发流程

1. 创建功能分支：
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/issue-number-description
   ```

2. 进行代码更改

3. 运行测试：
   ```bash
   # 运行所有测试
   python -m pytest
   
   # 运行特定测试
   python -m pytest tests/test_module.py
   
   # 带覆盖率的测试
   python -m pytest --cov=qtassist_self_evolution
   ```

4. 代码检查和格式化：
   ```bash
   # 代码格式化
   black .
   
   # 导入排序
   isort .
   
   # 代码检查
   flake8
   
   # 类型检查
   mypy qtassist_self_evolution
   ```

5. 提交代码：
   ```bash
   # 添加更改
   git add .
   
   # 提交（使用有意义的提交信息）
   git commit -m "feat: 添加新功能描述"
   ```

6. 同步上游仓库：
   ```bash
   git remote add upstream https://github.com/ptrade-code/qtassist-self-evolution.git
   git fetch upstream
   git rebase upstream/main
   ```

7. 推送分支：
   ```bash
   git push origin your-branch-name
   ```

8. 创建Pull Request：
   - 在GitHub上创建Pull Request
   - 填写PR模板
   - 关联相关issue（使用fixes #issue-number）
   - 等待代码审查

### 提交信息规范

使用[Conventional Commits](https://www.conventionalcommits.org/)规范：

- `feat:` 新功能
- `fix:` bug修复
- `docs:` 文档更新
- `style:` 代码格式调整（不影响功能）
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具变更

示例：
```
feat: 添加机器学习预测功能
fix: 修复数据库并发访问问题
docs: 更新安装指南
```

## 文档贡献

文档同样重要！您可以：

1. 修正文档中的错误
2. 添加使用示例
3. 改进文档结构
4. 翻译文档

## 项目结构

```
qtassist-self-evolution/
├── qtassist_self_evolution/    # 主包目录
│   ├── core/                   # 核心模块
│   │   ├── evolution_controller.py
│   │   ├── usage_tracker.py
│   │   └── ...
│   ├── webui/                  # Web界面
│   ├── __init__.py
│   ├── cli.py                  # 命令行接口
│   └── config.py               # 配置管理
├── docs/                       # 文档
├── tests/                      # 测试目录
├── examples/                   # 示例代码
├── pyproject.toml              # 项目配置
├── README.md                   # 项目说明
├── CONTRIBUTING.md             # 本文件
└── LICENSE                     # 许可证
```

## 获取帮助

如果您在贡献过程中遇到问题：

1. 查看项目文档
2. 在Issues中搜索相关问题
3. 创建新issue寻求帮助
4. 参与社区讨论

## 许可证

通过贡献代码，您同意您的贡献将在MIT许可证下发布。

感谢您的贡献！🎉