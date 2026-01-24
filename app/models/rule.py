from datetime import datetime

from sqlalchemy import Column, String, BigInteger, DateTime, func, Text, Boolean

from app.core.database import Base


class Rule(Base):
    __tablename__ = "rule"
    __table_args__ = {"schema": "sht"}

    id: int = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    section: str = Column(String(32), nullable=False)
    category: str = Column(String(32), nullable=False)
    regex: str = Column(String(255), nullable=False)
    downloader: str = Column(String(255), nullable=False)
    save_path: str = Column(String(255), nullable=False)
    create_time: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now(),
                                   server_onupdate=func.now(),
                                   comment="创建时间")
