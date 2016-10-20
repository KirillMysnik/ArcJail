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

import json
from traceback import format_exc
from warnings import warn

from commands.server import ServerCommand
from engines.server import global_vars
from events import Event
from mathlib import QAngle, Vector as Vector_MathLib

from path import Path

from advanced_ts import BaseLangStrings

from ..classes.geometry import Point, Vector, ConvexArea
from ..classes.meta_parser import MetaParser
from ..classes.string_values import value_from_string
from ..info import info
from ..internal_events import InternalEvent
from ..resource.paths import (
    ARCJAIL_DATA_PATH, MAPDATA_PATH, MAP_TRANSLATION_PATH)

from .ent_fire import new_output_connection
from .players import player_manager


ORIGIN_OFFSET_Z = 32


class CorruptGameSettings(Exception):
    pass


class CorruptMapData(Exception):
    pass


class InvalidValue(Warning):
    pass


class Area:
    def __init__(self):
        self.structures = []


class Spawnpoint:
    def __init__(self, origin, angles):
        self.origin = tuple(origin)
        self.angles = tuple(angles)


class StageActionGame:
    def __init__(self):
        self.module = None
        self._actions = {
            'OnPrepare': [],
            'OnStart': [],
            'OnEnd': [],
        }

    def set_action(self, output_name, connection_json):
        connection = new_output_connection(connection_json)
        self._actions[output_name].append(connection)

    def prepare(self):
        for connection in self._actions['OnPrepare']:
            connection.fire()

    def start(self):
        for connection in self._actions['OnStart']:
            connection.fire()

    def end(self):
        for connection in self._actions['OnEnd']:
            connection.fire()

    def destroy_connections(self):
        for action_group in self._actions.values():
            for connection in action_group:
                connection.destroy()


class LRGame(StageActionGame):
    def __init__(self):
        super().__init__()
        self.spawnpoints = []


class Game(StageActionGame):
    def __init__(self):
        super().__init__()
        self.caption = None
        self._areas = {
            'generic': [],
            'launch': [],
            'winners': [],
            'losers': []
        }
        self._actions['OnLastRequestStart'] = []
        self._spawnpoints = {}
        self._settings = {}

    def add_spawnpoint(self, team, spawnpoint):
        if team not in self._spawnpoints:
            self._spawnpoints[team] = []

        self._spawnpoints[team].append(spawnpoint)

    def get_spawnpoints(self, team):
        return tuple(self._spawnpoints.get(team, ()))

    def add_area(self, type_, area):
        type_title = {
            0: 'generic',
            1: 'launch',
            2: 'winners',
            3: 'losers',
        }[int(type_)]

        self._areas[type_title].append(area)

    def get_areas(self, type_):
        return tuple(self._areas.get(type_, ()))

    def last_request_start(self):
        for connection in self._actions['OnLastRequestStart']:
            connection.fire()

    def __getitem__(self, key):
        return self._settings[key]

    def __setitem__(self, key, value):
        self._settings[key] = value


_push_handlers = {}
_game_settings = {}
_map_status = 0
_map_strings = None


class MapData:
    settings = {}
    connections = {}

    areas = {}
    lrs = {}
    spawnpoints = {}
    games = {}

    cages = []
    jails = []
    armories = []
    stashes = []
    ct_zones = []

    shop_windows = []

    @classmethod
    def reset(cls):
        cls.settings = {}
        cls.connections = {}

        cls.areas = {}
        cls.lrs = {}
        cls.spawnpoints = {}
        cls.games = {}

        cls.cages = []
        cls.jails = []
        cls.armories = []
        cls.stashes = []
        cls.ct_zones = []

        cls.shop_windows = []

    @classmethod
    def destroy_connections(cls):
        for connections in cls.connections.values():
            for connection in connections:
                connection.destroy()


MapData.reset()


def reload_game_settings():
    _game_settings.clear()

    gamesettings_dat = ARCJAIL_DATA_PATH / 'gamesettings.dat'

    if not gamesettings_dat.isfile():
        raise IOError("Cannot locate gamesettings.dat")

    with open(gamesettings_dat) as f:
        meta = MetaParser(f.read())

    vars = meta['vars']
    if vars is None:
        raise CorruptGameSettings("Corrupt gamesettings.dat")

    vars = vars.strip()
    if not vars:
        return

    for line in vars.split('\n'):
        # NAME:FGD NAME:TYPE:DEFAULT:DESCRIPTION
        pieces = tuple(map(lambda piece: piece.strip(), line.split(':')))

        var = {}
        try:
            var['name'] = pieces[0].upper()
            var['fgd'] = pieces[1].lower() or ('setting_' + var['name'].lower())
            var['type'] = pieces[2].lower()
            var['default'] = value_from_string(pieces[3], var['type'])
            var['desc'] = pieces[4]
        except IndexError:
            raise CorruptGameSettings("Invalid gamesettings.dat structure "
                                      "near '{0}'".format(var['name']))
        except TypeError:
            raise CorruptGameSettings("Invalid gamesettings.dat var type "
                                      "near '{0}'".format(var['name']))

        _game_settings[var['name']] = var


def get_area_by_name(area_name):
    return MapData.areas[area_name]


def get_spawnpoint_by_name(spawnpoint_name):
    return MapData.spawnpoints[spawnpoint_name]


def get_cage_names():
    return tuple(MapData.cages)


def get_jail_names():
    return tuple(MapData.jails)


def reload_map_info():
    MapData.reset()

    mapdata_json = MAPDATA_PATH / '{0}.json'.format(global_vars.map_name)
    if not mapdata_json.isfile():
        return

    with open(mapdata_json) as f:
        try:
            data = json.load(f)
        except:
            raise CorruptMapData("Can't load JSON for {0}!".format(
                mapdata_json
            ))

    for section_name, section in data.items():
        if section_name == 'settings':
            for output_name, connections in section.get('connections', {}).items():
                MapData.connections[output_name] = []
                for connection_json in connections:
                    connection = new_output_connection(connection_json)
                    MapData.connections[output_name].append(connection)

            continue

        if section_name == 'areas':
            for area_name, area in section.items():
                MapData.areas[area_name] = Area()
                for structure in area['structures']:
                    sides = ConvexArea([
                        ConvexArea.ConvexAreaFace(map(
                            lambda p: Point(map(float, p.split())),
                            side[1:-1].split(') (')  # TODO: Use regex here
                        )) for side in structure
                    ])

                    MapData.areas[area_name].structures.append(sides)
            continue

        if section_name == 'spawnpoints':
            for spawnpoint_name, spawnpoint in section.items():
                origin = tuple(map(float, spawnpoint['origin'].split()))
                angles = tuple(map(float, spawnpoint['angles'].split()))
                MapData.spawnpoints[spawnpoint_name] = Spawnpoint(
                    origin, angles)
            continue

        if section_name == 'lrs':
            for game_name, game in section.items():
                MapData.lrs[game_name] = LRGame()
                MapData.lrs[game_name].module = game['module']

                for output_name, connections in game['connections'].items():
                    for connection_json in connections:
                        MapData.lrs[game_name].set_action(
                            output_name, connection_json)

                for spawnpoint_name in game['spawnpoints']:
                    MapData.lrs[game_name].spawnpoints.append(spawnpoint_name)
            continue

        if section_name == 'games':
            for game_name, game in section.items():
                MapData.games[game_name] = Game()
                MapData.games[game_name].module = game['module']
                MapData.games[game_name].slot_id = game['slot_id']
                MapData.games[game_name].caption = game.get('caption')

                for output_name, connections in game['connections'].items():
                    for connection_json in connections:
                        MapData.games[game_name].set_action(
                            output_name, connection_json)

                for team, spawnpoints in game['spawnpoints'].items():
                    for spawnpoint_name in spawnpoints:
                        MapData.games[game_name].add_spawnpoint(
                            team, spawnpoint_name)

                if not game['areas']:
                    raise CorruptMapData(
                        "Game '{0}' lacks its game areas".format(game_name))

                for area in game['areas']:
                    MapData.games[game_name].add_area(
                        area['areatype'], area['name'])

                for setting in _game_settings.values():
                    default_value = setting['default']
                    map_value = game['settings'].get(setting['fgd'], None)

                    if map_value is None:
                        value = default_value
                    else:
                        try:
                            value = value_from_string(
                                map_value, setting['type'])
                        except TypeError:
                            warn(
                                InvalidValue(
                                    "Invalid setting value for '{0}': "
                                    "'{1}'".format(setting['name'], map_value)
                                )
                            )
                            value = default_value

                    MapData.games[game_name][setting['name']] = value

            continue

        if section_name == 'cages':
            for cage_name in section:
                MapData.cages.append(cage_name)
            continue

        if section_name == 'jails':
            for jail_name in section:
                MapData.jails.append(jail_name)
            continue

        if section_name == 'shop_windows':
            MapData.shop_windows.extend(section)
            continue

    global _map_strings

    path = MAP_TRANSLATION_PATH / '{0}.ini'.format(global_vars.map_name)
    if path.isfile():
        _map_strings = BaseLangStrings(
            Path(info.basename) / "maps" / global_vars.map_name)

    else:
        _map_strings = None


def reload_map_scripts():
    # TODO
    pass


def get_map_string(id_):
    if _map_strings is None:
        raise KeyError

    return _map_strings[id_]


def is_shop_window(entity):
    return entity.get_key_value_int('hammerid') in MapData.shop_windows


def is_point_in_area(point, area):
    for structure in area.structures:
        if point in structure:
            return True
    return False


def is_player_in_area(player, area_name):
    area_name = area_name.lower()
    if area_name not in MapData.areas:
        return False

    player_point = Point(tuple(player.origin)) + Vector(0, 0, ORIGIN_OFFSET_Z)
    return is_point_in_area(player_point, MapData.areas[area_name])


def get_player_areas(player):
    rs = []
    player_point = Point(tuple(player.origin)) + Vector(0, 0, ORIGIN_OFFSET_Z)
    for area_name, area in MapData.areas.items():
        if is_point_in_area(player_point, area):
            rs.append(area_name)
    return tuple(rs)


def get_players_in_area(area_name):
    area_name = area_name.lower()
    if area_name not in MapData.areas:
        return []

    rs = []
    for player in player_manager.values():
        player_point = (Point(tuple(player.origin)) +
                        Vector(0, 0, ORIGIN_OFFSET_Z))

        if is_point_in_area(player_point, MapData.areas[area_name]):
            rs.append(player)

    return rs


def teleport_player(player, spawnpoint_name):
    spawnpoint = MapData.spawnpoints[spawnpoint_name]
    player.origin = Vector_MathLib(*spawnpoint.origin)
    player.view_angle = QAngle(*spawnpoint.angles)


def get_map_var(var_name, default=None):
    if var_name in MapData.settings:
        for value in MapData.settings[var_name]:
            return value

    return default


def get_map_var_list(var_name):
    return tuple(MapData.settings.get(var_name, ()))


def get_map_connections(output_name):
    return tuple(MapData.connections.get(output_name, ()))


def register_push_handler(slot_id, push_id, handler):
    if slot_id not in _push_handlers:
        _push_handlers[slot_id] = {}

    if push_id not in _push_handlers[slot_id]:
        _push_handlers[slot_id][push_id] = []

    if handler in _push_handlers[slot_id][push_id]:
        raise ValueError("Cannot register same handler to '{0}' "
                         "push twice".format(push_id))

    _push_handlers[slot_id][push_id].append(handler)


def unregister_push_handler(slot_id, push_id, handler):
    if slot_id not in _push_handlers:
        raise KeyError("Unknown slot id: '{0}'".format(slot_id))

    if push_id not in _push_handlers[slot_id]:
        raise KeyError("Unknown push id: '{0}'".format(push_id))

    if handler not in _push_handlers[slot_id][push_id]:
        raise ValueError("Handler '{0}' is not registered to handle "
                         "{1}.{2} push".format(handler, slot_id, push_id))

    _push_handlers[slot_id][push_id].remove(handler)

    if not _push_handlers[slot_id][push_id]:
        del _push_handlers[slot_id][push_id]

    if not _push_handlers[slot_id]:
        del _push_handlers[slot_id]


def get_games(module):
    return tuple(filter(lambda game: game.module == module,
                        MapData.games.values()))


def get_lrs(module):
    return tuple(filter(lambda game: game.module == module,
                       MapData.lrs.values()))


def get_map_status():
    return _map_status


@Event('server_spawn')
def on_server_spawn(game_event):
    reload_map_info()
    reload_map_scripts()

    for connection in get_map_connections('OnJailMapStart'):
        connection.fire()

    InternalEvent.fire('map_data_ready')


@InternalEvent('load')
def on_load():
    reload_game_settings()
    reload_map_info()
    reload_map_scripts()

    InternalEvent.fire('map_data_ready')


@InternalEvent('jail_game_started')
def on_jail_game_started():
    for connection_string in get_map_var_list('OnJailRoundStart'):
        connection = new_output_connection(connection_string)
        connection.fire()
        connection.destroy()


@ServerCommand('push')
def srv_push(command):
    if len(command) == 1:
        return

    try:
        _, slot_id, push_id, *args = command
    except ValueError:
        return

    if slot_id not in _push_handlers:
        return

    if push_id not in _push_handlers[slot_id]:
        return

    for handler in _push_handlers[slot_id][push_id]:
        try:
            handler(args)
        except:
            warn(Warning("Exception during handling {0}.{1} "
                "push:\n{2}".format(slot_id, push_id, format_exc())))


@ServerCommand('arcjail_reload_map_data')
def srv_arcjail_reload_map_data(command):
    for game in MapData.games.values():
        game.destroy_connections()

    for lr in MapData.lrs.values():
        lr.destroy_connections()

    MapData.destroy_connections()

    reload_map_info()


@ServerCommand('arcjail_reload_map_scripts')
def srv_arcjail_reload_map_scripts(command):
    reload_map_scripts()
