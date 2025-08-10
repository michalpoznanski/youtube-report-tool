# Trend module package
import logging

logger = logging.getLogger(__name__)
logger.info("[TREND/INIT] Trend module __init__ called")

from .routers.router import router
from .core.dispatcher import analyze_category
from .core.growth import update_growth
from .core.stats import publish_hour_stats

logger.info("[TREND/INIT] All imports successful")

__all__ = ['router', 'analyze_category', 'update_growth', 'publish_hour_stats']
