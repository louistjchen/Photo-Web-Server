from flask import render_template, redirect, url_for, request, g
from app import webapp


@webapp.route('/', methods=['GET'])
@webapp.route('/index', methods=['GET'])
@webapp.route('/main', methods=['GET'])

def main():
    return redirect(url_for('ec2_list'))
