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

from random import shuffle

from ....arcjail import InternalEvent

from ...jail_map import teleport_player, get_games

from ...player_colors import cancel_color_request, make_color_request

from ...players import broadcast, main_player_manager, tell

from ...rebels import get_rebels

from ...skins import cancel_model_request, make_model_request

from .. import (
    config_manager, game_event_handler, game_internal_event_handler,
    helper_set_winner, helper_set_loser, MIN_PLAYERS_IN_GAME, stage,
    strings_module)

from .map_game import MapGame


COLOR_PRIORITY = 2
SKIN_PRIORITY = 2
TEAM_NUM_MIN = 2
TEAM_NUM_MAX = 4


class MapGameTeamBased(MapGame):
    class PlayerTeam(list):
        def __init__(self, team_num, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.team_num = team_num

        @property
        def team_num_str(self):
            return 'team{}'.format(self.team_num)

    caption = '$games_base title_mapgame_teambased'
    num_teams = 2

    stage_groups = {
        'mapgame-prepare': [
            "mapgame-cancel-falldmg-protection",
            "mapgame-equip-noblock",
            "mapgame-teambased-split-teams",
            "mapgame-teleport-players",
            "mapgame-fire-mapdata-prepare-outputs",
            "mapgame-prepare-entry",
        ],
        'mapgame-teambased-split-teams': [
            "mapgame-teambased-split-teams",
        ],
        'mapgame-teambased-split-teams2': [
            "mapgame-teambased-split-teams2",
        ],
        'mapgame-teambased-split-teams3': [
            "mapgame-teambased-split-teams3",
        ],
        'mapgame-teambased-split-teams4': [
            "mapgame-teambased-split-teams4",
        ],
        'mapgame-teleport-players2': ["mapgame-teleport-players2", ],
        'mapgame-teleport-players3': ["mapgame-teleport-players3", ],
        'mapgame-teleport-players4': ["mapgame-teleport-players4", ],
        'game-end-draw': ['game-end-draw', ],
        'game-end-win-team1': ['game-end-win-team1', ],
        'game-end-win-team2': ['game-end-win-team2', ],
        'game-end-win-team3': ['game-end-win-team3', ],
        'game-end-win-team4': ['game-end-win-team4', ],
    }

    def __init__(self, leader_player, players, **kwargs):
        super().__init__(leader_player, players, **kwargs)

        assert TEAM_NUM_MIN <= self.num_teams <= TEAM_NUM_MAX

        self._starting_player_number = len(players)

        self._team1 = self.PlayerTeam(1)
        self._team2 = self.PlayerTeam(2)
        self._team3 = self.PlayerTeam(3)
        self._team4 = self.PlayerTeam(4)

    @property
    def team1(self):
        return tuple(self._team1)

    @property
    def team2(self):
        return tuple(self._team2)

    @property
    def team3(self):
        return tuple(self._team3)

    @property
    def team4(self):
        return tuple(self._team4)

    def get_player_team(self, player):
        if player in self._team1:
            return self._team1
        if player in self._team2:
            return self._team2
        if player in self._team3:
            return self._team3
        if player in self._team4:
            return self._team4

        raise IndexError("Player does not belong to this game")

    @stage('mapgame-teleport-players')
    def stage_mapgame_teleport_players(self):
        self.insert_stage_group(
            "mapgame-teleport-players{}".format(self.num_teams))

    @stage('mapgame-teleport-players2')
    def stage_mapgame_teleport_players2(self):
        spawnpoints = list(self.map_data.get_spawnpoints('team1'))
        shuffle(spawnpoints)

        for player in self._team1:
            teleport_player(player, spawnpoints.pop())

        spawnpoints = list(self.map_data.get_spawnpoints('team2'))
        shuffle(spawnpoints)

        for player in self._team2:
            teleport_player(player, spawnpoints.pop())

        teleport_player(self.leader, self.map_data.get_spawnpoints('team0')[0])

    @stage('mapgame-teleport-players3')
    def stage_mapgame_teleport_players3(self):
        spawnpoints = list(self.map_data.get_spawnpoints('team1'))
        shuffle(spawnpoints)

        for player in self._team1:
            teleport_player(player, spawnpoints.pop())

        spawnpoints = list(self.map_data.get_spawnpoints('team2'))
        shuffle(spawnpoints)

        for player in self._team2:
            teleport_player(player, spawnpoints.pop())

        spawnpoints = list(self.map_data.get_spawnpoints('team3'))
        shuffle(spawnpoints)

        for player in self._team3:
            teleport_player(player, spawnpoints.pop())

        teleport_player(self.leader, self.map_data.get_spawnpoints('team0')[0])

    @stage('mapgame-teleport-players4')
    def stage_mapgame_teleport_players4(self):
        spawnpoints = list(self.map_data.get_spawnpoints('team1'))
        shuffle(spawnpoints)

        for player in self._team1:
            teleport_player(player, spawnpoints.pop())

        spawnpoints = list(self.map_data.get_spawnpoints('team2'))
        shuffle(spawnpoints)

        for player in self._team2:
            teleport_player(player, spawnpoints.pop())

        spawnpoints = list(self.map_data.get_spawnpoints('team3'))
        shuffle(spawnpoints)

        for player in self._team3:
            teleport_player(player, spawnpoints.pop())

        spawnpoints = list(self.map_data.get_spawnpoints('team4'))
        shuffle(spawnpoints)

        for player in self._team4:
            teleport_player(player, spawnpoints.pop())

        teleport_player(self.leader, self.map_data.get_spawnpoints('team0')[0])

    @stage('mapgame-teambased-split-teams')
    def stage_mapgame_teambased_split_teams(self):
        self.insert_stage_group(
            "mapgame-teambased-split-teams{}".format(self.num_teams))

    @stage('undo-mapgame-teambased-split-teams')
    def stage_undo_mapgame_teambased_split_teams(self):
        for player in self._players:
            cancel_model_request(player, 'games-teambased')
            cancel_color_request(player, 'games-teambased')

    @stage('mapgame-teambased-split-teams2')
    def stage_mapgame_teambased_split_teams_2(self):
        self._team1 = self.PlayerTeam(1)
        self._team2 = self.PlayerTeam(2)

        players = self._players[:]
        shuffle(players)

        broadcast(strings_module['players_two_teams'].tokenize(
            color1=config_manager['team1_color'],
            color2=config_manager['team2_color'],
            team1=strings_module['team1'],
            team2=strings_module['team2'],
        ))

        while players:
            p1, p2 = players.pop(), players.pop()

            tell(p1, strings_module['your_team'].tokenize(
                color=config_manager['team1_color'],
                team=strings_module['team1']
            ))
            tell(p2, strings_module['your_team'].tokenize(
                color=config_manager['team2_color'],
                team=strings_module['team2']
            ))

            if config_manager['prefer_model_over_color']:
                make_model_request(
                    p1, SKIN_PRIORITY, 'games-teambased',
                    config_manager['team1_model']
                )
                make_model_request(
                    p2, SKIN_PRIORITY, 'games-teambased',
                    config_manager['team2_model']
                )
            else:
                make_color_request(
                    p1, COLOR_PRIORITY, 'games-teambased',
                    config_manager['team1_color']
                )
                make_color_request(
                    p2, COLOR_PRIORITY, 'games-teambased',
                    config_manager['team2_color']
                )

            self._team1.append(p1)
            self._team2.append(p2)

    @stage('mapgame-teambased-split-teams3')
    def stage_mapgame_teambased_split_teams_3(self):
        raise NotImplementedError

    @stage('mapgame-teambased-split-teams4')
    def stage_mapgame_teambased_split_teams_4(self):
        raise NotImplementedError

    @stage('game-end-draw')
    def stage_game_end_draw(self):
        broadcast(strings_module['draw'])
        self.set_stage_group('destroy')

    @stage('game-end-win-team1')
    def stage_game_end_win_team1(self):
        InternalEvent.fire(
            'jail_game_map_game_team_based_winners',
            winners=self._team1,
            num_teams=self.num_teams,
            starting_player_number=self._starting_player_number,
            team_num=1,
        )

        broadcast(strings_module['win_team'].tokenize(
            color=config_manager['team1_color'],
            team=strings_module['team1']
        ))
        for player in self._team1:
            helper_set_winner(player)

        for player in (self._team2 + self._team3 + self._team4):
            helper_set_loser(player)

        self.set_stage_group('destroy')

    @stage('game-end-win-team2')
    def stage_game_end_win_team2(self):
        InternalEvent.fire(
            'jail_game_map_game_team_based_winners',
            winners=self._team2,
            num_teams=self.num_teams,
            starting_player_number=self._starting_player_number,
            team_num=2,
        )

        broadcast(strings_module['win_team'].tokenize(
            color=config_manager['team2_color'],
            team=strings_module['team2']
        ))
        for player in self._team2:
            helper_set_winner(player)

        for player in (self._team1 + self._team3 + self._team4):
            helper_set_loser(player)

        self.set_stage_group('destroy')

    @stage('game-end-win-team3')
    def stage_game_end_win_team3(self):
        InternalEvent.fire(
            'jail_game_map_game_team_based_winners',
            winners=self._team3,
            num_teams=self.num_teams,
            starting_player_number=self._starting_player_number,
            team_num=3,
        )

        broadcast(strings_module['win_team'].tokenize(
            color=config_manager['team3_color'],
            team=strings_module['team3']
        ))
        for player in self._team3:
            helper_set_winner(player)

        for player in (self._team1 + self._team2 + self._team4):
            helper_set_loser(player)

        self.set_stage_group('destroy')

    @stage('game-end-win-team4')
    def stage_game_end_win_team4(self):
        InternalEvent.fire(
            'jail_game_map_game_team_based_winners',
            winners=self._team4,
            num_teams=self.num_teams,
            starting_player_number=self._starting_player_number,
            team_num=4,
        )

        broadcast(strings_module['win_team'].tokenize(
            color=config_manager['team4_color'],
            team=strings_module['team4']
        ))
        for player in self._team4:
            helper_set_winner(player)

        for player in (self._team1 + self._team2 + self._team3):
            helper_set_loser(player)

        self.set_stage_group('destroy')

    @game_event_handler('jailgame-player-death', 'player_death')
    def event_jailgame_player_death(self, game_event):
        player = main_player_manager.get_by_userid(
            game_event.get_int('userid'))

        if self.leader == player:
            self.set_stage_group('abort-leader-dead')

        elif player in self._players:
            self._players.remove(player)
            self.get_player_team(player).remove(player)

            if not all((self._team1,
                        self._team2,
                        self._team3,
                        self._team4)[:self.num_teams]):

                self.set_stage_group('abort-not-enough-players')

            elif len(self._players) < MIN_PLAYERS_IN_GAME:
                self.set_stage_group('abort-not-enough-players')

    @game_internal_event_handler(
        'jailgame-main-player-deleted', 'main_player_deleted')
    def event_jailgame_main_player_deleted(self, event_var):
        player = event_var['main_player']

        if self.leader == player:
            self.set_stage_group('abort-leader-disconnect')

        elif player in self._players:
            self._players.remove(player)

            for team_list in (self._team1,
                              self._team2,
                              self._team3,
                              self._team4):

                if player in team_list:
                    team_list.remove(player)

            if not (self._team1 and
                    self._team2 and
                    self._team3 and
                    self._team4):

                self.set_stage_group('abort-not-enough-players')

            elif len(self._players) < MIN_PLAYERS_IN_GAME:
                self.set_stage_group('abort-not-enough-players')

    @classmethod
    def get_available_launchers(cls, leader_player, players):
        if get_rebels():
            return ()

        len_players = len(players)
        if len_players < config_manager['min_players_number']:
            return ()

        if len_players % cls.num_teams:
            return ()

        result = []
        teams = ['team1', 'team2', 'team3', 'team4'][:cls.num_teams]
        for map_data in get_games(cls.module):
            p_min = map_data['MIN_PLAYERS']
            p_max = map_data['MAX_PLAYERS']

            if not len(map_data.get_spawnpoints('team0')):
                continue

            for team_num in teams:
                if (len(map_data.get_spawnpoints(team_num)) <
                        len_players // cls.num_teams):

                    break

            else:
                if (len_players >= p_min and
                        (p_max == -1 or len_players <= p_max)):

                    result.append(cls.GameLauncher(cls, map_data))

        return result
