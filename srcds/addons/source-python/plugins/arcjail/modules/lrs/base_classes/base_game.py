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

from ...games.base_classes.base_game import BaseGame

from .. import GameLauncher, remove_instance, stage


class BaseGame(BaseGame):
    settings = {}
    _caption = None
    module = None

    class GameLauncher(GameLauncher):
        def launch(self, players, **kwargs):
            return self.game_class(players, **kwargs)

    def __init__(self, players, **kwargs):
        self._prisoner, self._guard = players
        self._players = list(players)
        self._players_all = list(players)
        self._lock_stage_queue = False
        self._cur_stage_id = None
        self._stage_queue = []
        self._executed_stages = []
        self._settings = kwargs
        self._status = None
        self._results = {}

        for stage_ in self._stages_map.values():
            stage_.game_instance = self

        for game_event_handler_ in self._events.values():
            game_event_handler_.game_instance = self

        for game_internal_event_handler_ in self._internal_events.values():
            game_internal_event_handler_.game_instance = self

    @property
    def caption(self):
        return self._caption

    @stage('destroy')
    def stage_destroy(self):
        self.undo_stages()
        self._lock_stage_queue = True
        remove_instance(self)

        InternalEvent.fire('jail_lr_destroyed', game_instance=self)

    @property
    def guard(self):
        return self._guard

    @property
    def prisoner(self):
        return self._prisoner

    @property
    def status(self):
        return self._status

    @classmethod
    def get_available_launchers(cls):
        return (cls.GameLauncher(cls),)

    @stage('start-notify')
    def stage_start_notify(self):
        # Obsolete, as set-start-status does this for us
        pass
