# -*- coding: UTF-8 -*-
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class AccountStatus(str, Enum):
    ENABLED = 'enabled'
    DISABLED = 'disabled'
    MANUAL_REQUIRED = 'manual_required'


class CookieStatus(str, Enum):
    VALID = 'valid'
    EXPIRED = 'expired'
    REFRESHING = 'refreshing'
    INVALID = 'invalid'


class TaskStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


@dataclass
class LoginResult:
    success: bool
    cookie: str = ''
    reason: str = ''
    expire_at: Optional[datetime] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckResult:
    valid: bool
    reason: str = ''
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CookieRecord:
    platform: str
    store_code: str
    account: str
    cookie: str
    status: CookieStatus = CookieStatus.VALID
    expire_at: Optional[datetime] = None
    reason: str = ''
    extra: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class LoginTask:
    task_id: str
    platform: str
    store_code: str
    account: str
    password: str
    phone: Optional[int] = None
    sub_shop: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    locked_at: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    last_error: str = ''
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_login_kwargs(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'platform': self.platform,
            'account': self.account,
            'password': self.password,
            'phone': self.phone,
            'store_code': self.store_code,
            'sub_shop': self.sub_shop,
        }
