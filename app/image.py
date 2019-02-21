from flask import render_template, redirect, url_for, request, g, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.macro import *
from app.db import *


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@webapp.route('/image/<id1>/<id2>',methods=['GET'])
def image(id1,id2):

    print(id1)

    id1 = id1.replace("__","/");
    id2 = id2.replace("__","/");

    id1 = id1.replace(" ","");
    id2 = id2.replace(" ","");

    return render_template("image.html", image1="/"+id1,image2="/"+id2 )

