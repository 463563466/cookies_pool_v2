# -*- coding: UTF-8 -*-
# @author: ylw
# @file: engine
# @time: 2025/1/8
# @desc:
# import sys
# import os
import pandas as pd
from typing import Type, List, Optional, Union
from sqlalchemy.sql import text as sqlalchemy_text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

# F_PATH = os.path.dirname(__file__)
# sys.path.append(os.path.join(F_PATH, '..'))
# sys.path.append(os.path.join(F_PATH, '../..'))
from db_engine.engine_base import EngineBase
from settings import MySQLConfig


class Engine(EngineBase):
    def __init__(self, mysql_config: Type[MySQLConfig]):
        self.engine = self.engine_create(mysql_config)

    @staticmethod
    def tool_insert_dict2sql(data: dict, table: str) -> str:
        keys = list(data.keys())
        col = ','.join(keys)
        placeholder = ', '.join(['%s'] * len(keys))
        return f"""insert into {table} ({col}) values ({placeholder});"""

    @staticmethod
    def tool_replace_dict2sql(data: dict, table: str) -> str:
        keys = list(data.keys())
        col = ','.join(keys)
        placeholder = ', '.join(['%s'] * len(keys))
        return f"""replace into {table} ({col}) values ({placeholder});"""

    @staticmethod
    def __c_execute(sql: str, values: Optional[tuple] = None, *, conn: Connection, safe_ignorePK: bool = False) -> bool:
        """自定义 execute"""
        try:
            conn.execute(sql, values) if values else conn.execute(sqlalchemy_text(sql))
        except IntegrityError as e:
            if safe_ignorePK is True:
                return False
            raise e
        return True

    def fetch_data(self, sql: str, fetch_number: Optional[int] = None) -> List[dict]:
        _fetch_number = fetch_number if isinstance(fetch_number, int) and fetch_number > 0 else -1
        with self.connect_get() as conn:
            result = conn.execute(sqlalchemy_text(sql))
            data_row = result.fetchmany(_fetch_number) if _fetch_number > 0 else result.fetchall()
            return [dict(row) for row in data_row]

    def fetch_data2df(self, sql) -> pd.DataFrame:
        with self.connect_get() as conn:
            return pd.read_sql(sql, conn)

    def insert_execute(self, item: Union[dict, List[dict]], *, table: str, safe_ignorePK=False, conn: Connection):
        data_list = [item] if isinstance(item, dict) else item
        if not isinstance(data_list, list):
            raise ValueError("Invalid input type, expected dict, list of dicts")

        for idx, data in enumerate(data_list):
            if not isinstance(data, dict):
                raise ValueError(f"Invalid data at index {idx}: Expected a dictionary, but got {type(data).__name__}.")

            sql = self.tool_insert_dict2sql(data, table)
            self.__c_execute(sql, tuple(data.values()), conn=conn, safe_ignorePK=safe_ignorePK)

    def insert_data2table(self, item: Union[dict, List[dict]], *, table: str, safe_ignorePK=False):
        """执行【insert】操作"""
        with self.connect_get() as conn:
            self.insert_execute(item, table=table, safe_ignorePK=safe_ignorePK, conn=conn)


if __name__ == '__main__':
    def demo():
        engine = Engine(MySQLConfig)
        engine.engine_close()


    demo()
