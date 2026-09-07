#!/usr/bin/env bash
set -e

echo "🚀 正在启动保研面试模拟系统 Docker 容器..."
docker compose up -d --build

echo "✅ 启动成功！"
echo "📱 请在手机浏览器中访问: http://<你的服务器IP>:8000"
echo "🔍 查看容器运行日志: docker compose logs -f"
