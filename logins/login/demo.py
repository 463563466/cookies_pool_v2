# -*- coding: UTF-8 -*-
# @author: ylw
# @file: demo
# @time: 2025-01-12
# @desc:
# import sys
# import os
from typing import Any

# F_PATH = os.path.dirname(__file__)
# sys.path.append(os.path.join(F_PATH, '..'))
# sys.path.append(os.path.join(F_PATH, '../..'))

from logins.login_base import LoginBase
from lib.models import CheckResult, LoginResult


class DemoLogin(LoginBase):
    def login_status(self, platform, account, sub_shop, cookie: str, *args, **kwargs) -> CheckResult:
        print('登录未失效')
        return CheckResult(valid=True)

    def login(self, platform, account, password, phone=None, store_code=None, sub_shop=None, *args, **kwargs) -> LoginResult:
        print('登录成功')
        return LoginResult(
            success=True,
            cookie=f'demo_account={account};demo_store={store_code};',
            extra={'sub_shop': sub_shop},
        )


if __name__ == '__main__':
    pass
