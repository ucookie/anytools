#!/usr/bin/python
# -*-coding:utf-8 -*-

import urllib2
import json
import sys
import simplejson

reload(sys)
sys.setdefaultencoding('utf-8')
global ACCESSTOKEN
ACCESSTOKEN = ""

# ========================================================
# 需申请微信企业号，并且将接收消息的微信加入企业号用户组
# 接收消息的微信需要关注该企业号
# 发送消息前，需要先调用connect连接微信号
# ========================================================


class WeChat(object):
    """docstring for WeChat"""
    def __init__(self):
        # 时间标记
        # self.time_flag =
        self.time_out = 0
        self.corpid = ""
        self.corpsecret = ""
        # 接收人信息

    def _gettoken(self):
        gettoken_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + self.corpid + '&corpsecret=' + self.corpsecret
        # print gettoken_url
        try:
            token_file = urllib2.urlopen(gettoken_url)
        except urllib2.HTTPError as e:
            # print e.code
            print e.read().decode("utf8")
            sys.exit()
        token_data = token_file.read().decode('utf-8')
        token_json = json.loads(token_data)
        token_json.keys()
        token = token_json['access_token']
        # 凭证有效时间
        time_out = token_json['expires_in']
        return token, time_out

    def connect(self, corpid, corpsecret):
        """
        参数说明：
        corpid : 企业号提供
        corpsecret : 企业号提供
        """
        self.corpid = corpid
        self.corpsecret = corpsecret
        global ACCESSTOKEN
        ACCESSTOKEN, self.time_out = self._gettoken()

    def senddata(self, message, msgtype="text", user=[], party=[], tag=[]):
        """
        参数说明：
        message <str>: 发送的消息,文本或文件路径
        msgtype <str>: 默认文本信息,message为路径要求如下：
                       # 所有文件size必须大于5个字节
                       # 图片（image）:2MB，支持JPG,PNG格式
                       # 语音（voice）：2MB，播放长度不超过60s，支持AMR格式
                       # 视频（video）：10MB，支持MP4格式
                       # 普通文件（file）：20MB
        user list<str>: 用户名（企业号中提供）
        party list<str>: 部门（企业号中提供）
        tag list<str>: 组别（企业号中提供）
        """
        sending = Data()
        sending.message_des(user, party, tag)
        if not msgtype == "text":
            mediadata = SourceManage()
            mediadata.upload_temp(message, msgtype)
            sending.data = mediadata.temp_source_id
        return sending.senddata(msgtype)

# =======================================================
# 功能模块
# =======================================================


class Data(object):
    """
    about sending data imformation
    """
    def __init__(self):
        self.touser = str()
        self.party = str()
        self.tag = str()
        self.data = str()

    def _encode_info(self, info=[]):
        """
        encode list of [info] to standard type of the API
        """
        encodestr = str()
        for each in info:
            encodestr = encodestr + each + "|"
        return encodestr[:-1]

    def message_des(self, user, party, tag):
        """
        the destination of message
        """
        if len(user) > 0 or len(party) > 0 or len(tag) > 0:
            self.touser = self._encode_info(user)
            self.party = self._encode_info(party)
            self.tag = self._encode_info(tag)
        else:
            raise("Error")

    def senddata(self, msgtype="text"):
        """
        send media text
        """
        if msgtype == "text":
            media_id = "content"
        else:
            media_id = "media_id"
        global ACCESSTOKEN
        send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + ACCESSTOKEN
        send_values = {
            "touser": self.touser,    #企业号中的用户帐号
            "toparty": self.party,    #企业号中的部门id。
            "totag": self.tag, # 标签ID
            "msgtype": msgtype,#消息类型。
            "agentid": "1",    #企业号中的应用id。
            "%s" % msgtype: {
                media_id: self.data},
            "safe": "0"}
        # send_data = json.dumps(send_values, ensure_ascii=False)
        send_data = simplejson.dumps(send_values, ensure_ascii=False).encode('utf-8')
        send_request = urllib2.Request(send_url, send_data)
        response = json.loads(urllib2.urlopen(send_request).read())
        return response


class SourceManage(object):
    """
    source manage
    """
    def __init__(self):
        self.temp_source_id = "0"
        self.source_type = str()
        self.file_path = str()

    def _post(self):
        global ACCESSTOKEN
        post_url = "https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token=" + ACCESSTOKEN + "&type=" + self.source_type

        # add 'f' is to adapt for API
        path = r"f'" + self.file_path + "'"
        form_data = [("media", path)]
        content_type, body = self._encode_multipart_formdata(form_data)
        headers = {'Content-Type': 'multipart/form-data'}
        request = urllib2.Request(url=post_url, headers=headers, data=body)
        response = json.loads(urllib2.urlopen(request).read())
        return response

    def upload_temp(self, file_path, source_type):
        if source_type in ['image', 'voice', 'video', 'file']:
            self.file_path = file_path
            self.source_type = source_type
            self.temp_source_id = self._post()['media_id']

    # ==================================================================
    # 内部函数
    # ==================================================================

    def _get_content_type(self, filename):
        """
        file type
        """
        import mimetypes
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def _isfiledata(self, p_str):
        import re
        r_c = re.compile("^f'(.*)'$")
        rert = r_c.search(str(p_str))
        # rert = re.search("^f'(.*)'$", p_str)
        if rert:
            return rert.group(1)
        else:
            return None

    def _encode_multipart_formdata(self, fields):
        '''''
        该函数用于拼接multipart/form-data类型的http请求中body部分的内容
        返回拼接好的body内容及Content-Type的头定义
        '''
        import random
        import os
        BOUNDARY = '----------%s' % ''.join(random.sample('0123456789abcdef', 15))
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            filepath = self._isfiledata(value)
            if filepath:
                L.append('--' + BOUNDARY)
                L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, os.path.basename(filepath)))
                L.append('Content-Type: %s' % self._get_content_type(filepath))
                L.append('')
                L.append(self._ReadFileAsContent(filepath))
            else:
                L.append('--' + BOUNDARY)
                L.append('Content-Disposition: form-data; name="%s"' % key)
                L.append('')
                L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def _ReadFileAsContent(self, filename):
        """
        read file
        """
        try:
            with open(filename, 'rb') as fobj:
                filecontent = fobj.read()
        except Exception, e:
            print 'The Error Message in ReadFileAsContent(): ' + e.message
            return ''
        return filecontent
