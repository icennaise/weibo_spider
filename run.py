# -*- coding: utf-8 -*-
# @Time     : 2017/1/1 17:51
# @Author   : woodenrobot


from scrapy import cmdline

# def fab():
#     n=1
#     while n < 10:
#         yield n      # 使用 yield
#         n = n + 1
#     yield fab()
# for i in fab():
#     print(i)

name = 'weibo'
cmd = 'scrapy crawl {0}'.format(name)
cmdline.execute(cmd.split())