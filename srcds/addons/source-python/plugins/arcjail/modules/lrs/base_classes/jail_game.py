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

from ...players import broadcast, main_player_manager

from .. import (
    config_manager, game_event_handler, game_internal_event_handler,
    LastRequestGameStatus, launch_win_reward, stage, strings_module)

from .base_game import BaseGame


class JailGame(BaseGame):
    stage_groups = {
        'destroy': [
            "unsend-popups",
            "cancel-delays",
            "destroy",
        ],
        'init': [
            "register-event-handlers",
            "set-initial-status",
            "start-notify",
            "basegame-entry",
        ],
        'abort': ["abort", ],
        'abort-player-out': ["abort-player-out", ],
        'win': ["win", ],
        'winreward': ["winreward", ],
        'draw': ["draw", ],
    }

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self._popups = {}
        self._delays = []

    @stage('set-initial-status')
    def stage_set_initial_status(self):
        self._status = LastRequestGameStatus.NOT_STARTED

        InternalEvent.fire(
            'jail_lrs_status_set', instance=self, status=self._status)

    @stage('undo-set-initial-status')
    def stage_undo_set_initial_status(self):
        self._status = LastRequestGameStatus.FINISHED

        InternalEvent.fire(
            'jail_lrs_status_set', instance=self, status=self._status)

    @stage('set-start-status')
    def stage_set_start_status(self):
        self._status = LastRequestGameStatus.IN_PROGRESS

        InternalEvent.fire(
            'jail_lrs_status_set', instance=self, status=self._status)

        broadcast(strings_module['game_started'].tokenize(
            player1=self.prisoner.name,
            player2=self.guard.name,
            game=self.full_caption
        ))

    @stage('unsend-popups')
    def stage_unsend_popups(self):
        for popup in self._popups.values():
            popup.close()

        self._popups.clear()

    @stage('cancel-delays')
    def stage_cancel_delays(self):
        for delay in self._delays:
            if delay.running:
                delay.cancel()

        self._delays.clear()

    @stage('abort')
    def stage_abort(self):
        broadcast(strings_module['abort'])
        self.set_stage_group('destroy')

    @stage('abort-player-out')
    def stage_abort_not_enough_players(self):
        broadcast(strings_module['abort player_out'])
        self.set_stage_group('destroy')

    @stage('win')
    def stage_win(self):
        winner, loser = self._results['winner'], self._results['loser']
        if winner is None or loser is None:
            return

        InternalEvent.fire(
            'jail_lr_won', winner=winner, loser=loser, game_instance=self)

        if config_manager['victory_sound'] is not None:
            config_manager['victory_sound'].play(winner.index)

        broadcast(strings_module['common_victory'].tokenize(
            winner=winner.name,
            loser=loser.name,
            game=self.full_caption,
        ))

        self.set_stage_group('destroy')

        if not loser.dead:
            self.append_stage_group('winreward')

    @stage('winreward')
    def stage_winreward(self):
        launch_win_reward(self._results['winner'], self._results['loser'])

    @stage('draw')
    def stage_draw(self):
        InternalEvent.fire(
            'jail_lr_draw', prisoner=self.prisoner, guard=self.guard)

        broadcast(strings_module['common_draw'].tokenize(
            winner=self.prisoner.name,
            loser=self.guard.name,
            game=self.full_caption,
        ))

        self.set_stage_group('destroy')

    @game_event_handler('jailgame-player-death', 'player_death')
    def event_jailgame_player_death(self, game_event):
        player = main_player_manager.get_by_userid(
            game_event.get_int('userid'))

        if player in self._players:
            self._players.remove(player)

            self.set_stage_group('abort-player-out')

    @game_internal_event_handler(
        'jailgame-main-player-deleted', 'main_player_deleted')
    def event_jailgame_main_player_deleted(self, event_var):
        player = event_var['main_player']

        if player in self._players:
            self._players.remove(player)

            self.set_stage_group('abort-player-out')
