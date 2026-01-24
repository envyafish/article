import json

from sqlalchemy.orm import Session

from app.core.config import config_manager
from app.enum import DownloadClientEnum, PusherEnum, SystemConfigEnum
from app.models import Config
from app.modules.downloadclient.manager import downloadManager
from app.modules.notification.manager import pushManager
from app.schemas.config import JsonPayload
from app.schemas.response import success


def save_option(json_payload: JsonPayload, db: Session):
    key = json_payload.key
    config = db.query(Config).filter(Config.key == key).first()
    if config is None:
        config = Config()
        config.key = key
        config.content = json.dumps(json_payload.payload)
        db.add(config)
    else:
        config.content = json.dumps(json_payload.payload)
    if json_payload.key in [item.value for item in DownloadClientEnum]:
        downloadManager.reload(json_payload.key, json_payload.payload)
    if json_payload.key in [item.value for item in PusherEnum]:
        pushManager.reload(json_payload.key, json_payload.payload)
    if json_payload.key == SystemConfigEnum.SYSTEM_CONFIG.value:
        config_manager.reload(json_payload.payload)
    return success()


def get_option(key, db: Session):
    config = db.query(Config).filter(Config.key == key).first()
    if config:
        data = json.loads(str(config.content))
        return success(data)
    return success()


def list_all_downloader(db: Session):
    configs = db.query(Config).filter(Config.key.ilike('Downloader.%')).all()
    downloaders = []
    for config in configs:
        content = config.content
        downloader = json.loads(str(content))
        if downloader.get("save_paths"):
            downloader['id'] = config.key.replace('Downloader.', '')
            downloaders.append(downloader)
    return success(downloaders)
