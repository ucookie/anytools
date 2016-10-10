# -*- coding: utf-8 -*-
import urllib2


class HtmlDownloader(object):
    def download(self, url):
    	"""
        下载网页
        """
        if url is None:
            return None
        # 打开网页链接
        response = urllib2.urlopen(url)

        # 页面请求的状态值
        # 200请求成功、303重定向、400请求错误、401未授权
        # 403禁止访问、404文件未找到、500服务器错误
        if response.getcode() != 200:
            return None

        return response.read()
