import requests
import json

from app.enum import PusherEnum
from app.modules.notification.base import BaseSender
from app.utils.log import logger


class WeChatNotifier(BaseSender):
    conf: dict
    name = PusherEnum.WECHAT.value

    def __init__(self, conf: dict):
        self.conf = conf

    def get_access_token(self):
        if self.conf.get('corp_id') and self.conf.get('corp_secret') and self.conf.get('agent_id'):
            url = f"{self.conf.get('proxy', 'https://qyapi.weixin.qq.com').rstrip('/')}/cgi-bin/gettoken?corpid={self.conf.get('corp_id')}&corpsecret={self.conf.get('corp_secret')}"
            try:
                response = requests.get(url)
                response_data = response.json()
                if response_data['errcode'] == 0:
                    return response_data['access_token']
                else:
                    logger.error(f"获取微信token失败: {response_data['errmsg']}")
            except Exception as e:
                logger.error(f"获取微信token失败: {e}")
        return None

    def send(self, title=None, message=None, image_url=None):
        if self.conf.get('corp_id') and self.conf.get('corp_secret') and self.conf.get('agent_id'):
            access_token = self.get_access_token()
            url = f"{self.conf.get('proxy', 'https://qyapi.weixin.qq.com').rstrip('/')}/cgi-bin/message/send?access_token={access_token}"
            payload = {
                "touser": self.conf.get('to_user'),
                "msgtype": "news",
                "agentid": self.conf.get('agent_id'),
                "news": {
                    "articles": [
                        {
                            "title": title,
                            "description": message,
                            "url": "",
                            "picurl": image_url if self.conf.get('push_image') else None
                        }
                    ]
                }
            }
            try:
                response = requests.post(url, data=json.dumps(payload))
                response_data = response.json()
                if response_data['errcode'] != 0:
                    logger.error(f"发送微信消息失败: {response_data['errmsg']}")
            except Exception as e:
                logger.error(f"发送微信消息失败: {e}")
