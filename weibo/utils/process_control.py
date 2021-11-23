import datetime
def deal_with_empty_response():
    print(1)

def generate_next_date_payload(last_datetime,weibo_list):
    if last_datetime==None:
        pass
    else:
        weibo_list.append({'datetime':last_datetime})
    sorted_weibo_list = sorted(weibo_list, key=lambda x: x['datetime'])
    last_datetime=sorted_weibo_list[0]['datetime']
    for i in range(1,len(sorted_weibo_list)):
        if sorted_weibo_list[i]['datetime']-sorted_weibo_list[i-1]['datetime']>datetime.timedelta(seconds=3600*12):
            last_datetime=sorted_weibo_list[i]['datetime']
    print(last_datetime)
    return last_datetime+datetime.timedelta(seconds=3600)
