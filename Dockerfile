# 量化交易助手自我进化系统 - Docker镜像

FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -e .[all]

# 创建数据目录
RUN mkdir -p data logs models

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口（Web界面）
EXPOSE 5001

# 默认命令：启动Web界面
CMD ["python", "-m", "qtassist_self_evolution.cli", "web", "--host", "0.0.0.0"]