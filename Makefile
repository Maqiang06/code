# 量化交易助手自我进化系统 - Makefile

.PHONY: help install install-dev test lint format type-check clean build publish docs

# 默认目标
help:
	@echo "量化交易助手自我进化系统 - 构建工具"
	@echo ""
	@echo "可用命令:"
	@echo "  make install     安装包和依赖"
	@echo "  make install-dev 安装开发依赖"
	@echo "  make test        运行测试"
	@echo "  make lint        代码检查"
	@echo "  make format      代码格式化"
	@echo "  make type-check  类型检查"
	@echo "  make clean       清理构建文件"
	@echo "  make build       构建包"
	@echo "  make docs        生成文档"
	@echo "  make run-web     启动Web界面"
	@echo "  make run-system  启动系统"

# 安装包和依赖
install:
	pip install -e .[all]

# 安装开发依赖
install-dev:
	pip install -e .[all,dev]

# 运行测试
test:
	pytest -v --cov=qtassist_self_evolution --cov-report=html --cov-report=term-missing

# 快速测试
test-quick:
	pytest -v

# 代码检查
lint:
	flake8 qtassist_self_evolution --count --show-source --statistics
	black --check qtassist_self_evolution
	isort --check qtassist_self_evolution

# 代码格式化
format:
	black qtassist_self_evolution
	isort qtassist_self_evolution

# 类型检查
type-check:
	mypy qtassist_self_evolution --ignore-missing-imports

# 清理构建文件
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# 构建包
build: clean
	python -m build

# 检查包
check-build:
	twine check dist/*

# 生成文档
docs:
	@echo "生成文档..."
	@echo "请查看 docs/ 目录中的文档"

# 启动Web界面
run-web:
	python -m qtassist_self_evolution.cli web

# 启动系统
run-system:
	python -m qtassist_self_evolution.cli start

# 初始化系统
init:
	python -m qtassist_self_evolution.cli init

# 查看状态
status:
	python -m qtassist_self_evolution.cli status

# 运行所有检查和测试
all: install-dev format lint type-check test

# Docker构建（如果支持）
docker-build:
	docker build -t qtassist-self-evolution .

docker-run:
	docker run -p 5001:5001 qtassist-self-evolution