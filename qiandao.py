# -*- encoding:utf-8 -*-
import datetime
import requests
import json
import time
import requests
import json
import os
import time
import hmac
import hashlib
import base64
import utils
import urllib
import urllib.parse
from urllib.parse import urlencode
from urllib3.util import Retry


# 登录
def login(self):
    username, password = str(os.environ['WZXY_USERNAME']), str(os.environ['WZXY_PASSWORD'])
    url = f'{self.loginUrl}?username={username}&password={password}' 
    self.session = requests.session()
    # 登录
    response = self.session.post(url=url, data=self.body, headers=self.header)
    res = json.loads(response.text)
    if res["code"] == 0:
        print("使用账号信息登录成功")
        jwsession = response.headers['JWSESSION']
        self.setJwsession(jwsession)
        return True
    else:
        print(res)
        print("登录失败，请检查账号信息")
        self.status_code = 5
        return False

# 设置JWSESSION
def setJwsession(self, jwsession):
    # 如果找不到cache,新建cache储存目录与文件
    if not os.path.exists('.cache'): 
        print("正在创建cache储存目录与文件...")
        os.mkdir('.cache')
        data = {"jwsession": jwsession}
    elif not os.path.exists('.cache/cache.json'):
        print("正在创建cache文件...")
        data = {"jwsession": jwsession}
    # 如果找到cache,读取cache并更新jwsession
    else:
        print("找到cache文件，正在更新cache中的jwsession...")
        data = utils.processJson('.cache/cache.json').read()
        data['jwsession'] = jwsession                 
    utils.processJson(".cache/cache.json").write(data)
    self.jwsession = data['jwsession']  

# 获取JWSESSION
def getJwsession(self):
    if not self.jwsession:  # 读取cache中的配置文件
        data = utils.processJson(".cache/cache.json").read()
        self.jwsession = data['jwsession']  
    return self.jwsession

# 我在校园jwsession,抓包获得
jwsession = self.jwsession
# 在pushplus网站中可以找到 http://pushplus.hxtrip.com/
pushplus_token = 'cd51aa7b1a2f44259e7630ad316dfa64'


def pushplus_post(title, content):
    url = 'http://pushplus.hxtrip.com/send'
    data = {
        "token": pushplus_token,
        "title": title,
        "content": content
    }
    body = json.dumps(data).encode(encoding='utf-8')
    headers = {'Content-Type': 'application/json'}
    requests.post(url, data=body, headers=headers)


def get_sign_message():
    headers = {
        "jwsession": jwsession
    }
    post_data = {
        "page": 1,
        "size": 5
    }
    url = "https://student.wozaixiaoyuan.com/sign/getSignMessage.json"
    s = requests.session()
    r = s.post(url, data=post_data, headers=headers)
    r_json = json.loads(r.text)
    if r_json['code'] == 0:
        return r_json['data'][0]
    else:
        pushplus_post("签到提醒", "jwsession失效!")
        return 404


def do_sign(sign_message):
    if sign_message == 404:
        return 404
    headers = {
        "jwsession": jwsession
    }
    post_data = {
        "signId": str(sign_message['id']),
        "city": "西安市",
        "id": str(sign_message['logId']),
        "latitude": '34.108568',
        "longitude": '108.664053',
        "country": "中国",
        "district": "鄠邑区",
        "township": "五竹街道",
        "province": "陕西省"
    }

    url = "https://student.wozaixiaoyuan.com/sign/doSign.json"
    s = requests.session()
    r = s.post(url, data=json.dumps(post_data), headers=headers)
    r_json = json.loads(r.text)
    if r_json['code'] == 0:
        pushplus_post("签到提醒", "签到成功")
    else:
        pushplus_post("签到提醒", "签到失败,返回信息为:" + str(r_json))


def contrast_date(sign_message):
    # 得到签到的日期和时间
    sign_date_str = str(sign_message['start']).split(" ")[0]
    sign_time_str_start = str(sign_message['start']).split(" ")[1]
    sign_time_str_end = str(sign_message['end']).split(" ")[1]

    # 得到系统的日期和时间
    sys_time_info = datetime.datetime.now()
    sys_date_now = sys_time_info.date()
    sys_time_now = time.strftime("%H:%M", time.localtime())

    # 判断打卡的日期和今天的日期是否相同
    if str(sys_date_now) == sign_date_str:
        # 判断系统时间是否在打卡时间区间
        if sign_time_str_start <= sys_time_now <= sign_time_str_end:
            return 0
        elif sys_time_now <= sign_time_str_start:
            return -2
        elif sys_time_now >= sign_time_str_end:
            return -3
    else:
        return -1


def main():
    # while True:
    #     time_now = time.strftime("%H:%M:%S", time.localtime())
    #     if time_now == "21:40:00" or time_now == "21:40:01":
    #         # 得到最新的签到信息
    #         sign_info = get_sign_message()
    #         # 比对签到信息
    #         time_code = contrast_date(sign_info)
    #         if time_code == 0:
    #             do_sign(sign_info)
    #             time.sleep(10)
    #         elif time_code == -2:
    #             # 签到是今天但是签到没有开始，静默等待
    #             while time_code == 0:
    #                 time.sleep(10)
    #                 time_code = contrast_date(sign_info)
    #             # 时间开始之后执行签到
    #             do_sign(sign_info)
    #             time.sleep(10)
    #         elif time_code == -3:
    #             pushplus_post("签到提醒", "已过签到时间")
    #         elif time_code == -1:
    #             pushplus_post("签到提醒", "签到未发布或今天没有签到")
    #     time.sleep(2)

    # 得到最新的签到信息
    sign_info = get_sign_message()
    # 比对签到信息
    time_code = contrast_date(sign_info)
    if time_code == 0:
        do_sign(sign_info)
        time.sleep(10)
    elif time_code == -2:
        # 签到是今天但是签到没有开始，静默等待
        while time_code == 0:
            time.sleep(10)
            time_code = contrast_date(sign_info)
        # 时间开始之后执行签到
        do_sign(sign_info)
        time.sleep(10)
    elif time_code == -3:
        pushplus_post("签到提醒", "已过签到时间")
    elif time_code == -1:
        pushplus_post("签到提醒", "签到未发布或今天没有签到")

if __name__ == "__main__":
    main()
