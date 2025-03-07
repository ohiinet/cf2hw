# Mail: tongdongdong@outlook.com
import random
import time
import json
import requests
import os
import traceback
from dns.qCloud import QcloudApiv3 # QcloudApiv3 DNSPod 的 API 更新了 github@z0z0r4
from dns.aliyun import AliApi
from dns.huawei import HuaWeiApi
import sys

#可以从https://shop.hostmonit.com获取
KEY = os.environ["KEY"]  #"o1zrmHAF"
#CM:移动 CU:联通 CT:电信 AB:境外 DEF:默认
#修改需要更改的dnspod域名和子域名
DOMAINS = json.loads(os.environ["DOMAINS"])  #{"hostmonit.com": {"@": ["CM","CU","CT"], "shop": ["CM", "CU", "CT"], "stock": ["CM","CU","CT"]},"4096.me": {"@": ["CM","CU","CT"], "vv": ["CM","CU","CT"]}}
#腾讯云后台获取 https://console.cloud.tencent.com/cam/capi
SECRETID = os.environ["SECRETID"]    #'AKIDV**********Hfo8CzfjgN'
SECRETKEY = os.environ["SECRETKEY"]   #'ZrVs*************gqjOp1zVl'

#DNSPOD免费版只支持两条, 华为支持集合
AFFECT_NUM = 3
#DNS服务商 DNSPod改为1 阿里云解析改成2  华为云解析改成3 华为云解析集合3.1
DNS_SERVER = 3.1
#如果试用华为云解析 需要从API凭证-项目列表中获取
REGION_HW = 'cn-east-3'
#如果使用阿里云解析 REGION出现错误再修改 默认不需要修改 https://help.aliyun.com/document_detail/198326.html
REGION_ALI = 'cn-hongkong'
#解析生效时间，默认为600秒 (华为可设置300)
TTL = 300
#v4为筛选出IPv4的IP  v6为筛选出IPv6的IP
if len(sys.argv) >= 2:
    RECORD_TYPE = sys.argv[1]
else:
    RECORD_TYPE = "A"

#api
API_1 = 'https://api.hostmonit.com/get_optimization_ip' # hostmonit
#API_2 = 'https://api.345673.xyz/get_data'
API_2 = 'https://api.vvhan.com/tool/cf_ip'
API_3 = 'https://www.wetest.vip/api/cf2dns/get_cloudflare_ip'

#fixed ip
# remove: 8.20.125.1, 141.101.120.121, 141.101.123.173
if RECORD_TYPE == "A":
    API = API_3

    self_cm_cfips = ""
    self_cu_cfips = ""
    self_ct_cfips = ""
    self_def_cfips = ""
    self_cm_cfips_list = [{"ip": ip} for ip in self_cm_cfips.split(',')]
    self_cu_cfips_list = [{"ip": ip} for ip in self_cu_cfips.split(',')]
    self_ct_cfips_list = [{"ip": ip} for ip in self_ct_cfips.split(',')]
    self_def_cfips_list = [{"ip": ip} for ip in self_ct_cfips.split(',')]
else:
    API = API_3

    self_cm_cfips = ""
    self_cu_cfips = ""
    self_ct_cfips = ""
    self_def_cfips = ""
    self_cm_cfips_list = [{"ip": ip} for ip in self_cm_cfips.split(',')]
    self_cu_cfips_list = [{"ip": ip} for ip in self_cu_cfips.split(',')]
    self_ct_cfips_list = [{"ip": ip} for ip in self_ct_cfips.split(',')]
    self_def_cfips_list = [{"ip": ip} for ip in self_def_cfips.split(',')]

def get_optimization_ip():
    try:
        headers = headers = {'Content-Type': 'application/json'}
        data = {"key": KEY, "type": "v4" if RECORD_TYPE == "A" else "v6"}
        response = requests.post(API, json=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("CHANGE OPTIMIZATION IP ERROR: REQUEST STATUS CODE IS NOT 200")
            return None
    except Exception as e:
        print("CHANGE OPTIMIZATION IP ERROR: " + str(e))
        return None

def concatenate_ips(c_info, s_info):
    # Collect all IPs into a single string
    new_ips = []

    while c_info:
        iter_ip = c_info.pop(random.randint(0, len(c_info) - 1))["ip"]
        if not any(iter_ip in record["value"] for record in s_info):
            new_ips.append(iter_ip)
    if not new_ips:
        return ""
    return new_ips

def changeDNS(line, s_info, c_info, domain, sub_domain, cloud):
    global AFFECT_NUM, RECORD_TYPE

    lines = {"CM": "移动", "CU": "联通", "CT": "电信", "AB": "境外", "DEF": "默认"}
    line = lines[line]

    try:
        create_num = AFFECT_NUM - len(s_info)
        if create_num == 0:
            for info in s_info:
                if len(c_info) == 0:
                    break
                if DNS_SERVER != 3.1:
                    cf_ip = c_info.pop(random.randint(0,len(c_info)-1))["ip"]
                    if cf_ip in str(s_info):
                        continue
                else:
                    cf_ip = concatenate_ips(c_info, s_info)
                    if not cf_ip:
                        continue
                ret = cloud.change_record(domain, info["recordId"], sub_domain, cf_ip, RECORD_TYPE, line, TTL)
                if(DNS_SERVER != 1 or ret["code"] == 0):
                    print("DNS 更新成功: ----更新时间: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----线路: "+line+ "----IP地址: " + str(cf_ip) )
                else:
                    print("DNS 更新错误: ----更新时间: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----线路: "+line+ "----IP地址: " + str(cf_ip) + "----MESSAGE: " + ret["message"] )
        elif create_num > 0:
            for i in range(create_num):
                if len(c_info) == 0:
                    break
                if DNS_SERVER != 3.1:
                    cf_ip = c_info.pop(random.randint(0,len(c_info)-1))["ip"]
                    if cf_ip in str(s_info):
                        continue
                else:
                    cf_ip = concatenate_ips(c_info, s_info)
                    if not cf_ip:
                        continue
                ret = cloud.create_record(domain, sub_domain, cf_ip, RECORD_TYPE, line, TTL)
                if(DNS_SERVER != 1 or ret["code"] == 0):
                    print("DNS 更新成功: ----更新时间: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----线路: "+line+"----IP地址: " + str(cf_ip) )
                else:
                    print("DNS 更新错误: ----更新时间: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) +  "----线路: "+line+"----IP地址: " + str(cf_ip) + "----MESSAGE: " + ret["message"] )
        else:
            for info in s_info:
                if create_num == 0 or len(c_info) == 0:
                    break
                if DNS_SERVER != 3.1:
                    cf_ip = c_info.pop(random.randint(0,len(c_info)-1))["ip"]
                    if cf_ip in str(s_info):
                        create_num += 1
                        continue
                else:
                    cf_ip = concatenate_ips(c_info, s_info)
                    if not cf_ip:
                        continue
                ret = cloud.change_record(domain, info["recordId"], sub_domain, cf_ip, RECORD_TYPE, line, TTL)
                if(DNS_SERVER != 1 or ret["code"] == 0):
                    print("DNS 更新成功: ----更新时间: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----线路: "+line+" ----IP地址: " + cf_ip )
                else:
                     print("DNS 更新错误: ----更新时间: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----线路: "+line+" ----IP地址: " + cf_ip + "----MESSAGE: " + ret["message"] )
                create_num += 1
    except Exception as e:
            print("CHANGE DNS ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----MESSAGE: " + str(traceback.print_exc()))

def main(cloud):
    global AFFECT_NUM, RECORD_TYPE
    if len(DOMAINS) > 0:
        try:
            cfips = get_optimization_ip()
            if cfips == None or cfips["code"] != 200:
                print("GET CLOUDFLARE IP ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) )
                return
            cf_cmips = cfips["info"]["CM"][:3] + self_cm_cfips_list
            cf_cuips = cfips["info"]["CU"][:3] + self_cu_cfips_list
            cf_ctips = cfips["info"]["CT"][:3] + self_ct_cfips_list
            cf_defips = cf_ctips[:3] + self_def_cfips_list
            for domain, sub_domains in DOMAINS.items():
                for sub_domain, lines in sub_domains.items():
                    temp_cf_cmips = cf_cmips.copy()
                    temp_cf_cuips = cf_cuips.copy()
                    temp_cf_ctips = cf_ctips.copy()
                    temp_cf_abips = cf_ctips.copy()
                    temp_cf_defips = cf_defips.copy()
                    if DNS_SERVER == 1:
                        ret = cloud.get_record(domain, 20, sub_domain, "CNAME")
                        if ret["code"] == 0:
                            for record in ret["data"]["records"]:
                                if record["line"] == "移动" or record["line"] == "联通" or record["line"] == "电信":
                                    retMsg = cloud.del_record(domain, record["id"])
                                    if(retMsg["code"] == 0):
                                        rint("DNS 更新成功: ----更新时间: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))  + "----线路: "+record["line"] )
                                    else:
                                        print("DNS 更新错误: ----更新时间: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----线路: "+record["line"] + "----MESSAGE: " + retMsg["message"] )
                    ret = cloud.get_record(domain, 100, sub_domain, RECORD_TYPE)
                    if DNS_SERVER != 1 or ret["code"] == 0 :
                        if DNS_SERVER == 1 and "Free" in ret["data"]["domain"]["grade"] and AFFECT_NUM > 2:
                            AFFECT_NUM = 2
                        cm_info = []
                        cu_info = []
                        ct_info = []
                        ab_info = []
                        def_info = []
                        for record in ret["data"]["records"]:
                            if record["line"] == "移动":
                                info = {}
                                info["recordId"] = record["id"]
                                info["value"] = record["value"]
                                cm_info.append(info)
                            if record["line"] == "联通":
                                info = {}
                                info["recordId"] = record["id"]
                                info["value"] = record["value"]
                                cu_info.append(info)
                            if record["line"] == "电信":
                                info = {}
                                info["recordId"] = record["id"]
                                info["value"] = record["value"]
                                ct_info.append(info)
                            if record["line"] == "境外":
                                info = {}
                                info["recordId"] = record["id"]
                                info["value"] = record["value"]
                                ab_info.append(info)
                            if record["line"] == "默认":
                                info = {}
                                info["recordId"] = record["id"]
                                info["value"] = record["value"]
                                def_info.append(info)
                        for line in lines:
                            if line == "CM":
                                changeDNS("CM", cm_info, temp_cf_cmips, domain, sub_domain, cloud)
                            elif line == "CU":
                                changeDNS("CU", cu_info, temp_cf_cuips, domain, sub_domain, cloud)
                            elif line == "CT":
                                changeDNS("CT", ct_info, temp_cf_ctips, domain, sub_domain, cloud)
                            elif line == "AB":
                                changeDNS("AB", ab_info, temp_cf_abips, domain, sub_domain, cloud)
                            elif line == "DEF":
                                changeDNS("DEF", def_info, temp_cf_defips, domain, sub_domain, cloud)
        except Exception as e:
            print("CHANGE DNS ERROR: ----Time: " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "----MESSAGE: " + str(traceback.print_exc()))

if __name__ == '__main__':
    if DNS_SERVER == 1:
        cloud = QcloudApiv3(SECRETID, SECRETKEY)
    elif DNS_SERVER == 2:
        cloud = AliApi(SECRETID, SECRETKEY, REGION_ALI)
    elif DNS_SERVER == 3 or DNS_SERVER == 3.1:
        cloud = HuaWeiApi(SECRETID, SECRETKEY, REGION_HW)
    main(cloud)
