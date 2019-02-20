from flask import render_template, redirect, url_for, request, g, session
from app import webapp
from app.macro import *

from werkzeug.security import generate_password_hash, check_password_hash
from app.config import db_config

import mysql.connector
import random

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

def generate_salt():
    chars = []
    for i in range(16):
        chars.append(random.choice(salt_char))
    return "".join(chars)

@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@webapp.route('/register/form',methods=['GET'])
def register_form():

    return render_template("register.html", error_msg="", hidden="hidden")


@webapp.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', "")
    password = request.form.get('password', "")
    confirm_password = request.form.get('confirm_password', "")

    if username == "" or password == "" or confirm_password == "":
        error_msg = "Error: All fields are required!"
        return render_template("register.html", error_msg=error_msg, username=username, password=password, confirm_password=confirm_password, hidden="visible")

    if password != confirm_password:
        error_msg = "Error: Passwords are not equal"
        return render_template("register.html", error_msg=error_msg, username=username, password="",confirm_password="", hidden="visible")

    # input string validation
    for c in username:
        if c not in username_char:
            error_msg = "Error: Username must not contain character: " + c
            return render_template("register.html", error_msg=error_msg, username=username, password="", hidden="visible")
    for c in password:
        if c not in password_char:
            error_msg = "Error: Password must not contain character: " + c
            return render_template("register.html", error_msg=error_msg, username=username, password="", hidden="visible")

    salt = generate_salt()
    hashed_password = generate_password_hash(password+salt)

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT COUNT(1) FROM users WHERE username = '{}';".format(username))

    if cursor.fetchone()[0]:
        error_msg = "Error: Username has been used"
        return render_template("login.html", error_msg=error_msg, username="", password="", confirm_password="", hidden="visible")


    cursor.execute(''' INSERT INTO users (username,password,salt)
                               VALUES (%s,%s,%s)
            ''', (username, hashed_password, salt))
    cnx.commit()

    # record usernmae in the active session
    session['username'] = username
    return redirect(url_for('main'))
