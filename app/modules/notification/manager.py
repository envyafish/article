from jinja2 import Template
from typing import List
from .base import BaseSender
import logging

from .telegram import TelegramNotifier
from .wechat import WeChatNotifier
from ...enum import PusherEnum


class PushManager:
    def __init__(self):
        self.senders: List[BaseSender] = []

    def register(self, sender: BaseSender):
        self.senders.append(sender)

    def send(self, data: dict | str, with_template: bool = True, title: str = None, image_url: str = None):
        for sender in self.senders:
            if sender.conf.get('enable'):
                if with_template:
                    message = Template(sender.conf.get('template')).render(**data)
                    title = data.get('title')
                    image_url = data.get('image')
                else:
                    message = data
                try:
                    sender.send(title, message, image_url)
                except Exception as e:
                    logging.exception(
                        f"推送失败:{sender.name}{e}"
                    )

    def reload(self, name, config: dict):
        for sender in self.senders:
            if sender.name == name:
                self.senders.remove(sender)
        if name == PusherEnum.WECHAT.value:
            self.register(WeChatNotifier(config))
        if name == PusherEnum.TELEGRAM.value:
            self.register(TelegramNotifier(config))


pushManager = PushManager()
