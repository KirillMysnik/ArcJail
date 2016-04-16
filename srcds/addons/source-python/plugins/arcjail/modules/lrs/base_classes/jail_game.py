from ....arcjail import InternalEvent

from ...players import broadcast, main_player_manager

from .. import (
    config_manager, game_event_handler, LastRequestGameStatus, stage,
    strings_module)

from .base_game import BaseGame


class JailGame(BaseGame):
    stage_groups = {
        'destroy': [
            "unsend-popups",
            "destroy",
        ],
        'init': [
            "register-event-handlers",
            "set-initial-status",
            "basegame-entry",
        ],
        'abort': ["abort", ],
    }

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self._popups = {}

    @stage('set-initial-status')
    def stage_set_initial_status(self):
        self._status = LastRequestGameStatus.NOT_STARTED

    @stage('undo-set-initial-status')
    def stage_undo_set_initial_status(self):
        self._status = LastRequestGameStatus.FINISHED

    @stage('set-start-status')
    def stage_set_start_status(self):
        self._status = LastRequestGameStatus.IN_PROGRESS

        InternalEvent.fire('jail_lrs_start_status_set', instance=self)

        broadcast(strings_module['game_started'].tokenize(
            player1=self.prisoner.name,
            player2=self.guard.name,
            game=self.caption
        ))

    @stage('unsend-popups')
    def stage_unsend_popups(self):
        for popup in self._popups.values():
            popup.close()

        self._popups.clear()

    @stage('abort')
    def stage_abort(self):
        broadcast(strings_module['abort'])
        self.set_stage_group('destroy')

    @stage('abort-player-out')
    def stage_abort_not_enough_players(self):
        broadcast(strings_module['abort player_out'])
        self.set_stage_group('destroy')

    @stage('win')
    def _(self):
        winner, loser = self._results['winner'], self._results['loser']
        if winner is None or loser is None:
            return

        InternalEvent.fire('jail_lr_won', player=winner)
        InternalEvent.fire('jail_lr_lost', player=loser)

        if config_manager['victory_sound'] is not None:
            config_manager['victory_sound'].play(winner)

        broadcast(strings_module['common_victory'].tokenize(
            winner=winner.name,
            loser=loser.name,
            game=self.caption,
        ))

        self.set_stage_group('destroy')

    @game_event_handler('jailgame-player-death', 'player_death')
    def event_jailgame_player_death(self, game_event):
        player = main_player_manager[game_event.get_int('userid')]

        if player in self._players:
            self._players.remove(player)

            self.set_stage_group('abort-player-out')

    @game_event_handler('jailgame-player-disconnect', 'player_disconnect')
    def event_jailgame_player_disconnect(self, game_event):
        player = main_player_manager[game_event.get_int('userid')]

        if player in self._players:
            self._players.remove(player)

            self.set_stage_group('abort-player-out')