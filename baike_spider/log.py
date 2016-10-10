#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime


def syslog(owner, msg):
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_info = '[%s] [%s] [SYSLOG] : %s' % (time, owner, msg)
    with open('spider_log.txt', 'a') as foo:
        foo.write(log_info + '\n')
