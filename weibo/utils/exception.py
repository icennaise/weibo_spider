class WeiboNoResultException(Exception):

    def __init__(self):
        pass

    def __str__(self):
        return "微博提示找不到没有搜索到内容"


class BadSoupException(Exception):

    def __init__(self):
        pass

    def __str__(self):
        return "请求成功但未获取到内容，可能是遇到反爬或登录验证"
