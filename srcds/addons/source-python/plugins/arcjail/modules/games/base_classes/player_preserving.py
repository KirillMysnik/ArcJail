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

from ...players import broadcast, player_manager

from .. import (
    game_event_handler, game_internal_event_handler, stage, strings_module)

from .jail_game import JailGame


class PlayerPreserving(JailGame):
    stage_groups = {
        'abort-player-dead': ["abort-player-dead", ],
        'abort-player-disconnect': ["abort-player-disconnect", ],
        'abort-player-rebel': ["abort-player-rebel", ],
    }

    @stage('abort-player-dead')
    def stage_abort_player_dead(self):
        broadcast(strings_module['abort_player_dead'])
        self.set_stage_group('destroy')

    @stage('abort-player-disconnect')
    def stage_abort_player_disconnect(self):
        broadcast(strings_module['abort_player_disconnect'])
        self.set_stage_group('destroy')

    @stage('abort-player-rebel')
    def stage_abort_player_rebel(self):
        broadcast(strings_module['abort_player_rebel'])
        self.set_stage_group('destroy')

    @game_event_handler('playerpreserving-player-death', 'player_death')
    def event_playerpreserving_player_death(self, game_event):
        player = player_manager.get_by_userid(game_event['userid'])

        if player in self._players_all:
            self.set_stage_group('abort-player-dead')

    @game_internal_event_handler(
        'playerpreserving-main-player-deleted', 'player_deleted')
    def event_playerpreserving_player_deleted(self, player):
        if player in self._players_all:
            self.set_stage_group('abort-player-disconnect')

    @game_internal_event_handler(
        'playerpreserving-arcjail-rebel-set', 'jail_rebel_set')
    def event_playerpreserving_arcjail_rebel_set(self, player):
        if player in self._players_all:
            self.set_stage_group('abort-player-rebel')
