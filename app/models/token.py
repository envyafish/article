from datetime import datetime

from sqlalchemy import Column, String, BigInteger, DateTime, func, Text, Boolean

from app.core.database import Base


class Token(Base):
    __tablename__ = "token"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    token_key: str = Column(String(32), nullable=False)
    token_value: str = Column(String(255), nullable=False)
    create_time: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now(),
                                   server_onupdate=func.now(),
                                   comment="创建时间")
