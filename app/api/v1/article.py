
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from app.api.deps import get_current_user, api_key_or_jwt
from app.api.services import article_service
from app.core.config import root_path
from app.core.database import get_db
from app.models.user import User
from app.schemas.article import ArticleQuery

router = APIRouter()


@router.post("/search")
def get_article_list(query: ArticleQuery, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return article_service.get_article_list(db, query)


@router.get("/categories")
def get_category(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return article_service.get_category(db)


@router.get("/torrents")
def get_torrent(keyword, db: Session = Depends(get_db), auth=Depends(api_key_or_jwt)):
    return article_service.get_torrents(keyword, db)


@router.get("/download")
def download_article(tid: int, user: User = Depends(get_current_user)):
    return article_service.download_article(tid)


@router.get("/download/manul")
async def manul_download(tid: int, downloader, save_path, user: User = Depends(get_current_user)):
    return article_service.manul_download(tid, downloader, save_path)


templates = Jinja2Templates(directory=f"{root_path}/app/templates")
