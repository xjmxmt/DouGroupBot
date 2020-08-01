import requests
from lxml import etree
import time
import random
from queue import Empty, Queue

from util import DouUtil
from actions import RespGen
from mySelectors import NewPostSelector
from util import requestsWrapper
from util import SpellCorrect

log = DouUtil.log


# def get_headers(fileName=None):
#     name = 'headers.txt'
#     if (fileName is not None):
#         name = fileName
#     name = 'resources/' + name
#     headers = {}
#     with open(name, "r", encoding='utf-8') as f_headers:
#         hdrs = f_headers.readlines()
#     for line in hdrs:
#         key, value = line.split(": ")
#         headers[key] = value.strip()
#     return headers
#
#
# def login(url, pwd, userName, session):
#     loginData = {'ck': '', 'name': userName,
#                  'password': pwd, 'remember': 'true'}
#     loginHeaders = get_headers('login_headers.txt')
#     l = session.post(url, data=loginData, headers=loginHeaders)
#
#     if l.status_code == requests.codes['ok'] or l.status_code == requests.codes['found']:
#         print("Login Successfully")
#         return True
#     else:
#         print("Failed to Login")
#         log.error("Failed to Login", l.status_code)
#         session.close()
#         return False


def composeCmnt(session, response):
    cmntForm = {'ck': '', 'rv_comment': response.get('res'), 'captcha-solution': '', 'captcha-id': '',
                'start': 0, 'submit_btn': '发送'}
    cmntForm['ck'] = DouUtil.getCkFromCookies(session)
    return cmntForm


def prepareCaptcha(data, session, postUrl, r=None, spell_correct=None) -> dict:
    pic_url, pic_id = DouUtil.getCaptchaInfo(session, postUrl, r)
    verifyCode = ''
    pic_path = DouUtil.save_pic_to_disk(pic_url, session)
    log.debug(pic_url, pic_path)
    verifyCode = DouUtil.getTextFromPic(pic_path)
    verifyCode = spell_correct.correct(verifyCode)

    data['captcha-solution'] = verifyCode
    data['captcha-id'] = pic_id

    return data


def postCmnt(session, postUrl, request, response):
    data = composeCmnt(session._session, response)
    cmntUrl = postUrl + 'add_comment'
    r = session.post(cmntUrl, data=data, headers={'Referer': postUrl}, files=response)
    # print(r.text)
    # print(etree.HTML(r.text).xpath('//img[@id="captcha_image"]/@src'))
    code = str(r.status_code)
    if (code.startswith('4') or code.startswith('5')) and not code.startswith('404'):
        log.error(r.status_code)
        raise Exception
    elif 0 != len(etree.HTML(r.text).xpath('//img[@id="captcha_image"]')):  # 用来判断验证码
        print('Gotta deal with the captcha.😭')
        log.warning(r.status_code)

        spell_correct = SpellCorrect.SpellCorrect()  # 单词拼写纠错
        data = prepareCaptcha(data, session, postUrl, r, spell_correct)
        r = session.post(cmntUrl, data=data, headers={'Referer': postUrl}, files=response)

        retry = 2  # 尝试3次验证码
        while 0 != len(etree.HTML(r.text).xpath('//img[@id="captcha_image"]')):  # 验证码输错，需要再次输入时
            print(str(r.status_code))
            if retry <= 0:
                retry -= 1
                break
            data = prepareCaptcha(data, session, postUrl, r, spell_correct)

            r = session.post(cmntUrl, data=data, headers={'Referer': postUrl}, files=response)
            retry -= 1

            timeToSleep = 15
            time.sleep(timeToSleep)

        if retry < 0:  # 尝试3次验证码识别还是失败
            log.info("Fail.", request)
            # log.error(r.status_code)
            # DouUtil.alertUser()
            # pic_url, pic_id = DouUtil.getCaptchaInfo(session, postUrl, r)
            # code = DouUtil.callAdmin(session, pic_url, postUrl)
            # # data.update({'captcha-solution': code, 'captcha-id': pic_id})
            #
            # r = session.post(cmntUrl, data=data)
            # if 0 != len(
            #         etree.HTML(r.text).xpath('//img[@id="captcha_image"]')):
            #     raise Exception
        else:
            log.info("Success.", request + '  --' + data['rv_comment'])
    else:
        log.info("Success.", request + '  --' + data['rv_comment'])


def main():
    respGen = RespGen.RespGen()
    q = Queue()

    # cred = DouUtil.getCred()  # store userName and password
    # pwd = cred['pwd']
    # userName = cred['userName']
    # loginReqUrl = 'https://accounts.douban.com/passport/login'

    reqWrapper = requestsWrapper.ReqWrapper()
    s = reqWrapper._session
    s.headers.update({
        'Host': 'www.douban.com',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    # s.cookies.update(DouUtil.loadCookies())
    my_cookie_value = ''  # 填入自己的cookie值
    s.cookies.update({'cookies': my_cookie_value})

    slctr = NewPostSelector.NewPostSelector(q, reqWrapper)
    timeToSleep = 10

    while True:
        q = slctr.select()
        if q.qsize() == 0:
            log.debug("sleep for emty queue: ", timeToSleep)
            time.sleep(timeToSleep)
        else:
            timeToSleep = 20  # 每20秒回复一个
        log.info("****selection, q size: ", q.qsize(), "timeToSleep: " + str(timeToSleep) + "****")
        try:
            file = open('resources/record.txt', 'a', encoding='utf-8')

            while q.qsize() > 0:
                tup = q.get(timeout=5)

                question, postUrl, userid = tup[0], tup[1], tup[2]

                resp = respGen.getResp()

                postCmnt(reqWrapper, postUrl, question, resp)

                record = question + ': ' + resp.get('res') + '\n'
                print('record:', record)

                file.write(record)

        except Empty:
            log.info("Emptied q, one round finished")
        finally:
            file.close()
            DouUtil.flushCookies(s)


if __name__ == '__main__':
    main()
