from datetime import datetime

from sqlalchemy import Column, BigInteger, DateTime, func, Text, VARCHAR, Boolean

from app.core.database import Base


class TaskLog(Base):
    __tablename__ = "task_log"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_name: str = Column(VARCHAR(255), nullable=True)
    task_func: str = Column(VARCHAR(255), nullable=False)
    start_time: datetime = Column(DateTime, nullable=False)
    end_time: datetime = Column(DateTime, nullable=False)
    execute_seconds: int = Column(BigInteger, nullable=False)
    execute_result: str = Column(Text)
    execute_flag: str = Column(VARCHAR(255))
    success: bool = Column(Boolean, nullable=False)
    error: str = Column(Text)
    create_time: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now(),
                                   server_onupdate=func.now(),
                                   comment="创建时间")
