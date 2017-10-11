#!/usr/bin/python
# -*- coding:utf-8 -*-
import syslog
import re
import json
import time
import traceback
import os


class FileManage(object):
    """
    文件控制类
    """
    def __init__(self):
        # 当前行位置
        self.currline = 1
        # 文件夹路径
        self.path = "/var/log/app/"
        # 读取增量
        self.plusline = 100
        # 当前读取文件
        self.filename = ""

    def get_file_path(self):
        """
        获取最新的转存文件名
        @return <str> 文件绝对路径
        """
        # 获取路径下所有文件名
        files = os.listdir(self.path)
        repo = r"(?P<name>\bapp.log)-(?P<date>\d{8}\b)"
        file_list = list()
        for each in files:
            # 匹配结果
            re_result = re.match(repo, each)
            if str(re_result) == "None":
                continue
            file_list.append(re_result.groupdict())
        # 返回最新文件
        file_list.sort(key=lambda dict: dict['date'], reverse=True)
        filename = file_list[0]['name'] + '-' + file_list[0]['date']

        # 如果有最新文件则返回文件路径
        if filename != self.filename:
            self.filename = filename
        else:
            return ""

        return self.path + self.filename

    def get_data_from_log(self, filepath):
        """
        获取需要推送的日志
        @param <int> 开始文件行数
        @param <int> 截止文件行数
        @return list<str> 获取到的日志列表
        """
        print filepath
        log_list = list()
        # 文件不存在返回空列表
        if os.path.exists(filepath):
            with open(filepath, "r") as fobj:
                log_data = fobj.read().splitlines(False)
        else:
            return list()
        log_list = log_data[self.currline - 1:len(log_data)]
        return log_list


class Transform(object):
    """
    日志内容处理基类
    """
    def __init__(self):
        # 输入字符串
        self.input_str = ""

    def transform_str(self, input_str):
        pass


class JsonFormat(Transform):
    """
    将日志字符串处理成json字符串
    """
    def __init__(self):
        """记录参数"""
        self.facility = syslog.LOG_USER
        self.severity = syslog.LOG_INFO

    def transform_str(self, input_str):
        """将日志字符串解析成json格式"""
        # 字典key为time,host,owner,pid,level,other,msg
        repo = r"(?P<time>\w+ \d+ \d{2}:\d{2}:\d{2}) (?P<host>\w+) (?P<owner>\w+):( +)?(?P<pid>(\[\d+\])?)(?P<level>(\[\w+\])?) ?(?P<other>(\[\w+\])?) ?(?P<msg>(.*))"
        re_result = re.match(repo, input_str)

        if re_result:
            re_dict = re_result.groupdict()
        # 没有匹配到，返回空字符串
        else:
            return str()

        self.facility, self.severity = self.confirm_leave(re_dict['owner'], re_dict['level'])
        # 计算日志等级pri
        pri = self.facility + self.severity
        # syslog协议日志头e.g:Oct 9 22:33:20 localhost
        header = re_dict['time'] + " " + re_dict['host']
        # 进程号
        pid = re_dict['pid']
        # 日志模块
        owner = re_dict['owner']
        # 日志消息
        msg = re_dict['msg']

        return json.dumps(
            dict(PRI=str(pri), HEADER=header, PID=pid, OWNER=owner, MSG=msg),
            sort_keys=True)

    def confirm_leave(self, owner, level):
        """
        根据日志中的owner,level两个信息，确定facility,severity
        """
        # 给定默认值
        facility = syslog.LOG_USER
        severity = syslog.LOG_INFO
        # as日志级别对应syslog协议级别
        level_info = dict(INFO=syslog.LOG_INFO, WARN=syslog.LOG_WARNING,
                          ERROR=syslog.LOG_ERR, DEBUG=syslog.LOG_DEBUG)

        if level in level_info.keys():
            severity = level_info[level]

        # 判定级别
        if owner in ['ecms_troubleshoot']:
            severity = syslog.syslog.LOG_EMERG

        return facility, severity


class SyslogManage(object):
    def __init__(self):
        """
        给定默认日志等级
        """
        self.facility = syslog.LOG_USER
        self.severity = syslog.LOG_INFO
        self.message = ""

    def push_log_to_server(self):
        """推送日志"""
        try:
            # 单次日志大小超过 128 * 1024 会被不记录该条日志，因此将日志切分记录
            step = 127 * 1024
            for i in xrange(0, len(self.message), step):
                syslog.openlog("", 0, self.facility)
                syslog.syslog(self.severity, self.message[i:i + step])
        except BaseException:
            traceback.print_exc()


def main():
    """main"""
    try:
        filelog = FileManage()
        trans = JsonFormat()
        sendlog = SyslogManage()

        while True:
            list_log = filelog.get_data_from_log(filelog.get_file_path())
            for each in list_log:
                sendlog.message = trans.transform_str(each)
                # 跳过空字符串
                if len(sendlog.message) == 0:
                    continue
                sendlog.facility = trans.facility
                sendlog.severity = trans.severity
                sendlog.push_log_to_server()
            time.sleep(10)

    except KeyboardInterrupt:
        print "C + C"


if __name__ == '__main__':
    main()
