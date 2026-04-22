# -*- coding: UTF-8 -*-
# @author: ylw
# @file: dp_content
# @time: 2025/1/10
# @desc:
# import sys
# import os
from DrissionPage import WebPage, WebPageTab, ChromiumOptions
from DrissionPage.errors import PageDisconnectedError


# F_PATH = os.path.dirname(__file__)
# sys.path.append(os.path.join(F_PATH, '..'))
# sys.path.append(os.path.join(F_PATH, '../..'))


class DpTabContext:
    def __init__(self, page: WebPage, url: str):
        self._tab: WebPageTab = page.new_tab(url)

    def __enter__(self) -> WebPageTab:
        return self._tab

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._tab.close()


class DpContextSync:
    __last_url = "chrome://new-tab-page-third-party/"

    def __init__(self, browser, page, last_url=None):
        self.__browser: ChromiumOptions = browser
        self._page: WebPage = page
        self._last_url = last_url or self.__last_url

    def __enter__(self):
        return self.__browser, self._page

    def __exit__(self, exc_type, exc_val, exc_tb):
        tabas_id = self._page.tab_ids
        if self._last_url == 'close':
            self._page.quit(timeout=1, force=True)
            return

        this_page_id = self._page.tab_id
        default_tab = self._page.new_tab(self._last_url).tab_id
        for t_id in tabas_id:
            if t_id == default_tab or t_id == this_page_id:
                continue
            try:
                self._page.close_tabs(t_id)
            except PageDisconnectedError:
                pass

        self._page.set.window.mini()
        self._page.close_tabs(this_page_id)


if __name__ == '__main__':
    pass
