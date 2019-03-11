import datetime
import os
import time

import cv2 as cv
from flask import render_template, redirect, url_for, request, session

from app.db import *

def retrieve_images(username):
    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM photos WHERE username = '{}';".format(username))
    ret = []
    for row in cursor:
        original = download_file_from_s3(row[2])
        face = download_file_from_s3(row[3])
        ret.append([row[0], original, face])
    return ret

@webapp.route('/logout', methods=['GET'])
def logout():
    log_http_request('/logout', 'get')
    session.pop('username', None)
    session.pop('ret_msg', None)
    return redirect(url_for('main'))
