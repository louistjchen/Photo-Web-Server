from flask import Flask

from app.macro import secret_key

webapp = Flask(__name__)
webapp.secret_key = secret_key

from app import main
from app import login
from app import register
from app import profile
from app import image
from app import api
