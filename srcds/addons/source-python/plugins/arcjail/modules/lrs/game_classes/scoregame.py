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

from ....resource.strings import build_module_strings

from ...damage_hook import get_hook, protected_player_manager

from ...games.scoregame import (
    get_goal_sound, config_manager as config_manager_games)

from ...games import play_flawless_effects

from ...players import broadcast

from ..base_classes.map_game_team_based import MapGameTeamBased

from .. import add_available_game, push, stage


strings_module = build_module_strings('lrs/scoregame')


class ScoreGameBase(MapGameTeamBased):
    stage_groups = {
        'scoregame-new-score2': ['scoregame-new-score2', ],
        'scoregame-check-team-scores': ['scoregame-check-team-scores', ],
    }

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self.score = {
            self.prisoner.index: 0,
            self.guard.index: 0,
        }
        self.win_score = (self.map_data['MAX_SCORE'] if
                          self.map_data['MAX_SCORE'] > 0 else
                          config_manager_games['win_score'])

    @stage('scoregame-new-score2')
    def stage_scoregame_new_score2(self):
        broadcast(strings_module['new_score2'].tokenize(
            player1=self.prisoner.name,
            score1=self.score[self.prisoner.index],
            player2=self.guard.name,
            score2=self.score[self.guard.index]
        ))

        self.set_stage_group('scoregame-check-team-scores')

    @stage('scoregame-check-team-scores')
    def stage_scoregame_check_team_scores(self):
        if self.score[self.prisoner.index] == self.win_score:
            winner, loser = self.prisoner, self.guard

        elif self.score[self.guard.index] == self.win_score:
            winner, loser = self.guard, self.prisoner

        else:
            return

        self._results['winner'] = winner
        self._results['loser'] = loser

        if self.score[loser.index] == 0:
            play_flawless_effects(self._players)

        self.set_stage_group('win')

    @push(None, 'end_game')
    def push_end_game(self, args):
        if self.score[self.prisoner.index] > self.score[self.guard.index]:
            winner, loser = self.prisoner, self.guard
        elif self.score[self.prisoner.index] < self.score[self.guard.index]:
            winner, loser = self.guard, self.prisoner
        else:
            self.set_stage_group('draw')
            return

        self._results['winner'] = winner
        self._results['loser'] = loser

        if self.score[loser.index] == 0:
            play_flawless_effects(self._players)

        self.set_stage_group('win')

    @push(None, 'scoregames_score_point')
    def push_scoregames_score_point(self, args):
        try:
            team_num = int(args[0])
            assert 1 <= team_num <= 2
        except (IndexError, ValueError, AssertionError):
            return

        if team_num == 1:
            self.score[self.prisoner.index] += 1
        else:
            self.score[self.guard.index] += 1

        InternalEvent.fire('jail_stop_accepting_bets', instance=self)

        goal_sound = get_goal_sound(self.map_data['GOAL_SOUND'])
        if goal_sound is not None:
            goal_sound.play(self.prisoner.index, self.guard.index)

        self.set_stage_group('scoregame-new-score2')


class ScoreGameStandard(ScoreGameBase):
    caption = strings_module['title standard']
    module = 'scoregame_standard'

add_available_game(ScoreGameStandard)


class ScoreGameAllowDeaths(ScoreGameBase):
    caption = strings_module['title allowdeaths']
    module = 'scoregame_allowdeaths'

add_available_game(ScoreGameAllowDeaths)


class ScoreGameNoPropKill(ScoreGameBase):
    caption = strings_module['title nopropkill']
    module = 'scoregame_nopropkill'

    stage_groups = {
        'mapgame-prepare': [
            "mapgame-cancel-falldmg-protection",
            "mapgame-equip-noblock",
            "scoregame-equip-damage-hooks",
            "mapgame-swap-guard",
            "mapgame-teleport-players",
            "mapgame-fire-mapdata-prepare-outputs",
            "mapgame-prepare-entry",
        ],
    }

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self._counters = {}

    @stage('scoregame-equip-damage-hooks')
    def stage_scoregame_equip_damage_hooks(self):
        for player in self._players:
            p_player = protected_player_manager[player.index]

            self._counters[player.index] = p_player.new_counter()
            self._counters[player.index].hook_hurt = get_hook('')

            p_player.set_protected()

    @stage('undo-scoregame-equip-damage-hooks')
    def stage_undo_scoregame_equip_damage_hooks(self):
        for player in self._players_all:
            p_player = protected_player_manager[player.index]
            p_player.delete_counter(self._counters[player.index])
            p_player.unset_protected()

add_available_game(ScoreGameNoPropKill)
