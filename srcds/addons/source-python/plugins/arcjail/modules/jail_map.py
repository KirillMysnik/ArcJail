from json import load as json_load
from warnings import warn

from engines.server import global_vars

from ..classes.geometry import Point, Vector, Plane, ConvexArea
from ..classes.meta_parser import MetaParser
from ..classes.string_values import value_from_string

from ..resource.paths import ARCJAIL_DATA_PATH, MAPDATA_PATH

from .ent_fire import new_output_connection


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
map_strings = None


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
    for game in MapData.games.values():
        game.destroy_connections()

    for lr in MapData.lrs.values():
        lr.destroy_connections()

    MapData.destroy_connections()
    MapData.reset()

    mapdata_json = MAPDATA_PATH / '{0}.json'.format(global_vars.map_name)
    if not mapdata_json.isfile():
        return

    with open(mapdata_json) as f:
        try:
            data = json_load(f)
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

    # TODO: Add map_strings