import json
import re
import threading
from datetime import datetime, timedelta
from typing import Any, Iterable, Tuple

from croniter import croniter
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.task_log import TaskLog
from app.scheduler import restart_scheduler, FUNC_MAP, find_func
from app.schemas.response import success, error
from app.schemas.task import TaskForm, TaskLogFilter


def list_task(db: Session):
    task_list = db.query(Task).all()
    return success(task_list)


def validate_func_args(args: Any, args_list: Iterable[str]) -> Tuple[bool, str]:
    if not args_list:
        return True,""
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError as e:
            return False, f"args 不是合法 JSON：{e}"

    if not isinstance(args, dict):
        return False, "args 必须是 JSON 对象（dict）"

    missing_fields = [field for field in args_list if field not in args]
    if missing_fields:
        return False, f"缺少必要字段：{missing_fields}"

    return True, ""


CRON_BASIC = re.compile(r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$')


def validate_cron_min_interval(
    cron_expr: str,
    min_interval_seconds: int = 3600,
    horizon_hours: int = 48
) -> bool:
    base = datetime.now()
    end_time = base + timedelta(hours=horizon_hours)

    try:
        itr = croniter(cron_expr, base)
    except Exception:
        # 非法 cron
        return False

    prev_time = itr.get_next(datetime)

    while True:
        next_time = itr.get_next(datetime)

        if next_time > end_time:
            break

        interval = (next_time - prev_time).total_seconds()
        if interval < min_interval_seconds:
            return False

        prev_time = next_time

    return True


def add_task(db: Session, task_form: TaskForm):
    func = find_func(task_form.task_func)
    valid_result = validate_func_args(task_form.task_args, func['func_args'])
    if not valid_result:
        return error(valid_result[1])

    if not validate_cron_min_interval(task_form.task_cron):
        return error("cron表达式校验未通过.不允许频率低于1小时")
    task = Task(**task_form.model_dump(exclude={"id"}))
    db.add(task)
    db.flush()
    db.commit()
    restart_scheduler()
    return success(task)


def update_task(db: Session, task_form: TaskForm):
    func = find_func(task_form.task_func)
    valid_result,valid_message = validate_func_args(task_form.task_args, func['func_args'])
    if not valid_result:
        return error(valid_message)
    if not validate_cron_min_interval(task_form.task_cron):
        return error("cron表达式校验未通过.不允许频率低于1小时")
    task = db.query(Task).filter_by(id=task_form.id).first()
    if task:
        task.task_name = task_form.task_name
        task.task_func = task_form.task_func
        task.task_args = task_form.task_args
        task.task_cron = task_form.task_cron
        task.enable = task_form.enable
        db.commit()
        db.flush()
        restart_scheduler()
    return success(task)


def delete_task(db: Session, task_id):
    task = db.get(Task, task_id)
    if task:
        db.delete(task)
        db.commit()
        restart_scheduler()
    return success()


def run_task(db: Session, task_id: int):
    task = db.get(Task, task_id)
    if task:
        args = task.task_args
        kwargs = {}
        if args:
            kwargs = json.loads(str(args))
        threading.Thread(
            target=find_func(task.task_func)["func"],
            kwargs=kwargs
        ).start()
    return success()


def page_task(db: Session, params: TaskLogFilter):
    stmt = select(TaskLog)

    if params.task_func:
        stmt = stmt.where(TaskLog.task_func.like(f"%{params.task_func}%"))

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(total_stmt).scalar_one()

    offset = (params.page - 1) * params.page_size

    items_stmt = (
        stmt
        .order_by(TaskLog.id.desc())
        .offset(offset)
        .limit(params.page_size)
    )

    items = db.execute(items_stmt).scalars().all()
    return success({
        "total": total,
        "items": items
    })


def list_func():
    return success(FUNC_MAP)
