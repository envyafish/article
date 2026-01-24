import json

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import session_scope
from app.models.task import Task
from app.scheduler.download_scheduler import download_by_route
from app.scheduler.sht_sheduler import sync_sht_by_tid, sync_sht_by_max_page

scheduler = AsyncIOScheduler()

FUNC_MAP = [
    {
        "func_name": "sync_sht_by_tid",
        "func_label": "色花堂爬虫-智能版",
        "func_args": [],
        "func": sync_sht_by_tid
    },
    {
        "func_name": "sync_sht_by_max_page",
        "func_label": "色花堂爬虫-全量版",
        "func_args": ["max_page"],
        "func": sync_sht_by_max_page
    },
    {
        "func_name": "download_by_route",
        "func_label": "规则入库任务",
        "func_args": ["rule_id_list"],
        "func": download_by_route
    },
]


def find_func(func_name):
    for func in FUNC_MAP:
        if func["func_name"] == func_name:
            return func
    return None


def list_task():
    with session_scope() as session:
        tasks = session.query(Task).filter(Task.enable == True).all()
    return tasks


def push_job():
    tasks = list_task()
    for task in tasks:
        args = task.task_args
        kwargs = {}
        if args:
            kwargs = json.loads(args)
        scheduler.add_job(find_func(task.task_func)["func"], kwargs=kwargs,
                          trigger=CronTrigger.from_crontab(expr=task.task_cron))


def start_scheduler():
    push_job()
    scheduler.start()


def restart_scheduler():
    scheduler.remove_all_jobs()
    push_job()
