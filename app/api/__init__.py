import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, FileResponse
from starlette.staticfiles import StaticFiles

from app.api.v1 import article, user, config, task, download_log, rule, token
from app.core.config import root_path, config_manager
from app.core.database import Base, engine, session_scope
from app.enum import PusherEnum, DownloadClientEnum, SystemConfigEnum
from app.models import Config
from app.modules.downloadclient.cloudnas.cloudnas import CloudNas
from app.modules.downloadclient.manager import downloadManager
from app.modules.downloadclient.qbittorrent import QBitTorrentClient
from app.modules.downloadclient.thunder import Thunder
from app.modules.downloadclient.transmission import TransmissionClient
from app.modules.notification.manager import pushManager
from app.modules.notification.telegram import TelegramNotifier
from app.modules.notification.wechat import WeChatNotifier
from app.scheduler import start_scheduler, scheduler
from app.utils.log import logger


def load_system_config():
    with session_scope() as session:
        config = session.query(Config).filter(Config.key == SystemConfigEnum.SYSTEM_CONFIG.value).first()
        if config:
            system_config = json.loads(config.content)
            config_manager.reload(system_config)


def load_downloader_manager():
    with session_scope() as session:
        configs = session.query(Config).filter(Config.key.ilike('Downloader.%')).all()
        for config in configs:
            key = config.key
            download_config = json.loads(config.content)
            if key == DownloadClientEnum.QBITTORRENT.value:
                downloadManager.register(QBitTorrentClient(download_config))
            if key == DownloadClientEnum.TRANSMISSION.value:
                downloadManager.register(TransmissionClient(download_config))
            if key == DownloadClientEnum.THUNDER.value:
                downloadManager.register(Thunder(download_config))
            if key == DownloadClientEnum.CLOUDDRIVE.value:
                downloadManager.register(CloudNas(download_config))


def load_pusher_manager():
    with session_scope() as session:
        configs = session.query(Config).filter(Config.key.ilike('Notification.%')).all()
        for config in configs:
            key = config.key
            push_config = json.loads(config.content)
            if key == PusherEnum.WECHAT.value:
                pushManager.register(WeChatNotifier(push_config))
            if key == PusherEnum.TELEGRAM.value:
                pushManager.register(TelegramNotifier(push_config))


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # 加载系统配置
    load_system_config()
    # 加载下载管理器
    load_downloader_manager()
    # 加载通知管理器
    load_pusher_manager()
    start_scheduler()
    logger.success("服务已启动: http://127.0.0.1:8000")
    yield
    if scheduler.running:
        scheduler.shutdown(wait=True)


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段先用 *
    allow_credentials=True,
    allow_methods=["*"],  # 必须包含 OPTIONS
    allow_headers=["*"],  # 必须包含 X-Token
)

app.include_router(article.router, prefix='/api/v1/articles', tags=["article"])
app.include_router(user.router, prefix='/api/v1/users', tags=["user"])
app.include_router(config.router, prefix='/api/v1/config', tags=["config"])
app.include_router(task.router, prefix='/api/v1/tasks', tags=["task"])
app.include_router(download_log.router, prefix='/api/v1/download-log', tags=["download-log"])
app.include_router(rule.router, prefix='/api/v1/rules', tags=["rule"])
app.include_router(token.router, prefix='/api/v1/tokens', tags=["token"])

DIST_DIR = os.path.join(root_path, "frontend", "dist")

app.mount("/", StaticFiles(directory=os.path.join(DIST_DIR)), name="frontend")


@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    # 如果是 API 请求 404，还是返回正常的 404 JSON
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    # 如果是页面请求 404，返回 index.html
    return FileResponse(os.path.join(DIST_DIR, "index.html"))


# 针对根目录的直接访问
@app.get("/")
async def read_index():
    return FileResponse(os.path.join(DIST_DIR, "index.html"))
