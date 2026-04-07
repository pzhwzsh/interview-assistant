from fastapi import APIRouter
from app.utils.metrics import metrics
from datetime import datetime

router = APIRouter()


@router.get("/admin/dashboard")
async def admin_dashboard():
    """管理面板数据"""
    summary = metrics.get_summary()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "counters": dict(metrics.counters),
        "gauges": metrics.gauges,
        "performance": summary,
        "system_health": {
            "status": "healthy",
            "uptime_seconds": 0
        }
    }
