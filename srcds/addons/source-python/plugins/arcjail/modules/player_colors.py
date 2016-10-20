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

from colors import Color
from events import Event
from players.helpers import index_from_userid

from ..internal_events import InternalEvent


DEFAULT_COLOR = Color(255, 255, 255)


class PlayerColorRequest:
    def __init__(self, id_, priority, color):
        self.id = id_
        self.priority = priority
        self.color = color

requests = {}


@Event('round_start')
def on_round_start(game_event):
    requests.clear()


@Event('player_death_real')
def on_player_death_real(game_event):
    index = index_from_userid(game_event['userid'])
    if index in requests:
        del requests[index]


@InternalEvent('player_deleted')
def on_player_deleted(player):
    if player.index in requests:
        del requests[player.index]


@InternalEvent('player_respawn')
def on_player_respawn(player):
    if player.index in requests:
        del requests[player.index]
    _update_player(player)


def _update_player(player):
    if player.dead:
        return

    if player.index not in requests:
        player.color = DEFAULT_COLOR
        return

    request_max = None
    for request in requests[player.index]:
        if request_max is None or request.priority >= request_max.priority:
            request_max = request

    if request_max:
        player.color = request_max.color
    else:
        player.color = DEFAULT_COLOR


def make_color_request(player, priority, id_, color):
    if player.index not in requests:
        requests[player.index] = []

    for request in requests[player.index]:
        if request.id == id_:
            requests[player.index].remove(request)
            break

    requests[player.index].append(PlayerColorRequest(id_, priority, color))
    _update_player(player)


def cancel_color_request(player, id_):
    if player.index not in requests:
        return

    for request in requests[player.index]:
        if request.id == id_:
            requests[player.index].remove(request)
            break

    if not requests[player.index]:
        del requests[player.index]

    _update_player(player)
