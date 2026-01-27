from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password, SECRET_KEY, ALGORITHM
from app.models.user import User
from app.schemas.response import error, success


def create_user(db: Session, username: str, password: str):
    user = db.query(User).first()
    if user:
        return error(f"已存在用户,无法再次创建账号")
    user = User(
        username=username,
        hashed_password=get_password_hash(password)
    )
    db.add(user)
    return success()


def clear_user(db: Session, token: str):
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).first()
        if user:
            db.delete(user)
        return success()
    except JWTError:
        return error(f"口令错误")


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_user(db: Session, username: str, password: str):
    user = db.query(User).first()
    user.username = username
    user.hashed_password = get_password_hash(password)
    db.flush()
    return success()




