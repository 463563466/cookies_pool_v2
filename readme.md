# CookiesPool V2

轻量级 cookie 生命周期管理框架。

它不负责实现具体平台登录。短信、滑块、扫码和风控差异很大，具体登录细节应由业务方实现。框架只负责管理账号、登录任务、cookie 状态、失败重试、定时调度和保存 cookie 的抽象流程。

## 适用场景

- 单机运行，维护几十个以内的商家后台账号。
- 登录方式由业务方实现，例如密码、短信、扫码、浏览器缓存复用。
- cookie 保存到业务自己的数据库。
- 需要定时刷新、检测过期、失败冷却和人工介入状态。

## 快速开始

```python
from engine import engine
from lib.cookie_pool import CookiePool
from lib.cookie_pool_config import CookiePoolConfig

from accounts.account_base_class import AccountBaseClass
from account_config import ALL_ACCOUNT_INFO

from logins.login.demo import DemoLogin
from notify.notify_feishu import NotifyFeishu, FeishuKey
from settings import FEISHU_GROUP_CONFIG


cp = CookiePool(engine, CookiePoolConfig(
    account_config=AccountBaseClass('平台', ALL_ACCOUNT_INFO['平台']),
    platform='平台-平台',
    maintainer=[12345678901],
    timer=(5, 23, 10),
    open_init_task=False,
    open_check=False,
))
cp.register_login_instance(DemoLogin)
cp.register_notify_tools(NotifyFeishu, FeishuKey, FEISHU_GROUP_CONFIG)
cp.start()
```

`cp.start()` 是正式运行入口，会启动阻塞式调度器。

运行 demo：

```bash
python demo.py
```

## 框架职责

框架负责：

- 同步账号配置。
- 下发登录任务。
- 调度用户实现的登录类。
- 管理任务状态和 cookie 状态。
- 处理失败重试、冷却和 `manual_required`。
- 调用存储层保存登录结果。

业务方负责：

- 实现具体平台登录。
- 实现 cookie 有效性检测。
- 实现 cookie 如何入库、加密、查询和提供给业务使用。

## 运行流程

```text
注册登录类
  -> 注册通知类
  -> start()
  -> 定时下发登录任务
  -> 定时领取任务并登录
  -> 保存登录结果
  -> 定时检测 cookie
  -> cookie 过期后重新下发登录任务
```

## 核心任务

`enqueue_initial_login_tasks()`

同步账号配置并下发登录任务。同账号已有 `pending` 或 `running` 任务时不会重复下发。

`process_login_tasks()`

领取待登录任务，调用用户实现的 `login()`，保存 `LoginResult`。成功后任务变为 `success`；失败后进入冷却，连续失败后账号进入 `manual_required`。

`check_cookies_and_enqueue_expired()`

调用用户实现的 `login_status()` 检测 cookie。失效时标记为 `expired`，并重新下发登录任务。

## 接入登录类

```python
from logins.login_base import LoginBase
from lib.models import CheckResult, LoginResult


class ShopLogin(LoginBase):
    def login(self, platform, account, password, phone=None, store_code=None, sub_shop=None, *args, **kwargs) -> LoginResult:
        return LoginResult(
            success=True,
            cookie='name=value;',
            reason='',
            extra={'sub_shop': sub_shop},
        )

    def login_status(self, platform, account, sub_shop, cookie: str, *args, **kwargs) -> CheckResult:
        return CheckResult(valid=True)
```

`LoginResult` 表示登录结果，`CheckResult` 表示 cookie 检测结果。

## 接入存储层

`CookieStore` 是框架的存储契约。默认实现是内存存储，只适合 demo 和测试；生产环境建议继承它并接入业务数据库。

```python
from lib.cookie_store import CookieStore


class MySQLCookieStore(CookieStore):
    def save_login_result(self, account_id, login_result, *, platform):
        # 保存 cookie、状态、失败原因、过期时间等。
        # 建议以 platform + account_id 做幂等更新。
        ...

    def list_cookies_for_check(self, platform):
        # 返回需要框架检测的有效 cookie 记录。
        ...
```

框架只定义保存和检测所需的抽象方法，不规定业务侧如何读取 cookie。

## 状态模型

账号状态：

- `enabled`
- `disabled`
- `manual_required`

cookie 状态：

- `valid`
- `expired`
- `refreshing`
- `invalid`

任务状态：

- `pending`
- `running`
- `success`
- `failed`
- `cancelled`

## 依赖

```text
python==3.9.9
DrissionPage==4.0.4.25
SQLAlchemy==1.4.7
pandas==1.3.5
loguru==0.7.2
apscheduler
requests
```
