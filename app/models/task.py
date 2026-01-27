from datetime import datetime

from sqlalchemy import Column, String, BigInteger, DateTime, func, Text, Boolean

from app.core.database import Base


class Task(Base):
    __tablename__ = "task"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_name: str = Column(String(32), nullable=False)
    task_func: str = Column(String(32), nullable=False)
    task_args: str = Column(Text)
    task_cron: str = Column(String(32), nullable=False)
    enable: bool = Column(Boolean, nullable=True)
    create_time: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now(),
                                   server_onupdate=func.now(),
                                   comment="创建时间")
