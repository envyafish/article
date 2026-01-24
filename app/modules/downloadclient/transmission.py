import time

import transmission_rpc

from app import utils
from app.enum import DownloadClientEnum
from app.modules.downloadclient.base import BaseDownloader
from app.utils.log import logger


class TransmissionClient(BaseDownloader):
    config: dict = None
    name = DownloadClientEnum.TRANSMISSION.value
    client: transmission_rpc.Client = None
    anti_leech: bool = True

    def __init__(self, conf):
        self.config = conf

    def login_transmission(self):
        if self.config.get('url') and self.config.get('username') and self.config.get('password'):
            host, port = utils.get_host_and_port(self.config.get('url'))
            try:
                self.client = transmission_rpc.Client(
                    host=host,
                    port=port,
                    username=self.config.get('username'),
                    password=self.config.get('password')
                )
                self.client.session_stats()
                return True
            except Exception as e:
                logger.error(f"Transmission连接失败：{e}")
        return False

    def download(self, magnet, save_path):
        if self.login_transmission():
            try:
                logger.info(f"添加磁力链接到Transmission成功")
                self.client.add_torrent(torrent=magnet,
                                        download_dir=save_path)
                torrent_hash = magnet.split('btih:')[1].split('&')[0].lower()
                max_retries = 10
                retries = 0
                torrent_info = None
                torrent_id = None

                while retries < max_retries:
                    try:
                        torrent_info = self.client.get_torrent(torrent_hash)
                        torrent_id = torrent_info.id
                        if torrent_info:
                            break
                    except Exception as e:
                        logger.error(f"获取文件信息出错: {e}")
                    time.sleep(6)
                    retries += 1

                if not torrent_info:
                    logger.error("无法获取文件信息")
                    return False
                small_file_ids = []
                for file_info in torrent_info.files():
                    file_size_mb = file_info.size / (1024 * 1024)
                    if file_size_mb < 200:
                        small_file_ids.append(file_info.id)

                if small_file_ids:
                    self.client.change_torrent(ids=[torrent_id],
                                               files_unwanted=small_file_ids,
                                               seed_ratio_limit=0 if self.anti_leech else None)
                    logger.info(f"添加磁力链接成功")
                return True
            except Exception as e:
                logger.error(f"添加磁链链接失败:{e}")
                return False
        return False
