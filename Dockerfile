FROM python:3.12-slim

# 设置工作目录与环境变量
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000

# 先复制依赖清单利用 Docker 缓存层
COPY requirements.txt .

# 安装基础运行依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码与静态资源
COPY app/ ./app/
COPY main.py .

# 暴露服务端口
EXPOSE 8000

# 健康检查：确保容器内服务可用
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/').read()" || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
