# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Weibo(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name="weibo"
    table_name="weibo_cards"
    parser_datetime='None'
    mid = scrapy.Field()
    mhash = scrapy.Field()
    userid = scrapy.Field()
    username = scrapy.Field()
    datetime = scrapy.Field()
    source = scrapy.Field()
    seqid = scrapy.Field()
    text = scrapy.Field()
    repost = scrapy.Field()
    comment = scrapy.Field()
    like = scrapy.Field()
    heat = scrapy.Field()
    querydatetime = scrapy.Field()
    created_at = scrapy.Field()
    updated_at = scrapy.Field()

#Weibo(mid=mid, mhash=mhash, userid=userID, username=userName, datetime=timeList, source=deviceList, seqid=seqid, text=text, repost=text_repost,comment=text_comment, like=text_like, heat=text_repost*15+text_comment*5+text_like*2+100)