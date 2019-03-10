import random
import boto3

import mysql.connector
from flask import g

from app import webapp
from app.macro import *

db_config = {'user': 'ece1779',
             'password': 'secret',
             'host': '127.0.0.1',
             'database': 'a1'}

AWSAccessKeyId = 'AKIAJJ3IQ3G2KAR3UR7Q'
AWSSecretKey = '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'
bucket = 'photo-web-server'


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


def upload_file_to_s3(upload, filename):

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWSAccessKeyId,
        aws_secret_access_key=AWSSecretKey
    )
    s3.upload_file(upload, bucket, filename)
