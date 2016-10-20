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
from listeners.tick import Delay

from controlled_cvars.handlers import bool_handler, float_handler

from ..internal_events import InternalEvent
from ..resource.strings import build_module_strings

from . import build_module_config
from .game_status import GameStatus, get_status
from .jail_map import get_map_connections, register_push_handler
from .jail_menu import new_available_option
from .leaders import is_leader
from .players import broadcast, tell


WARNING_DELAY = 30
GAME_NOT_STARTED_CHECK_DELAY = 0.5


strings_module = build_module_strings('cell_opener')
config_manager = build_module_config('cell_opener')


config_manager.controlled_cvar(
    bool_handler,
    "enabled",
    default=1,
    description="Enable/Disable cell opener",
)


config_manager.controlled_cvar(
    float_handler,
    "open_delay",
    default=60.0,
    description="Delay before jails are automatically opened, -1 to disable",
)


_delays = {}


def get_connections_open():
    return get_map_connections('ToOpenJails')


def get_connections_close():
    return get_map_connections('ToCloseJails')


def cancel_delays():
    for delay_name in ('warning', 'auto_open'):
        if delay_name in _delays:
            _delays[delay_name].cancel()
            del _delays[delay_name]


def open():
    cancel_delays()

    for connection in get_connections_open():
        connection.fire()


def close():
    for connection in get_connections_close():
        connection.fire()


def get_open_denial_reason(player):
    if not get_connections_open():
        return strings_module['fail_not_supported']

    if not is_leader(player):
        return strings_module['fail_not_leader']

    return None


def get_close_denial_reason(player):
    if not get_connections_close():
        return strings_module['fail_not_supported']

    if not is_leader(player):
        return strings_module['fail_not_leader']

    return None


@Event('round_start')
def on_round_start(game_event):
    if not config_manager['enabled']:
        return

    if not get_connections_open():
        return

    def check_callback():
        del _delays['notstarted_check']
        if get_status() == GameStatus.NOT_STARTED:
            broadcast(strings_module['opened not_started'])
            open()

    if 'notstarted_check' in _delays:
        _delays['notstarted_check'].cancel()

    _delays['notstarted_check'] = Delay(
        GAME_NOT_STARTED_CHECK_DELAY, check_callback)


@InternalEvent('jail_game_status_started')
def on_jail_game_status_started():
    if not get_connections_open():
        return

    if config_manager['open_delay'] - WARNING_DELAY > 0:
        def warning_callback():
            del _delays['warning']
            broadcast(strings_module['auto_open_warning'].tokenize(
                delay=WARNING_DELAY,
            ))

        if 'warning' in _delays:
            _delays['warning'].cancel()

        _delays['warning'] = Delay(
            config_manager['open_delay'] - WARNING_DELAY, warning_callback)

    def auto_open_callback():
        del _delays['auto_open']
        open()
        broadcast(strings_module['opened auto'])

    if 'auto_open' in _delays:
        _delays['auto_open'].cancel()

    if config_manager['open_delay'] >= 0:
        _delays['auto_open'] = Delay(
            config_manager['open_delay'], auto_open_callback)


@InternalEvent('unload')
def on_unload():
    for delay in _delays.values():
        delay.cancel()

    _delays.clear()


# =============================================================================
# >> PUSH HANDLER
# =============================================================================
def push_handler(args):
    cancel_delays()


register_push_handler('slot-main', 'jail_cells_opened', push_handler)


# =============================================================================
# >> JAIL MENU ENTRIES
# =============================================================================
def jailmenu_open(player):
    reason = get_open_denial_reason(player)
    if reason is None:
        open()

    else:
        tell(player, reason)


def jailmenu_open_handler_active(player):
    return get_open_denial_reason(player) is None


new_available_option(
    'cells-open',
    strings_module['jailmenu_entry_open'],
    jailmenu_open,
    jailmenu_open_handler_active,
    jailmenu_open_handler_active,
)


def jailmenu_close(player):
    reason = get_close_denial_reason(player)
    if reason is None:
        close()

    else:
        tell(player, reason)


def jailmenu_close_handler_active(player):
    return get_close_denial_reason(player) is None


new_available_option(
    'cells-close',
    strings_module['jailmenu_entry_close'],
    jailmenu_close,
    jailmenu_close_handler_active,
    jailmenu_close_handler_active,
)
