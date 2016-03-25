from paths import CFG_PATH, GAME_PATH, PLUGIN_DATA_PATH

from ..info import info


ARCJAIL_CFG_PATH = CFG_PATH / info.basename
ARCJAIL_DATA_PATH = PLUGIN_DATA_PATH / info.basename
DOWNLOADLISTS_PATH = ARCJAIL_CFG_PATH / "downloadlists"
MAPDATA_PATH = GAME_PATH / "mapdata"
