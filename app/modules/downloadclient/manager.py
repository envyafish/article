from typing import List

from app.enum import DownloadClientEnum
from app.modules.downloadclient.base import BaseDownloader
from app.modules.downloadclient.cloudnas.cloudnas import CloudNas
from app.modules.downloadclient.qbittorrent import QBitTorrentClient
from app.modules.downloadclient.thunder import Thunder
from app.modules.downloadclient.transmission import TransmissionClient


class DownloadManager:
    def __init__(self):
        self.downloaders: List[BaseDownloader] = []

    def register(self, downloader: BaseDownloader):
        self.downloaders.append(downloader)

    def download(self, downloader_name, magnet, save_path):
        for downloader in self.downloaders:
            if downloader_name == downloader.name:
                return downloader.download(magnet, save_path)
        return False

    def reload(self, name, config: dict):
        for downloader in self.downloaders:
            if downloader.name == name:
                self.downloaders.remove(downloader)
        if name == DownloadClientEnum.QBITTORRENT.value:
            self.register(QBitTorrentClient(config))
        if name == DownloadClientEnum.TRANSMISSION.value:
            self.register(TransmissionClient(config))
        if name == DownloadClientEnum.THUNDER.value:
            self.register(Thunder(config))
        if name == DownloadClientEnum.CLOUDDRIVE.value:
            self.register(CloudNas(config))


downloadManager = DownloadManager()
