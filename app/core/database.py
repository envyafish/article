from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import config_manager
from app.utils.log import logger

postgres_host = config_manager.get().POSTGRES_HOST
postgres_port = config_manager.get().POSTGRES_PORT
postgres_user = config_manager.get().POSTGRES_USER
postgres_password = config_manager.get().POSTGRES_PASSWORD
postgres_database = config_manager.get().POSTGRES_DB


database_url = config_manager.get().DATABASE_URL or f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_database}"
engine = create_engine(database_url)
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
