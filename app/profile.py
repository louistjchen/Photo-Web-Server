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
        ret.append([row[0], row[1], row[2][4:], row[3][4:]])
    return ret

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
