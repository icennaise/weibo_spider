

def log(func):
    def wrapper(*args, **kw):
        print('call %s():' % func.__name__)
        return func(*args, **kw)

    return wrapper

def a():
    sl = sorted(self.weibo_datetime_list)
    for i in range(len(sl) - 1):
        sl[i]=[sl[i],sl[i+1]-sl[i]]
    sl[-1]=[sl[-1],datetime.timedelta(seconds=0)]
    rl=sorted(sl,key=lambda x:x[1])