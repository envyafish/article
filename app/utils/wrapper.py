import time
import functools
from datetime import datetime
import traceback

from app.core.database import session_scope
from app.models.task_log import TaskLog
from app.modules.notification.manager import pushManager
from app.utils import serialize_result


def task_monitor(func):
    """
    定时任务监控装饰器：
    记录函数名称、开始时间、结束时间、执行时长、执行结果
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from app.scheduler import find_func
        func_name = func.__name__
        start_time = datetime.now()
        start_perf = time.perf_counter()

        result = None
        success = True
        error_msg = None

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            error_msg = traceback.format_exc()
            raise
        finally:
            end_perf = time.perf_counter()
            end_time = datetime.now()
            duration = int(end_perf - start_perf)
            f = find_func(func_name)
            task_log = TaskLog(
                task_name=f['func_label'],
                task_func=func_name,
                start_time=start_time,
                end_time=end_time,
                execute_seconds=duration,
                execute_result=serialize_result(result),
                success=success,
                error=error_msg)

            with session_scope() as session:
                session.add(task_log)
            if f["func_name"] in ['sync_sht_by_tid', 'sync_sht_by_max_page']:
                for row in result:
                    if row['success_count'] > 0 or len(row['fail_list']) > 0:
                        text = (
                            f"【板块】：{row['section']}\n"
                            f"✅ 成功数量：{row['success_count']}\n"
                            f"📄 页码：{row['page']}\n"
                            f"❌ 失败列表：{','.join(row['fail_list'])}"
                        )
                        pushManager.send(text, with_template=False, title="爬取任务结果")
            if f["func_name"] in ['download_by_route']:
                for row in result:
                    if row['success_count'] > 0 or len(row['fail_list']) > 0:
                        text = (
                            f"【任务ID】：{row['id']}\n"
                            f"✅ 成功数量：{row['success_count']}\n"
                            f"❌ 失败列表：{','.join(row['fail_list'])}"
                        )
                        pushManager.send(text, with_template=False, titile="下载任务结果")
    return wrapper
