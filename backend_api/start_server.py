"""
AI 时间管理系统 - 后端 API 启动文件

这个文件用于启动 FastAPI 应用，避免模块重载问题。
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 启动 AI 时间管理系统 API 服务...")
    print("📖 API 文档: http://localhost:8000/docs")
    print("🔍 ReDoc 文档: http://localhost:8000/redoc")
    print("💚 健康检查: http://localhost:8000/health")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
