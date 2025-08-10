import os, logging
from apscheduler.triggers.cron import CronTrigger
from .loader import load_latest
from .dispatcher import analyze_category
from .growth import update_growth
from .store.trend_store import stats_path, save_json
from .stats import publish_hour_stats

log = logging.getLogger("trend")

def register_trend_job(scheduler, category="PODCAST"):
    hour = int(os.environ.get("TREND_RUN_HOUR", "2"))
    minute = int(os.environ.get("TREND_RUN_MINUTE", "0"))
    def job():
        try:
            df, report_date = load_latest(category)
            if df is None:
                log.info(f"[TREND] no report for {category}")
                return
            analyze_category(category, df)  # side effect: liczy rank + stats
            update_growth(category, df, report_date)
            st = publish_hour_stats(df)
            save_json(stats_path(category, report_date), st)
            log.info(f"[TREND] done for {category} @ {report_date}")
        except Exception as e:
            log.exception(f"[TREND] job failed: {e}")
    scheduler.add_job(job, CronTrigger(hour=hour, minute=minute), id=f"trend_{category.lower()}_daily", replace_existing=True)
