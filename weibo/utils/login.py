import pickle
import time
import requests

#import login_config
from weibo.utils.util import *
from weibo.utils.login_config import *


def loginsess():
    sess = requests.session()
    sess.keep_alive = False
    try:
        local_cookies = load_cookies()
        sess.cookies.update(local_cookies)
        print("load cookies succeed"
              "加载cookies成功")
        if not is_logined(sess):
            print("cookies expire"
                  "cookies失效，请重新登录")
            return login_action(sess)
        return sess
    except Exception:
        print("load cookies failed"
              "加载cookies失败，请重新登录")
        return login_action(sess)

def loginsesstest():
    sess = requests.session()
    sess.keep_alive = False
    local_cookies = load_cookies()
    sess.cookies.update(local_cookies)
    print("load cookies succeed"
          "加载cookies成功")
    return sess



def login():
    sess = requests.session()
    sess.keep_alive = False
    try:
        local_cookies = load_cookies()
        sess.cookies.update(local_cookies)
        print("load cookies succeed"
              "加载cookies成功")
        if not is_logined(sess):
            print("cookies expire"
                  "cookies失效，请重新登录")
            return login_action(sess).cookies
        return local_cookies
    except Exception:
        print("load cookies failed"
              "加载cookies失败，请重新登录")
        return login_action(sess).cookies

def logintest():
    import requests
    sess = requests.session()
    sess.keep_alive = False
    local_cookies = load_cookies()
    sess.cookies.update(local_cookies)
    print("load cookies succeed"
              "加载cookies成功")
    return local_cookies


def login_action(sess):
    QRID = _get_QRcode_QRID(sess)
    alt = _get_QRcode_Result(sess, QRID)
    crossDomainUrlList = _get_Cross_Domain_Url_List(sess, alt)
    return _get_Cookies_By_CrossDomainUrlList(sess, crossDomainUrlList)


def load_cookies():
    print('Loading Cookie!')

    with open('cookies/weibo.cookies', 'rb') as f:
        local_cookies = pickle.load(f)
    #
    return local_cookies


def _save_cookies(cookies):
    cookies_file = 'cookies/weibo.cookies'
    with open(cookies_file, 'wb') as f:
        pickle.dump(cookies, f)


def is_logined(sess):
    url = "https://s.weibo.com/weibo"
    payload = {
        'q': '房价|学区房|疫情',
        'typeall': 1,
        'suball': 1,
        'timescope': "custom:2021-05-02-0:2021-05-02-12",
    }
    t0 = time.time()
    resp = sess.get(url, params=payload, headers=headers, proxies=proxies)
    soup = BeautifulSoup(resp.text)
    t1 = time.time()

    if soup.find(attrs={'id': 'pl_feedlist_index'}):
        print('登录状态校验：成功，用时：' + str(t1 - t0))
        return 1
    else:
        print('登录状态校验：失败，用时：' + str(t1 - t0))
        return 0


def _get_QRcode_QRID(sess):
    url = 'https://login.sina.com.cn/sso/qrcode/image'
    payload = {
        'entry': 'weibo',
        'size': 180,
        'callback': str(int(time.time() * 1000)),
    }
    headers = {
        'User-Agent': user_agent
    }
    resp = sess.get(url=url, headers=headers, params=payload, proxies=proxies)
    b = resp.text.split('(')[-1].split(')')[0]

    j = json.loads(b)
    qrid = j['data']['qrid']
    url = "https:" + j['data']['image']
    print(url)
    resp = sess.get(url=url, headers=headers, proxies=proxies)
    if not response_status(resp):
        logger.info('获取二维码失败')
        return False

    QRCode_file = 'QRcode.png'
    save_image(resp, QRCode_file)
    logger.info('二维码获取成功，请打开微博APP扫描')
    open_image(QRCode_file)
    return qrid


def _get_QRcode_Result(sess, qrid):
    qrid_url = 'https://login.sina.com.cn/sso/qrcode/check'
    headers = {
        'User-Agent': user_agent
    }
    payload = {
        'entry': 'weibo',
        'qrid': qrid,
        'callback': "STK_" + str(int(time.time() * 1000)),
    }
    while 1:
        payload['callback'] = "STK_" + str(int(time.time() * 1000))
        resp = sess.get(url=qrid_url, headers=headers, params=payload, proxies=proxies)
        time.sleep(2)
        b = resp.text.split('(')[-1].split(')')[0]
        j = json.loads(b)
        status_code = j['retcode']
        print(resp.text)
        if status_code == 20000000:
            return j['data']['alt']


def _get_Cross_Domain_Url_List(sess, alt):
    alt_url = 'https://login.sina.com.cn/sso/login.php'
    headers = {
        'User-Agent': user_agent
    }
    payload = {
        'entry': 'weibo',
        'returntype': "TEXT",
        'crossdomain': 1,
        'cdult': 3,
        'domain': "weibo.com",
        'alt': alt,
        'savestate': 30,
        'callback': "STK_" + str(int(time.time() * 1000)),
    }
    resp = sess.get(url=alt_url, headers=headers, params=payload, proxies=proxies)
    print(resp.text)
    b = resp.text.split('(')[-1].split(')')[0]
    j = json.loads(b)
    j['crossDomainUrlList'][0] = j['crossDomainUrlList'][0] + '&action=login'
    return j['crossDomainUrlList']


def _get_Cookies_By_CrossDomainUrlList(sess, crossDomainUrlList):
    for i in crossDomainUrlList:
        sess.get(i, headers=headers, proxies=proxies)
    _save_cookies(sess.cookies)
    return sess
