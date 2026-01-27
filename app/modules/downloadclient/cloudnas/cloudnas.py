import struct
from urllib.parse import unquote

import requests

from app import utils
from app.enum import DownloadClientEnum
from app.modules.downloadclient.base import BaseDownloader
from app.modules.downloadclient.cloudnas import clouddrive_pb2
from app.utils.log import logger


class CloudNas(BaseDownloader):
    config: dict = None
    name = DownloadClientEnum.CLOUDDRIVE.value

    def __init__(self, conf):
        self.config = conf

    def get_token(self):
        if self.config.get('url') and self.config.get('username') and self.config.get('password'):
            try:
                logger.info(f"开始获取CD2 token:{self.config.get('url')}")
                request = clouddrive_pb2.GetTokenRequest(userName=self.config.get('username'),
                                                         password=self.config.get('password'))
                protobuf_bytes = request.SerializeToString()
                prefix = b'\x00' + struct.pack('>I', len(protobuf_bytes))
                payload = prefix + protobuf_bytes

                headers = {
                    "Content-Type": "application/grpc-web",
                    "Accept": "*/*",
                    "X-User-Agent": "grpc-python/1.0",
                    "X-Grpc-Web": "1",
                }
                url = f"{self.config.get('url').rstrip('/')}/clouddrive.CloudDriveFileSrv/GetToken"
                response = requests.post(url, data=payload, headers=headers)
                raw_response = response.content
                if len(raw_response) >= 5:
                    length = int.from_bytes(raw_response[1:5], byteorder="big")
                    message_bytes = raw_response[5:5 + length]

                    jwt_token = clouddrive_pb2.JWTToken()
                    jwt_token.ParseFromString(message_bytes)
                    if jwt_token.success:
                        logger.info(f"获取CD2 token成功")
                        return jwt_token.token
                logger.error("获取CD2 token失败")
            except Exception as e:
                logger.error(f"获取CD2 token失败:{e}")
        return None

    def download(self, magnet, save_path):
        if self.config.get('url') and self.config.get('username') and self.config.get('password'):
            logger.info(f"开始处理CD2离线下载任务：{magnet}")
            token = self.get_token()
            if token:
                request = clouddrive_pb2.AddOfflineFileRequest(urls=magnet, toFolder=save_path)
                protobuf_bytes = request.SerializeToString()
                prefix = b'\x00' + struct.pack('>I', len(protobuf_bytes))
                payload = prefix + protobuf_bytes

                headers = {
                    "Content-Type": "application/grpc-web",
                    "Accept": "*/*",
                    "X-User-Agent": "grpc-python/1.0",
                    "X-Grpc-Web": "1",  # 关键：告诉服务器你是 grpc-web 客户端
                    "Authorization": "Bearer " + token,
                }
                url = f"{self.config.get('url').rstrip('/')}/clouddrive.CloudDriveFileSrv/AddOfflineFiles"
                try:
                    response = requests.post(url, data=payload, headers=headers)
                    if response.headers:
                        if response.headers.get("grpc-message"):
                            logger.error(unquote(response.headers.get("grpc-message")))
                    raw_response = response.content
                    if len(raw_response) >= 5:
                        length = int.from_bytes(raw_response[1:5], byteorder="big")
                        message_bytes = raw_response[5:5 + length]
                        result = clouddrive_pb2.FileOperationResult()
                        result.ParseFromString(message_bytes)
                        if result.success:
                            logger.info("CD2离线下载成功")
                            return True
                        else:
                            logger.error(f"CD2离线下载失败:{result.errorMessage}")
                    else:
                        logger.error(f"CD2离线下载失败")
                except Exception as e:
                    logger.error(f"CD2离线下载失败:{e}")
        return False
