from ...players import broadcast, main_player_manager

from .. import (
    game_event_handler, game_internal_event_handler, stage, strings_module)

from .jail_game import JailGame


class PlayerPreserving(JailGame):
    stage_groups = {
        'abort-player-dead': ["abort-player-dead", ],
        'abort-player-disconnect': ["abort-player-disconnect", ],
        'abort-player-rebel': ["abort-player-rebel", ],
    }

    @stage('abort-player-dead')
    def stage_abort_player_dead(self):
        broadcast(strings_module['abort_player_dead'])
        self.set_stage_group('destroy')

    @stage('abort-player-disconnect')
    def stage_abort_player_disconnect(self):
        broadcast(strings_module['abort_player_disconnect'])
        self.set_stage_group('destroy')

    @stage('abort-player-rebel')
    def stage_abort_player_rebel(self):
        broadcast(strings_module['abort_player_rebel'])
        self.set_stage_group('destroy')

    @game_event_handler('playerpreserving-player-death', 'player_death')
    def event_playerpreserving_player_death(self, game_event):
        player = main_player_manager[game_event.get_int('userid')]
        if player in self._players_all:
            self.set_stage_group('abort-player-death')

    @game_event_handler(
        'playerpreserving-player-disconnect', 'player_disconnect')
    def event_playerpreserving_player_disconnect(self, game_event):
        player = main_player_manager[game_event.get_int('userid')]
        if player in self._players_all:
            self.set_stage_group('abort-player-disconnect')

    @game_internal_event_handler(
        'playerpreserving-arcjail-rebel-set', 'jail_rebel_set')
    def event_playerpreserving_arcjail_rebel_set(self, event_var):
        player = event_var['player']
        if player in self._players_all:
            self.set_stage_group('abort-player-rebel')