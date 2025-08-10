# Trend module package
from .routers.router import router
from .core.dispatcher import analyze_category
from .core.growth import update_growth
from .core.stats import publish_hour_stats

__all__ = ['router', 'analyze_category', 'update_growth', 'publish_hour_stats']
