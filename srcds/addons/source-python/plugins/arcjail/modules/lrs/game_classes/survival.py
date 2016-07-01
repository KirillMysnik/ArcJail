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

from warnings import warn

from cvars import ConVar

from ....arcjail import InternalEvent

from ...damage_hook import (
    get_hook, is_world, protected_player_manager,
    strings_module as strings_damage_hook)

from ...equipment_switcher import saved_player_manager

from ...falldmg_protector import protect as falldmg_protect

from ...games.game_classes.survival import (
    PossibleDeadEndWarning, strings_module as strings_games)

from ...games import play_flawless_effects

from ...no_ff_spam import (
    disable as no_ff_spam_disable, enable as no_ff_spam_enable)

from ...players import main_player_manager

from ...show_damage import show_damage

from ...silent_cvars import silent_set

from ..base_classes.map_game import MapGame
from ..base_classes.map_game_team_based import MapGameTeamBased

from .. import (
    add_available_game, game_event_handler, push, stage)


def build_survival_base(*parent_classes):
    class SurvivalBase(*parent_classes):
        stage_groups = {
            'mapgame-start': [
                "mapgame-equip-weapons",
                "mapgame-register-push-handlers",
                "mapgame-apply-cvars",
                "mapgame-fire-mapdata-outputs",
                "mapgame-entry",
            ],
            'mapgame-prepare': [
                "mapgame-cancel-falldmg-protection",
                "mapgame-equip-noblock",
                "mapgame-swap-guard",
                "survival-equip-damage-hooks",
                "mapgame-teleport-players",
                "mapgame-fire-mapdata-prepare-outputs",
                "mapgame-prepare-entry",
            ],
            'destroy': [
                "prepare-cancel-delays",
                "unsend-popups",
                "destroy",
                "survival-fall-protection",
            ],
        }

        def __init__(self, players, **kwargs):
            super().__init__(players, **kwargs)

            self._counters = {}
            self._flawless = {
                self.prisoner.index: True,
                self.guard.index: True,
            }

        @stage('survival-equip-damage-hooks')
        def stage_survival_equip_damage_hooks(self):
            def hook_hurt_for_prisoner(counter, info):
                min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']

                if info.damage >= min_damage:
                    self._flawless[self.prisoner.index] = False

                    InternalEvent.fire('jail_stop_accepting_bets',
                                       instance=self)

                    return True

                return False

            def hook_hurt_for_guard(counter, info):
                min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']

                if info.damage >= min_damage:
                    self._flawless[self.guard.index] = False

                    InternalEvent.fire('jail_stop_accepting_bets',
                                       instance=self)

                    return True

                return False

            for hook_hurt, player in zip(
                    (hook_hurt_for_prisoner, hook_hurt_for_guard),
                    self._players
            ):

                p_player = protected_player_manager[player.index]
                counter = p_player.new_counter(
                    display=strings_damage_hook['health game'])

                if self.map_data['ALLOW_SELFDAMAGE']:
                    counter.hook_hurt = get_hook('SW', next_hook=hook_hurt)

                else:
                    warn(PossibleDeadEndWarning(
                        "Self-damage is disabled and it's a non-ff game! "
                        "Players may have problems dying. "
                        "Tell map creator about this problem."))

                    counter.hook_hurt = get_hook('', next_hook=hook_hurt)

                counter.health = self.map_data['INITIAL_HEALTH']

                self._counters[player.index] = [counter, ]

                p_player.set_protected()

        @stage('undo-survival-equip-damage-hooks')
        def stage_undo_survival_equip_damage_hooks(self):
            for player in self._players_all:
                p_player = protected_player_manager[player.index]
                for counter in self._counters[player.index]:
                    p_player.delete_counter(counter)

                p_player.unset_protected()

        @stage('survival-fall-protection')
        def stage_survival_fall_protection(self):
            for player in self._players:
                falldmg_protect(player, self.map_data)

        @game_event_handler('jailgame-player-death', 'player_death')
        def event_jailgame_player_death(self, game_event):
            player = main_player_manager.get_by_userid(
                game_event.get_int('userid'))

            if player == self.prisoner:
                winner, loser = self.guard, self.prisoner
            else:
                winner, loser = self.prisoner, self.guard

            if self._flawless[winner.index]:
                play_flawless_effects(self._players)

            self._results['winner'] = winner
            self._results['loser'] = loser

            self.set_stage_group('win')

        @game_event_handler('survival-player-death', 'player_death')
        def event_survival_player_death(self, game_event):
            player = main_player_manager.get_by_userid(
                game_event.get_int('userid'))

            if player not in self._players:
                return

            saved_player = saved_player_manager[player.index]
            saved_player.strip()

        @push(None, 'end_game')
        def push_end_game(self, args):
            self.set_stage_group('abort-map-cancelled')

    return SurvivalBase


class SurvivalPlayerBased(build_survival_base(MapGame)):
    _caption = strings_games['title playerbased_standard']
    module = 'survival_playerbased_standard'

add_available_game(SurvivalPlayerBased)


class SurvivalTeamBased(build_survival_base(MapGameTeamBased)):
    _caption = strings_games['title teambased_standard']
    module = 'survival_teambased_standard'

add_available_game(SurvivalTeamBased)


def build_survival_friendlyfire_base(*parent_classes):
    class SurvivalFriendlyFireBase(*parent_classes):
        cvar_friendlyfire = ConVar('mp_friendlyfire')

        stage_groups = {
            'mapgame-start': [
                "mapgame-equip-weapons",
                "mapgame-register-push-handlers",
                "mapgame-apply-cvars",
                "mapgame-fire-mapdata-outputs",
                "survival-enable-ff",
                "mapgame-entry",
            ]
        }

        @stage('survival-enable-ff')
        def stage_survival_enable_ff(self):
            no_ff_spam_enable()

            self._cvars['friendlyfire'] = self.cvar_friendlyfire.get_bool()

            silent_set(self.cvar_friendlyfire, 'bool', True)

        @stage('undo-survival-enable-ff')
        def stage_undo_survival_enable_ff(self):
            no_ff_spam_disable()

            silent_set(
                self.cvar_friendlyfire, 'bool', self._cvars['friendlyfire'])

        @stage('survival-equip-damage-hooks')
        def stage_survival_equip_damage_hooks(self):
            for player in self._players:
                p_player = protected_player_manager[player.index]

                def hook_min_damage(counter, info, player=player):
                    min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']

                    if info.damage >= min_damage:
                        self._flawless[player.index] = False

                        InternalEvent.fire('jail_stop_accepting_bets',
                                           instance=self)

                        return True

                    return False

                def hook_game_p(counter, info, player=player):
                    if (info.attacker == player.index or
                            is_world(info.attacker)):

                        return False

                    attacker = main_player_manager[info.attacker]
                    if attacker in self._players:
                        show_damage(attacker, info.damage)
                        return hook_min_damage(counter, info)

                    return False

                def hook_sw_game_p(counter, info, player=player):
                    if (info.attacker == player.index or
                            is_world(info.attacker)):

                        return hook_min_damage(counter, info)

                    attacker = main_player_manager[info.attacker]
                    if attacker in self._players:
                        show_damage(attacker, info.damage)
                        return hook_min_damage(counter, info)

                    return False

                counter = p_player.new_counter(
                    display=strings_damage_hook['health game'])

                if self.map_data['ALLOW_SELFDAMAGE']:
                    counter.hook_hurt = hook_sw_game_p
                else:
                    counter.hook_hurt = hook_game_p

                counter.health = self.map_data['INITIAL_HEALTH']

                self._counters[player.index] = [counter, ]
                p_player.set_protected()

    return SurvivalFriendlyFireBase


class SurvivalTeamBasedFriendlyFire(
        build_survival_friendlyfire_base(SurvivalTeamBased)):

    _caption = strings_games['title teambased_friendlyfire']
    module = 'survival_teambased_friendlyfire'

add_available_game(SurvivalTeamBasedFriendlyFire)


class SurvivalPlayerBasedFriendlyFire(
        build_survival_friendlyfire_base(SurvivalPlayerBased)):

    _caption = strings_games['title playerbased_friendlyfire']
    module = 'survival_playerbased_friendlyfire'

add_available_game(SurvivalPlayerBasedFriendlyFire)
