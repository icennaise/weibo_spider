import datetime
import time

import requests
import scrapy
from bs4 import BeautifulSoup

from weibo.items import Weibo
from weibo.utils.exception import WeiboNoResultException, BadSoupException
from weibo.utils.log import logger

def soupCheck(soup):
    if weiboNoResult(soup):
        raise WeiboNoResultException
    content_div = soup.find(attrs={'id': 'pl_feedlist_index'})
    if content_div is None:
        raise BadSoupException


def infoExtract(response, keyword):
    if isinstance(response,scrapy.Request):
        soup = BeautifulSoup(response.body)
    else:
        soup = response
    if weiboNoResult(soup):
        return None
    content_div = soup.find(attrs={'id': 'pl_feedlist_index'})
    if content_div is None:
        return None
    content_list = content_div.find_all(attrs={'class': "card-wrap"})

    for card in content_list:
        result = cardInfoExtract(card)
        yield result


def textExtract(card):
    """提取微博正文内容"""
    candi_text_list = card.find_all('p', {'class': 'txt'})
    candi_text = None
    # candiCommentText=None
    for i in candi_text_list:
        if 'nick-name' in i.attrs:  # 这是正文类别 #由于展开全文必定出现在后面，所以不必判断直接覆盖即可
            candi_text = i.get_text().replace('\u200b', '').strip()

    return candi_text


def cardInfoExtract(card):
    '''
    由于微博的搜索结果会出现异常
    同一页的两个结果会出现极大差异，考虑使用requests进行流程控制。
    '''
    # 提取微博信息————————————————————————————————————————————————#
    if not card:
        print('解析出错')
    if not card.has_attr('mid'):
        print('解析出错？')
    mid = card['mid']
    # RawData.insertRawData(mid,card)
    time_tag_list = card.find_all(attrs={'class': "from"})
    mhash, device_list, parse_time = dealTimeList(time_tag_list)

    name_tag = card.find(attrs={'class': 'name'})
    user_id = name_tag['href'].split('/')[-1].split('?')[0]
    user_name = name_tag['nick-name']
    seqid = name_tag['suda-data'].split('|')[0].split(':')[-1]  # 采集时间戳
    text = textExtract(card)

    text_repost_comment_like_tag = card.find(attrs={'class': 'card-act'})
    text_repost_comment_like_list = text_repost_comment_like_tag.ul.find_all('a')
    candi_repost = text_repost_comment_like_list[0].get_text().split(' ')[-1]
    candi_comment = text_repost_comment_like_list[1].get_text().split(' ')[-1]
    candi_like = text_repost_comment_like_list[2].get_text().split(' ')[-2]
    text_repost = int(candi_repost) if candi_repost.isdigit() else 0
    text_comment = int(candi_comment) if candi_comment.isdigit() else 0
    text_like = int(candi_like) if candi_like.isdigit() else 0

    w = Weibo(mid=mid, mhash=mhash, userid=user_id, username=user_name, datetime=parse_time,
              source=parseSource(device_list),
              seqid=seqid, text=text, repost=text_repost, comment=text_comment, like=text_like,
              heat=text_repost * 15 + text_comment * 5 + text_like * 2 + 100)
    timestamp = int(w['seqid'][:10])
    w['querydatetime'] = datetime.datetime.fromtimestamp(timestamp)
    #cardComment = card.find(attrs={'class': 'card-comment'})
    return w


def rootInfoExtract(card_comment):
    commentText = commentTextExtract(card_comment)
    if inDenyAccessStrList(commentText):
        pass
        # textCard = Card(mid, mhash, userID, userName, timeList, deviceList, seqid, text, textRepost,
        #                text_comment, text_like, keyword)
        # Relation.insertRelation(mid, -1)
        # textCard.show()
        # continue
    comment_name_tag = card_comment.find(attrs={'class': 'name'})
    try:
        rootuid = comment_name_tag['href'].split('/')[-1].split('?')[0]
    except Exception as e:
        pass
        # logger.info(card_comment)
        # logger.info("发现无法访问的内容，跳过解析")
        # textCard = Weibo(mid, mhash, userID, userName, timeList, deviceList, seqid, text, text_repost,
        #                  text_comment, text_like, keyword)
        # Relation.insertRelation(mid, -1)
        # textCard.show()
        # continue
    rootname = comment_name_tag['nick-name']
    timeTag = card_comment.find(attrs={'class': 'from'})
    tempList = timeTag.get_text().split()
    # 可获得时间和发送平台
    commentDeviceList = None
    commentTimeList = tempList
    if '来自' in tempList:
        index = tempList.index('来自')
        commentTimeList = tempList[:index]
        commentDeviceList = tempList[index:]

    actTag = card_comment.find('ul', attrs={"class": "act s-fr"})
    repostCommentLikeList = actTag.find_all('a')
    rootmid = repostCommentLikeList[2]['action-data'].split('=')[-1]
    rootmhash = repostCommentLikeList[0]['href'].split('/')[-1].split('?')[0]

    candi_repost = repostCommentLikeList[0].get_text().split(' ')[-1]
    candi_comment = repostCommentLikeList[1].get_text().split(' ')[-1]
    candi_like = repostCommentLikeList[2].get_text().split(' ')[-1]
    commentRepost = int(candi_repost) if candi_repost.isdigit() else 0
    commentComment = int(candi_comment) if candi_comment.isdigit() else 0
    commentLike = int(candi_like) if candi_like.isdigit() else 0

    # commentCard=Card(rootmid,rootmhash,rootuid,rootname,commentTimeList,commentDeviceList,seqid,commentText,commentRepost,commentComment,commentLike,keyword)
    # commentCard.show()
    # textCard = Card(mid, mhash, userID, userName, timeList, deviceList, seqid, text, text_repost,
    #                 text_comment, text_like, keyword)
    # textCard.show()
    # Relation.insertRelation(mid, rootmid)


def commentTextExtract(card):
    """若存在转发源微博，提取源微博正文内容"""
    candi_text_list = card.find_all('p', {'class': 'txt'})
    candi_comment_text = None
    for i in candi_text_list:
        candi_comment_text = i.get_text().replace('\u200b', '').strip()

    return candi_comment_text  # 正文爬取结果


def inDenyAccessStrList(text):
    deny_access_str_list = ["根据博主设置，此内容无法访问", "该账号因用户自行申请关闭，现已无法查看。", "抱歉，作者已设置仅展示半年内微博，此微博已不可见。", "抱歉，此微博已被作者删除。",
                            "该账号因被投诉违反法律法规和《微博社区公约》的相关规定，现已无法查看。", "该账号因被投诉违反《微博社区公约》的相关规定，现已无法查看。",
                            "抱歉，由于作者设置，你暂时没有这条微博的查看权限哦。", "该微博包含营销推广内容且未备案", "该账号行为异常，存在安全风险，用户验证之前暂时不能查看。",
                            "该微博因被多人投诉，根据《微博社区公约》，已被删除。", "抱歉，此微博已被删除。", "博文涉及营销推广正在审核中，暂时无法传播", "由于博主设置，目前内容暂不可见。"]
    for i in deny_access_str_list:
        if i in text:
            return True
    return False


def parseSource(device_list):
    if device_list is not None:
        return ''.join(device_list[1:])
    else:
        return None


def parseTimeStr(time_list, seqid=str(time.time())):
    # 时间格式共有以下几种：
    # 16秒前、36分钟前、今天14：47、06月04日 23:50、2020年06月30日 22:59
    timestamp = int(seqid[:10])
    querydatetime = datetime.datetime.fromtimestamp(timestamp)
    timeStr = ''.join(time_list)
    if '秒前' in timeStr:
        s = int(timeStr.replace("秒前", '').strip())
        return querydatetime - datetime.timedelta(seconds=s)
    elif '分钟前' in timeStr:
        m = int(timeStr.replace("分钟前", '').strip())
        return querydatetime - datetime.timedelta(minutes=m)
    elif '今天' in timeStr:
        time = timeStr.replace("今天", '').strip()
        date = querydatetime.strftime("%Y-%m-%d")
        y, m, d = date.split('-')
        if ':' in time:
            h, minute = time.split(':')
        else:
            h, minute = time.split('：')
        return datetime.datetime(int(y), int(m), int(d), int(h), int(minute))
    elif '月' in timeStr and '年' not in timeStr:
        s = timeStr.strip().split('日')
        y = querydatetime.strftime("%Y")
        m = s[0].split('月')[0]
        d = s[0].split('月')[1].split('日')[0]
        h, minute = s[1].split(':')
        return datetime.datetime(int(y), int(m), int(d), int(h), int(minute))
    elif '年' in timeStr:
        s = timeStr.strip().split(' ')
        y = s[0].split('年')[0]
        m = s[0].split('年')[1].split('月')[0]
        d = s[0].split('月')[1].split('日')[0]
        h = s[0].split('日')[1].split(':')[0]
        minute = s[0].split(':')[1]
        return datetime.datetime(int(y), int(m), int(d), int(h), int(minute))
    else:
        raise Exception('时间格式判断出错：{}'.format(timeStr))


def getSoupPage(response):
    if isinstance(response,scrapy.Request):
        soup = BeautifulSoup(response.body)
    else:
        soup=response
    if weiboNoResult(soup):
        return 0
    contentDiv = soup.find(attrs={'id': 'pl_feedlist_index'})
    if contentDiv == None:
        return False
    pagesTag = contentDiv.find('span', attrs={'class': 'list'})
    if pagesTag == None:
        return 1
    pagesList = pagesTag.find_all('li')
    pages = len(pagesList)
    return pages


def weiboNoResult(response):
    if isinstance(response,scrapy.Request):
        soup = BeautifulSoup(response.body)
    else:
        soup=response
    return soup.find(attrs={'class': "card-no-result"}) is not None


def dealTimeList(time_tag_list, root=False):
    parse_time, device_list, time_tag = chooseLaterTime(time_tag_list)
    mhash = time_tag.a['href'].split('?')[0].split('/')[-1]
    # 可获得时间和发送平台

    return mhash, device_list, parse_time


def chooseLaterTime(time_tag_list):
    return sorted(map(splitTimeAndDevice, time_tag_list), key=lambda x: (x[0]), reverse=True)[0]


def splitTimeAndDevice(time_tag):
    text_time_list = time_tag.get_text().split()
    if '来自' in text_time_list:
        index = text_time_list.index('来自')
        time_list = text_time_list[:index]
        device_list = text_time_list[index:]
    else:
        device_list = None
        time_list = text_time_list
    return parseTimeStr(time_list), device_list, time_tag
