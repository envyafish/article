from sqlalchemy.orm import Session

from app import utils
from app.models.token import Token
from app.schemas.response import success, error


def list_token(db: Session):
    tokens = db.query(Token).order_by(Token.create_time.desc()).all()
    return success(tokens)


def create_token(db: Session, key: str):
    token = db.query(Token).filter(Token.token_key == key).first()
    if token:
        return error("该令牌名称已存在")
    token_value = utils.generate_secure_random_string(32)
    token = Token(token_key=key, token_value=token_value)
    db.add(token)
    return success()


def delete_token(db: Session, token_id: int):
    token = db.get(Token, token_id)
    db.delete(token)
    return success()
