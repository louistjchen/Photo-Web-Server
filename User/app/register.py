from flask import render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash

from app.db import *


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@webapp.route('/register', methods=['GET'])
def register_form():
    log_http_request('/register', 'get')
    return render_template("register.html", ret_msg="", hidden="hidden")


@webapp.route('/register', methods=['POST'])
def register():
    log_http_request('/register', 'post')
    username = request.form.get('username', "")
    password = request.form.get('password', "")
    confirm_password = request.form.get('confirm_password', "")
    session.pop('ret_msg', None)

    if username == "" or password == "" or confirm_password == "":
        ret_msg = "Error: All fields are required!"
        return render_template("register.html", ret_msg=ret_msg, username=username, password=password,
                               confirm_password=confirm_password, hidden="visible")

    if password != confirm_password:
        ret_msg = "Error: Passwords are not equal"
        return render_template("register.html", ret_msg=ret_msg, username=username, password="", confirm_password="",
                               hidden="visible")

    # input string validation
    for c in username:
        if c not in username_char:
            ret_msg = "Error: Username must not contain character: " + c
            return render_template("register.html", ret_msg=ret_msg, username=username, password="", hidden="visible")
    for c in password:
        if c not in password_char:
            ret_msg = "Error: Password must not contain character: " + c
            return render_template("register.html", ret_msg=ret_msg, username=username, password="", hidden="visible")

    salt = generate_salt()
    hashed_password = generate_password_hash(password + salt)

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT COUNT(1) FROM users WHERE username = '{}';".format(username))

    if cursor.fetchone()[0]:
        ret_msg = "Error: Username has been used"
        return render_template("register.html", ret_msg=ret_msg, username="", password="", hidden="visible")

    cursor.execute(''' INSERT INTO users (username,password,salt)
                               VALUES (%s,%s,%s)
            ''', (username, hashed_password, salt))
    cnx.commit()

    # record usernmae in the active session
    session['username'] = username
    return redirect(url_for('main'))
