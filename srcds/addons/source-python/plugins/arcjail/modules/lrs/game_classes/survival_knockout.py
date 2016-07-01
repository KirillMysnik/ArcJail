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

from ....arcjail import InternalEvent

from ...damage_hook import is_world, protected_player_manager

from ...games.game_classes.survival_knockout import (
    push_by_damage_info, strings_module as strings_games)

from ...players import main_player_manager

from ...show_damage import show_damage

from .. import add_available_game, stage

from .survival import (
    SurvivalPlayerBasedFriendlyFire, SurvivalTeamBasedFriendlyFire)


def build_survival_knockout_base(*parent_classes):
    class SurvivalKnockoutBase(*parent_classes):
        @stage('survival-equip-damage-hooks')
        def stage_survival_equip_damage_hooks(self):
            for player in self._players:
                p_player = protected_player_manager[player.index]
                self._counters[player.index] = []

                def hook_game_player(counter, info, player=player):
                    if (info.attacker == player.index or
                            is_world(info.attacker)):

                        return False

                    attacker = main_player_manager[info.attacker]
                    if attacker in self._players:
                        self._flawless[player.index] = False

                        InternalEvent.fire('jail_stop_accepting_bets',
                                           instance=self)

                        show_damage(attacker, info.damage)
                        push_by_damage_info(
                            player, attacker, info, self.map_data)

                    return False

                def hook_w_min_damage(counter, info):
                    if not is_world(info.attacker):
                        return False

                    min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']
                    return info.damage >= min_damage

                counter1 = p_player.new_counter()
                counter1.hook_hurt = hook_game_player

                counter2 = p_player.new_counter()
                counter2.hook_hurt = hook_w_min_damage
                counter2.health = self.map_data['INITIAL_HEALTH']

                self._counters[player.index].append(counter1)
                self._counters[player.index].append(counter2)

                p_player.set_protected()

    return SurvivalKnockoutBase


class SurvivalKnockoutPlayerBased(
        build_survival_knockout_base(SurvivalPlayerBasedFriendlyFire)):

    _caption = strings_games['title knockout_playerbased']
    module = 'survival_knockout_playerbased'

add_available_game(SurvivalKnockoutPlayerBased)


class SurvivalKnockoutTeamBased(
        build_survival_knockout_base(SurvivalTeamBasedFriendlyFire)):

    _caption = strings_games['title knockout_teambased']
    module = 'survival_knockout_teambased'

add_available_game(SurvivalKnockoutTeamBased)
