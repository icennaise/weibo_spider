import datetime
import json
import time

import scrapy

from weibo.utils.database import get_database_conn
from weibo.utils.extractor import infoExtract, getSoupPage, weiboNoResult
from weibo.utils.login import login, logintest
from weibo.utils.process_control import generate_next_date_payload, deal_with_empty_response
from weibo.utils.util import parseTimeStr, formatDatetime, urlAddPayload


class WeiboSpider(scrapy.Spider):
    name = "weibo"
    #cookies = logintest().get_dict()
    cookies = login().get_dict()
    begin_time = None
    end_time = None
    keyword = None

    def start_requests(self):
        url = "https://s.weibo.com/weibo"
        #yield self.queryRequest('新冠肺炎', '2021-1-1-0','2021-11-1-0')
        yield from self.queryRequest('新冠肺炎', '2021-01-01-00','2021-10-14-10')

    # 考虑使用装饰器进行错误检查
    def entrance_parse(self, response):
        yield from infoExtract(response, WeiboSpider.keyword)
        page_num = getSoupPage(response)
        if page_num==0:
            deal_with_empty_response()
        for i in range(2, page_num):
            next_page = response.url + "&page=" + str(i)
            yield response.follow(next_page, self.middle_parse)
        i += 1
        next_page = response.url + "&page=" + str(i)
        yield response.follow(next_page, self.final_parse)

    def middle_parse(self, response):
        yield from infoExtract(response, WeiboSpider.keyword)

    def final_parse(self, response):
        for weibo in infoExtract(response, WeiboSpider.keyword):
            yield weibo
        end_time = generate_next_date_payload(weibo['datetime'])
        yield self.queryThePage(self.keyword, self.begin_time, end_time)



    def queryRequest(self, keyword, begin_time=None, end_time=datetime.datetime.now().strftime('%Y-%m-%d-%H')):
        '''
        微博搜索的最小时间间隔单位为1h，查询格式为2021-05-02-0:2021-05-02-12
        目前采用的搜索方法是，不给出 begin_time,迭代 end_time，搜索结果将倒序给出
        '''
        self.begin_time = begin_time
        self.end_time = end_time
        self.keyword = keyword
        self.get_weibo_keyword_id(keyword)
        return self.queryThePage(keyword, begin_time, end_time)
        # query_record.searchEnd()

    def queryThePage(self, keyword, begin_time, end_time=datetime.datetime.now().strftime('%Y-%m-%d-%H')):
        """
        尝试改变爬取策略，更改为由后往前爬取
        :param keyword: 搜索关键词
        :param begin_time: 搜索开始时间，格式为“2020-1-1-0”
        :param end_time: 搜索结束时间
        :return:
        """
        url = "https://s.weibo.com/weibo"
        payload = {
            'q': keyword,
            'typeall': '1',
            'suball': '1',
            'timescope': "custom:{0}:{1}".format('', end_time),
        }
        return scrapy.FormRequest(
            url=urlAddPayload(url, payload),
            formdata=payload,
            cookies=self.cookies,
            callback=self.entrance_parse)

    def get_weibo_keyword_id(self, keyword):
        mydb = get_database_conn()
        cursor = mydb.cursor()
        sql = "select id FROM `weibo_keywords` where keyword='%s'" % keyword
        cursor.execute(sql)
        results = cursor.fetchone()
        if results:
            self.weibo_keyword_id = results[0]
