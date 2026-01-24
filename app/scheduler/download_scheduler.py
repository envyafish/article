import json
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import exists

from app.api.services import article_service
from app.core.database import session_scope
from app.models import Config, Article, DownloadLog, Rule
from app.utils.wrapper import task_monitor


@task_monitor
def download_by_route(route_index_list):
    results = []
    with session_scope() as session:
        rules = session.query(Rule).filter(Rule.id.in_(route_index_list)).all()
    if rules:
        for rule in rules:
            success_count = 0
            fail_list = []
            now = datetime.now(timezone.utc)  # 如果数据库存的是 UTC 时间
            start_time = now - timedelta(hours=24)
            with session_scope() as session:
                query = session.query(Article).filter(Article.create_time.between(start_time, now),
                                                      ~exists().where(DownloadLog.tid == Article.tid))
                if rule.section:
                    query = query.filter(Article.section == rule.section)
                if rule.category:
                    query = query.filter(Article.category == rule.category)
                articles = query.all()
                if rule.regex:
                    pattern = re.compile(rule.regex)
                    articles = [
                        article
                        for article in articles
                        if article.title and pattern.search(article.title)
                    ]
            for article in articles:
                is_success = article_service.download_magnet(article.tid, article.magnet, rule.downloader,
                                                             rule.save_path)
                if is_success:
                    success_count += 1
                else:
                    fail_list.append(article.tid)
            results.append({
                "success_count": success_count,
                "fail_list": fail_list,
                "id": rule.id
            })
    return results
