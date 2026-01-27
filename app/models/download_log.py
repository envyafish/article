from datetime import datetime

from sqlalchemy import Column,  String, BigInteger, DateTime, func, Text

from app.core.database import Base


class DownloadLog(Base):
    __tablename__ = "download_log"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    tid: int = Column(BigInteger)
    downloader: str = Column(String(32))
    save_path: str = Column(String(255))
    create_time: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now(),
                                           server_onupdate=func.now(),
                                           comment="创建时间")