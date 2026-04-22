# -*- coding: UTF-8 -*-
# @author: ylw
# @file: feishu_notify
# @time: 2025/1/9
# @desc:
# import sys
# import os
from dataclasses import dataclass
from typing import Union, Type

# F_PATH = os.path.dirname(__file__)
# sys.path.append(os.path.join(F_PATH, '..'))
# sys.path.append(os.path.join(F_PATH, '../..'))
from notify.feishu.feishu_api import FeishuApi, FeishuKey
from notify.notify import NotifyBase


@dataclass
class NotifyToolsInitConfig:
    platform: str
    group_name: str
    maintainer: Union[str, list]
    feishu_key: Type[FeishuKey]
    feishu_group_info: dict


class NotifyFeishu(NotifyBase, FeishuApi):
    def __init__(self, _feishu_key: Type[FeishuKey], feishu_group_info: dict):
        super().__init__()

        self._feishu_key = _feishu_key
        self._feishu_group_info = feishu_group_info

    def send_message(self, group_name: str, mobiles: list = 'all', content: str = ''):
        if isinstance(mobiles, list):
            mobiles = [str(mobile) for mobile in mobiles]
        elif isinstance(mobiles, str):
            mobiles = [mobiles]
        users_info = {m: self.api_user_info(m) for m in mobiles}

        base_content_text = '<at user_id="{user_id}">{name}</at>'
        content_text = ''
        for mobile in mobiles:
            user_info = users_info[mobile]
            content_text += base_content_text.format(user_id=user_info['user_id'], name=user_info['name'])
        content_text += f" {content}"

        group_info = self._feishu_group_info[group_name]
        self.api_send_message(group_info['url'], group_info['key'], content_text)


if __name__ == '__main__':
    def demo():
        from settings import FEISHU_GROUP_CONFIG

        aa = NotifyFeishu(FeishuKey, FEISHU_GROUP_CONFIG)
        aa.send_message('数据采集监控', ['************'], content="这是一段测试文本")
        aa.send_message('数据采集监控', ['************'], content="这是一段测试文本")


    demo()
