from typing import Dict, List

from sqlalchemy import func, exists
from sqlalchemy.orm import Session

from app.core.database import session_scope
from app.models import DownloadLog, Rule
from app.models.article import Article
from app.modules.downloadclient.manager import downloadManager
from app.modules.notification.manager import pushManager
from app.schemas.article import ArticleQuery
from app.schemas.response import success, error


def get_article_list(db: Session, query: ArticleQuery) -> Dict:
    in_stock_expr = exists().where(
        DownloadLog.tid == Article.tid
    )
    q = db.query(Article, in_stock_expr.label("in_stock"))
    if query.keyword:
        q = q.filter(Article.title.ilike(f"%{query.keyword}%"))
    if query.section:
        q = q.filter(Article.section == query.section)
    if query.category:
        q = q.filter(Article.category == query.category)
    total = q.count()
    page = query.page
    offset = (page - 1) * query.page_size
    rows = (
        q.order_by(Article.tid.desc())
        .offset(offset)
        .limit(query.page_size)
        .all()
    )
    items = []
    for article, in_stock in rows:
        setattr(article, "in_stock", in_stock)
        items.append(article)
    has_more = len(items) == query.page_size
    return success({
        "page": page,
        "pageSize": query.page_size,
        "total": total,
        "items": items,
        "hasMore": has_more
    })


cn_keywords: List[str] = ['中字', '中文字幕', '色花堂', '字幕']
uc_keywords: List[str] = ['UC', '无码', '步兵']
uhd_keywords: List[str] = ['4k', '8k', '2160p', '4K', '8K', '2160P']


def has_chinese(title: str):
    chinese = False
    for keyword in cn_keywords:
        if title.find(keyword) > -1:
            chinese = True
            break
    return chinese


def has_uc(title: str):
    uc = False
    for keyword in uc_keywords:
        if title.find(keyword) > -1:
            uc = True
            break
    return uc


def has_uhd(title: str):
    uhd = False
    for keyword in uhd_keywords:
        if title.find(keyword) > -1:
            uhd = True
            break
    return uhd


def get_torrents(keyword, db: Session) -> Dict:
    articles = db.query(Article).filter(Article.title.ilike(f"%{keyword}%")).all()
    torrents = []
    for article in articles:
        torrent = {
            'id': article.tid,
            'site': 'sehuatang',
            'size_mb': article.size,
            'seeders': 66,
            'title': article.title,
            'download_url': article.magnet,
            'free': True,
            'chinese': has_chinese(f"{article.title}{article.section}"),
            'uc': has_uc(f"{article.title}{article.section}"),
            'uhd': has_uhd(f"{article.title}{article.section}")
        }
        torrents.append(torrent)
    return success(torrents)


def get_category(db: Session):
    item_count = func.count(Article.tid).label("item_count")
    result = db.query(Article.section, Article.category, item_count).group_by(
        Article.section, Article.category).order_by(item_count.desc()).all()
    grouped = {}

    for section, category, count in result:
        if section not in grouped:
            grouped[section] = {
                "name": section,
                "count": 0,
                "categories": []
            }
        if category:
            grouped[section]["categories"].append({
                "name": category,
                "count": count
            })

        grouped[section]["count"] += count
    return success(list(grouped.values()))


import re


def calc_score(rule, section, category, title):
    score = 0

    if rule.section == section:
        score += 10
    elif rule.section == "ALL":
        score += 1
    else:
        return 0

    if rule.category == category:
        score += 5
    elif rule.category == "ALL":
        score += 1
    else:
        return 0

    rule_regex = rule.regex

    if rule_regex:
        if re.search(rule_regex, title):
            score += 20
        else:
            return 0
    else:
        score += 1
    return score


def match_best_rules(rules, section, category, title):
    best_score = 0
    best_rules = []

    for rule in rules:
        score = calc_score(rule, section, category, title)
        if score == 0:
            continue

        if score > best_score:
            best_score = score
            best_rules = [rule]
        elif score == best_score:
            best_rules.append(rule)

    return best_rules


def download_magnet(tid, magnet, downloader, save_path):
    is_success = downloadManager.download(f'Downloader.{downloader}', magnet, save_path)
    if is_success:
        with session_scope() as db:
            download_log = DownloadLog()
            download_log.tid = tid
            download_log.magnet = magnet
            download_log.save_path = save_path
            download_log.downloader = downloader
            db.add(download_log)
    return is_success


def convert_message_data(article: Article, downloader: str, save_path: str):
    return {
        "title": article.title,
        "image": article.preview_images.split(',')[0] if article.preview_images else None,
        "section": article.section,
        "category": article.category,
        "size": article.size,
        "magnet": article.magnet,
        "publish_date": article.publish_date,
        "tid": article.tid,
        "detail_url": article.detail_url,
        "downloader": downloader,
        "save_path": save_path,
    }


def download_article(tid: int):
    with session_scope() as db:
        article = db.get(Article, tid)
        rules = db.query(Rule).all()
    success_count = 0
    if article and rules:
        section = article.section
        category = article.category
        best_rules = match_best_rules(rules, section, category, article.title)
        for rule in best_rules:
            is_success = download_magnet(article.tid, article.magnet, rule.downloader, rule.save_path)
            if is_success:
                pushManager.send(convert_message_data(article, rule.downloader, rule.save_path))
                success_count += 1
    if success_count > 0:
        return success(message="成功创建下载任务")
    return error("创建下载任务失败")


def manul_download(tid, downloader, save_path):
    with session_scope() as db:
        article = db.get(Article, tid)
    is_success = download_magnet(article.tid, article.magnet, downloader, save_path)
    if is_success:
        return success(message="成功创建下载任务")
    return error("创建下载任务失败")
