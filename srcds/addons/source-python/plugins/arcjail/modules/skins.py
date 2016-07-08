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

from json import load as json_load
from random import choice

from core import GAME_NAME
from engines.precache import Model

from ..arcjail import InternalEvent, load_downloadables

from ..classes.base_player_manager import BasePlayerManager

from ..resource.paths import ARCJAIL_CFG_PATH, DOWNLOADLISTS_PATH

from .teams import GUARDS_TEAM, PRISONERS_TEAM


DEFAULT_SKIN_PRIORITY = 1


# downloadlists/skins.res
if (DOWNLOADLISTS_PATH / "skins-{}.res".format(GAME_NAME)).isfile():
    _downloadables = load_downloadables("skins-{}.res".format(GAME_NAME))
else:
    _downloadables = load_downloadables("skins.res")


# other/skins.json
_groups_json_path = ARCJAIL_CFG_PATH / "other" / "skins-{}.json".format(GAME_NAME)
if not _groups_json_path.isfile():
    _groups_json_path = ARCJAIL_CFG_PATH / "other" / "skins.json"

with open(_groups_json_path) as f:
    groups = json_load(f)['groups']

precache = {}
for group in groups:
    for model_path in group.values():
        if not model_path:
            continue

        if model_path not in precache:
            precache[model_path] = Model(model_path)


class ModelRequest:
    def __init__(self, id_, priority, model_id):
        self.id = id_
        self.priority = priority
        self.model_id = model_id


class ModelPlayer(list):
    def __init__(self, player):
        super().__init__()

        self.player = player
        self._group = choice(groups)

    def _update(self):
        if self.player.dead:
            return

        if not self:
            return

        request_max = None
        for request in self:
            if request_max is None or request.priority >= request_max.priority:
                request_max = request

        model_path = self._group[request_max.model_id]
        if model_path:
            self.player.model = precache[model_path]

    def make_request(self, id_, priority, model_id):
        for request in self:
            if request.id == id_:
                self.remove(request)
                break

        self.append(ModelRequest(id_, priority, model_id))
        self._update()

    def cancel_request(self, id_):
        for request in self:
            if request.id == id_:
                self.remove(request)
                break
        else:
            return

        self._update()

model_player_manager = BasePlayerManager(ModelPlayer)


@InternalEvent('player_respawn')
def on_player_respawn(event_var):
    player = event_var['player']
    model_player = model_player_manager[player.index]
    model_player.clear()

    if player.team == PRISONERS_TEAM:
        model_id = "regular_prisoner"
    elif player.team == GUARDS_TEAM:
        model_id = "guard"
    else:
        return

    model_player.make_request(
        'default-skin',
        DEFAULT_SKIN_PRIORITY,
        model_id,
    )


@InternalEvent('main_player_created')
def on_main_player_created(event_var):
    player = event_var['main_player']
    model_player_manager.create(player)


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    player = event_var['main_player']
    model_player_manager.delete(player)
