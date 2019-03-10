import datetime
import os
import time

import cv2 as cv
from flask import render_template, redirect, url_for, request, session

from app.db import *

import boto3

def get_image_extension(name):
    ret = ""
    for c in reversed(name):
        ret = c + ret
        if c == '.':
            return ret
    return ""


def retrieve_last_image(username):
    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM photos WHERE username = '{}' ORDER BY id DESC LIMIT 1;".format(username))
    ret = []
    for row in cursor:
        ret.append([row[0], row[1], row[2][4:], row[3][4:]])
    return ret

@webapp.route('/upload', methods=['GET'])
def upload_():
    ret_msg = session['ret_msg'] if 'ret_msg' in session else ""
    session.pop('ret_msg', None)
    hidden = "hidden" if ret_msg == "" else "visible"
    if 'username' in session:
        username = session['username']
    return render_template("upload.html", username=username, ret_msg=ret_msg, hidden=hidden)


@webapp.route('/upload', methods=['POST'])
# Upload a new image and tranform it
def upload():
    ret_msg = None
    session.pop('ret_msg', None)

    # check if the post request has the file part
    if 'image_file' not in request.files:
        ret_msg = 'Error: Missing uploaded file'
        return render_template("profile.html", ret_msg=ret_msg)

    new_file = request.files['image_file']
    filename = new_file.filename
    extension = get_image_extension(filename)
    if extension == "":
        extension = ".jpg"

    # if user does not select file, browser also
    # submit a empty part without filename
    if filename == '':
        ret_msg = 'Error: Missing file name'
        return render_template("profile.html", ret_msg=ret_msg)

    # create a directory for use if not exist
    username = session['username']
    directory = 'app/static/users/' + username + "/"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # set filename as timestamp
    ts = time.time()
    filename1 = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')
    filename2 = filename1 + "_face"
    filename1 = filename1 + extension
    filename2 = filename2 + extension
    fname1 = os.path.join(directory, filename1)
    fname2 = os.path.join(directory, filename2)
    new_file.save(fname1)

    cwd = os.getcwd()
    face_cascade = cv.CascadeClassifier(cwd + '/app/train_file/face.xml')
    img = cv.imread(fname1)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for (x, y, w, h) in faces:
        cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

    cv.imwrite(fname2, img)
    ret_msg = 'Success: Image has been successfully uploaded. Please see below.'

    # write filename1 and filename2 associated with username into database
    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute(''' INSERT INTO photos (username,imagepath1,imagepath2)
                               VALUES (%s,%s,%s)
            ''', (username, fname1, fname2))
    cnx.commit()

    # upload 2 files onto s3
    upload_file_to_s3(fname1, username+'/'+filename1)
    upload_file_to_s3(fname2, username+'/'+filename2)

    # retrieve all images associated with username from database
    image = retrieve_last_image(username)
    session['ret_msg'] = ret_msg
    #
    session.pop('ret_msg', None)
    hidden = "hidden" if ret_msg == "" else "visible"
    if 'username' in session:
        username = session['username']
    return render_template("upload.html", username=username, ret_msg=ret_msg, hidden=hidden, images=image)
