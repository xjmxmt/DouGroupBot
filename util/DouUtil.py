import os
import time
from lxml import etree
import requests
import base64
import hashlib
from PIL import Image
import re

from util import Logger as myLogger

from config import myConfig

# 百度ocr识别验证码
import sys
import json
import base64

# 保证兼容python2以及python3
IS_PY3 = sys.version_info.major == 3
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.parse import quote_plus

# 防止https证书校验不正确
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

API_KEY = ''

SECRET_KEY = ''

OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"

"""  TOKEN start """
TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'


log = myLogger.Logger()


"""
    获取token
"""
def fetch_token():
    params = {'grant_type': 'client_credentials',
              'client_id': API_KEY,
              'client_secret': SECRET_KEY}
    post_data = urlencode(params)
    if (IS_PY3):
        post_data = post_data.encode('utf-8')
    req = Request(TOKEN_URL, post_data)
    try:
        f = urlopen(req, timeout=5)
        result_str = f.read()
    except URLError as err:
        print(err)
    if (IS_PY3):
        result_str = result_str.decode()


    result = json.loads(result_str)

    if ('access_token' in result.keys() and 'scope' in result.keys()):
        if not 'brain_all_scope' in result['scope'].split(' '):
            print ('please ensure has check the  ability')
            exit()
        return result['access_token']
    else:
        print ('please overwrite the correct API_KEY and SECRET_KEY')
        exit()

"""
    读取文件
"""
def read_file(image_path):
    f = None
    try:
        f = open(image_path, 'rb')
        return f.read()
    except:
        print('read image file fail')
        return None
    finally:
        if f:
            f.close()


"""
    调用远程服务
"""
def request(url, data):
    req = Request(url, data.encode('utf-8'))
    has_error = False
    try:
        f = urlopen(req)
        result_str = f.read()
        if (IS_PY3):
            result_str = result_str.decode()
        return result_str
    except  URLError as err:
        print(err)


# 以下是原代码
def getCookiesFromSession(session):
    cookies = session.cookies.get_dict()
    return cookies

def getCkFromCookies(session):
    cookies = getCookiesFromSession(session)
    ck = cookies.get('ck')
    if (ck is None):
        log.error("No ck found in cookies", cookies)
        raise Exception('No ck found in cookies')

    return ck

def loadCookies():
    cookies = {}
    with open('resources/cookies.txt', "r", encoding='utf-8') as f_cookie:
        douban_cookies = f_cookie.readlines()[0].split("; ")
        for line in douban_cookies:
            key, value = line.split("=", 1)
            cookies[key] = value
        return cookies

def flushCookies(session: requests.Session):
    cookies = session.cookies.get_dict()
    line = ""
    with open('resources/cookies.txt', "w", encoding='utf-8') as f_cookie:
        for k, v in cookies.items():
            line += k +'='+v+'; '
        line = line[:len(line)-2]
        f_cookie.write(line)

def getCred(fileName='confidentials/pwd.txt'):
    data = {}
    with open(fileName, 'r', encoding='utf-8') as reader:
        lines = reader.readlines()
        for li in lines:
            k, v = li.strip().split('=')
            data[k.strip()] = v.strip()
    
    return data


def getAccessToken():
    url = ''
    cred = getCred('')
    myid = cred['myid']
    mysecret = cred['mysecret']
    url = url + '&client_id='+myid+'&client_secret='+mysecret
    json = requests.get(url).json()
    # if json.get('error') is None:
    return json['access_token']
    
# def getTextFromPic(fileName) -> str:
#     img = None
#     # 二进制方式打开图片文件
#     with open(fileName, 'rb') as f:
#         img = base64.b64encode(f.read())
#
#     params = {"image":img, 'language_type':'ENG'}
#     header = {'Content-Type':'application/x-www-form-urlencoded'}
#     request_url = ""
#     accessToken = getAccessToken()
#     request_url = request_url + "?access_token=" + accessToken
#     r = requests.post(request_url, data=params, headers=header)
#
#     # log.info(r.json())
#     resp = r.json()
#     word = resp.get('words_result')
#     if word is None or len(word) == 0:
#         log.error("In getTextFromPic", resp)
#         return ""
#     text = resp['words_result'][0]['words'].lower()
#     return re.sub(r"[^a-z]+", '', text)

def getTextFromPic(fileName) -> str:
    # 获取access token
    token = fetch_token()

    # 拼接通用文字识别高精度url
    image_url = OCR_URL + "?access_token=" + token

    text = ''

    # 读取书籍页面图片
    file_content = read_file(fileName)

    # 调用文字识别服务
    result = request(image_url, urlencode({'image': base64.b64encode(file_content)}))

    # 解析返回结果
    result_json = json.loads(result)
    for words_result in result_json["words_result"]:
        text = text + words_result["words"]

    text = text.strip()

    # 打印文字
    print(text)

    return text


def getCaptchaInfo(session, postUrl, r=None):
    if r is not None:
        return parseCaptchaInfo(r)
    time.sleep(10)
    r = session.get(postUrl)
    # error handling
    html = etree.HTML(r.text)
    pic_url = html.xpath('//img[@id="captcha_image"]/@src')[0]
    pic_id = html.xpath('//input[@name="captcha-id"]/@value')[0]
    # pic_id = re.search(r'id=(.*):', pic_url).group(1)
    return pic_url, pic_id

def parseCaptchaInfo(r):
    html = etree.HTML(r.text)
    pic_url = html.xpath('//img[@id="captcha_image"]/@src')[0]
    pic_id = html.xpath('//input[@name="captcha-id"]/@value')[0]

    # pic_id = re.search(r'id=(.*):', pic_url).group(1)
    print(pic_url, pic_id)

    return pic_url, pic_id

def save_pic_to_disk(pic_url, session):
    # 将链接中的图片保存到本地，并返回文件名
    try:
        res = session.get(pic_url)
        if res.status_code == 200:
            # 求取图片的md5值，作为文件名，以防存储重复的图片
            md5_obj = hashlib.md5()
            md5_obj.update(res.content)
            md5_code = md5_obj.hexdigest()
            # file_name = myConfig.imgPath + str(md5_code) + ".jpg"
            file_name = './captchas/' + str(md5_code) + ".jpg"
            print(file_name)
            # 如果图片不存在，则保存
            if not os.path.exists(file_name):
                with open(file_name, "wb") as f:
                    f.write(res.content)
            return file_name
        else:
            log.warning("in func save_pic_to_disk(), fail to save pic. pic_url: " + pic_url +
                                      ", res.status_code: " + str(res.status_code))
            raise Exception
    except Exception as e:
        log.error(e)


if __name__ == "__main__":
    # dic = loadCookies()
    # print(dic)

    # token = getAccessToken()
    # fileName = 'resources/captchas/captcha.jpg'
    # text = getTextFromPic(fileName)
    path = '../captchas/'
    li = os.listdir(path)
    print(len(li))
    # for entry in li:
    #     text = getTextFromPic(path+entry)
    #     print(text)