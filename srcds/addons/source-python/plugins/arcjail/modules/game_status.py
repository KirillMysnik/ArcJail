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

from events import Event

from ..arcjail import InternalEvent

from ..resource.strings import build_module_strings


strings_module = build_module_strings('game_status')


class GameStatus:
    FREE = 1
    BUSY = 2
    NOT_STARTED = 3

    @classmethod
    def is_valid_status(cls, status):
        return status in (cls.FREE, cls.BUSY, cls.NOT_STARTED)


_status = None


def get_status():
    return _status


def set_status(status):
    if not GameStatus.is_valid_status(status):
        raise ValueError("Invalid status: '{0}'".format(status))

    global _status
    if _status == GameStatus.NOT_STARTED and status == GameStatus.FREE:
        InternalEvent.fire('jail_game_status_started')

    _status = status


@Event('round_start')
def on_round_start(game_event):
    global _status
    _status = GameStatus.NOT_STARTED

    InternalEvent.fire('jail_game_status_reset')


@InternalEvent('load')
def on_load(event_var):
    global _status
    _status = GameStatus.NOT_STARTED
