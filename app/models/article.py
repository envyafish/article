from datetime import datetime, date
from typing import Dict

from sqlalchemy import Column, String, Integer, Text, Date, DateTime, func

from app.core.database import Base
from app.utils import dict_trans_obj


class Article(Base):
    __tablename__ = "article"

    tid: str = Column(Integer, nullable=False, primary_key=True)
    title: str = Column(String(255), nullable=False)
    publish_date: date = Column(Date)
    magnet: str = Column(Text, nullable=False)
    preview_images: str = Column(Text)
    detail_url: str = Column(String(255))
    size: int = Column(Integer())
    section: str = Column(String(255), nullable=False)
    category: str = Column(String(255))
    create_time: datetime = Column(DateTime(timezone=True), server_default=func.now())
    update_time: datetime = Column(DateTime(timezone=True), onupdate=func.now())

    def __init__(self, data: Dict):
        dict_trans_obj(data, self)

