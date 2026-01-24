from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.services import rule_service
from app.core.database import get_db
from app.models import User
from app.schemas.rule import RuleForm

router = APIRouter()


@router.get('/')
def list_rule(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return rule_service.list_rule(db)


@router.post('/')
def add_rule(rule_form: RuleForm, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return rule_service.add_rule(db, rule_form)


@router.put('/')
def update_rule(rule_form: RuleForm, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return rule_service.update_rule(db, rule_form)


@router.delete('/{rule_id}')
def delete_rule(rule_id, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return rule_service.delete_rule(db, rule_id)
