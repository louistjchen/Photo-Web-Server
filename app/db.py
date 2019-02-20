from app import webapp
from flask import g
from app.macro import *

import mysql.connector
import random

db_config = {'user': 'ece1779',
             'password': 'secret',
             'host': '127.0.0.1',
             'database': 'a1'}

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

def generate_salt():
    chars = []
    for i in range(16):
        chars.append(random.choice(salt_char))
    return "".join(chars)
