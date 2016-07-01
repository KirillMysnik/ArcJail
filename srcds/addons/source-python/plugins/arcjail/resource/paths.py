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

from paths import (
    CFG_PATH, GAME_PATH, LOG_PATH, PLUGIN_DATA_PATH, TRANSLATION_PATH)

from ..info import info


ARCJAIL_CFG_PATH = CFG_PATH / info.basename
ARCJAIL_DATA_PATH = PLUGIN_DATA_PATH / info.basename
ARCJAIL_LOG_PATH = LOG_PATH / info.basename
DOWNLOADLISTS_PATH = ARCJAIL_CFG_PATH / "downloadlists"
MAPDATA_PATH = GAME_PATH / "mapdata"
MAP_TRANSLATION_PATH = TRANSLATION_PATH / info.basename / "maps"
