from random import choice

from listeners.tick import Delay

from ...resource.strings import build_module_strings

from ..jail_map import get_players_in_area

from ..players import broadcast

from .base_classes.map_game import MapGame

from . import (
    add_available_game, format_player_names, helper_set_loser,
    helper_set_neutral, helper_set_winner, push, stage,
    strings_module as strings_games)


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
        'game-end-draw': ['game-end-draw', ],
    }

    def __init__(self, leader_player, players, **kwargs):
        super().__init__(leader_player, players, **kwargs)

        self._recollect_delay = None
        self._results = {}

    @stage('game-end-draw')
    def stage_game_end_draw(self):
        broadcast(strings_module['draw'])
        self.set_stage_group('destroy')

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

    stage_groups = {
        'game-end-player-won': ['game-end-player-won', ],
    }

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
            self._results['winner'] = choice(tuple(winners))
            self.set_stage_group('game-end-player-won')

    @stage('game-end-player-won')
    def stage_game_end_player_won(self):
        winner = self._results['winner']

        broadcast(strings_games['win_player'].tokenize(player=winner.name))

        for player in self._players_all:
            if player == winner:
                helper_set_winner(player)

            else:
                helper_set_neutral(player)

        self.set_stage_group('destroy')

    @push(None, 'race_player_won')
    def push_race_player_won(self, args):
        if self._recollect_delay is not None:
            return

        self.collect_winners()

add_available_game(RaceSingleWinnerStandard)


class RaceMultipleWinnersStandard(RaceBase):
    caption = strings_module['title multiple_winners standard']
    module = 'race_multiple_winners_standard'

    stage_groups = {
        'game-end-players-won': ['game-end-players-won', ],
    }

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
            self._results['winners'] = winners
            self.set_stage_group('game-end-players-won')

    @stage('game-end-players-won')
    def stage_game_end_players_won(self):
        winners = self._results['winners']

        broadcast(strings_games['win_players'].tokenize(
            players=format_player_names(winners)))

        for player in self._players_all:
            if player in winners:
                helper_set_winner(player)

            else:
                helper_set_neutral(player)

        self.set_stage_group('destroy')

    @push(None, 'race_players_won')
    def push_race_players_won(self, args):
        if self._recollect_delay is not None:
            return

        self.collect_winners()

add_available_game(RaceMultipleWinnersStandard)


class RaceSingleLoserStandard(RaceBase):
    caption = strings_module['title single_loser standard']
    module = 'race_single_loser_standard'

    stage_groups = {
        'game-end-player-lost': ['game-end-player-lost', ],
    }

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
            self._results['loser'] = choice(tuple(losers))
            self.set_stage_group('game-end-player-lost')

    @stage('game-end-player-lost')
    def stage_game_end_player_lost(self):
        loser = self._results['loser']

        broadcast(strings_games['lose_player'].tokenize(player=loser.name))

        for player in self._players_all:
            if player == loser:
                helper_set_loser(player)

            else:
                helper_set_neutral(player)

        self.set_stage_group('destroy')

    @push(None, 'race_player_lost')
    def push_race_player_lost(self, args):
        if self._recollect_delay is not None:
            return

        self.collect_losers()

add_available_game(RaceSingleLoserStandard)


class RaceMultipleLosersStandard(RaceBase):
    caption = strings_module['title multiple_losers standard']
    module = 'race_multiple_losers_standard'

    stage_groups = {
        'game-end-players-lost': ['game-end-players-lost', ],
    }

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
            self.set_stage_group('game-end-players-lost')

    @stage('game-end-players-lost')
    def stage_game_end_players_lost(self):
        losers = self._results['losers']

        broadcast(strings_games['lose_players'].tokenize(
            players=format_player_names(losers)))

        for player in self._players_all:
            if player in losers:
                helper_set_loser(player)

            else:
                helper_set_neutral(player)

        self.set_stage_group('destroy')

    @push(None, 'race_players_lost')
    def push_race_players_lost(self, args):
        if self._recollect_delay is not None:
            return

        self.collect_losers()

add_available_game(RaceMultipleLosersStandard)