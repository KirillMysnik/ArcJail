from listeners.tick import Delay
from messages import TextMsg

from controlled_cvars import sound_nullable_handler, string_handler

from ..arcjail import InternalEvent

from ..classes.base_player_manager import BasePlayerManager

from ..resource.strings import build_module_strings

from . import build_module_config

TEXT_VISIBLE_TIMEOUT = 2
MARKER_VISIBLE_TIMEOUT = 0.2
EMPTY_CENTER_MESSAGE = TextMsg("")


strings_module = build_module_strings('show_damage')
config_manager = build_module_config('show_damage')

config_manager.controlled_cvar(
    sound_nullable_handler,
    "hit_sound",
    default="arcjail/hitsound.wav",
    description="Path to a hit sound, leave empty to disable",
)
config_manager.controlled_cvar(
    string_handler,
    "hit_marker_material",
    default="overlays/arcjail/hitmarker",
    description="Path to a hit marker material (VMT-file) without VMT "
                "extension, leave empty to disable",
)


class ShowDamagePlayer:
    def __init__(self, player):
        self.player = player
        self._current_damage = 0
        self._reset_text_delay = None
        self._reset_marker_delay = None

    def _reset_text(self):
        self._current_damage = 0
        EMPTY_CENTER_MESSAGE.send(self.player.index)

    def _reset_marker(self):
        self.player.client_command('r_screenoverlay off')

    def show_damage(self, amount):
        self._current_damage += amount

        # Display damage amount
        TextMsg(strings_module['health'].tokenize(
            amount=self._current_damage)).send(self.player.index)

        # Play hit sound
        if config_manager['hit_sound'] is not None:
            config_manager['hit_sound'].play(self.player.index)

        # Show hit marker
        if config_manager['hit_marker_material'] != "":
            self.player.client_command(
                'r_screenoverlay {}'.format(config_manager['hit_sound']))

        # Cancel delays if any
        if (self._reset_text_delay is not None and
                self._reset_text_delay.running):

            self._reset_text_delay.cancel()

        if (self._reset_marker_delay is not None and
                self._reset_marker_delay.running):

            self._reset_marker_delay.cancel()

        # Relaunch delays
        self._reset_text_delay = Delay(TEXT_VISIBLE_TIMEOUT, self._reset_text)
        self._reset_marker_delay = Delay(
            MARKER_VISIBLE_TIMEOUT, self._reset_marker)


show_damage_player_manager = BasePlayerManager(ShowDamagePlayer)


@InternalEvent('main_player_created')
def on_main_player_created(event_var):
    player = event_var['main_player']
    show_damage_player_manager.create(player)


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    player = event_var['main_player']
    show_damage_player_manager.delete(player)


def show_damage(player, amount):
    sd_player = show_damage_player_manager[player.userid]
    sd_player.show_damage(amount)
