# -*- coding: UTF-8 -*-
# @author: ylw
# @file: engine_base
# @time: 2025/1/8
# @desc:
# import sys
# import os
from urllib import parse
from functools import wraps
from typing import Type, TypeVar, cast, Callable, ContextManager, Optional, Any

from sqlalchemy import create_engine
from sqlalchemy import __version__ as sqlalchemy_version
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine import Connection

# F_PATH = os.path.dirname(__file__)
# sys.path.append(os.path.join(F_PATH, '..'))
# sys.path.append(os.path.join(F_PATH, '../..'))
from db_engine.switch_db import SwitchDB
from settings import MySQLConfig


class EngineBase:
    CONN_MODE = "mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset={charset}"
    engine: Optional[Engine] = None
    __F = TypeVar('__F', bound=Callable[..., Optional[Any]])

    def __new__(cls, *args, **kwargs):
        if cls is EngineBase:
            raise TypeError("Cannot instantiate EngineBase directly. It must be subclassed.")
        return super().__new__(cls)

    def engine_create(self, mysql_config: Type[MySQLConfig]) -> Engine:
        return create_engine(self.CONN_MODE.format(
            user=mysql_config.user.value,
            password=parse.quote(mysql_config.password.value),
            host=mysql_config.host.value,
            port=mysql_config.port.value,
            charset=mysql_config.charset.value,
            db=mysql_config.db.value,
        ), pool_recycle=3600, pool_pre_ping=True)

    def engine_close(self):
        try:
            self.engine.dispose()
        except:
            pass

    def connect_get(self, close_with_result=False) -> Connection:
        """
        获取数据库连接，并根据不同版本和配置来处理事务。
        :param close_with_result: 是否在操作后关闭连接（默认为 False）。
        :return: 数据库连接对象，可能会自动管理事务。
        """
        if sqlalchemy_version.startswith('2.'):
            return self.engine.begin(close_with_result=close_with_result)
        return self.engine.connect(close_with_result=close_with_result)

    def with_switch_db(self, dbname: str, current_dbname: Optional[str] = None) -> ContextManager:
        return SwitchDB(self.engine, dbname, current_dbname=current_dbname)

    def with_txn_wrapper(self, func):
        """事务装饰器, 自动处理事务的开始, 提交和回滚"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取数据库连接
            with self.connect_get() as conn:
                with conn.begin():
                    return func(*args, **kwargs, conn=conn)

        return cast(self.__F, wrapper)


if __name__ == '__main__':
    pass
