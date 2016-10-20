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
from filters.players import PlayerIter
from listeners import OnClientActive, OnClientDisconnect, OnLevelInit
from messages import SayText2
from players.entity import Player

from ..classes.base_player_manager import BasePlayerManager
from ..internal_events import InternalEvent
from ..resource.strings import COLOR_SCHEME, strings_common


_initial_spawns = []


class PlayerManager(BasePlayerManager):
    def create(self, player):
        player = super().create(player)
        InternalEvent.fire('player_created', player=player)

    def delete(self, player):
        player = super().delete(player)
        InternalEvent.fire('player_deleted', player=player)

player_manager = PlayerManager(lambda player: player)


def tell(players, message, **tokens):
    """Send a SayText2 message to a list of Admin instances."""
    if isinstance(players, Player):
        players = (players, )

    player_indexes = [player.index for player in players]

    tokens.update(COLOR_SCHEME)

    message = message.tokenize(**tokens)
    message = strings_common['chat_base'].tokenize(
        message=message, **COLOR_SCHEME)

    SayText2(message=message).send(*player_indexes)


def broadcast(message, **tokens):
    """Send a SayText2 message to all registered users."""
    tell(list(player_manager.values()), message, **tokens)


@InternalEvent('load')
def on_load():
    for player in PlayerIter():
        player_manager.create(player)

    InternalEvent.fire('players_loaded')


@InternalEvent('unload')
def on_unload():
    for player in list(player_manager.values()):
        player_manager.delete(player)


@Event('player_spawn')
def on_player_spawn(game_event):
    player = player_manager.get_by_userid(game_event['userid'])

    if player.index not in _initial_spawns:
        _initial_spawns.append(player.index)
        return

    InternalEvent.fire('player_respawn', player=player)


@OnClientActive
def listener_on_client_active(index):
    player = Player(index)
    player_manager.create(player)


@OnClientDisconnect
def listener_on_client_disconnect(index):
    if index not in player_manager:
        return

    player = player_manager[index]
    player_manager.delete(player)


@OnLevelInit
def listener_on_level_init(map_name):
    for player in list(player_manager.values()):
        player_manager.delete(player)
