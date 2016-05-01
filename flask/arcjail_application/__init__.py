# This file is part of ArcJail.
#
# ArcJail is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ArcJail is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ArcJail.  If not, see <http://www.gnu.org/licenses/>.

from ConfigParser import ConfigParser
import os.path

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)

APP_SETTINGS = 'arcjail_application.settings'
app.config.from_object(APP_SETTINGS)

APP_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
CONFIG_FILE = os.path.join(APP_DATA_PATH, "config.ini")

config = ConfigParser()
config.read(CONFIG_FILE)

db = SQLAlchemy(app)

import motdplayer
motdplayer.init(app, db)

db.create_all()
db.session.commit()

from motdplayer.plugin_instance import PluginInstance

plugin_instance = PluginInstance(app, config.get('server', 'id'), 'arcjail')

import views
