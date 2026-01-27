import json
import secrets
import string
from datetime import date, datetime
from typing import Dict, get_origin, get_args, Union, Any
from urllib.parse import urlparse



def dict_trans_obj(source: Dict, target: object):
    if not source or not target:
        return

    annotations = getattr(target, "__annotations__", None)
    if not annotations:
        return

    for name, field_type in annotations.items():
        if name not in source:
            continue

        value = source.get(name)
        if value is None:
            setattr(target, name, None)
            continue

        origin = get_origin(field_type)
        args = get_args(field_type)
        if origin is Union and len(args) == 2 and type(None) in args:
            field_type = args[0] if args[1] is type(None) else args[1]

        try:
            if field_type is date and isinstance(value, str):
                value = date.fromisoformat(value)

            elif field_type is datetime and isinstance(value, str):
                value = datetime.fromisoformat(value)

        except ValueError as e:
            raise ValueError(f"Invalid date format for field '{name}': {value}") from e

        setattr(target, name, value)


def get_host_and_port(url):
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port

    # 如果端口号为空，则根据方案设置默认端口
    if port is None:
        if parsed_url.scheme == 'http':
            port = 80
        elif parsed_url.scheme == 'https':
            port = 443

    return host, port


def serialize_result(result: Any) -> str:
    """
    将 dict / list[dict] 安全序列化为字符串，用于数据库存储
    """

    try:
        return json.dumps(
            result,
            ensure_ascii=False,  # 支持中文
            default=str,  # datetime / Decimal 等兜底转字符串
        )
    except Exception as e:
        # 理论上不会发生，但作为最后保险
        return json.dumps(
            {"_serialize_error": str(e)},
            ensure_ascii=False
        )



def generate_secure_random_string(length: int) -> str:
    # 选择字符集（包括字母和数字）
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))