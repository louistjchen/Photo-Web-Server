from flask import render_template

from app.db import *


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@webapp.route('/image/<id>', methods=['GET'])
def image(id):

    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM photos WHERE id = '{}';".format(id))
    original = None
    face = None
    for row in cursor:
        original = download_file_from_s3(row[2])
        face = download_file_from_s3(row[3])
        break

    return render_template("image.html", image1=original, image2=face)
