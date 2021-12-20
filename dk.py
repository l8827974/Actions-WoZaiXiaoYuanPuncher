# -*- encoding:utf-8 -*-
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
        if not self.jwsession:  # 读取cache中的配置文件
            data = utils.processJson(".cache/cache.json").read()
            self.jwsession = data['jwsession']  
        return self.jwsession

    # 获取打卡列表，判断当前打卡时间段与打卡情况，符合条件则自动进行打卡
   function DoSign(id,logId){
    const url = `https://student.wozaixiaoyuan.com/sign/doSign.json`;
    const method = `POST`;
    const headers = {
    'Accept-Encoding' : `gzip,compress,br,deflate`,
    'content-type' : `application/x-www-form-urlencoded`,
    'Connection' : `keep-alive`,
    'Referer' : `https://servicewechat.com/wxce6d08f781975d91/182/page-frame.html`,
    'Host' : `student.wozaixiaoyuan.com`,
    'User-Agent' : `Mozilla/5.0 (Linux; Android 6.0.1; M2 E Build/MMB29U; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2853 MMWEBSDK/20210501 Mobile Safari/537.36 MMWEBID/5060 MicroMessenger/8.0.6.1900(0x2800063D) Process/appbrand0 WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 MiniProgramEnv/android`,
    'jwsession' : `bd0c7f5ffa9748d4a6cc8f62085752bb`
    };
    const body = `{"id":`+ logId +`,"signId":`+ id +`,"latitude":34.108568,"longitude":108.664053,"country":"中国","province":"陕西省","city":"西安市","district":"鄠邑区","township":"五竹街道"}`;

    const myRequest = {
        url: url,
        method: method,
        headers: headers,
        body: body
    };

    $task.fetch(myRequest).then(response => {
        const data = JSON.parse(response.body)
        if(data.code == 0){
          $notify("签到成功","签到成功","签到成功")
        }
      }, reason => {
          $notify("签到失败","签到失败","签到请求失败")
      });
}

function Sign(){
    GetMessage()
    DoSign()
}


Sign()







if __name__ == '__main__':
    # 找不到cache，登录+打卡
    wzxy = WoZaiXiaoYuanPuncher()
    if not os.path.exists('.cache'):
        print("找不到cache文件，正在使用账号信息登录...")
        loginStatus = wzxy.login()
        if loginStatus:
            wzxy.PunchIn()
        else:
            print("登陆失败，请检查账号信息")
    else:
        print("找到cache文件，尝试使用jwsession打卡...")
        wzxy.PunchIn()
    wzxy.sendNotification()
