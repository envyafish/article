from abc import ABC, abstractmethod


class BaseDownloader(ABC):
    config: dict
    name: str

    @abstractmethod
    def download(self, magnet: str, save_path: str):
        pass
