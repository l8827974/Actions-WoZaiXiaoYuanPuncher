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

class WoZaiXiaoYuanPuncher:
    def __init__(self):
        # JWSESSION
        self.jwsession = None
        # 打卡时段
        self.seq = None
        # 打卡结果
        self.status_code = 0
        # 登陆接口
        self.loginUrl = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username"
        # 请求头
        self.header = {
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.13(0x18000d32) NetType/WIFI Language/zh_CN miniProgram",
            "Content-Type": "application/json;charset=UTF-8",
            "Content-Length": "2",
            "Host": "gw.wozaixiaoyuan.com",
            "Accept-Language": "en-us,en",
            "Accept": "application/json, text/plain, */*"
        }
        # 请求体（必须有）
        self.body = "{}"

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
    if not jwsession:  # 读取cache中的配置文件
        data = utils.processJson(".cache/cache.json").read()
        jwsession = data['jwsession']  
    return jwsession

# 我在校园jwsession,抓包获得
#jwsession = self.getJwsession()
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


def qiandao(self):
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
# 推送打卡结果
    def sendNotification(self):
        notifyTime = utils.getCurrentTime()
        notifyResult = self.getResult()
        notifySeq = self.getSeq()

        if os.environ.get('SCT_KEY'):
            # serverchan 推送
            notifyToken = os.environ['SCT_KEY']
            url = "https://sctapi.ftqq.com/{}.send"
            body = {
                "title": "⏰ 我在校园打卡结果通知",
                "desp": "打卡项目：日检日报\n\n打卡情况：{}\n\n打卡时段：{}\n\n打卡时间：{}".format(notifyResult, notifySeq, notifyTime)
            }
            requests.post(url.format(notifyToken), data=body)
            print("消息经Serverchan-Turbo推送成功")
        if os.environ.get('PUSHPLUS_TOKEN'):
            # pushplus 推送
            url = 'http://www.pushplus.plus/send'
            notifyToken = os.environ['PUSHPLUS_TOKEN']
            content = json.dumps({
                "打卡项目": "日检日报",
                "打卡情况": notifyResult,
                "打卡时段": notifySeq,
                "打卡时间": notifyTime
            }, ensure_ascii=False)
            msg = {
                "token": notifyToken,
                "title": "⏰ 我在校园打卡结果通知",
                "content": content,
                "template": "json"
            }
            requests.post(url, data=msg)
            print("消息经pushplus推送成功")
        if os.environ.get('DD_BOT_ACCESS_TOKEN'):
            # 钉钉推送
            DD_BOT_ACCESS_TOKEN = os.environ["DD_BOT_ACCESS_TOKEN"]
            DD_BOT_SECRET = os.environ["DD_BOT_SECRET"]
            timestamp = str(round(time.time() * 1000))  # 时间戳
            secret_enc = DD_BOT_SECRET.encode('utf-8')
            string_to_sign = '{}\n{}'.format(timestamp, DD_BOT_SECRET)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))  # 签名
            print('开始使用 钉钉机器人 推送消息...', end='')
            url = f'https://oapi.dingtalk.com/robot/send?access_token={DD_BOT_ACCESS_TOKEN}&timestamp={timestamp}&sign={sign}'
            headers = {'Content-Type': 'application/json;charset=utf-8'}
            data = {
                'msgtype': 'text',
                'text': {'content': f'⏰ 我在校园打卡结果通知\n---------\n打卡项目：日检日报\n\n打卡情况：{notifyResult}\n\n打卡时间: {notifyTime}'}
            }
            response = requests.post(url=url, data=json.dumps(data), headers=headers, timeout=15).json()
            if not response['errcode']:
                print('消息经钉钉机器人推送成功！')
            else:
                print('消息经钉钉机器人推送失败！')
        if os.environ.get('BARK_TOKEN'):
            # bark 推送
            notifyToken = os.environ['BARK_TOKEN']
            req = "{}/{}/{}".format(notifyToken, "⏰ 我在校园打卡（日检日报）结果通知", notifyResult)
            requests.get(req)
            print("消息经bark推送成功")
        if os.environ.get("MIAO_CODE"):
            baseurl = "https://miaotixing.com/trigger"
            body = {
                "id": os.environ['MIAO_CODE'],
                "text": "打卡项目：日检日报\n\n打卡情况：{}\n\n打卡时段：{}\n\n打卡时间：{}".format(notifyResult, notifySeq, notifyTime)
            }
            requests.post(baseurl, data=body)
            print("消息经喵推送推送成功")
if __name__ == "__main__":
     wzxy = WoZaiXiaoYuanPuncher()
    if not os.path.exists('.cache'):
        print("找不到cache文件，正在使用账号信息登录...")
        loginStatus = wzxy.login()
        if loginStatus:
            wzxy.qiandao()
        else:
            print("登陆失败，请检查账号信息")
    else:
        print("找到cache文件，尝试使用jwsession打卡...")
        wzxy.qiandao()
    wzxy.sendNotification()
    main()
