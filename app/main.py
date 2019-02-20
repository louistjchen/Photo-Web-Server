from flask import render_template, redirect, url_for, request, g, session
from app import webapp
from app.profile import retrieve_images


@webapp.route('/', methods=['GET'])
@webapp.route('/index', methods=['GET'])
@webapp.route('/main', methods=['GET'])
# Display an HTML page with links
def main():
    if 'username' in session:
        username = session['username']
        images = retrieve_images(username)
        return render_template("profile.html", username=username, images=images)
    else:
        return render_template("login.html", username="", password="", hidden="hidden")
