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

import os
from traceback import format_exc
from warnings import warn

from commands.say import SayCommand
from events import Event
from filters.players import PlayerIter
from listeners.tick import Delay
from menus import PagedMenu, PagedOption
from players.helpers import get_client_language

from path import Path

from advanced_ts import BaseLangStrings

from controlled_cvars.handlers import (
    bool_handler, color_handler, float_handler, int_handler,
    sound_nullable_handler, string_handler
)

from ...arcjail import InternalEvent, load_downloadables

from ...info import info

from ...resource.paths import ARCJAIL_LOG_PATH

from ...resource.strings import build_module_strings, COLOR_SCHEME

from ..admin import section

from ..effects.sprites import set_player_sprite

from ..game_status import get_status, GameStatus, set_status
from ..game_status import strings_module as strings_game_status

from ..jail_menu import new_available_option

from ..leaders import is_leader

from ..overlays import show_overlay

from ..players import main_player_manager, tell

from .. import build_module_config, parse_modules


MIN_PLAYERS_IN_GAME = 2
MAX_PLAYERS_NAMES_LIST_LENGTH = 36
MAX_PLAYER_NAME_LENGTH = 10

strings_module = build_module_strings('games/common')
strings_game_captions = BaseLangStrings(Path(info.basename) / "games")
config_manager = build_module_config('games/common')

config_manager.controlled_cvar(
    bool_handler,
    "enabled",
    default=1,
    description="Enable/Disable !games feature",
)
config_manager.controlled_cvar(
    int_handler,
    "min_players_number",
    default=2,
    description="Minimum number of prisoners to be able to "
                "launch the game with",
)
config_manager.controlled_cvar(
    bool_handler,
    "launch_from_cage",
    default=1,
    description="Allow area-specific games to be launched from the cage",
)
config_manager.controlled_cvar(
    bool_handler,
    "launch_from_anywhere",
    default=0,
    description="Allow area-specific games to be launched from "
                "any place on the map",
)
config_manager.controlled_cvar(
    string_handler,
    "winner_sprite",
    default="arcjail/winner.vmt",
    description="Winner sprite (don't forget to include VMT/SPR extension)",
)
config_manager.controlled_cvar(
    string_handler,
    "loser_sprite",
    default="arcjail/loser.vmt",
    description="Loser sprite (don't forget to include VMT/SPR extension)",
)
config_manager.controlled_cvar(
    float_handler,
    "sprite_duration",
    default=5.0,
    description="How long sprites above players heads should "
                "last, 0 - disable",
)
config_manager.controlled_cvar(
    color_handler,
    "team1_color",
    default="0,146,226",
    description="Color for players in team Alpha",
)
config_manager.controlled_cvar(
    string_handler,
    "team1_model",
    default="models/player/arcjail/team_alpha/team_alpha.mdl",
    description="Model for team Alpha players",
)
config_manager.controlled_cvar(
    color_handler,
    "team2_color",
    default="235,200,0",
    description="Color for players in team Bravo",
)
config_manager.controlled_cvar(
    string_handler,
    "team2_model",
    default="models/player/arcjail/team_bravo/team_bravo.mdl",
    description="Model for team Bravo players",
)
config_manager.controlled_cvar(
    color_handler,
    "team3_color",
    default="255,0,170",
    description="Color for players in team Charlie",
)
config_manager.controlled_cvar(
    string_handler,
    "team3_model",
    default="models/player/arcjail/team_charlie/team_charlie.mdl",
    description="Model for team Charlie players",
)
config_manager.controlled_cvar(
    color_handler,
    "team4_color",
    default="255,102,0",
    description="Color for players in team Delta",
)
config_manager.controlled_cvar(
    string_handler,
    "team4_model",
    default="models/player/arcjail/team_delta/team_delta.mdl",
    description="Model for team Delta players",
)
config_manager.controlled_cvar(
    bool_handler,
    "prefer_model_over_color",
    default=1,
    description="Enable/Disable marking prisoners with a model (TEAMX_MODEL) "
                "instead of color (TEAMX_COLOR)",
)
config_manager.controlled_cvar(
    sound_nullable_handler,
    "winner_sound",
    default="arcjail/gamewin.mp3",
    description="Winner sound",
)
config_manager.controlled_cvar(
    sound_nullable_handler,
    "loser_sound",
    default="",
    description="Loser sound",
)
config_manager.controlled_cvar(
    sound_nullable_handler,
    "prepare_sound",
    default="arcjail/gameprepare.mp3",
    description="Prepare sound",
)
config_manager.controlled_cvar(
    sound_nullable_handler,
    "countdown_sound",
    default="arcjail/beep2.mp3",
    description="Countdown sound",
)
config_manager.controlled_cvar(
    string_handler,
    "countdown_3_material",
    default="overlays/arcjail/3",
    description="Path to a '3' material (VMT-file) without VMT "
                "extension, leave empty to disable",
)
config_manager.controlled_cvar(
    string_handler,
    "countdown_2_material",
    default="overlays/arcjail/2",
    description="Path to a '2' material (VMT-file) without VMT "
                "extension, leave empty to disable",
)
config_manager.controlled_cvar(
    string_handler,
    "countdown_1_material",
    default="overlays/arcjail/1",
    description="Path to a '1' material (VMT-file) without VMT "
                "extension, leave empty to disable",
)
config_manager.controlled_cvar(
    float_handler,
    "prepare_timeout",
    default=3.0,
    description="Preparation timeout for games that require it",
)
config_manager.controlled_cvar(
    sound_nullable_handler,
    "flawless_sound",
    default="arcjail/flawless.mp3",
    description="Additional sound to play if the victory was flawless, "
                "leave empty to disable",
)
config_manager.controlled_cvar(
    string_handler,
    "flawless_material",
    default="overlays/arcjail/flawless",
    description="Path to a FLAWLESS! material (VMT-file) without VMT "
                "extension, leave empty to disable",
)


class DestructionFailure(Warning):
    pass


class GameLauncher:
    def __init__(self, game_class):
        self.caption = game_class._caption
        self.game_class = game_class

    def __eq__(self, other):
        if type(other) != GameLauncher:
            return False

        return self.game_class == other.game_class

    def __hash__(self):
        return hash(self.game_class)

    def launch(self, leader_player, players, **kwargs):
        raise NotImplementedError

    def get_launch_denial_reason(self, leader_player, players, **kwargs):
        if self not in self.game_class.get_available_launchers(
                leader_player, players):

            return strings_module['fail_game_unavailable']

        return None


_popups = {}
_game_instances = []
_available_game_classes = []
_downloadables_sounds = load_downloadables('games-base-sounds.res')
_downloadables_materials = load_downloadables('games-base-materials.res')
_saved_game_status = None
_flawless_effects_delays = []


def _launch_game(launcher, leader_player, players, **kwargs):
    game = launcher.launch(leader_player, players=players, **kwargs)
    set_instance(game)
    game.set_stage_group('init')


def get_players_to_play():
    rs = []
    for player in PlayerIter(('jail_prisoner', 'alive')):
        if player.index in main_player_manager:
            rs.append(main_player_manager[player.index])

    return tuple(rs)


def get_available_launchers(leader_player, players):
    result = []
    for game_class in _available_game_classes:
        result.extend(
            game_class.get_available_launchers(leader_player, players))

    return tuple(result)


def get_game_denial_reason(player):
    from ..lrs import config_manager as config_manager_lrs

    if not config_manager['enabled']:
        return strings_module['fail_disabled']

    if _game_instances:
        return strings_module['fail_game_already_started']

    status = get_status()
    if status == GameStatus.BUSY:
        return strings_game_status['busy']

    if status == GameStatus.NOT_STARTED:
        return strings_game_status['not_started']

    if not is_leader(player):
        return strings_module['fail_leaders_only']

    if not get_available_launchers(player, get_players_to_play()):
        return strings_module['fail_none_available']

    if (len(PlayerIter(['jail_prisoner', 'alive'])) <=
            config_manager_lrs['prisoners_limit']):

        return strings_module['fail lrs_available']

    return None


def add_available_game(game_class):
    _available_game_classes.append(game_class)


def remove_available_game(game_class):
    _available_game_classes.remove(game_class)


def set_instance(game):
    global _saved_game_status
    if _saved_game_status is None:
        _saved_game_status = get_status()

    if game is None:
        set_status(_saved_game_status)
        _saved_game_status = None
        _game_instances.clear()

    else:
        set_status(GameStatus.BUSY)
        _game_instances.append(game)


def get_instance():
    return _game_instances[0] if _game_instances else None


def helper_set_winner(player, effects=True):
    InternalEvent.fire('jail_game_winner', player=player)

    if player.dead or not effects:
        return

    if (config_manager['winner_sprite'] != "" and
            config_manager['sprite_duration'] > 0):

        set_player_sprite(player,
                          config_manager['winner_sprite'],
                          config_manager['sprite_duration'])

    if config_manager['winner_sound'] is not None:
        config_manager['winner_sound'].play(player.index)


def helper_set_loser(player, effects=True):
    InternalEvent.fire('jail_game_loser', player=player)

    if player.dead or not effects:
        return

    if (config_manager['loser_sprite'] != "" and
            config_manager['sprite_duration'] > 0):

        set_player_sprite(player,
                          config_manager['loser_sprite'],
                          config_manager['sprite_duration'])

    if config_manager['loser_sound'] is not None:
        config_manager['loser_sound'].play(player.index)


def helper_set_neutral(player):
    InternalEvent.fire('jail_game_neutral', player=player)


def send_popup(player):
    reason = get_game_denial_reason(player)
    if reason:
        tell(player, reason)
        return

    if player.userid in _popups:
        _popups[player.userid].close()

    players = get_players_to_play()

    def select_callback(popup, player_index, option):
        reason = get_game_denial_reason(player)
        if reason is not None:
            tell(player, reason)
            return

        launcher = option.value
        reason = launcher.get_launch_denial_reason(player, players)
        if reason is not None:
            tell(player, reason)
            return

        _launch_game(launcher, player, players)

    popup = _popups[player.userid] = PagedMenu(
        select_callback=select_callback,
        title=strings_module['popup title_choose']
    )

    for launcher in get_available_launchers(player, players):
        popup.append(PagedOption(
            text=launcher.caption,
            value=launcher,
            highlight=True,
            selectable=True
        ))

    popup.send(player.index)


def reset():
    global _saved_game_status
    _saved_game_status = None

    game = get_instance()
    if game is not None:
        try:
            game.set_stage_group('destroy')
        except Exception as e:
            warn(DestructionFailure(
                "Couldn't properly destroy the game. "
                "Exception: {}. Traceback:\n{}".format(e, format_exc())
            ))
        finally:
            set_instance(None)

    for popup in _popups.values():
        popup.close()

    _popups.clear()

    for flawless_efects_delay in _flawless_effects_delays:
        if flawless_efects_delay.running:
            flawless_efects_delay.cancel()

    _flawless_effects_delays.clear()


def play_flawless_effects(players):
    def callback():
        if config_manager['flawless_sound'] is not None:
            config_manager['flawless_sound'].play(
                *[player_.index for player_ in players])

        if config_manager['flawless_material'] != "":
            for player in players:
                show_overlay(player, config_manager['flawless_material'], 3)

    _flawless_effects_delays.append(Delay(1.5, callback))


def format_player_names(players):
    names = []
    for player in players:
        if len(player.name) > MAX_PLAYER_NAME_LENGTH:
            names.append(player.name[:MAX_PLAYER_NAME_LENGTH] + "~")
        else:
            names.append(player.name)

    string = ', '.join(names)
    if len(string) > MAX_PLAYERS_NAMES_LIST_LENGTH:
        string = string[:MAX_PLAYERS_NAMES_LIST_LENGTH] + "..."

    return string


@Event('round_start')
def on_round_start(game_event):
    reset()


@InternalEvent('unload')
def on_unload(event_var):
    reset()


@SayCommand('!games')
def say_games(command, index, team_only):
    player = main_player_manager[index]
    send_popup(player)


# =============================================================================
# >> JAIL MENU ENTRIES
# =============================================================================
def jailmenu_games(player):
    send_popup(player)


def jailmenu_games_handler_active(player):
    return get_game_denial_reason(player) is None


new_available_option(
    'launch-game',
    strings_module['jailmenu_entry_option'],
    jailmenu_games,
    handler_active=jailmenu_games_handler_active,
)


# =============================================================================
# >> ARCADMIN ENTRIES
# =============================================================================
if section is not None:
    from arcadmin.classes.menu import Command, Section

    class PrintAvailableGames(Command):
        @staticmethod
        def select_callback(admin):
            lines = []
            players = get_players_to_play()
            language = get_client_language(admin.player.index)

            def translated(caption):
                if isinstance(caption, str):
                    return caption

                return caption.tokenize(**COLOR_SCHEME).get_string(language)

            for i, game_class in enumerate(_available_game_classes, start=1):
                lines.append(
                    "{}. *** GAME CLASS: {} (caption: {}) ***".format(
                        i,
                        game_class.__name__,
                        translated(game_class.caption),
                    )
                )

                lines.append("Available launchers for the "
                             "current number of alive "
                             "prisoners ({}):".format(len(players)))

                for j, game_launcher in enumerate(
                    game_class.get_available_launchers(
                        admin.player, players
                    ),
                    start=1
                ):

                    lines.append("{}.{}. {}".format(
                        i, j, translated(game_launcher.caption)))

                    denial_reason = game_launcher.get_launch_denial_reason(
                        admin.player, players)

                    if denial_reason is not None:
                        denial_reason = translated(denial_reason)

                    lines.append("Launch denial reason: {}".format(
                        denial_reason
                    ))

                lines.append("")

            try:
                with open(ARCJAIL_LOG_PATH / "available-games.txt", "w") as f:
                    f.write("\n".join(lines))

                tell(
                    admin.player,
                    strings_module[
                        'arcadmin dump_available_games saved'
                    ].tokenize(
                        file=ARCJAIL_LOG_PATH / "available-games.txt"
                    )
                )

            except OSError:
                tell(admin.player,
                     strings_module['arcadmin dump_available_games failed'])

    games_section = section.add_child(
        Section, strings_module['arcadmin section'])

    games_section.add_child(
        PrintAvailableGames,
        strings_module['arcadmin option dump_available_games'],
        'jail.debug', 'available-games-list'
    )


# =============================================================================
# >> DECORATORS
# =============================================================================
def stage(stage_id):
    def stage_gen(func):
        stage_ = Stage(stage_id)
        stage_.callback = func
        return stage_
    return stage_gen


class Stage:
    def __init__(self, stage_id):
        self.stage_id = stage_id
        self.callback = None
        self.game_instance = None

    def __call__(self, *args, **kwargs):
        if self.callback is not None:
            self.callback(self.game_instance, *args, **kwargs)


def game_event_handler(alias, event):
    def decorator(func):
        game_event_handler_ = GameEventHandler(alias, event)
        game_event_handler_.callback = func
        return game_event_handler_
    return decorator


class GameEventHandler:
    def __init__(self, alias, event):
        self.alias = alias
        self.event = event
        self.callback = None
        self.game_instance = None

    def __call__(self, event_data):
        if self.callback is not None:
            self.callback(self.game_instance, event_data)

    def __eq__(self, other):
        if not isinstance(other, GameEventHandler):
            return False

        return (
            (self.game_instance, self.callback) ==
            (other.game_instance, other.callback)
        )


def game_internal_event_handler(alias, event):
    def decorator(func):
        game_internal_event_handler_ = GameInternalEventHandler(alias, event)
        game_internal_event_handler_.callback = func
        return game_internal_event_handler_
    return decorator


class GameInternalEventHandler:
    def __init__(self, alias, event):
        self.alias = alias
        self.event = event
        self.callback = None
        self.game_instance = None

    def __call__(self, event_data):
        if self.callback is not None:
            self.callback(self.game_instance, event_data)


class Push:
    def __init__(self, slot_id, push_id):
        self.slot_id = slot_id
        self.push_id = push_id
        self.callback = None
        self.game_instance = None

    def __call__(self, args):
        if self.callback is not None:
            self.callback(self.game_instance, args)


def push(slot_id, push_id):
    def decorator(func):
        push_ = Push(slot_id, push_id)
        push_.callback = func
        return push_
    return decorator


# =============================================================================
# >> METACLASS
# =============================================================================
class GameMeta(type):
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        cls._stages_map = {}
        cls._internal_events = {}
        cls._events = {}
        cls._stage_groups = {}
        for base in bases[::-1]:
            cls._events.update(base._events)
            cls._stages_map.update(base._stages_map)
            cls._stage_groups.update(base._stage_groups)

        for key, value in namespace.items():
            if isinstance(value, Stage):
                cls._stages_map[value.stage_id] = value

            elif isinstance(value, GameInternalEventHandler):
                cls._internal_events[value.alias] = value

            elif isinstance(value, GameEventHandler):
                cls._events[value.alias] = value

            elif key == 'stage_groups':
                cls._stage_groups.update(value)

        return cls


# =============================================================================
# >> BASE CLASSES IMPORT
# =============================================================================
from . import base_classes


# =============================================================================
# >> SUBMODULES IMPORT
# =============================================================================
current_dir = os.path.dirname(__file__)
__all__ = parse_modules(current_dir)

from . import *

# =============================================================================
# >> GAMES IMPORT
# =============================================================================
from . import game_classes
