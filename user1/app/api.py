import datetime
import os
import time

import cv2 as cv
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from app.db import *

image_format = ['.jpg', '.jpeg', '.bmp', '.png', '.gif', '.tif']


def get_image_extension(name):
    ret = ""
    for c in reversed(name):
        ret = c + ret
        if c == '.':
            return ret
    return ""


@webapp.route('/api/register', methods=['POST'])
def api_register():
    log_http_request('/api/register', 'post')
    print("Receiving /api/register api...")
    username = request.form.get('username', "")
    password = request.form.get('password', "")

    if username == "" or password == "":
        return jsonify({"HTTP Status Code" : 400, "Message" : "Error: All fields are required!"})

    # input string validation
    for c in username:
        if c not in username_char:
            return jsonify({'HTTP Status Code' : 400, "Message" : "Error: Username must not contain character: " + c})
    for c in password:
        if c not in password_char:
            return jsonify({'HTTP Status Code' : 400, "Message" : "Error: Password must not contain character: " + c})

    salt = generate_salt()
    hashed_password = generate_password_hash(password + salt)

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT COUNT(1) FROM users WHERE username = '{}';".format(username))

    if cursor.fetchone()[0]:
        return jsonify({'HTTP Status Code' : 400, "Message" : "Error: Username has been used"})

    cursor.execute(''' INSERT INTO users (username,password,salt)
                               VALUES (%s,%s,%s)
            ''', (username, hashed_password, salt))
    cnx.commit()

    return jsonify({'HTTP Status Code' : 200, "Message" : "Success: User is registered successfully"})


@webapp.route('/api/upload', methods=['POST'])
def api_upload():
    log_http_request('/api/upload', 'post')
    print("Receiving /api/upload api...")
    username = request.form.get('username', "")
    password = request.form.get('password', "")

    # check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'HTTP Status Code' : 400, "Message" : "Error: Missing uploaded file"})
    new_file = request.files['file']

    # authenticate user
    # input string validation
    for c in username:
        if c not in username_char:
            return jsonify({'HTTP Status Code' : 400, "Message" : "Error: Username must not contain character: " + c})
    for c in password:
        if c not in password_char:
            return jsonify({'HTTP Status Code' : 400, "Message" : "Error: Password must not contain character: " + c})

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT COUNT(1) FROM users WHERE username = '{}';".format(username))

    if not cursor.fetchone()[0]:
        return jsonify({'HTTP Status Code' : 401, "Message" : "Error: No such user"})

    cursor.execute("SELECT salt from users WHERE username = '{}';".format(username))
    salt = cursor.fetchone()[0]
    cursor.execute("SELECT password FROM users WHERE username = '{}';".format(username))

    if check_password_hash(cursor.fetchone()[0], password + salt) == False:
        return jsonify({'HTTP Status Code' : 401, "Message" : "Error: Password wrong"})

    # upload file onto database
    filename = new_file.filename
    extension = get_image_extension(filename)
    if extension not in image_format:
        return jsonify({'HTTP Status Code' : 400,
                        "Message" : "Error: Input file must be of type JPEG/BMP/PNG/GIF/TIFF"})

    # if user does not select file, browser also
    # submit a empty part without filename
    if filename == '':
        return jsonify({'HTTP Status Code' : 400, "Message" : "Error: Missing file name"})

    directory = 'app/static/temp/'
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

    filename1 = username + '/' + filename1
    filename2 = username + '/' + filename2

    # write filename1 and filename2 associated with username into database
    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute(''' INSERT INTO photos (username,imagepath1,imagepath2)
                               VALUES (%s,%s,%s)
            ''', (username, filename1, filename2))
    cnx.commit()

    # upload 2 files onto s3
    upload_file_to_s3(fname1, filename1)
    upload_file_to_s3(fname2, filename2)

    # deleting local cached files
    os.remove(fname1)
    os.remove(fname2)

    return jsonify({'HTTP Status Code' : 200, "Message" : "Success: Photo is uploaded successfully"})
