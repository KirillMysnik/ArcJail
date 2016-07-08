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
from listeners import OnClientActive, OnClientDisconnect, OnLevelShutdown
from messages import SayText2
from players.entity import Player
from players.teams import teams_by_name

from ..arcjail import InternalEvent

from ..classes.base_player_manager import BasePlayerManager

from ..resource.strings import COLOR_SCHEME, strings_common


class MainPlayerManager(BasePlayerManager):
    def create(self, player):
        main_player = super().create(player)
        InternalEvent.fire('main_player_created', main_player=main_player)

    def delete(self, player):
        main_player = super().delete(player)
        InternalEvent.fire('main_player_deleted', main_player=main_player)

main_player_manager = MainPlayerManager(lambda player: player)


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
    tell(list(main_player_manager.values()), message, **tokens)


@InternalEvent('load')
def on_load(event_var):
    for player in PlayerIter():
        main_player_manager.create(player)

    InternalEvent.fire('main_players_loaded')


@InternalEvent('unload')
def on_unload(event_var):
    for player in list(main_player_manager.values()):
        main_player_manager.delete(player)


@Event('player_spawn')
def on_player_spawn(game_event):
    player = main_player_manager.get_by_userid(game_event.get_int('userid'))
    if player.team != teams_by_name['un']:
        InternalEvent.fire(
            'player_respawn',
            player=player,
            game_event=game_event,
        )


@OnClientActive
def listener_on_client_active(index):
    player = Player(index)
    main_player_manager.create(player)


@OnClientDisconnect
def listener_on_client_disconnect(index):
    if index not in main_player_manager:
        return

    player = main_player_manager[index]
    main_player_manager.delete(player)


@OnLevelShutdown
def listener_on_level_init():
    for player in list(main_player_manager.values()):
        main_player_manager.delete(player)
