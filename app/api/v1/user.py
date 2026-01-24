from datetime import timedelta

from fastapi import Depends,  APIRouter
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_current_user
from app.api.services import user_service
from app.core import security
from app.core.database import get_db
from app.core.security import create_access_token
from app.models import User
from app.schemas.response import success, error
from app.utils.log import logger

router = APIRouter()


@router.post("/login")
def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return error("用户名或密码错误")
    token = create_access_token({"sub": user.username})
    return success({"access_token": token})


@router.post("/")
def create_user(username, password, db: Session = Depends(get_db)):
    return user_service.create_user(db, username, password)


@router.put("/")
def update_user(username, password, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return user_service.update_user(db, username, password)


@router.get("/reset-token")
def init_reset_token():
    token = security.create_access_token({"sub": "del_action"}, expires_delta=timedelta(hours=1))
    logger.warning(f"已生成重置密码口令: {token}")
    return success(message="已在服务端生成口令，请于1小时内完成密码重置")


@router.delete("/reset")
def delete_user(token: str, db: Session = Depends(get_db)):
    return user_service.clear_user(db, token)
