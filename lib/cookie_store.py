# -*- coding: UTF-8 -*-
# @author: ylw
# @file: cookie_store
# @time: 2025/1/10
# @desc:
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from accounts.account_base_class import AccountConfig
from db_engine.engine import Engine
from lib.models import (
    AccountStatus,
    CookieRecord,
    CookieStatus,
    LoginResult,
    LoginTask,
    TaskStatus,
)
from settings import TableConfig
from utils.wrapper import Wrapper

from logger import logger


class CookieStore:
    """
    cookie 管理存储契约。

    默认实现使用内存数据，方便 demo 和单元测试直接跑通完整生命周期。
    生产环境建议继承本类，将这些方法映射到自己的 MySQL 表结构或任务队列。
    """

    task_table = TableConfig.tasks.value
    cookie_table = TableConfig.cookies.value

    PLATFORM_RENAME_MAP = {}

    def __init__(self, engine: Optional[Engine] = None, *, cooldown_seconds: int = 600, max_failures: int = 3):
        self.engine = engine
        self.cooldown_seconds = cooldown_seconds
        self.max_failures = max_failures
        self._accounts: Dict[str, AccountConfig] = {}
        self._account_status: Dict[str, AccountStatus] = {}
        self._cookies: Dict[str, CookieRecord] = {}
        self._tasks: Dict[str, LoginTask] = {}
        self._task_seq = 0

    @staticmethod
    def _account_key(platform: str, store_code: str) -> str:
        return f'{platform}:{store_code}'

    def sync_accounts(self, platform: str, account_config: Dict[str, AccountConfig]):
        """同步账号配置到存储层，供任务下发和状态判断使用。"""
        for store_code, account in account_config.items():
            key = self._account_key(platform, store_code)
            self._accounts[key] = account
            self._account_status.setdefault(key, AccountStatus.ENABLED)

    def list_accounts(self, platform: str) -> List[AccountConfig]:
        """列出指定平台启用中的账号。"""
        accounts = []
        for key, account in self._accounts.items():
            if not key.startswith(f'{platform}:'):
                continue
            if self._account_status.get(key) != AccountStatus.ENABLED:
                continue
            accounts.append(account)
        return accounts

    def enqueue_login_task(self, account_id: str, *, platform: str, reason: str = '') -> Optional[str]:
        """下发登录任务。同账号已有 pending/running 任务时保持幂等。"""
        account_key = self._account_key(platform, account_id)
        account = self._accounts.get(account_key)
        if not account:
            logger.info(f'账号不存在，无法下发任务: {account_key}')
            return None
        if self._account_status.get(account_key) != AccountStatus.ENABLED:
            logger.info(f'账号不可用，跳过下发任务: {account_key}')
            return None

        for task in self._tasks.values():
            if task.platform == platform and task.store_code == account_id and task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                return task.task_id

        self._task_seq += 1
        task_id = f'{platform}-{account_id}-{self._task_seq}'
        self._tasks[task_id] = LoginTask(
            task_id=task_id,
            platform=platform,
            store_code=account.store_code,
            account=account.account,
            password=account.password,
            phone=account.phone,
            sub_shop=account.sub_shop,
            last_error=reason,
            max_retries=self.max_failures,
        )
        return task_id

    def claim_login_task(self, platform: str, limit: int = 1) -> List[LoginTask]:
        """领取待登录任务，领取后状态进入 running。"""
        now = datetime.now()
        claimed = []
        for task in self._tasks.values():
            if len(claimed) >= limit:
                break
            if task.platform != platform or task.status != TaskStatus.PENDING:
                continue
            if task.cooldown_until and task.cooldown_until > now:
                continue
            account_key = self._account_key(task.platform, task.store_code)
            if self._account_status.get(account_key) != AccountStatus.ENABLED:
                continue
            task.status = TaskStatus.RUNNING
            task.locked_at = now
            task.updated_at = now
            claimed.append(task)
        return claimed

    def save_login_result(self, account_id: str, login_result: LoginResult, *, platform: str):
        """保存登录结果。成功时写入有效 cookie，失败时标记 cookie 无效。"""
        account_key = self._account_key(platform, account_id)
        account = self._accounts.get(account_key)
        if not account:
            raise KeyError(f'账号不存在: {account_key}')

        if not login_result.success:
            old_record = self._cookies.get(account_key)
            if old_record:
                old_record.status = CookieStatus.INVALID
                old_record.reason = login_result.reason
                old_record.updated_at = datetime.now()
            return

        self._cookies[account_key] = CookieRecord(
            platform=platform,
            store_code=account.store_code,
            account=account.account,
            cookie=login_result.cookie,
            status=CookieStatus.VALID,
            expire_at=login_result.expire_at,
            reason=login_result.reason,
            extra=login_result.extra,
        )
        logger.info(f'储存cookie成功: {platform} {account.store_code}')

    def save_cookie(self, account_id: str, login_result: LoginResult, *, platform: str):
        """兼容旧方法名：保存登录结果。"""
        return self.save_login_result(account_id, login_result, platform=platform)

    def mark_task_success(self, task_id: str):
        task = self._tasks[task_id]
        task.status = TaskStatus.SUCCESS
        task.updated_at = datetime.now()
        task.last_error = ''

    def mark_task_failed(self, task_id: str, reason: str):
        task = self._tasks[task_id]
        task.retry_count += 1
        task.last_error = reason
        task.updated_at = datetime.now()

        account_key = self._account_key(task.platform, task.store_code)
        if task.retry_count >= task.max_retries:
            task.status = TaskStatus.FAILED
            self._account_status[account_key] = AccountStatus.MANUAL_REQUIRED
            return

        task.status = TaskStatus.PENDING
        task.cooldown_until = datetime.now() + timedelta(seconds=self.cooldown_seconds)

    def list_cookies_for_check(self, platform: str) -> List[CookieRecord]:
        """列出需要检测的有效 cookie。"""
        records = []
        for key, record in self._cookies.items():
            if record.platform != platform or record.status != CookieStatus.VALID:
                continue
            if self._account_status.get(key) != AccountStatus.ENABLED:
                continue
            records.append(record)
        return records

    def mark_cookie_expired(self, platform: str, store_code: str, reason: str = ''):
        account_key = self._account_key(platform, store_code)
        record = self._cookies.get(account_key)
        if record:
            record.status = CookieStatus.EXPIRED
            record.reason = reason
            record.updated_at = datetime.now()

    # 兼容旧方法名
    def fetch_task(self, platform):
        return [record.__dict__.copy() for record in self.list_cookies_for_check(platform)]

    def send_task(self, platform: str, store_code):
        return self.enqueue_login_task(store_code, platform=platform)

    def get_task_queue(self, platform: str) -> List[dict]:
        return [task.to_login_kwargs() for task in self.claim_login_task(platform)]

    @Wrapper.retry_until_done(10, 6, desc="获取验证码失败")
    def sms_verify_code(self, phone: int, platform: str, send_time: Optional[str] = None) -> Optional[str]:
        """获取短信验证码。默认实现仅用于 demo，生产环境应继承后接入短信来源。"""
        return "123456"


if __name__ == '__main__':
    pass
