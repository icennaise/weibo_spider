import pymysql


def get_database_conn():
    host = "10.15.20.193"
    user = "root"
    password = "root"
    db = "test"
    return pymysql.connect(host=host, user=user, password=password, db=db)