from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import config_manager
from app.utils.log import logger

engine = create_engine(config_manager.get().DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)
Base = declarative_base()


@contextmanager
def session_scope() -> Generator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"数据库操作失败：{str(e)}")
        raise
    finally:
        if session.is_active:
            session.expunge_all()
            session.close()


def get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"数据库操作失败：{str(e)}")
        raise
    finally:
        if session.is_active:
            session.expunge_all()
            session.close()
