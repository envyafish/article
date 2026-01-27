from datetime import datetime

from sqlalchemy import Column,  String, BigInteger, DateTime, func, Text

from app.core.database import Base


class Config(Base):
    __tablename__ = "config"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    key: str = Column(String(32), unique=True, index=True, nullable=False)
    content: str = Column(Text, unique=True, index=True, nullable=True)
    create_time: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now(),
                                           server_onupdate=func.now(),
                                           comment="创建时间")