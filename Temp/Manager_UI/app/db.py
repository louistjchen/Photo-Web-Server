import mysql.connector
import time
import calendar

from flask import g
from app import webapp
from app.config import db_config


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database']
                                   )


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def retrieve_http_request_rate(id):

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT * FROM requests WHERE instanceid = '{}';".format(id))
    timestamps = []
    for row in cursor:
        timestamps.append(int(row[2]))
        timestamps.reverse()

    current = calendar.timegm(time.gmtime())
    timeframe = 30
    ret = [[i-timeframe+1, 0] for i in range(30)]
    for timestamp in timestamps:
        diff = current - timestamp
        minute = int(diff/60)
        if minute < 30:
            ret[minute-timeframe+1][1] = ret[minute-timeframe+1][1] + 1
        else:
            break

    return ret
