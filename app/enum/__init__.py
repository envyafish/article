from enum import unique, Enum


@unique
class DownloadClientEnum(Enum):
    QBITTORRENT = "Downloader.qbittorrent"
    TRANSMISSION = "Downloader.transmission"
    THUNDER = "Downloader.thunder"
    CLOUDDRIVE = "Downloader.clouddrive"


@unique
class PusherEnum(Enum):
    WECHAT = "Notification.wechat"
    TELEGRAM = "Notification.telegram"

@unique
class SystemConfigEnum(Enum):
    SYSTEM_CONFIG = "SystemConfig"