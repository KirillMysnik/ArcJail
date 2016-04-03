from ...players import broadcast, main_player_manager

from ...rebels import get_rebels

from .. import (
    config_manager, game_event_handler, MIN_PLAYERS_IN_GAME, stage,
    strings_module)

from .base_game import BaseGame


class JailGame(BaseGame):
    stage_groups = {
        'destroy': [
            "unsend-popups",
            "destroy",
        ],
        'abort': ["abort", ],
        'abort-leader-dead': ["abort-leader-dead", ],
        'abort-leader-disconnect': ["abort-leader-disconnect", ],
        'abort-not-enough-players': ["abort-not-enough-players", ],
    }

    def __init__(self, leader_player, players, **kwargs):
        super().__init__(leader_player, players, **kwargs)

        self._popups = {}

    @stage('unsend-popups')
    def stage_unsend_popups(self):
        for popup in self._popups.values():
            popup.close()

        self._popups.clear()

    @stage('abort')
    def stage_abort(self):
        broadcast(strings_module['aborted'])
        self.set_stage_group('destroy')

    @stage('abort-leader-dead')
    def stage_abort_leader_dead(self):
        broadcast(strings_module['abort_leader_dead'])
        self.set_stage_group('destroy')

    @stage('abort-leader-disconnect')
    def stage_abort_leader_disconnect(self):
        broadcast(strings_module['abort_leader_disconnect'])
        self.set_stage_group('destroy')

    @stage('abort-not-enough-players')
    def stage_abort_not_enough_players(self):
        broadcast(strings_module['abort_not_enough_players'])
        self.set_stage_group('destroy')

    @game_event_handler('jailgame-player-death', 'player_death')
    def event_jailgame_player_death(self, game_event):
        player = main_player_manager[game_event.get_int('userid')]
        if self.leader == player:
            self.set_stage_group('abort-leader-dead')

        else:
            if player in self._players:
                self._players.remove(player)

            if len(self._players) < MIN_PLAYERS_IN_GAME:
                self.set_stage_group('abort-not-enough-players')

    @game_event_handler('jailgame-player-disconnect', 'player_disconnect')
    def event_jailgame_player_disconnect(self, game_event):
        player = main_player_manager[game_event.get_int('userid')]
        if self.leader == player:
            self.set_stage_group('abort-leader-disconnect')

        else:
            if player in self._players:
                self._players.remove(player)

            if len(self._players) < MIN_PLAYERS_IN_GAME:
                self.set_stage_group('abort-not-enough-players')

    @classmethod
    def get_available_launchers(cls, leader_player, players):
        if get_rebels():
            return ()

        if len(players) < config_manager['min_players_number']:
            return ()

        return (cls.GameLauncher(cls), )
