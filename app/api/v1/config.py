from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.services import config_service
from app.core.database import get_db
from app.models import User
from app.schemas.config import JsonPayload

router = APIRouter()


@router.get("/{key}")
def list_option(key: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if key == 'downloaders':
        return config_service.list_all_downloader(db)
    return config_service.get_option(key, db)


@router.post('/')
def save_option(payload: JsonPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return config_service.save_option(payload, db)
