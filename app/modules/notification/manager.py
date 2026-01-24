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

    def send(self, data: dict):
        for sender in self.senders:
            if sender.conf.get('enable'):
                message = Template(sender.conf.get('template')).render(**data)
                try:
                    sender.send(data.get('title'), message, data.get('image'))
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
