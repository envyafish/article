import os
import threading
from pathlib import Path

from pydantic.v1 import BaseSettings

root_path = '/' if os.environ.get('DOCKER_ENV') else os.path.dirname(Path(__file__).resolve().parent.parent)
data_path = os.path.join(root_path, 'data')
env_path = os.path.join(data_path, 'app.env')


class Settings(BaseSettings):
    DATABASE_URL: str | None
    PROXY: str | None
    FLARE_SOLVERR_URL: str | None
    POSTGRES_HOST: str | None
    POSTGRES_PORT: str | None
    POSTGRES_USER: str | None
    POSTGRES_PASSWORD: str | None
    POSTGRES_DB: str | None

    class Config:
        env_file = os.path.join(env_path)


class ConfigManager:
    config_key = 'SystemConfig'

    def __init__(self):
        self._settings = Settings()
        self._lock = threading.Lock()

    def get(self) -> Settings:
        return self._settings

    def reload(self, data):
        self._settings = Settings(**data)


config_manager = ConfigManager()
