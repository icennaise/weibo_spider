# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import datetime

import pymysql
from itemadapter import ItemAdapter

from weibo.utils.database import get_database_conn


class WeiboPipeline:
    def __init__(self):
        self.mydb = get_database_conn()
        self.cursor = self.mydb.cursor()

    def process_item(self, item, spider):
        #print(1)
        if item.name == "weibo":
            self.insertWeibo(item)
            self.insertKeyword(item['mid'], spider.keyword,spider.weibo_keyword_id)
        return item

    def insertWeibo(self, original_item):
        item= original_item.copy()
        item['datetime']=item['datetime'].isoformat()
        item['created_at'] = datetime.datetime.now().isoformat()
        placeholder = ', '.join(['%s'] * len(item))
        columns = ', '.join(map(lambda x: '`%s`' % x, item.keys()))
        try:
            sql = "Insert Into %s (%s) Values (%s);" % (item.table_name, columns, placeholder)
            self.cursor.execute(sql, list(item.values()))
            self.mydb.commit()
        except pymysql.err.IntegrityError:
            pass
        except Exception as e:
            print(str(e))
            self.mydb.rollback()


    def insertKeyword(self,mid,keyword,weibo_keyword_id):
        sql = "INSERT INTO weibo_keyword_relations(mid,keyword,weibo_keyword_id)VALUES(%s, '%s',%s )" % (mid, keyword,weibo_keyword_id)
        try:
            self.cursor.execute(sql)
            self.mydb.commit()
        except pymysql.err.IntegrityError:
            pass
