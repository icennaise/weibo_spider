import datetime
def deal_with_empty_response():
    print(1)

def generate_next_date_payload(parser_datetime):
    parser_datetime+=datetime.timedelta(seconds=3600)
    return parser_datetime.isoformat()