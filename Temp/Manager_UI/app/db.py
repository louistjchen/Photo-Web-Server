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


def delete_outdated(delete):
    query = "DELETE FROM requests WHERE id = %s"

    cnx = get_db()
    cursor = cnx.cursor()
    for id in delete:
        print("deleting "+str(id))
        cursor.execute(query, (id,))
    cnx.commit()


def retrieve_http_request_rate(id):

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT * FROM requests WHERE instanceid = '{}';".format(id))
    timestamps = []
    delete = []
    for row in cursor:
        timestamps.append(row)
        timestamps.reverse()


    t = time.gmtime()
    current = calendar.timegm(t) - t.tm_sec + 60
    timeframe = 30
    ret = [[0-i, 0] for i in range(timeframe)]
    for ts in timestamps:
        timestamp = int(ts[2])
        diff = current - timestamp
        minute = int(diff/60)
        if minute < timeframe:
            ret[minute][1] = ret[minute][1] + 1
        else:
            delete.append(ts[0])

    delete_outdated(delete)

    return ret
