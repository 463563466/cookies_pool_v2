# -*- coding: UTF-8 -*-
# @author: ylw
# @file: dp_baes
# @time: 2025/1/10
# @desc:
# import sys
# import os
from typing import Callable, Union, Optional, ContextManager, List, Dict
from DrissionPage import WebPage, ChromiumOptions

# F_PATH = os.path.dirname(__file__)
# sys.path.append(os.path.join(F_PATH, '..'))
# sys.path.append(os.path.join(F_PATH, '../..'))
from dp.dp_content import DpTabContext, DpContextSync
from dp.tools import calculate_number, path_join

from logger import logger


class DpBase:
    browser: ChromiumOptions = None
    page: WebPage = None

    port: int = None
    user_data_path: str = None

    @staticmethod
    def new_tab_context(page: WebPage, url) -> ContextManager:
        """封装获得新的 tab窗口， 上下文写法"""
        return DpTabContext(page, url)

    @staticmethod
    def new_tab_contex(page: WebPage, url) -> ContextManager:
        """兼容旧方法名。"""
        return DpBase.new_tab_context(page, url)

    def get_page_cookie(self, page: Optional[WebPage] = None, *, all_domain=True, as_dict=False) -> Union[str, dict]:
        """返回当前页面下的cookie"""
        _page = page or self.page
        if not isinstance(_page, WebPage):
            return {} if as_dict else ''
        return ''.join([f"{ck['name']}={ck['value']};" for ck in _page.cookies(all_domains=all_domain, as_dict=False)])

    def get_all_domains_cookie(self, page: Optional[WebPage] = None) -> List[Dict[str, str]]:
        """返回当前页面的所有cookie,并且包含 `domain`"""
        _page = page or self.page
        return _page.cookies(all_domains=True, as_dict=False)

    def _set_path_port(self, port, account_tag, archive_data_path: str):
        port = port or calculate_number(account_tag)  # 根据账号名称计算出来浏览器所使用的端口
        self.browser.set_paths(local_port=port)
        self.port = port
        logger.info(f"计算端口: {account_tag} -> {port}")

        if not archive_data_path:
            return
        user_data_path = path_join(archive_data_path, account_tag, True)
        self.browser.set_paths(user_data_path=user_data_path)
        self.user_data_path = user_data_path
        logger.info(f"设置浏览器缓存: {account_tag} -> {user_data_path}")

    def register_browser(self, func: Callable, before_func: Optional[Callable] = None, last_url='close', **kwargs):
        """注册自动化浏览器页面"""
        self.browser: ChromiumOptions = ChromiumOptions().auto_port()
        if before_func:
            before_func()
        self.page: WebPage = WebPage(chromium_options=self.browser)

        with DpContextSync(self.browser, self.page, last_url=last_url) as (browser, page):
            result = func(page, **kwargs)

        return result


if __name__ == '__main__':
    pass
