import random
import time
from sqlalchemy import func, select
from app.core.database import session_scope
from app.models.article import Article
from app.utils.log import logger
from app.modules.crawler.sht import sht
from app.utils.wrapper import task_monitor

section_map = {
    '2': "国产原创",
    '36': "亚洲无码原创",
    '38': "欧美无码",
    '37': "亚洲有码原创",
    '103': "高清中文字幕",
    '104': "素人有码系列",
    '151': "4K原版",
    '152': "韩国主播",
    "160": "VR视频区",
    "39": "动漫原创",
    "107": "三级写真"
}

@task_monitor
def sync_sht_by_tid():
    result = []
    for fid in section_map:
        section = section_map[fid]
        success_count, page, fail_list = sync_new_article(fid, 1, 100)
        result.append(
            {
                "section": section,
                "success_count": success_count,
                "page": page-1,
                "fail_list": fail_list,
            }
        )
    return result

@task_monitor
def sync_sht_by_max_page(max_page):
    result = []
    for fid in section_map:
        section = section_map[fid]
        success_count, page, fail_list = sync_new_article_no_stop(fid, 1, max_page)
        result.append(
            {
                "section": section,
                "success_count": success_count,
                "page": page-1,
                "fail_list": fail_list,
            }
        )
    return result


def sync_new_article(fid, start_page=1, max_page=100):
    fid = str(fid)
    section = section_map[fid]
    fail_id_list = []
    page = start_page
    success_count = 0
    # 作为终止阈值
    with session_scope() as session:
        stop_tid = session.query(func.max(Article.tid)) \
                       .filter(Article.section == section) \
                       .scalar() or 0

    logger.info(f"[{section}] 数据库最大TID: {stop_tid}")
    articles = []
    while page <= max_page:
        time.sleep(1)
        logger.info(f"[{section}] 抓取第 {page} 页")
        tid_list = []
        # 页面级重试
        for retry in range(3):
            tid_list = sht.crawler_tid_list(
                f"https://sehuatang.org/forum.php?mod=forumdisplay&fid={fid}&mobile=2&page={page}"
            )
            if tid_list:
                break
            logger.warning(f"第{page}页抓取失败，第{retry + 1}次重试")
            time.sleep(10)

        if not tid_list:
            logger.info(f"连续抓取3次第{page}页失败,退出任务")
            break
        else:
            min_tid = min(tid_list)
            logger.info(f"当前页最小TID: {min_tid}")

            # 批量判断数据库是否已存在
            with session_scope() as session:
                existing_article_tids = (
                    session.execute(
                        select(Article.tid).filter(Article.tid.in_(tid_list))
                    ).scalars().all()
                )

            for tid in tid_list:
                if tid in existing_article_tids:
                    continue

                detail_url = (
                    f"https://sehuatang.org/forum.php?"
                    f"mod=viewthread&tid={tid}&extra=page%3D1&mobile=2"
                )

                try:
                    data = sht.crawler_detail(detail_url)
                    if not data:
                        fail_id_list.append(tid)
                        continue

                    data.update({
                        "tid": tid,
                        "section": section,
                        "detail_url": detail_url
                    })
                    article = Article(data)
                    articles.append(article)
                    success_count += 1
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"TID {tid} 抓取失败: {e}")
                    fail_id_list.append(tid)

            # 终止条件
            if min_tid <= stop_tid:
                logger.info(f"[{section}] 已到达历史最大TID，任务结束")
                break
            page += 1
    with session_scope() as session:
        session.add_all(articles)
    retry_fail_id_list = retry_fail_tid(fid, fail_id_list)
    return success_count, page, retry_fail_id_list


def sync_new_article_no_stop(fid, start_page=1, max_page=100):
    fid = str(fid)
    section = section_map[fid]
    fail_id_list = []
    page = start_page
    success_count = 0
    articles = []
    while page <= max_page:
        time.sleep(1)
        logger.info(f"[{section}] 抓取第 {page} 页")
        tid_list = []
        # 页面级重试
        for retry in range(3):
            tid_list = sht.crawler_tid_list(
                f"https://sehuatang.org/forum.php?mod=forumdisplay&fid={fid}&mobile=2&page={page}"
            )
            if tid_list:
                break
            logger.warning(f"第{page}页抓取失败，第{retry + 1}次重试")
            time.sleep(10)

        if not tid_list:
            logger.info(f"连续抓取3次第{page}页失败,退出任务")
            break
        else:
            # 批量判断数据库是否已存在
            with session_scope() as session:
                existing_article_tids = (
                    session.execute(
                        select(Article.tid).filter(Article.tid.in_(tid_list))
                    ).scalars().all()
                )

            for tid in tid_list:
                if tid in existing_article_tids:
                    continue

                detail_url = (
                    f"https://sehuatang.org/forum.php?"
                    f"mod=viewthread&tid={tid}&extra=page%3D1&mobile=2"
                )

                try:
                    data = sht.crawler_detail(detail_url)
                    if not data:
                        fail_id_list.append(tid)
                        continue

                    data.update({
                        "tid": tid,
                        "section": section,
                        "detail_url": detail_url
                    })
                    article = Article(data)
                    articles.append(article)
                    success_count += 1
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"TID {tid} 抓取失败: {e}")
                    fail_id_list.append(tid)
            page += 1
    with session_scope() as session:
        session.add_all(articles)
    retry_fail_id_list = retry_fail_tid(fid, fail_id_list)
    return success_count, page, retry_fail_id_list


def retry_fail_tid(fid, fail_id_list):
    fail_id_list = list(set(fail_id_list))
    if not fail_id_list:
        return []
    section = section_map[fid]
    logger.info(f"[{section}] 开始补抓失败ID，共 {len(fail_id_list)} 条")
    articles = []
    for tid in fail_id_list[:]:
        detail_url = (
            f"https://sehuatang.org/forum.php?"
            f"mod=viewthread&tid={tid}&extra=page%3D1&mobile=2"
        )
        try:
            data = sht.crawler_detail(detail_url)
            if not data:
                continue
            data.update({
                "tid": tid,
                "section": section,
                "detail_url": detail_url
            })
            article = Article(data)
            articles.append(article)
            fail_id_list.remove(tid)
            time.sleep(random.uniform(2, 3))
        except Exception as e:
            logger.exception(f"TID {tid} 二次抓取仍失败:{e}")
    with session_scope() as session:
        session.add_all(articles)
    logger.info(f"[{section}] 最终失败列表: {fail_id_list}")
    return fail_id_list
