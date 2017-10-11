#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Readme:
    e.p: 1.初始化 readobj = KeepalivedCtl('/etc/keepalived.conf')
         2.读取keepalived配置文件 ret = readobj.read_conf(),
         验证输出使用 print json.dumps(obj=ret, indent=4, sort_keys=True)
"""


class KeepalivedCtl(object):

    @classmethod
    def __init__(cls, path):
        cls._conf_path = path
        cls._conf_lines = list()
        with open(path) as fobj:
            read_temp = fobj.readlines()
        for line_temp in read_temp:
            cls._conf_lines.append(line_temp.strip())

    @classmethod
    def read_conf(cls):
        """
        读取keepalived配置文件,返回一个字典
        """
        conf_dict = dict()

        global_defs_info = dict()
        # 获取 global_defs 关键字信息
        (scope_start, scope_end) = cls._get_key_scope("global_defs")
        if scope_start != scope_end:
            global_defs_info['exists'] = True
            config = cls._conf_lines
            for index in range(scope_start, scope_end):
                if config[index].find("router_id") != -1:
                    tmp_list = config[index].strip().split(' ')
                    if len(tmp_list) > 1:
                        global_defs_info['router_id'] = tmp_list[1]

        (scope_start, scope_end) = cls._get_key_scope("vrrp_instance")
        if scope_start != scope_end:
            vrrp_instance_info = cls._get_vrrp_instance_info(scope_start, scope_end)
            vrrp_instance_info['exists'] = True
        conf_dict['global_defs'] = global_defs_info
        conf_dict['vrrp_instance'] = vrrp_instance_info

        return conf_dict

    # ====================================================================
    # 内部函数
    # ====================================================================
    @classmethod
    def _get_key_scope(cls, key):
        """
        获取指定关键字作用域
        @param string key: keepalived.conf 中指定的关键字信息,如 global_defs、vrrp_instance
        @return(tuple(int, int)): 返回关键字的作用范围
        """
        # 读取文件,以 list 形式返回
        brace_count = 0
        scope_start = 0
        scope_end = 0
        is_exists = False

        for idx, row in enumerate(cls._conf_lines):
            if row.find(key) != -1:
                is_exists = True
                brace_count += 1
                scope_start = idx
                continue

            if is_exists:
                # 遇到左花括号, brace_count + 1
                if row.find("{") != -1:
                    brace_count += 1

                # 遇到右花括号, brace_count - 1
                if row.find("}") != -1:
                    brace_count -= 1

                # 当 brace_count = 0时,表示一段完整的程序段读完
                if brace_count == 0:
                    scope_end = idx
                    break
        if brace_count != 0:
            raise Exception("Get scope failed, please check keepalived configuration key=({0})."
                            .format(key))
        return (scope_start, scope_end)

    @classmethod
    def _get_unicast_peer_info(cls, scope_start, scope_end):
        """
        读取 keepalived.conf 获取指定 vrrp_instance 中 unicast_peer 信息
        @param int scope_start: unicast_peer 作用域开始
        @param int scope_end: unicast_peer 作用域结束
        retrun string: keepalived.conf 中 vrrp_instance->unicast_peer ip
        """
        unicast_peer_ip = ""
        # 读取 keepalived.conf 文件,获取
        for index in range(scope_start, scope_end):
            # 忽略第一条
            if cls._conf_lines[index].find("{") != -1:
                continue
            # 当遇到 '}' 字符时终止
            if cls._conf_lines[index].find("}") != -1:
                break
            unicast_peer_ip = cls._conf_lines[index].strip()

        return unicast_peer_ip

    @classmethod
    def _get_vrrp_instance_info(cls, scope_start, scope_end):
        """
        读取 keepalived.conf 获取指定 vrrp_instance 相关配置信息
        @param int scope_start: vrrp_instance 作用域开始
        @param int scope_end: vrrp_instance 作用域结束
        retrun ncTVrrpInstanceInfo: keepalived.conf 中 vrrp_instance 相关信息
        """
        # 定义结构信息
        virtual_ipaddress = []
        vrrp_instance_info = {}
        # 定义 vrrp_instance 的关键字字典,用于保存 vrrp_instance 关键字的值
        vrrp_instance_dict = {}

        # 定义 vrrp_instance 的关键字列表
        vrrp_instance_key_list = ["vrrp_instance_name", "state", "interface",
                                  "virtual_router_id", "priority", "advert_int",
                                  "auth_type", "auth_pass", "unicast_src_ip", "notify_master",
                                  "notify_backup"]

        # 读取 keepalived.conf 文件,获取
        with open(cls._conf_path) as fobj:
            read_temp = fobj.readlines()
        config = list()
        for line_temp in read_temp:
            config.append(line_temp.strip())
        for index in range(scope_start, scope_end):
            for vrrp_instance_key in vrrp_instance_key_list:
                if config[index].find(vrrp_instance_key) != -1:
                    tmp_list = config[index].strip().split(' ')
                    if len(tmp_list) > 1:
                        vrrp_instance_dict[vrrp_instance_key] = tmp_list[1]
                        break
                elif config[index].find("vrrp_instance") != -1:
                    tmp_list = config[index].strip().split(' ')
                    if len(tmp_list) > 1:
                        vrrp_instance_dict["vrrp_instance_name"] = tmp_list[1]
                        break
                elif config[index].find("label") != -1:
                    virtual_ipaddress.append(config[index].strip())
                    break
                elif config[index].find("unicast_peer") != -1:
                    scope_start_unicast = index
                    scope_end_unicast = scope_end
                    unicast_peer_ip = cls._get_unicast_peer_info(
                        scope_start_unicast, scope_end_unicast)
                    vrrp_instance_info['unicast_peer'] = unicast_peer_ip
                else:
                    continue
            vrrp_instance_info['authentication'] = dict()
            # 将字典中的值赋值结构化
            if "vrrp_instance_name" in vrrp_instance_dict:
                vrrp_instance_info['name'] = vrrp_instance_dict["vrrp_instance_name"]
            if "state" in vrrp_instance_dict:
                vrrp_instance_info['state'] = vrrp_instance_dict["state"]
            if "interface" in vrrp_instance_dict:
                vrrp_instance_info['interface_name'] = vrrp_instance_dict["interface"]
            if "virtual_router_id" in vrrp_instance_dict:
                vrrp_instance_info['virtual_router_id'] = int(vrrp_instance_dict["virtual_router_id"])
            if "priority" in vrrp_instance_dict:
                vrrp_instance_info['priority'] = int(vrrp_instance_dict["priority"])
            if "advert_int" in vrrp_instance_dict:
                vrrp_instance_info['advert_int'] = vrrp_instance_dict["advert_int"]
            if "auth_type" in vrrp_instance_dict:
                vrrp_instance_info['authentication']['auth_type'] = vrrp_instance_dict["auth_type"]
            if "auth_pass" in vrrp_instance_dict:
                vrrp_instance_info['authentication']['auth_pass'] = vrrp_instance_dict["auth_pass"]
            if "unicast_src_ip" in vrrp_instance_dict:
                vrrp_instance_info['unicast_src_ip'] = vrrp_instance_dict["unicast_src_ip"]

            vrrp_instance_info['virtual_ipaddress'] = []
            for vip_info in virtual_ipaddress:
                # ["10.10.0.80/24 label em4:ivip dev em4",
                #  "192.168.100.80/24 label em4:ovip dev em4"]
                virtual_ipaddress_info = dict()
                if vip_info.find('/') != -1:
                    tmp_list = vip_info.strip().split('/')
                    if len(tmp_list) == 2:
                        virtual_ipaddress_info['ipaddr'] = tmp_list[0]
                        tmp_list = tmp_list[1].split(' ')
                        if len(tmp_list) == 5:
                            virtual_ipaddress_info['netmask'] = tmp_list[0]
                            virtual_ipaddress_info['virtual_nic_name'] = tmp_list[2]
                            virtual_ipaddress_info['nic_name'] = tmp_list[4]
                vrrp_instance_info['virtual_ipaddress'].append(virtual_ipaddress_info)

        return vrrp_instance_info
