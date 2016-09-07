#
# A simple Flask example
#
# Installation:
# pip install [packages]
# Where packages are:
# flask-script, flask-bootstrap, flask-moment
# flask-wtf, flask-sqlalchemy
#

import os
from datetime import datetime

from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, render_template
from flask import request, current_app, flash
from flask import session, make_response
from flask import redirect, abort

from config import config

MODE = 'development'

base_dir = os.path.dirname(os.path.realpath(__file__))
crashes_dir = os.path.join(base_dir, 'crash_files')

app = Flask(__name__)
app.config.from_object(config[MODE])

####################################################
# DATABASE
####################################################
db = SQLAlchemy(app)


class Crashes(db.Model):
    __tablename__ = 'Crashes'
    Id = db.Column(db.Integer, primary_key = True)
    NodeId = db.Column(db.String(256))
    Victim = db.Column(db.String(256))
    Cpu = db.Column(db.String(256))
    EventName = db.Column(db.String(256))
    Ip = db.Column(db.String(256))
    StackTrace = db.Column(db.String(256))
    CrashLabel = db.Column(db.String(256))
    Exploitable = db.Column(db.String(256))
    FileName = db.Column(db.String(256))

    def __repr__(self):
        return '<Crash %r>' % self.Id

# This is idempotent for existing tables
db.create_all()

####################################################
# ROUTES
####################################################
moment = Moment(app)
manager = Manager(app)
bootstrap = Bootstrap(app)

@app.route('/')
def index():
    return render_template('index.html',
                           current_time = datetime.utcnow())

@app.route('/victims/<name>')
def user(name):
    if len(name) > 3:
        flash('Name tooooo long...')
        abort(404)

    return render_template('user.html', name = name)

@app.route('/crashes')
def crashes():
    crash_list = Crashes.query.all()
    return render_template('crashes.html', crash_list = crash_list)

@app.route('/crash_files/<file>')
def get_crash_file(file):
    return app.send_static_file(os.path.join('crash_files', file))

@app.route('/coverage')
def coverage():
    return render_template('coverage.html')

####################################################
# CUSTOM ERROR PAGES
####################################################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    print "Initializing..."
    manager.run()
