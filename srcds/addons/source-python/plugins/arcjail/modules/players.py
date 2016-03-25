from events import Event
from filters.players import PlayerIter
from listeners import OnClientActive, OnClientDisconnect, OnLevelInit
from messages import SayText2
from players.entity import Player

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

    player_indexes = [player.player.index for player in players]

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


@InternalEvent('unload')
def on_unload(event_var):
    for player in list(main_player_manager.values()):
        main_player_manager.delete(player)


@Event('player_spawn')
def on_player_spawn(game_event):
    userid = game_event.get_int('userid')
    if userid in main_player_manager:
        InternalEvent.fire(
            'player_respawn',
            player=main_player_manager[userid],
            game_event=game_event,
        )


@OnClientActive
def listener_on_client_active(index):
    player = Player(index)
    main_player_manager.create(player)


@OnClientDisconnect
def on_client_disconnect(index):
    player = Player(index)
    main_player_manager.delete(player)


@OnLevelInit
def listener_on_level_init(map_name):
    for player in list(main_player_manager.keys()):
        main_player_manager.delete(player)
