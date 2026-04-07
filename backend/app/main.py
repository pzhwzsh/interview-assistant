from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.models.database import init_db, engine
from app.utils.metrics import metrics
from sqlalchemy import text
import logging
import time
import json
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("interview-assistant")

app = FastAPI(
    title="Interview Assistant API",
    version="1.0.0",
    description="AI-powered interview practice system with adaptive difficulty"
)

# 配置 CORS (生产环境建议指定具体域名)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # 记录请求指标
        metrics.counters['requests_total'] += 1
        metrics.histograms['request_duration'].append(duration * 1000)

        logger.info(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "client_ip": request.client.host if request.client else None
        }))
        return response
    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        raise e


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，捕获所有未处理的异常"""
    logger.error(f"Unhandled exception for {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal Server Error",
            "detail": "An unexpected error occurred. Please check server logs."
        }
    )


# 注册路由
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(router, tags=["Interview Core"])
app.include_router(admin_router, prefix="/api/admin", tags=["Administration"])


@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Application started successfully. Database initialized.")


@app.get("/")
async def root():
    return {
        "message": "Interview Assistant API is running",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查接口，可用于 Docker 探针"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
async def get_metrics():
    """获取系统运行指标"""
    return metrics.get_summary()

