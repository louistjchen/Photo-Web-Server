from flask import redirect, url_for, request, session
from werkzeug.security import check_password_hash

from app.db import *


@webapp.route('/login', methods=['POST'])
def login():

    log_http_request('/login', 'post')
    username = request.form.get('username', "")
    password = request.form.get('password', "")
    session.pop('ret_msg', None)

    # input string validation
    for c in username:
        if c not in username_char:
            session['ret_msg'] = "Error: Username must not contain character: " + c
            return redirect(url_for('main'))
    for c in password:
        if c not in password_char:
            session['ret_msg'] = "Error: Password must not contain character: " + c
            return redirect(url_for('main'))

    cnx = get_db()
    cursor = cnx.cursor()

    cursor.execute("SELECT COUNT(1) FROM users WHERE username = '{}';".format(username))

    if not cursor.fetchone()[0]:
        session['ret_msg'] = "Error: No such user"
        return redirect(url_for('main'))

    cursor.execute("SELECT salt from users WHERE username = '{}';".format(username))
    salt = cursor.fetchone()[0]
    cursor.execute("SELECT password FROM users WHERE username = '{}';".format(username))

    if check_password_hash(cursor.fetchone()[0], password + salt):
        session['username'] = username
        return redirect(url_for('main'))
    else:
        session['ret_msg'] = "Error: Password wrong"
        return redirect(url_for('main'))
