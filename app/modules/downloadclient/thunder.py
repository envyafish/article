import re

import requests

from app.enum import DownloadClientEnum
from app.modules.downloadclient.base import BaseDownloader
from app.utils.log import logger


class Thunder(BaseDownloader):
    device_id: str = None
    config: dict = None
    name = DownloadClientEnum.THUNDER.value

    def __init__(self, conf):
        self.config = conf
        self.device_id = self.get_device_id()

    def get_pan_auth(self):
        try:
            index_url = f"{self.config.get('url').rstrip('/')}/webman/3rdparty/pan-xunlei-com/index.cgi/"
            headers = {
                "Authorization": self.config.get('authorization')
            }
            response = requests.get(index_url, headers=headers)
            if response.status_code == 200:
                pattern = r'uiauth\(.*?\)\s*{\s*return\s*"([^"]+)"'
                match = re.search(pattern, response.text)
                return match.group(1)
            else:
                logger.error(f"获取迅雷授权code失败:{response.status_code}")
        except Exception as e:
            logger.error(f"获取迅雷授权code失败:{e}")

    def get_device_id(self):
        if self.config.get('url'):
            try:
                headers = {
                    'pan-auth': self.get_pan_auth(),
                    "Authorization": self.config.get('authorization')
                }
                response = requests.get(
                    f"{self.config.get('url').rstrip('/')}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/tasks?type=user%23runner&device_space=",
                    headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('error'):
                        logger.error(f"获取迅雷设备ID失败:{data['error']}")
                    else:
                        device_id = data['tasks'][0]['params']['target']
                        return device_id
                else:
                    logger.error(f"获取迅雷设备ID失败:{response.status_code}")
            except Exception as e:
                logger.error(f"获取迅雷设备ID失败:{e}")
        return None

    def analyze_size(self, magnet):
        if self.config.get('url'):
            try:
                list_url = f"{self.config.get('url').rstrip('/')}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/resource/list"
                data = {
                    "page_size": 1000,
                    "urls": magnet
                }
                headers = {
                    'pan-auth': self.get_pan_auth(),
                    "Authorization":  self.config.get('authorization')
                }
                logger.info(f"开始解析磁力链接:{magnet}")
                response = requests.post(list_url, json=data, headers=headers)
                if response.status_code == 200:
                    files = response.json()
                    file_size = files['list']['resources'][0]['file_size']
                    return int(file_size / 1024 / 1024)
                else:
                    logger.error(f"解析磁力链接失败:{response.status_code}")
            except Exception as e:
                logger.error(f"解析磁力链接失败:{e}")
        return 0

    def download(self, magnet,file_id):
        if self.config.get('url') and self.device_id:
            try:
                list_url = f"{self.config.get('url').rstrip('/')}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/resource/list"
                data = {
                    "page_size": 1000,
                    "urls": magnet
                }
                pan_auth = self.get_pan_auth()
                headers = {
                    'pan-auth': pan_auth,
                    "Authorization": self.config.get('authorization')
                }
                logger.info(f"开始处理磁力链接下载任务:{magnet}")
                response = requests.post(list_url, json=data, headers=headers)
                if response.status_code == 200:
                    files = response.json()
                    file_name = files['list']['resources'][0]['name']
                    logger.info(f"解析磁力链接完成,种子名称：{file_name}")
                    resource = files['list']['resources'][0]
                    dir = resource.get('dir')
                    resources = []
                    indexs = []
                    file_size = 0
                    if dir:
                        resources = dir.get('resources')
                        if resources:
                            filter_resources = []
                            for index, resource in enumerate(resources):
                                if resource['file_size'] > 1000000000:
                                    indexs.append(str(index))
                                    filter_resources.append(resource)
                            file_size = 0
                            for resource in filter_resources:
                                logger.info(
                                    f"过滤后文件：{resource['name']},体积：{int(resource['file_size'] / 1024 / 1024)}MB")
                                file_size += resource['file_size']
                    if not resources:
                        resources = [resource]
                        file_size = resource['file_size']
                        indexs = "0"
                    task_url = f"{self.config.get('url')}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/task"
                    data = {
                        "params": {
                            "parent_folder_id": file_id,
                            "url": magnet,
                            "target": self.device_id,
                            "total_file_count": str(len(resources)),
                            "sub_file_index": ','.join(indexs)
                        },
                        "file_name": file_name,
                        "file_size": str(file_size),
                        "name": file_name,
                        "type": "user#download-url",
                        "space": self.device_id,
                    }
                    logger.info(f"开始创建迅雷下载任务：{magnet}")
                    response = requests.post(task_url, json=data, headers=headers)
                    if response.status_code == 200:
                        logger.info("成功推送磁力连接到迅雷")
                        return True
                    else:
                        logger.error(f"推送迅雷下载失败:{response.status_code}")
                else:
                    logger.error(f"解析磁力链接失败:{response.status_code}")
            except Exception as e:
                logger.error(f"处理磁力链接下载任务失败:{e}")
        return False
