# -*- coding: UTF-8 -*-
# @author: ylw
# @file: account
# @time: 2025/1/10
# @desc:
# import sys
# import os
from dataclasses import dataclass, field
from typing import Dict, Optional


# F_PATH = os.path.dirname(__file__)
# sys.path.append(os.path.join(F_PATH, '..'))
# sys.path.append(os.path.join(F_PATH, '../..'))


@dataclass
class AccountConfig:
    platform: str  # 平台
    account: str  # 账
    password: str  # 密
    store_code: str  # 账号编码/子店铺编码
    sub_shop: str = field(default=None)  # 子店铺/抖音
    phone: Optional[int] = field(default=None)  # 手机号
    remarks: str = field(default='')  # 备注


class AccountBaseClass:

    def __init__(self, platform, data: Dict[str, Dict[str, str]]):
        self._account_data: Dict[str, AccountConfig] = self._init_config(platform, data)

    @staticmethod
    def _init_config(platform, data: Dict[str, Dict[str, str]]) -> Dict[str, AccountConfig]:
        new_data: Dict[str, AccountConfig] = {}
        for store_code, account_info in data.items():
            new_data[store_code] = AccountConfig(
                platform=platform,
                account=account_info['account'],
                password=account_info['password'],
                store_code=store_code,
                sub_shop=account_info.get('sub_shop'),
                phone=account_info.get('phone'),
                remarks=account_info.get('remarks'),
            )
        return new_data

    def account_config(self) -> Dict[str, AccountConfig]:
        """动态加载账号配置/暴露一个口子出去/子店铺经常改名的问题可以在这里进行处理(子类重写, 默认不处理)"""
        return self._account_data


if __name__ == '__main__':
    pass
