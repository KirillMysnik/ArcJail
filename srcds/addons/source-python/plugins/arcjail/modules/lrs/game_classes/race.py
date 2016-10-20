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

from random import choice

from listeners.tick import Delay
from players.teams import teams_by_name

from ...games.game_classes.race import (
    MAX_RECOLLECT_ITERATIONS, RECOLLECT_PLAYERS_INTERVAL,
    strings_module as strings_games)
from ...jail_map import get_players_in_area

from .. import add_available_game, push, stage
from ..base_classes.map_game import MapGame


class RaceBase(MapGame):
    stage_groups = {
        'destroy': [
            "prepare-cancel-delays",
            "cancel-recollect-delay",
            "unsend-popups",
            "destroy",
        ],
    }

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self._recollect_delay = None

    @staticmethod
    def _filter_func(player):
        if player.dead:
            return False

        if player.team != teams_by_name['t']:
            return False

        return True

    @stage('cancel-recollect-delay')
    def stage_cancel_recollect_delay(self):
        if self._recollect_delay is not None:
            if self._recollect_delay.running:
                self._recollect_delay.cancel()

            self._recollect_delay = None

    @push(None, 'end_game')
    def push_end_game(self, args):
        self.set_stage_group('draw')


class RaceSingleWinnerStandard(RaceBase):
    caption = strings_games['title single_winner standard']
    module = 'race_single_winner_standard'

    def collect_winners(self, iteration=1):
        winners = set()
        for area_name in self.map_data.get_areas('winners'):
            winners.update(get_players_in_area(area_name))

        winners = list(filter(self._filter_func, winners))

        if not winners:
            if iteration == MAX_RECOLLECT_ITERATIONS:
                self.set_stage_group('draw')

            else:
                self._recollect_delay = Delay(
                    RECOLLECT_PLAYERS_INTERVAL,
                    self.collect_winners,
                    iteration + 1,
                )

        else:
            self._results['winner'] = winner = choice(tuple(winners))

            if winner == self.prisoner:
                self._results['loser'] = self.guard
            else:
                self._results['loser'] = self.prisoner

            self.set_stage_group('win')

    @push(None, 'race_player_won')
    def push_race_player_won(self, args):
        if self._recollect_delay is not None:
            return

        self.collect_winners()

add_available_game(RaceSingleWinnerStandard)


class RaceSingleLoserStandard(RaceBase):
    caption = strings_games['title single_loser standard']
    module = 'race_single_loser_standard'

    def collect_losers(self, iteration=1):
        losers = set()
        for area_name in self.map_data.get_areas('losers'):
            losers.update(get_players_in_area(area_name))

        losers = list(filter(self._filter_func, losers))

        if not losers:
            if iteration == MAX_RECOLLECT_ITERATIONS:
                self.set_stage_group('draw')

            else:
                self._recollect_delay = Delay(
                    RECOLLECT_PLAYERS_INTERVAL,
                    self.collect_losers,
                    iteration + 1,
                )

        else:
            self._results['loser'] = loser = choice(tuple(losers))

            if loser == self.prisoner:
                self._results['winner'] = self.guard
            else:
                self._results['winner'] = self.prisoner

            self.set_stage_group('win')

    @push(None, 'race_player_lost')
    def push_race_player_lost(self, args):
        if self._recollect_delay is not None:
            return

        self.collect_losers()

add_available_game(RaceSingleLoserStandard)
