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

from controlled_cvars.handlers import bool_handler, int_handler

from ...resource.strings import build_module_strings

from ..damage_hook import (
    get_hook, is_world, protected_player_manager,
    strings_module as strings_damage_hook)

from ..equipment_switcher import saved_player_manager

from ..falldmg_protector import protect as falldmg_protect

from ..no_ff_spam import (
    disable as no_ff_spam_disable, enable as no_ff_spam_enable)

from ..players import broadcast, main_player_manager

from ..rebels import register_rebel_filter, unregister_rebel_filter

from ..show_damage import show_damage

from ..silent_cvars import silent_set

from ..teams import GUARDS_TEAM

from .. import build_module_config

from .base_classes.map_game import MapGame
from .base_classes.map_game_team_based import MapGameTeamBased

from . import (
    add_available_game, config_manager as config_manager_common,
    game_event_handler, helper_set_loser, helper_set_winner, push, stage,
    strings_module as strings_common)


class PossibleDeadEndWarning(Warning):
    pass


strings_module = build_module_strings('games/survival')
config_manager = build_module_config('games/survival')

config_manager.controlled_cvar(
    bool_handler,
    "enabled",
    default=1,
    description="Enable/Disable Survival Games"
)
config_manager.controlled_cvar(
    int_handler,
    "playerbased_percentage",
    default=50,
    description="Dead players percentage when the game ends"
)


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
            'destroy': [
                "prepare-cancel-delays",
                "unsend-popups",
                "destroy",
                "survival-fall-protection",
            ],
        }

        def __init__(self, leader_player, players, **kwargs):
            super().__init__(leader_player, players, **kwargs)

            self._counters = {}
            self._rebel_filter = None

        @stage('survival-equip-damage-hooks')
        def stage_survival_equip_damage_hooks(self):
            def hook_min_damage(counter, info):
                min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']
                return info.damage >= min_damage

            for player in main_player_manager.values():
                if player.dead:
                    continue

                p_player = protected_player_manager[player.index]
                self._counters[player.userid] = []
                if player in self._players:
                    counter1 = p_player.new_counter(
                        display=strings_damage_hook['health against_guards'])

                    counter1.hook_hurt = get_hook('G')

                    counter2 = p_player.new_counter(
                        display=strings_damage_hook['health game'])

                    if self.map_data['ALLOW_SELFDAMAGE']:
                        counter2.hook_hurt = get_hook(
                            'SW', next_hook=hook_min_damage)

                    else:
                        warn(PossibleDeadEndWarning(
                            "Self-damage is disabled and it's a non-ff game! "
                            "Players may have problems dying. "
                            "Tell map creator about this problem."))

                        counter2.hook_hurt = get_hook(
                            '', next_hook=hook_min_damage)

                    counter2.health = self.map_data['INITIAL_HEALTH']

                    self._counters[player.userid].append(counter1)
                    self._counters[player.userid].append(counter2)

                elif player.team == GUARDS_TEAM:
                    counter = p_player.new_counter()
                    if self.map_data['ALLOW_REBELLING']:
                        counter.hook_hurt = get_hook('SWP')
                        counter.display = strings_damage_hook[
                            'health against_prisoners']

                    else:
                        counter.hook_hurt = get_hook('SW')
                        counter.display = strings_damage_hook['health general']

                    self._counters[player.userid].append(counter)

                p_player.set_protected()

            if not self.map_data['ALLOW_REBELLING']:
                def rebel_filter(player):
                    return player not in self._players_all

                self._rebel_filter = rebel_filter
                register_rebel_filter(rebel_filter)

        @stage('undo-survival-equip-damage-hooks')
        def stage_undo_survival_equip_damage_hooks(self):
            for player in main_player_manager.values():
                if player.dead:
                    continue

                if player.userid not in self._counters:
                    continue

                p_player = protected_player_manager[player.index]
                for counter in self._counters[player.userid]:
                    p_player.delete_counter(counter)

                p_player.unset_protected()

            if self._rebel_filter is not None:
                unregister_rebel_filter(self._rebel_filter)

        @stage('survival-fall-protection')
        def stage_survival_fall_protection(self):
            for player in self._players:
                falldmg_protect(player, self.map_data)

            if not self.leader.dead and self.leader not in self._players:
                falldmg_protect(self.leader, self.map_data)

        @game_event_handler('survival-player-death', 'player_death')
        def event_survival_player_death(self, game_event):
            player = main_player_manager.get_by_userid(
                game_event.get_int('userid'))

            if player not in self._players_all:
                return

            saved_player = saved_player_manager[player.index]
            saved_player.strip()

    return SurvivalBase


class SurvivalTeamBased(build_survival_base(MapGameTeamBased)):
    caption = strings_module['title teambased_standard']
    module = 'survival_teambased_standard'

    stage_groups = {
        'mapgame-prepare': [
            "mapgame-cancel-falldmg-protection",
            "mapgame-equip-noblock",
            "survival-equip-damage-hooks",
            "mapgame-teambased-split-teams",
            "mapgame-teleport-players",
            "mapgame-fire-mapdata-prepare-outputs",
            "mapgame-prepare-entry",
        ],
        'survival-end-win-single-team': [
            'survival-end-win-single-team',
        ],
        'survival-end-win-multiple-teams': [
            'survival-end-win-multiple-teams',
        ],
    }

    def __init__(self, leader_player, players, **kwargs):
        super().__init__(leader_player, players, **kwargs)

        self._score = {
            'team1': 0,
            'team2': 0,
            'team3': 0,
            'team4': 0,
        }

    @stage('mapgame-entry')
    def stage_mapgame_entry(self):
        self._score['team1'] = len(self._team1)
        self._score['team2'] = len(self._team2)
        self._score['team3'] = len(self._team3)
        self._score['team4'] = len(self._team4)

    @stage('survival-end-win-single-team')
    def stage_survival_end_win_single_team(self):
        for team in (self._team1, self._team2, self._team3, self._team4):
            if team:
                self.set_stage_group(
                    'game-end-win-team{}'.format(team.team_num))

                break

    @stage('survival-end-win-multiple-teams')
    def stage_survival_end_win_multiple_teams(self):
        max_team = None
        for team in (self._team1,
                     self._team2,
                     self._team3,
                     self._team4)[:self.num_teams]:

            if max_team is None or len(team) > len(max_team):
                max_team = team

        self.set_stage_group('game-end-win-team{}'.format(max_team.team_num))

    @game_event_handler('jailgame-player-death', 'player_death')
    def event_jailgame_player_death(self, game_event):
        player = main_player_manager.get_by_userid(
            game_event.get_int('userid'))

        if self.leader == player:
            self.set_stage_group('abort-leader-dead')
            return

        if player not in self._players:
            return

        team = self.get_player_team(player)
        team.remove(player)

        self._players.remove(player)

        self._score[team.team_num_str] -= 1

        if self._score[team.team_num_str] <= 0:
            if self.num_teams == 2:
                self.set_stage_group('survival-end-win-single-team')
            else:
                self.set_stage_group('survival-end-win-multiple-teams')

            return

        broadcast(strings_module['player_out'].tokenize(
            player=player.name,
            team=strings_common['team{}'.format(team.team_num)],
            color=config_manager_common['team{}_color'.format(team.team_num)],
        ))

add_available_game(SurvivalTeamBased)


class SurvivalPlayerBased(build_survival_base(MapGame)):
    caption = strings_module['title playerbased_standard']
    module = 'survival_playerbased_standard'

    stage_groups = {
        'mapgame-prepare': [
            "mapgame-cancel-falldmg-protection",
            "mapgame-equip-noblock",
            "survival-equip-damage-hooks",
            "mapgame-teleport-players",
            "mapgame-fire-mapdata-prepare-outputs",
            "mapgame-prepare-entry",
        ],
        'survival-end-players-alive': [
            'survival-end-players-alive',
        ],
    }

    def __init__(self, leader_player, players, **kwargs):
        super().__init__(leader_player, players, **kwargs)

        self._score = 0
        self._end_score = 0

    @stage('mapgame-entry')
    def stage_mapgame_entry(self):
        self._score = len(self._players)

        map_percentage = self.map_data['PLAYERS_DEAD_PERCENTAGE']
        config_percentage = config_manager['playerbased_percentage']

        percentage = (
            map_percentage if map_percentage > -1 else config_percentage)

        self._end_score = self._score * (100 - percentage) / 100

    @stage('survival-end-players-alive')
    def stage_survival_end_players_alive(self):
        self._results['winners'] = self._players[:]
        self.set_stage_group('game-end-players-won')

    @push(None, 'end_game')
    def push_end_game(self, args):
        self.set_stage_group('survival-end-players-alive')

    @game_event_handler('jailgame-player-death', 'player_death')
    def event_jailgame_player_death(self, game_event):
        player = main_player_manager.get_by_userid(
            game_event.get_int('userid'))

        if self.leader == player:
            self.set_stage_group('abort-leader-dead')
            return

        if player not in self._players:
            return

        self._players.remove(player)
        helper_set_loser(player, effects=False)

        self._score -= 1
        if self._score <= self._end_score:
            self.set_stage_group('survival-end-players-alive')

        else:
            broadcast(strings_module['player_out_playerbased'].tokenize(
                player=player.name,
            ))

add_available_game(SurvivalPlayerBased)


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

    return SurvivalFriendlyFireBase


class SurvivalTeamBasedFriendlyFire(
        build_survival_friendlyfire_base(SurvivalTeamBased)):

    caption = strings_module['title teambased_friendlyfire']
    module = 'survival_teambased_friendlyfire'

    @stage('survival-equip-damage-hooks')
    def stage_survival_equip_damage_hooks(self):
        def hook_min_damage(counter, info):
            min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']
            return info.damage >= min_damage

        def hook_enemy_p(counter, info):
            """
            Damage done by:
               - prisoners from the other teams
            """
            victim = counter.owner.player

            if info.attacker == victim.index or is_world(info.attacker):
                return False

            attacker = main_player_manager[info.attacker]

            if attacker in self._players and (
                victim in self._team1 and attacker not in self._team1 or
                victim in self._team2 and attacker not in self._team2 or
                victim in self._team3 and attacker not in self._team3 or
                victim in self._team4 and attacker not in self._team4
            ):

                show_damage(attacker, info.damage)

                return hook_min_damage(counter, info)

            return False

        def hook_sw_enemy_p(counter, info):
            """
            Damage done by:
               - self
               - world
               - prisoners from the other teams
            """
            victim = counter.owner.player

            if info.attacker == victim.index or is_world(info.attacker):
                return hook_min_damage(counter, info)

            attacker = main_player_manager.get(info.attacker)

            if attacker in self._players and (
                victim in self._team1 and attacker not in self._team1 or
                victim in self._team2 and attacker not in self._team2 or
                victim in self._team3 and attacker not in self._team3 or
                victim in self._team4 and attacker not in self._team4
            ):

                show_damage(attacker, info.damage)

                return hook_min_damage(counter, info)

            return False

        def hook_game_p(counter, info):
            """
            Damage done by:
               - prisoners from the other teams
               - prisoners from the same team
            """
            victim = counter.owner.player

            if info.attacker == victim.index or is_world(info.attacker):
                return False

            attacker = main_player_manager[info.attacker]

            if attacker in self._players:
                show_damage(attacker, info.damage)

                return hook_min_damage(counter, info)

            return False

        def hook_sw_game_p(counter, info):
            """
            Damage done by:
               - self
               - world
               - prisoners from the other teams
               - prisoners from the same team
            """
            victim = counter.owner.player

            if info.attacker == victim.index or is_world(info.attacker):
                return hook_min_damage(counter, info)

            attacker = main_player_manager.get(info.attacker)

            if attacker in self._players:
                show_damage(attacker, info.damage)

                return hook_min_damage(counter, info.damage)

            return False

        for player in main_player_manager.values():
            if player.dead:
                continue

            p_player = protected_player_manager[player.index]
            self._counters[player.userid] = []
            if player in self._players:
                counter1 = p_player.new_counter(
                    display=strings_damage_hook['health against_guards'])

                counter1.hook_hurt = get_hook('G')

                counter2 = p_player.new_counter(
                    display=strings_damage_hook['health game'])

                if self.map_data['RESTORE_HEALTH_ON_FF']:
                    if self.map_data['ALLOW_SELFDAMAGE']:
                        counter2.hook_hurt = hook_sw_enemy_p
                    else:
                        counter2.hook_hurt = hook_enemy_p

                else:
                    if self.map_data['ALLOW_SELFDAMAGE']:
                        counter2.hook_hurt = hook_sw_game_p
                    else:
                        counter2.hook_hurt = hook_game_p

                counter2.health = self.map_data['INITIAL_HEALTH']

                self._counters[player.userid].append(counter1)
                self._counters[player.userid].append(counter2)

            elif player.team == GUARDS_TEAM:
                counter = p_player.new_counter()
                if self.map_data['ALLOW_REBELLING']:
                    counter.hook_hurt = get_hook('SWP')
                    counter.display = strings_damage_hook[
                        'health against_prisoners']

                else:
                    counter.hook_hurt = get_hook('SW')
                    counter.display = strings_damage_hook['health general']

                self._counters[player.userid].append(counter)

            p_player.set_protected()

        if not self.map_data['ALLOW_REBELLING']:
            def rebel_filter(player):
                return player not in self._players_all

            self._rebel_filter = rebel_filter
            register_rebel_filter(rebel_filter)

add_available_game(SurvivalTeamBasedFriendlyFire)


class SurvivalPlayerBasedFriendlyFire(
        build_survival_friendlyfire_base(SurvivalPlayerBased)):

    caption = strings_module['title playerbased_friendlyfire']
    module = 'survival_playerbased_friendlyfire'

    @stage('survival-equip-damage-hooks')
    def stage_survival_equip_damage_hooks(self):
        def hook_min_damage(counter, info):
            min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']
            return info.damage >= min_damage

        def hook_enemy_p(counter, info):
            victim = counter.owner.player

            if info.attacker == victim.index or is_world(info.attacker):
                return False

            attacker = main_player_manager[info.attacker]

            if attacker in self._players:
                show_damage(attacker, info.damage)

                return hook_min_damage(counter, info)

            return False

        def hook_sw_enemy_p(counter, info):
            victim = counter.owner.player

            if info.attacker == victim.index or is_world(info.attacker):
                return hook_min_damage(counter, info)

            attacker = main_player_manager[info.attacker]

            if attacker in self._players:
                show_damage(attacker, info.damage)

                return hook_min_damage(counter, info)

            return False

        for player in main_player_manager.values():
            if player.dead:
                continue

            p_player = protected_player_manager[player.index]
            self._counters[player.userid] = []
            if player in self._players:
                counter1 = p_player.new_counter(
                    display=strings_damage_hook['health against_guards'])

                counter1.hook_hurt = get_hook('G')

                counter2 = p_player.new_counter(
                    display=strings_damage_hook['health game'])

                if self.map_data['ALLOW_SELFDAMAGE']:
                    counter2.hook_hurt = hook_sw_enemy_p

                else:
                    counter2.hook_hurt = hook_enemy_p

                counter2.health = self.map_data['INITIAL_HEALTH']

                self._counters[player.userid].append(counter1)
                self._counters[player.userid].append(counter2)

            elif player.team == GUARDS_TEAM:
                counter = p_player.new_counter()
                if self.map_data['ALLOW_REBELLING']:
                    counter.hook_hurt = get_hook('SWP')
                    counter.display = strings_damage_hook[
                        'health against_prisoners']

                else:
                    counter.hook_hurt = get_hook('SW')
                    counter.display = strings_damage_hook['health general']

                self._counters[player.userid].append(counter)

            p_player.set_protected()

        if not self.map_data['ALLOW_REBELLING']:
            def rebel_filter(player):
                return player not in self._players_all

            self._rebel_filter = rebel_filter
            register_rebel_filter(rebel_filter)

    @stage('undo-survival-equip-damage-hooks')
    def stage_undo_survival_equip_damage_hooks(self):
        for player in main_player_manager.values():
            if player.dead:
                continue

            if player.userid not in self._counters:
                continue

            p_player = protected_player_manager[player.index]
            for counter in self._counters[player.userid]:
                p_player.delete_counter(counter)

            p_player.unset_protected()

        if self._rebel_filter is not None:
            unregister_rebel_filter(self._rebel_filter)

add_available_game(SurvivalPlayerBasedFriendlyFire)
