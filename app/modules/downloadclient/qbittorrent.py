import time

import qbittorrentapi

from app.enum import DownloadClientEnum
from app.modules.downloadclient.base import BaseDownloader
from app.utils.log import logger


class QBitTorrentClient(BaseDownloader):
    config: dict = None
    name = DownloadClientEnum.QBITTORRENT.value
    anti_leech: bool = True
    client: qbittorrentapi.Client = None

    def __init__(self, conf):
        self.config = conf

    def login_qb(self):
        if self.config.get('url') and self.config.get('username') and self.config.get('password'):
            self.client = qbittorrentapi.Client(
                host=self.config.get('url'),
                username=self.config.get('username'),
                password=self.config.get('password')
            )
            try:
                self.client.auth_log_in()
                return True
            except Exception as e:
                logger.error(f"qBittorrent连接失败: {e}")
        return False


    def download(self, magnet, save_path):
        if self.login_qb():
            try:
                logger.info(f"添加磁力链接到QBittorrent成功")
                self.client.torrents_add(urls=magnet,
                                         save_path=save_path,
                                         seeding_time_limit=0 if self.anti_leech else None)
                torrent_hash = magnet.split('btih:')[1].split('&')[0].lower()
                max_retries = 10
                retries = 0
                files_info = []

                while retries < max_retries:
                    try:
                        files_info = self.client.torrents_files(torrent_hash)
                        if files_info:
                            break
                    except Exception as e:
                        logger.error(f"获取文件信息出错: {e}")
                    time.sleep(6)
                    retries += 1

                if not files_info:
                    logger.error("无法获取文件信息")
                    return False
                small_file_ids = []
                for file_info in files_info:
                    file_size_mb = file_info['size'] / (1024 * 1024)
                    if file_size_mb < 200:
                        small_file_ids.append(file_info['index'])
                if small_file_ids:
                    self.client.torrents_file_priority(torrent_hash, small_file_ids, 0)
                    logger.info(f"添加磁力链接成功")
                return True
            except Exception as e:
                logger.error(f"添加磁链链接失败:{e}")
                return False
        return False
