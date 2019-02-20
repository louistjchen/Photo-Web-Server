from flask import render_template, redirect, url_for, request, g, session
from app import webapp
from werkzeug.security import generate_password_hash, check_password_hash

from app.config import db_config
from app.macro import *

import mysql.connector

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


@webapp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', "")
    password = request.form.get('password', "")

    # input string validation
    for c in username:
        if c not in username_char:
            ret_msg = "Error: Username must not contain character: " + c
            return render_template("login.html", ret_msg=ret_msg, hidden="visible", username=username, password="")
    for c in password:
        if c not in password_char:
            ret_msg = "Error: Password must not contain character: " + c
            return render_template("login.html", ret_msg=ret_msg, hidden="visible", username=username, password="")

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT COUNT(1) FROM users WHERE username = '{}';".format(username))

    if not cursor.fetchone()[0]:
        ret_msg = "Error: No such user"
        return render_template("login.html", ret_msg=ret_msg, hidden="visible", username="", password="")

    cursor.execute("SELECT salt from users WHERE username = '{}';".format(username))
    salt = cursor.fetchone()[0]
    cursor.execute("SELECT password FROM users WHERE username = '{}';".format(username))

    if check_password_hash(cursor.fetchone()[0], password + salt):
        session['username'] = username
        return redirect(url_for('main'))
    else:
        ret_msg = "Error: Password wrong"
        return render_template("login.html", ret_msg=ret_msg, hidden="visible", username="", password="")
