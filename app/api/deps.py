from fastapi import Depends, HTTPException, Header,Request
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.models import Token
from app.models.user import User
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 无效")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key"), db: Session = Depends(get_db)):
    token = db.query(Token).filter(Token.token_value == x_api_key).first()
    if not token:
        raise HTTPException(status_code=401, detail="鉴权未通过")
    return token


def api_key_or_jwt(
    request: Request,
    db: Session = Depends(get_db)
):
    # 1️⃣ 尝试 API Key
    try:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return verify_api_key(
                x_api_key=api_key,
                db=db
            )
    except HTTPException:
        pass

    # 2️⃣ 尝试 JWT
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.replace("Bearer ", "")
            return get_current_user(
                token=token,
                db=db
            )
    except HTTPException:
        pass

    # 3️⃣ 都失败
    raise HTTPException(
        status_code=401,
        detail="API Key 或 Token 鉴权失败"
    )