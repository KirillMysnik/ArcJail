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

from entities.entity import Entity
from entities.helpers import index_from_inthandle
from events.manager import event_manager
from listeners.tick import Delay, on_tick_listener_manager
from messages import TextMsg

from ....arcjail import internal_event_manager

from ...overlays import show_overlay

from ...players import broadcast, main_player_manager

from .. import config_manager, stage, strings_module

from .base_game import BaseGame


class PrepareTime(BaseGame):
    stage_groups = {
        'init': ["prepare-prepare", ],
        'destroy': [
            "prepare-cancel-delays",
            "unsend-popups",
            "destroy",
        ],
        'prepare-start': [
            'prepare-freeze',
            'prepare-register-event-handlers',
            'prepare-entry',
        ],
        'abort-prepare-interrupted': ["abort-prepare-interrupted", ],
        'prepare-continue': [
            "prepare-cancel-countdown",
            "prepare-undo-prepare-start",
            "register-event-handlers",
            "start-notify",
            "basegame-entry",
        ],
    }

    def __init__(self, leader_player, players, **kwargs):
        super().__init__(leader_player, players, **kwargs)

        self._prepare_delay = None
        self._prepare_countdown = None

    @stage('prepare-prepare')
    def stage_prepare_prepare(self):
        if self._settings.get('prepare', True):
            indexes = list(player.index for player in self._players)
            if self.leader.index not in indexes:
                indexes.append(self.leader.index)

            def callback():
                self.undo_stages('prepare-start')
                self.set_stage_group('prepare-continue')

            self._prepare_delay = Delay(
                config_manager['prepare_timeout'], callback)

            def countdown(ticks_left):
                if (ticks_left > 3 or ticks_left < 1 or config_manager[
                        'countdown_{}_material'.format(ticks_left)] == ""):

                    TextMsg(str(ticks_left)).send(*indexes)

                else:
                    for player in self._players:
                        show_overlay(player, config_manager[
                            'countdown_{}_material'.format(ticks_left)], 1)

                if config_manager['countdown_sound'] is not None:
                    config_manager['countdown_sound'].play(*indexes)

                self._prepare_countdown = Delay(1.0, countdown, ticks_left - 1)

            countdown(int(config_manager['prepare_timeout']))

            broadcast(strings_module['stage_prepare'])

            if config_manager['prepare_sound'] is not None:
                config_manager['prepare_sound'].play(*indexes)

            self.set_stage_group('prepare-start')

        else:
            self.set_stage_group('prepare-continue')

    def _prepare_event_handler_player_death(self, game_event):
        player = main_player_manager[game_event.get_int('userid')]
        if player in self._players or player == self.leader:
            self.set_stage_group('abort-prepare-interrupted')

    def _prepare_event_handler_main_player_deleted(self, event_var):
        player = event_var['player']
        if player in self._players or player == self.leader:
            self.set_stage_group('abort-prepare-interrupted')

    def _prepare_event_handler_player_hurt(self, game_event):
        player = main_player_manager[game_event.get_int('userid')]
        if player in self._players or player == self.leader:
            self.set_stage_group('abort-prepare-interrupted')

    @stage('prepare-register-event-handlers')
    def stage_prepare_register_event_handlers(self):
        event_manager.register_for_event(
            'player_death', self._prepare_event_handler_player_death)

        event_manager.register_for_event(
            'player_hurt', self._prepare_event_handler_player_hurt)

        internal_event_manager.register_event_handler(
            'main_player_deleted',
            self._prepare_event_handler_main_player_deleted
        )

    @stage('undo-prepare-register-event-handlers')
    def stage_undo_prepare_register_event_handlers(self):
        event_manager.unregister_for_event(
            'player_death', self._prepare_event_handler_player_death)

        event_manager.unregister_for_event(
            'player_hurt', self._prepare_event_handler_player_hurt)

        internal_event_manager.unregister_event_handler(
            'main_player_deleted',
            self._prepare_event_handler_main_player_deleted
        )

    @stage('prepare-cancel-delays')
    def stage_prepare_cancel_delays(self):
        for delay in (self._prepare_delay, self._prepare_countdown):
            if delay is not None and delay.running:
                delay.cancel()

    @stage('prepare-cancel-countdown')
    def stage_prepare_cancel_countdown(self):
        if self._prepare_countdown is not None:
            self._prepare_countdown.cancel()

    @stage('prepare-undo-prepare-start')
    def stage_prepare_undo_prepare_start(self):
        self.undo_stages('prepare-start')

    @stage('prepare-entry')
    def stage_prepare_entry(self):
        pass

    def _prepare_freeze_tick_handler(self):
        for player in self._players:
            try:
                weapon_index = index_from_inthandle(player.active_weapon)
            except (OverflowError, ValueError):
                continue

            weapon = Entity(weapon_index)
            weapon.next_attack += 1
            weapon.next_secondary_fire_attack += 1

    @stage('prepare-freeze')
    def stage_prepare_freeze(self):
        on_tick_listener_manager.register_listener(
            self._prepare_freeze_tick_handler)

        for player in self._players:
            player.stuck = True

    @stage('undo-prepare-freeze')
    def stage_undo_prepare_freeze(self):
        on_tick_listener_manager.unregister_listener(
            self._prepare_freeze_tick_handler)

        for player in self._players:
            player.stuck = False

            try:
                weapon_index = index_from_inthandle(player.active_weapon)
            except:
                continue

            weapon = Entity(weapon_index)
            weapon.next_attack = 0
            weapon.next_secondary_fire_attack = 0

    @stage('abort-prepare-interrupted')
    def stage_abort_prepare_interrupted(self):
        broadcast(strings_module['abort_prepare_interrupted'])

        if config_manager['prepare_sound'] is not None:
            config_manager['prepare_sound'].stop()

        self.set_stage_group('destroy')
