from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.services import token_service
from app.core.database import get_db
from app.models import User


router = APIRouter()

@router.get("/")
def list_token(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return token_service.list_token(db)

@router.post("/")
def create_token(key: str,db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return token_service.create_token(db,key)


@router.delete("/{token_id}")
def delete_token(token_id: int,db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return token_service.delete_token(db,token_id)