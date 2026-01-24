import json
import threading

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.task_log import TaskLog
from app.scheduler import restart_scheduler, FUNC_MAP, find_func
from app.schemas.response import success
from app.schemas.task import TaskForm, TaskLogFilter


def list_task(db: Session):
    task_list = db.query(Task).all()
    return success(task_list)


def add_task(db: Session, task_form: TaskForm):
    task = Task(**task_form.model_dump(exclude={"id"}))
    db.add(task)
    db.flush()
    db.commit()
    restart_scheduler()
    return success(task)


def update_task(db: Session, task_form: TaskForm):
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
