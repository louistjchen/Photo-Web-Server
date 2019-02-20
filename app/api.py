from flask import render_template, redirect, url_for, request, g, session
from app import webapp
from werkzeug.security import generate_password_hash, check_password_hash
from app.macro import *
from app.db import *

import os
import cv2 as cv
import random
import time
import datetime


def get_image_extension(name):
    ret = ""
    for c in reversed(name):
        ret = c + ret
        if c == '.':
            return ret
    return ""

@webapp.route('/api/register', methods=['POST'])
def api_register():
    print("Receiving /api/register api...")
    username = request.form.get('username', "")
    password = request.form.get('password', "")

    if username == "" or password == "":
        return "Error: All fields are required!\n"

    # input string validation
    for c in username:
        if c not in username_char:
            return "Error: Username must not contain character: " + c + "\n"
    for c in password:
        if c not in password_char:
            return "Error: Password must not contain character: " + c + "\n"

    salt = generate_salt()
    hashed_password = generate_password_hash(password+salt)

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT COUNT(1) FROM users WHERE username = '{}';".format(username))

    if cursor.fetchone()[0]:
        return "Error: Username has been used\n"

    cursor.execute(''' INSERT INTO users (username,password,salt)
                               VALUES (%s,%s,%s)
            ''', (username, hashed_password, salt))
    cnx.commit()

    return "Success\n"

@webapp.route('/api/upload', methods=['POST'])
def api_upload():
    print("Receiving /api/upload api...")
    username = request.form.get('username', "")
    password = request.form.get('password', "")

    # check if the post request has the file part
    if 'file' not in request.files:
        return "Error: Missing uploaded file\n"
    new_file = request.files['file']

    # authenticate user
    # input string validation
    for c in username:
        if c not in username_char:
            return "Error: Username must not contain character: " + c + "\n"
    for c in password:
        if c not in password_char:
            return "Error: Password must not contain character: " + c + "\n"

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT COUNT(1) FROM users WHERE username = '{}';".format(username))

    if not cursor.fetchone()[0]:
        return "Error: No such user\n"

    cursor.execute("SELECT salt from users WHERE username = '{}';".format(username))
    salt = cursor.fetchone()[0]
    cursor.execute("SELECT password FROM users WHERE username = '{}';".format(username))

    if check_password_hash(cursor.fetchone()[0], password + salt) == False:
        return "Error: Password wrong\n"

    # upload file onto database
    filename = new_file.filename
    extension = get_image_extension(filename)
    if extension == "":
        extension = ".jpg"

    # if user does not select file, browser also
    # submit a empty part without filename
    if filename == '':
        return "Error: Missing file name\n"

    # create a directory for use if not exist
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
#    eye_cascade = cv.CascadeClassifier(cwd + '/app/train_file/eye.xml')
    img = cv.imread(fname1)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for (x, y, w, h) in faces:
        cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = img[y:y + h, x:x + w]
#        eyes = eye_cascade.detectMultiScale(roi_gray)
#        for (ex, ey, ew, eh) in eyes:
#            cv.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

    cv.imwrite(fname2, img)

    # write filename1 and filename2 associated with username into database
    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute(''' INSERT INTO photos (username,imagepath1,imagepath2)
                               VALUES (%s,%s,%s)
            ''', (username, fname1, fname2))
    cnx.commit()

    return "Success\n"
