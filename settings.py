# -*- coding: UTF-8 -*-
# @author: ylw
# @file: config
# @time: 2025/1/8
# @desc:
# import sys
# import os
from enum import Enum
from typing import Dict

# F_PATH = os.path.dirname(__file__)
# sys.path.append(os.path.join(F_PATH, '..'))
# sys.path.append(os.path.join(F_PATH, '../..'))

COOKIE_POLL_MAINTAINER = '开始'

ERROR_CODE_MAP: Dict[int, str] = {
    200: "成功",
    401: "密码错误",
    402: "店铺下架",
}


class TableConfig(Enum):
    all_account = 'work_all_account'
    cookies = 'work_all_account_cookie'
    tasks = 'work_all_account_cookie_tasks'
    verifycode = 'work_verification_code'


class MySQLConfig(Enum):
    host = '****************'
    port = 3306
    db = '****************'
    user = '****************'
    password = '****************'
    charset = 'utf8mb4'


class FeishuKey(Enum):
    secret_key = '****************'
    app_id = '****************'


FEISHU_GROUP_CONFIG = {
    "****************": {
        "url": 'https://open.feishu.cn/open-apis/bot/v2/hook/****************',
        "key": '****************'
    }
}

if __name__ == '__main__':
    pass
