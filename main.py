"""
保研面试模拟系统启动入口
直接运行: python main.py
或使用: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"🚀 启动保研面试模拟系统服务...")
    print(f"📱 局域网/服务器访问地址: http://{settings.HOST}:{settings.PORT}")
    print(f"💻 本地调试地址: http://127.0.0.1:{settings.PORT}")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
