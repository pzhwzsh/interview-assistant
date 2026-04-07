import time
import functools
import logging
from typing import Dict, Any
from collections import defaultdict

logger = logging.getLogger("interview-assistant.metrics")


class MetricsCollector:
    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = defaultdict(list)

    def increment(self, name: str, value: int = 1):
        self.counters[name] += value

    def set_gauge(self, name: str, value: float):
        self.gauges[name] = value

    def observe(self, name: str, value: float):
        self.histograms[name].append(value)
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-500:]

    def get_summary(self) -> Dict[str, Any]:
        summary = {}
        for name, values in self.histograms.items():
            if values:
                summary[name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        return summary


metrics = MetricsCollector()


def monitor_performance(metric_name: str):
    """性能监控装饰器"""

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.observe(f"{metric_name}_duration", duration)
                metrics.increment(f"{metric_name}_success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.observe(f"{metric_name}_duration", duration)
                metrics.increment(f"{metric_name}_error")
                logger.error(f"{metric_name} failed: {str(e)}")
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.observe(f"{metric_name}_duration", duration)
                metrics.increment(f"{metric_name}_success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.observe(f"{metric_name}_duration", duration)
                metrics.increment(f"{metric_name}_error")
                logger.error(f"{metric_name} failed: {str(e)}")
                raise

        return async_wrapper if functools.iscoroutinefunction(func) else sync_wrapper

    return decorator
