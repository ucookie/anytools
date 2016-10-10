# -*- coding: utf-8 -*-
import log

MODE_NAME = 'UrlManager'


class UrlManager(object):
    def __init__(self):
        self.new_urls = set()
        self.old_urls = set()

    def add_new_url(self, url):
        """
        添加新的访问链接
        """
        if url is None:
            return
        if url not in self.new_urls and url not in self.old_urls:
            self.new_urls.add(url)

    def add_new_urls(self, urls):
        """
        添加多条访问连接
        """
        if urls is None or len(urls) == 0:
            return
        for url in urls:
            self.add_new_url(url)
        log.syslog(MODE_NAME, 'add some new urls')

    def has_new_url(self):
        """
        判断链接池是否为空
        """
        return len(self.new_urls) != 0

    def get_new_url(self):
        """
        获取链接池中的一条数据
        """
        new_url = self.new_urls.pop()
        self.old_urls.add(new_url)
        return new_url
