from datetime import datetime

from sqlalchemy import Column, Integer, String, BigInteger, DateTime, func

from app.core.database import Base


class User(Base):
    __tablename__ = "user"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    username: str = Column(String(32), unique=True, index=True, nullable=False)
    hashed_password: str = Column(String(128), nullable=False)
    is_active: int = Column(Integer, server_default="1")
    create_time: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now(),
                                           server_onupdate=func.now(),
                                           comment="创建时间")
    update_time: datetime = Column(DateTime(timezone=True), server_default=func.now(),
                                           server_onupdate=func.now(),
                                           nullable=False,
                                           comment="更新时间")