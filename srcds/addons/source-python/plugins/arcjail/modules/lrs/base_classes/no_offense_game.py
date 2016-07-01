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

from ...damage_hook import get_hook, protected_player_manager

from .. import stage

from .jail_game import JailGame


class NoOffenseGame(JailGame):
    stage_groups = {
        'nooffensegame-start': [
            "equip-damage-hooks",
            'nooffensegame-entry',
        ],
    }

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self._counters = {}

    @stage('basegame-entry')
    def stage_basegame_entry(self):
        self.set_stage_group('nooffensegame-start')

    @stage('nooffensegame-entry')
    def stage_nooffensegame_entry(self):
        pass

    @stage('equip-damage-hooks')
    def stage_equip_damage_hooks(self):
        for player in self._players:
            p_player = protected_player_manager[player.index]

            counter = self._counters[player.index] = p_player.new_counter()
            counter.hook_hurt = get_hook('SW')

            p_player.set_protected()

    @stage('undo-equip-damage-hooks')
    def stage_undo_equip_damage_hooks(self):
        for player in self._players_all:
            p_player = protected_player_manager[player.index]
            p_player.delete_counter(self._counters[player.index])
            p_player.unset_protected()
