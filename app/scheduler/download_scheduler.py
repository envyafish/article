import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, List

from sqlalchemy import exists

from app.api.services import article_service
from app.core.database import session_scope
from app.models import Config, Article, DownloadLog, Rule
from app.utils.log import logger
from app.utils.wrapper import task_monitor


def to_number_list(
    value: Any,
    *,
    allow_float: bool = False,
    empty_ok: bool = False
) -> List[int | float]:
    """
    将 value 转换为数字列表

    :param value: list / str
    :param allow_float: 是否允许浮点数
    :param empty_ok: 是否允许空列表
    :return: 数字列表
    :raises ValueError: 无法转换
    """

    def cast(v: str):
        return float(v) if allow_float else int(v)

    # 1️⃣ 已经是 list
    if isinstance(value, list):
        try:
            result = [cast(v) for v in value]
        except Exception:
            raise ValueError("列表中包含非数字元素")

        if not result and not empty_ok:
            raise ValueError("不允许空列表")

        return result

    # 2️⃣ 是字符串，尝试分割
    if isinstance(value, str):
        value = value.strip()

        if not value:
            if empty_ok:
                return []
            raise ValueError("空字符串无法转换为数字列表")

        # 统一分隔符
        for sep in [",", "|", " "]:
            value = value.replace(sep, ",")

        parts = [p for p in value.split(",") if p]

        try:
            result = [cast(p) for p in parts]
        except Exception:
            raise ValueError("字符串中包含非数字内容")

        if not result and not empty_ok:
            raise ValueError("不允许空列表")

        return result

    raise ValueError(f"不支持的类型：{type(value).__name__}")

@task_monitor
def download_by_route(route_index_list):
    try:
        rule_id_list = to_number_list(route_index_list)
    except ValueError as e:
        logger.error(f"订阅任务执行失败: {e}")
        return None

    results = []
    with session_scope() as session:
        rules = session.query(Rule).filter(Rule.id.in_(rule_id_list)).all()
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
