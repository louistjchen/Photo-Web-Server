from flask import render_template, redirect, url_for, request, g, session
from app.db import *

import os
import time
import datetime
import cv2 as cv

def get_image_extension(name):
    ret = ""
    for c in reversed(name):
        ret = c + ret
        if c == '.':
            return ret
    return ""

def retrieve_images(username):
    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM photos WHERE username = '{}';".format(username))
    ret = []
    for row in cursor:
        ret.append([row[0], row[1], row[2][4:], row[3][4:]])
    return ret

@webapp.route('/profile', methods=['POST'])
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
    eye_cascade = cv.CascadeClassifier(cwd + '/app/train_file/eye.xml')
    img = cv.imread(fname1)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for (x, y, w, h) in faces:
        cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = img[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for (ex, ey, ew, eh) in eyes:
            cv.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

    cv.imwrite(fname2, img)
    ret_msg = 'Success: Image has been successfully uploaded. Please see below.'

    # write filename1 and filename2 associated with username into database
    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute(''' INSERT INTO photos (username,imagepath1,imagepath2)
                               VALUES (%s,%s,%s)
            ''', (username, fname1, fname2))
    cnx.commit()

    # retrieve all images associated with username from database
    images = retrieve_images(username)
    session['ret_msg'] = ret_msg
    return redirect(url_for('main'))
    return render_template("profile.html", username=username, ret_msg=ret_msg, images=images)


@webapp.route('/profile/delete/<int:id>', methods=['POST'])
# Deletes the specified student from the database.
def delete_image(id):
    session.pop('ret_msg', None)

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT * FROM photos WHERE id = '{}';".format(id))
    row = cursor.fetchone()
    if row:
        if os.path.isfile(row[2]):
            os.remove(row[2])
        if os.path.isfile(row[3]):
            os.remove(row[3])

    cursor.execute("DELETE FROM photos WHERE id = '{}';".format(id))
    cnx.commit()
    session['ret_msg'] = "Image is succesfully deleted!\n"
    return redirect(url_for('main'))

@webapp.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    session.pop('ret_msg', None)
    return redirect(url_for('main'))
