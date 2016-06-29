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

from ....resource.strings import build_module_strings

from ...jail_map import get_players_in_area

from ..base_classes.map_game import MapGame

from .. import add_available_game, push, stage


RECOLLECT_PLAYERS_INTERVAL = 0.25
MAX_RECOLLECT_ITERATIONS = 8


strings_module = build_module_strings('games/race')


class RaceBase(MapGame):
    stage_groups = {
        'destroy': [
            "prepare-cancel-delays",
            "cancel-recollect-delay",
            "unsend-popups",
            "destroy",
        ],
    }

    def __init__(self, leader_player, players, **kwargs):
        super().__init__(leader_player, players, **kwargs)

        self._recollect_delay = None

    @stage('cancel-recollect-delay')
    def stage_cancel_recollect_delay(self):
        if self._recollect_delay is not None:
            if self._recollect_delay.running:
                self._recollect_delay.cancel()

            self._recollect_delay = None

    @push(None, 'end_game')
    def push_end_game(self, args):
        self.set_stage_group('game-end-draw')


class RaceSingleWinnerStandard(RaceBase):
    caption = strings_module['title single_winner standard']
    module = 'race_single_winner_standard'

    def collect_winners(self, iteration=1):
        winners = set()
        for area_name in self.map_data.get_areas('winners'):
            winners.update(get_players_in_area(area_name))

        if not winners:
            if iteration == MAX_RECOLLECT_ITERATIONS:
                self.set_stage_group('game-end-draw')

            else:
                self._recollect_delay = Delay(
                    RECOLLECT_PLAYERS_INTERVAL,
                    self.collect_winners,
                    iteration + 1,
                )

        else:
            self._results['losers'] = ()
            self._results['winners'] = (choice(tuple(winners)), )
            self.set_stage_group('game-end-players-won')

    @push(None, 'race_player_won')
    def push_race_player_won(self, args):
        if self._recollect_delay is not None:
            return

        self.collect_winners()

add_available_game(RaceSingleWinnerStandard)


class RaceMultipleWinnersStandard(RaceBase):
    caption = strings_module['title multiple_winners standard']
    module = 'race_multiple_winners_standard'

    def collect_winners(self, iteration=1):
        winners = set()
        for area_name in self.map_data.get_areas('winners'):
            winners.update(get_players_in_area(area_name))

        if not winners:
            if iteration == MAX_RECOLLECT_ITERATIONS:
                self.set_stage_group('game-end-draw')

            else:
                self._recollect_delay = Delay(
                    RECOLLECT_PLAYERS_INTERVAL,
                    self.collect_winners,
                    iteration + 1,
                )

        else:
            self._results['losers'] = ()
            self._results['winners'] = winners
            self.set_stage_group('game-end-players-won')

    @push(None, 'race_players_won')
    def push_race_players_won(self, args):
        if self._recollect_delay is not None:
            return

        self.collect_winners()

add_available_game(RaceMultipleWinnersStandard)


class RaceSingleLoserStandard(RaceBase):
    caption = strings_module['title single_loser standard']
    module = 'race_single_loser_standard'

    def collect_losers(self, iteration=1):
        losers = set()
        for area_name in self.map_data.get_areas('losers'):
            losers.update(get_players_in_area(area_name))

        if not losers:
            if iteration == MAX_RECOLLECT_ITERATIONS:
                self.set_stage_group('game-end-draw')

            else:
                self._recollect_delay = Delay(
                    RECOLLECT_PLAYERS_INTERVAL,
                    self.collect_losers,
                    iteration + 1,
                )

        else:
            self._results['losers'] = (choice(tuple(losers)), )
            self._results['winners'] = ()
            self.set_stage_group('game-end-players-won')

    @push(None, 'race_player_lost')
    def push_race_player_lost(self, args):
        if self._recollect_delay is not None:
            return

        self.collect_losers()

add_available_game(RaceSingleLoserStandard)


class RaceMultipleLosersStandard(RaceBase):
    caption = strings_module['title multiple_losers standard']
    module = 'race_multiple_losers_standard'

    def collect_losers(self, iteration=1):
        losers = set()
        for area_name in self.map_data.get_areas('losers'):
            losers.update(get_players_in_area(area_name))

        if not losers:
            if iteration == MAX_RECOLLECT_ITERATIONS:
                self.set_stage_group('game-end-draw')

            else:
                self._recollect_delay = Delay(
                    RECOLLECT_PLAYERS_INTERVAL,
                    self.collect_losers,
                    iteration + 1,
                )

        else:
            self._results['losers'] = losers
            self._results['winners'] = ()
            self.set_stage_group('game-end-players-won')

    @push(None, 'race_players_lost')
    def push_race_players_lost(self, args):
        if self._recollect_delay is not None:
            return

        self.collect_losers()

add_available_game(RaceMultipleLosersStandard)
