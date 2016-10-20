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

from ...internal_events import InternalEvent

from ..damage_hook import (
    is_world, protected_player_manager, strings_module as strings_damage_hook)
from ..players import player_manager
from ..teams import GUARDS_TEAM, PRISONERS_TEAM

from . import get_player_game_instance, LastRequestGameStatus


class CrossGameAttackHandler:
    def __init__(self):
        self._enabled = 0
        self._counters = {}

    def _set_hook_on_player(self, player):
        p_player = protected_player_manager[player.index]
        if player.team in (GUARDS_TEAM, PRISONERS_TEAM):
            def hook_sw_nongame_players(counter, info, player=player):
                if (info.attacker == player.index or
                        is_world(info.attacker)):
                    return True

                attacker = player_manager[info.attacker]
                if attacker.team == player.team:
                    return False

                if get_player_game_instance(attacker) is not None:
                    return False

                return True

            counter = p_player.new_counter()
            counter.hook_hurt = hook_sw_nongame_players
            counter.display = strings_damage_hook['health general']

            self._counters[player.index] = counter
            p_player.set_protected()

    def _set_hooks(self):
        for player in player_manager.values():
            if player.dead:
                return

            # Note that we don't do any checks if the player takes part
            # in Last Request - because we only can be called from _enable()
            # and Last Request strips our hooks from its participants anyways
            # later in on_jail_lrs_status_set()
            self._set_hook_on_player(player)

    def _unset_hooks(self):
        for index, counter in self._counters.items():
            p_player = protected_player_manager[index]
            p_player.delete_counter(counter)
            p_player.unset_protected()

        self._counters.clear()

    def _enable(self):
        self._enabled += 1
        if self._enabled == 1:
            self._set_hooks()

    def _disable(self):
        if self._enabled == 0:
            raise ValueError("Already disabled enough times")

        self._enabled -= 1
        if self._enabled == 0:
            self._unset_hooks()

    def on_jail_lrs_status_set(self, instance, status):
        if status == LastRequestGameStatus.NOT_STARTED:
            self._enable()

            for index in (instance.guard.index, instance.prisoner.index):
                if index not in self._counters:
                    continue

                p_player = protected_player_manager[index]
                p_player.delete_counter(self._counters[index])
                p_player.unset_protected()

                del self._counters[index]

        elif status == LastRequestGameStatus.FINISHED:
            for player in instance.players:

                # Note how we don't check if the player is dead because
                # instance.players can only contain living players
                self._set_hook_on_player(player)

            self._disable()

cross_game_attack_handler = CrossGameAttackHandler()


@InternalEvent('jail_lrs_status_set')
def on_jail_lrs_status_set(instance, status):
    cross_game_attack_handler.on_jail_lrs_status_set(instance, status)
