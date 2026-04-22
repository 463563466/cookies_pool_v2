# -*- coding: UTF-8 -*-
# @author: ylw
# @file: poll_init_config
# @time: 2025/1/9
# @desc:
# import sys
# import os
from dataclasses import dataclass, field
from typing import List, Optional
from accounts.account_base_class import AccountBaseClass

# F_PATH = os.path.dirname(__file__)
# sys.path.append(os.path.join(F_PATH, '..'))
# sys.path.append(os.path.join(F_PATH, '../..'))

__all__ = [
    'CookiePoolConfig',
]


@dataclass
class CookiePoolConfig:
    account_config: AccountBaseClass  # 账号配置信息类
    platform: str  # 登录平台  格式：【平台-子平台 | 平台】
    maintainer: Optional[List[int]]  # 登录程序报错， 通知给负责人 类型: list
    timer: tuple = field(default=(5, 23, 30))  # 定时运行时间 tuple：[每天的开始时间(h), 结束时间(h), 检测间隔(单位分钟)]
    open_init_task: bool = field(default=True)  # 程序初始化下发cookie任务
    open_check: bool = field(default=True)  # 需要检测cookie是否过期

    def __post_init__(self):
        # 检查 account_config 是否为字典类型
        if not isinstance(self.account_config, AccountBaseClass):
            raise ValueError('All account_config values must be AccountConfig.')

        if not self.maintainer:
            self.maintainer = None

        # 检查 timer 参数
        if not isinstance(self.timer, tuple) or len(self.timer) != 3:
            raise ValueError('timer must be a tuple of length 3.')

        start, end, interval = self.timer
        if not (0 <= start < 24) or not (0 <= end < 24) or not (0 < interval < 60):
            raise ValueError('Timer parameters must be: start(0-23), end(0-23), interval(1-59).')

        # 检查 open_init_task 和 open_check 是否为布尔值
        if not isinstance(self.open_init_task, bool):
            raise ValueError('open_init_task must be a boolean value.')

        if not isinstance(self.open_check, bool):
            raise ValueError('open_check must be a boolean value.')


if __name__ == '__main__':
    pass
