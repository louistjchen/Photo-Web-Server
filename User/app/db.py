import random
import boto3
import time
import calendar
import urllib.request

import mysql.connector
from flask import g

from app import webapp
from app.macro import *

db_config = {'user': 'master',
             'password': 'ece1779pass',
             'host': 'ece1779.c3z9wvey8adq.us-east-2.rds.amazonaws.com',
             'database': 'a2'}

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

def get_s3():

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWSAccessKeyId,
        aws_secret_access_key=AWSSecretKey
    )
    return s3

def upload_file_to_s3(upload, filename):

    s3 = get_s3()
    s3.upload_file(upload, bucket, filename)

def download_file_from_s3(filename):

    s3 = get_s3()
    url = s3.generate_presigned_url('get_object',
                              Params={
                                  'Bucket': bucket,
                                  'Key': filename,
                              },
                              ExpiresIn=3600)
    return url

def log_http_request(url, method):

    # instanceid = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read().decode()
    instanceid = 'louis_macbook'
    timestamp = calendar.timegm(time.gmtime())

    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute(''' INSERT INTO requests (instanceid,timestamp,url,method)
                               VALUES (%s,%s,%s,%s)
            ''', (instanceid, timestamp, url, method))
    cnx.commit()


