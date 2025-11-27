from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.api.v1 import health, jobs

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="提供 YouTube 網址或上傳影片，去除人聲並產生伴奏影片",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全域例外處理"""
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "內部伺服器錯誤，請稍後再試"
        }
    )


# Register routers
app.include_router(health.router, prefix="/api/v1", tags=["健康檢查"])
app.include_router(jobs.router, prefix="/api/v1", tags=["任務管理"])


@app.get("/")
async def root():
    """根路徑"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running"
    }
