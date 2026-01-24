from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.services import task_service
from app.core.database import get_db
from app.models import User
from app.schemas.task import TaskForm, TaskLogFilter

router = APIRouter()


@router.get('/')
def list_task(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_service.list_task(db)


@router.post('/')
def add_task(task_form: TaskForm, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_service.add_task(db, task_form)


@router.put('/')
def update_task(task_form: TaskForm, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_service.update_task(db, task_form)


@router.delete('/{task_id}')
def delete_task(task_id, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_service.delete_task(db, task_id)


@router.get('/run/{task_id}')
def run_task(task_id, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_service.run_task(db, task_id)


@router.post('/log/search')
def page_task_log(params: TaskLogFilter, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return task_service.page_task(db, params)


@router.get('/funcs')
def list_func(user: User = Depends(get_current_user)):
    return task_service.list_func()
