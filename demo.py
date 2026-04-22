# -*- coding: UTF-8 -*-
from engine import engine
from lib.cookie_pool import CookiePool
from lib.cookie_pool_config import CookiePoolConfig

from accounts.account_base_class import AccountBaseClass
from account_config import ALL_ACCOUNT_INFO

from logins.login.demo import DemoLogin
from notify.notify_feishu import NotifyFeishu, FeishuKey
from settings import FEISHU_GROUP_CONFIG


def demo():
    """
    阻塞式运行入口：注册登录类和通知类后，由调度器持续维护 cookie。
    真实业务中只需要把 DemoLogin 替换成自己的平台登录类。
    """
    cp = CookiePool(engine, CookiePoolConfig(
        account_config=AccountBaseClass('平台', ALL_ACCOUNT_INFO['平台']),
        platform='平台-平台',
        maintainer=[12345678901],
        timer=(5, 23, 10),
        open_init_task=False,
        open_check=False
    ))
    cp.register_login_instance(DemoLogin)
    cp.register_notify_tools(NotifyFeishu, FeishuKey, FEISHU_GROUP_CONFIG)
    cp.start()


if __name__ == '__main__':
    demo()
