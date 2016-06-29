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

from controlled_cvars.handlers import (
    bool_handler, int_handler, sound_nullable_handler)

from ....arcjail import load_downloadables

from ....resource.strings import build_module_strings

from ...damage_hook import get_hook, protected_player_manager

from ...players import broadcast

from ... import build_module_config

from ..base_classes.map_game_team_based import MapGameTeamBased
from ..base_classes.player_preserving import PlayerPreserving

from .. import (
    add_available_game, config_manager as config_manager_common,
    play_flawless_effects, push, stage, strings_module as strings_common)


strings_module = build_module_strings('games/scoregame')
config_manager = build_module_config('games/scoregame')

config_manager.controlled_cvar(
    bool_handler,
    "enabled",
    default=1,
    description="Enable/Disable Score Games"
)
config_manager.controlled_cvar(
    int_handler,
    "win_score",
    default=5,
    description="Goals that team must score to win"
)
config_manager.controlled_cvar(
    sound_nullable_handler,
    "goal_sound1",
    default="arcjail/goal1.mp3",
    description="Goal Sound #1 (Referee whistle)"
)
config_manager.controlled_cvar(
    sound_nullable_handler,
    "goal_sound2",
    default="arcjail/hitsound.wav",
    description="Goal Sound #1 (Click)"
)
config_manager.controlled_cvar(
    sound_nullable_handler,
    "goal_sound3",
    default="buttons/bell1.wav",
    description="Goal Sound #3 (Bell)"
)

_downloadables_sounds = load_downloadables('games-scoregames-sounds.res')


def get_goal_sound(sound_num):
    if sound_num == 1:
        return config_manager['goal_sound1']
    if sound_num == 2:
        return config_manager['goal_sound2']
    if sound_num == 3:
        return config_manager['goal_sound3']
    return None


class ScoreGameBase(MapGameTeamBased):
    stage_groups = {
        'scoregame-new-score2': ['scoregame-new-score2', ],
        'scoregame-new-score3': ['scoregame-new-score3', ],
        'scoregame-new-score4': ['scoregame-new-score4', ],
        'scoregame-check-team-scores': ['scoregame-check-team-scores', ],
    }

    def __init__(self, leader_player, players, **kwargs):
        super().__init__(leader_player, players, **kwargs)

        self.score = {
            'team1': 0,
            'team2': 0,
            'team3': 0,
            'team4': 0,
        }
        self.win_score = (self.map_data['MAX_SCORE'] if
                          self.map_data['MAX_SCORE'] > 0 else
                          config_manager['win_score'])

    @stage('scoregame-new-score2')
    def stage_scoregame_new_score2(self):
        broadcast(strings_module['new_score2'].tokenize(
            color1=config_manager_common['team1_color'],
            team1=strings_common['team1'],
            score1=self.score['team1'],
            color2=config_manager_common['team2_color'],
            team2=strings_common['team2'],
            score2=self.score['team2']
        ))

        self.set_stage_group('scoregame-check-team-scores')

    @stage('scoregame-new-score3')
    def stage_scoregame_new_score3(self):
        broadcast(strings_module['new_score2'].tokenize(
            color1=config_manager_common['team1_color'],
            team1=strings_common['team1'],
            score1=self.score['team1'],
            color2=config_manager_common['team2_color'],
            team2=strings_common['team2'],
            score2=self.score['team2'],
            color3=config_manager_common['team3_color'],
            team3=strings_common['team3'],
            score3=self.score['team3']
        ))

        self.set_stage_group('scoregame-check-team-scores')

    @stage('scoregame-new-score4')
    def stage_scoregame_new_score4(self):
        broadcast(strings_module['new_score2'].tokenize(
            color1=config_manager_common['team1_color'],
            team1=strings_common['team1'],
            score1=self.score['team1'],
            color2=config_manager_common['team2_color'],
            team2=strings_common['team2'],
            score2=self.score['team2'],
            color3=config_manager_common['team3_color'],
            team3=strings_common['team3'],
            score3=self.score['team3'],
            color4=config_manager_common['team4_color'],
            team4=strings_common['team4'],
            score4=self.score['team4'],
        ))

        self.set_stage_group('scoregame-check-team-scores')

    @stage('scoregame-check-team-scores')
    def stage_scoregame_check_team_scores(self):
        if self.score['team1'] == self.win_score:
            if self.score['team2'] == 0:
                play_flawless_effects(self._players)

            self.set_stage_group('game-end-win-team1')

        elif self.score['team2'] == self.win_score:
            if self.score['team1'] == 0:
                play_flawless_effects(self._players)

            self.set_stage_group('game-end-win-team2')

        elif self.score['team3'] == self.win_score:
            self.set_stage_group('game-end-win-team3')

        elif self.score['team4'] == self.win_score:
            self.set_stage_group('game-end-win-team4')

    @push(None, 'scoregames_score_point')
    def push_scoregames_score_point(self, args):
        try:
            team_num = int(args[0])
            assert 1 <= team_num <= self.num_teams
        except (IndexError, ValueError, AssertionError):
            return

        goal_sound = get_goal_sound(self.map_data['GOAL_SOUND'])
        if goal_sound is not None:
            indexes = list([player.index for player in self._players])
            indexes.append(self.leader.index)
            goal_sound.play(*indexes)

        self.score['team{}'.format(team_num)] += 1
        self.set_stage_group(
            'scoregame-new-score{}'.format(self.num_teams))


class ScoreGameStandard(ScoreGameBase, PlayerPreserving):
    caption = strings_module['title standard']
    module = 'scoregame_standard'

add_available_game(ScoreGameStandard)


class ScoreGameNoPropKill(ScoreGameBase, PlayerPreserving):
    caption = strings_module['title nopropkill']
    module = 'scoregame_nopropkill'

    stage_groups = {
        'mapgame-prepare': [
            "mapgame-cancel-falldmg-protection",
            "mapgame-equip-noblock",
            "scoregame-equip-damage-hooks",
            "mapgame-teambased-split-teams",
            "mapgame-teleport-players",
            "mapgame-fire-mapdata-prepare-outputs",
            "mapgame-prepare-entry",
        ],
    }

    def __init__(self, leader_player, players, **kwargs):
        super().__init__(leader_player, players, **kwargs)

        self._counters = {}

    @stage('scoregame-equip-damage-hooks')
    def stage_scoregame_equip_damage_hooks(self):
        for player in self._players:
            p_player = protected_player_manager[player.index]

            self._counters[player.index] = p_player.new_counter()
            self._counters[player.index].hook_hurt = get_hook('G')

            p_player.set_protected()

    @stage('undo-scoregame-equip-damage-hooks')
    def stage_undo_scoregame_equip_damage_hooks(self):
        for player in self._players_all:
            p_player = protected_player_manager[player.index]
            p_player.delete_counter(self._counters[player.index])
            p_player.unset_protected()


add_available_game(ScoreGameNoPropKill)


class ScoreGameAllowDeaths(ScoreGameBase):
    caption = strings_module['title allowdeaths']
    module = 'scoregame_allowdeaths'

add_available_game(ScoreGameAllowDeaths)
