from ConfigParser import ConfigParser
import os.path


APP_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
CONFIG_FILE = os.path.join(APP_DATA_PATH, "config.ini")

config = ConfigParser()
config.read(CONFIG_FILE)


app = None
db = None
plugin_instance = None


def init(app_, db_):
    global app, db, plugin_instance

    app = app_
    db = db_

    from motdplayer.plugin_instance import PluginInstance

    plugin_instance = PluginInstance(app, config.get('server', 'id'), 'arcrpg')

    import views
