# -*- coding: UTF-8 -*-
# @author: ylw
# @file: cookie_poll
# @time: 2025/1/8
# @desc:
# import sys
# import os
import traceback
import inspect
from typing import Any, cast, Dict, Optional
from functools import wraps

# F_PATH = os.path.dirname(__file__)
# sys.path.append(os.path.join(F_PATH, '..'))
# sys.path.append(os.path.join(F_PATH, '../..'))
from lib.cookie_pool_base import CookiePoolBase, LoginBase, NotifyBase, Engine
from lib.cookie_store import CookieStore
from lib.cookie_pool_config import CookiePoolConfig
from lib.models import CheckResult, LoginResult
from accounts.account_base_class import AccountBaseClass, AccountConfig

from utils.wrapper import Wrapper

from logger import logger

FUNC_LOCK_MAP = {}


def synchronized_method(func):
    """
    装饰器：加锁限制同步运行
    :param func: 需要加锁的目标函数
    :return: 包装后的函数
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_id = id(func)
        if FUNC_LOCK_MAP.get(func_id, True) is False:
            return

        try:
            FUNC_LOCK_MAP[func_id] = False
            return func(*args, **kwargs)
        except Exception as e:
            logger.info(traceback.format_exc())
            raise e
        finally:
            FUNC_LOCK_MAP[func_id] = True

    return cast(Wrapper.F, wrapper)


class CookiePool(CookiePoolBase):

    def __init__(
            self,
            engine: Engine,
            config: CookiePoolConfig,
            debugger: bool = False,
            store: Optional[CookieStore] = None
    ):
        if not isinstance(config, CookiePoolConfig):
            return
        # 工具
        self.engine: Engine = engine
        self.cookie_store = store or CookieStore(self.engine)

        # 任务配置相关
        self.account_config: AccountBaseClass = config.account_config
        self.platform: str = config.platform  # 平台
        self.maintainer: list = config.maintainer  # 通知负责人
        self.timer: tuple = config.timer  # 定时运行时间 tuple：[每天的开始时间(h), 结束时间(h), 检测间隔(单位分钟)]
        self.open_init_task = config.open_init_task  # 主动下发任务
        self.open_check = config.open_check  # 主动检测
        self.debugger = debugger  # debugger模式

        # 类
        self.login_instance: Optional[LoginBase] = None
        self.notify_tools: Optional[NotifyBase] = None

        self._sync_accounts()
        if config.open_init_task:
            self.enqueue_initial_login_tasks()

    @staticmethod
    def _normalize_login_result(result: Any) -> LoginResult:
        if isinstance(result, LoginResult):
            return result
        if isinstance(result, dict):
            return LoginResult(
                success=bool(result.get('success', result.get('cookie'))),
                cookie=result.get('cookie', ''),
                reason=result.get('reason', ''),
                expire_at=result.get('expire_at'),
                extra=result.get('extra', result),
            )
        return LoginResult(success=bool(result), reason='' if result else '登录失败')

    @staticmethod
    def _normalize_check_result(result: Any) -> CheckResult:
        if isinstance(result, CheckResult):
            return result
        if isinstance(result, dict):
            return CheckResult(
                valid=bool(result.get('valid', result.get('success'))),
                reason=result.get('reason', ''),
                extra=result.get('extra', result),
            )
        return CheckResult(valid=bool(result), reason='' if result else 'cookie已失效')

    def _sync_accounts(self):
        account_config: Dict[str, AccountConfig] = self.account_config.account_config()
        self.cookie_store.sync_accounts(self.platform, account_config)

    def _call_login(self, login_kwargs: Dict[str, Any]) -> Any:
        login_params = inspect.signature(self.login_instance.login).parameters
        if 'password' not in login_params and 'pwd' in login_params:
            login_kwargs = login_kwargs.copy()
            login_kwargs['pwd'] = login_kwargs.pop('password')
        return self.login_instance.login(**login_kwargs)

    def enqueue_initial_login_tasks(self):
        """主动推送任务"""
        self._sync_accounts()
        account_config: Dict[str, AccountConfig] = self.account_config.account_config()
        for store_code in account_config.keys():
            self.cookie_store.enqueue_login_task(store_code, platform=self.platform, reason='initial_enqueue')

    def check_cookies_and_enqueue_expired(self):
        """登录失效,推送任务(需要进行检测)"""
        if not self.login_instance:
            raise RuntimeError('请先注册登录类')

        cookie_records = self.cookie_store.list_cookies_for_check(self.platform)
        if not cookie_records:
            logger.info("暂时无账号需要检测")
            return
        for cookie_record in cookie_records:
            account = cookie_record.account
            store_code = cookie_record.store_code
            sub_shop = cookie_record.extra.get('sub_shop')
            cookie = cookie_record.cookie
            notify_shop = sub_shop or account  # 根据不同的平台, 选择 店铺或者子店铺 进行通知

            status = self._normalize_check_result(
                self.login_instance.login_status(self.platform, account, sub_shop, cookie)
            )
            if status.valid is True:
                logger.info(f"{self.platform} {notify_shop} cookie未过期")
                continue

            logger.info(f"{self.platform} {notify_shop} cookie过期, 下发到任务数据库")
            self.cookie_store.mark_cookie_expired(self.platform, store_code, status.reason)
            self.cookie_store.enqueue_login_task(store_code, platform=self.platform, reason=status.reason)

    @synchronized_method
    def process_login_tasks(self):
        """根据任务队列生成cookie"""
        if not self.login_instance:
            raise RuntimeError('请先注册登录类')

        tasks = self.cookie_store.claim_login_task(self.platform)
        for task in tasks:
            try:
                login_result = self._normalize_login_result(self._call_login(task.to_login_kwargs()))
                self.cookie_store.save_login_result(task.store_code, login_result, platform=self.platform)
                if login_result.success:
                    self.cookie_store.mark_task_success(task.task_id)
                    continue
                self.cookie_store.mark_task_failed(task.task_id, login_result.reason or '登录失败')
            except Exception as e:
                logger.info(traceback.format_exc())
                self.cookie_store.mark_task_failed(task.task_id, str(e))
                raise e


if __name__ == '__main__':
    def demo():
        from settings import MySQLConfig
        from accounts.account_base_class import AccountBaseClass
        from account_config import ALL_ACCOUNT_INFO

        from logins.login.demo import DemoLogin
        from notify.notify_feishu import NotifyFeishu, FeishuKey
        from settings import FEISHU_GROUP_CONFIG

        cp = CookiePool(Engine(MySQLConfig), CookiePoolConfig(
            account_config=AccountBaseClass('平台', ALL_ACCOUNT_INFO['平台']),
            platform='平台-平台',
            maintainer=[12345678901],  # 消息通知人手机号
            timer=(5, 23, 10),
            open_init_task=False,
            open_check=False
        ))
        cp.register_login_instance(DemoLogin)  # 注册登录类
        cp.register_notify_tools(NotifyFeishu, FeishuKey, FEISHU_GROUP_CONFIG)  # 注册通知类

        cp.start()


    demo()
