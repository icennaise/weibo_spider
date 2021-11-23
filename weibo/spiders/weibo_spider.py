import datetime
import json
import time

import requests
import scrapy
from bs4 import BeautifulSoup

from weibo.utils.database import get_database_conn
from weibo.utils.exception import WeiboNoResultException, BadSoupException
from weibo.utils.extractor import infoExtract, getSoupPage, weiboNoResult, soupCheck
from weibo.utils.login import login, logintest, loginsess, loginsesstest
from weibo.utils.process_control import generate_next_date_payload, deal_with_empty_response
from weibo.utils.util import parseTimeStr, formatDatetime, urlAddPayload
from weibo.utils.login_config import *


class WeiboSpider(scrapy.Spider):
    name = "weibo"
    cookies = logintest().get_dict()
    # weibo_datetime_list=[]
    # cookies = login().get_dict()
    # sess = loginsess()
    begin_time = None
    end_time = None
    keyword = None
    headers = headers

    def start_requests(self):
        url = "https://s.weibo.com/weibo"
        # yield self.queryRequest('新冠肺炎', '2021-1-1-0','2021-11-1-0')
        yield scrapy.Request(url=url, cookies=self.cookies, callback=self.queryRequest, dont_filter=True)
        # yield from self.queryRequest('新冠肺炎', '2021-01-01-00', '2021-10-18-00')

    # def queryRequest(self, keyword='新冠肺炎', begin_time='2021-01-01-00', end_time=datetime.datetime.now().strftime('%Y-%m-%d-%H')):
    def queryRequest(self, response, keyword='新冠肺炎', begin_time='2021-01-01-00', end_time='2021-08-11-09'):
        '''
        微博搜索的最小时间间隔单位为1h，查询格式为2021-05-02-0:2021-05-02-12
        目前采用的搜索方法是，不给出 begin_time,迭代 end_time，搜索结果将倒序给出
        '''
        self.begin_time = begin_time
        self.end_time = end_time
        self.keyword = keyword
        self.get_weibo_keyword_id(keyword)
        return self.queryThePage(keyword, begin_time, end_time)

    def queryThePage(self, keyword, begin_time, end_time=datetime.datetime.now().strftime('%Y-%m-%d-%H')):
        """
        尝试改变爬取策略，更改为由后往前爬取
        :param keyword: 搜索关键词
        :param begin_time: 搜索开始时间，格式为“2020-1-1-0”
        :param end_time: 搜索结束时间
        :return:
        """
        last_datetime = None
        while last_datetime is None or end_time > begin_time:
            weibo_list = []
            first_page = self.getFirstPage(keyword, end_time)
            page_num = getSoupPage(first_page)
            for page_soup in self.getMultiPages(keyword, end_time, page_num):
                time.sleep(0.8)
                for weibo in infoExtract(page_soup, keyword):
                    weibo_list.append(weibo)
            last_datetime = generate_next_date_payload(last_datetime, weibo_list)
            end_time=last_datetime.isoformat()
            for i in weibo_list:
                if not isinstance(i,dict):
                    yield i

    def getFirstPage(self, keyword, end_time):
        return self.get_weibo_search_soup(keyword, end_time)

    def getMultiPages(self, keyword, end_time, page_num):
        for i in range(1, page_num+1):
            yield self.get_weibo_search_soup(keyword, end_time, i)

    def get_weibo_search_soup(self, keyword, end_time, page=1):
        url = "https://s.weibo.com/weibo"
        payload = {
            'q': keyword,
            'typeall': '1',
            'suball': '1',
            'timescope': "custom:{0}:{1}".format('', end_time),
            'page': page,
        }
        while 1:
            try:
                # resp = self.sess.get(url, params=payload, headers=self.headers)
                resp = requests.get(url, params=payload, cookies=self.cookies)
                assert resp.status_code == 200
            except AssertionError:
                print("请求失败，判断遇到反爬或登录验证，将暂停爬取，请检查登录状态")
                time.sleep(600)
            except:
                print("网络请求失败")
                time.sleep(10)
            else:
                '''
                对soup进行检查
                '''
                soup = BeautifulSoup(resp.text)
                try:
                    soupCheck(soup)
                except WeiboNoResultException as e:
                    time.sleep(10)
                    print(e)
                except BadSoupException as e:
                    time.sleep(600)
                    print(e)
                else:
                    return soup

    def get_weibo_keyword_id(self, keyword):
        mydb = get_database_conn()
        cursor = mydb.cursor()
        sql = "select id FROM `weibo_keywords` where keyword='%s'" % keyword
        cursor.execute(sql)
        results = cursor.fetchone()
        if results:
            self.weibo_keyword_id = results[0]

    def calDiff(self):
        pass
