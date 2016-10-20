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

from contextlib import suppress
from random import shuffle

from cvars import ConVar
from entities.constants import INVALID_ENTITY_INDEX
from entities.entity import Entity
from entities.helpers import edict_from_index

from ...games import Push
from ...games.base_classes.map_game import DEFAULT_GRAVITY

from ...equipment_switcher import (
    register_weapon_drop_filter, register_weapon_pickup_filter,
    saved_player_manager, unregister_weapon_drop_filter,
    unregister_weapon_pickup_filter)

from ...falldmg_protector import unprotect

from ...jail_map import (
    get_games, get_map_string, register_push_handler, teleport_player,
    unregister_push_handler)

from ...noblock import lock as lock_noblock
from ...noblock import unlock as unlock_noblock
from ...noblock import set_default, set_force_off, set_force_on

from ...players import broadcast

from ...silent_cvars import silent_set

from ...team_balancer import lock_teams, unlock_teams

from ...teams import GUARDS_TEAM, PRISONERS_TEAM

from .. import GameLauncher, stage, strings_game_captions, strings_module

from .prepare_time import PrepareTime


class MapGame(PrepareTime):
    cvar_pushscale = ConVar('phys_pushscale')
    cvar_timescale = ConVar('phys_timescale')
    cvar_gravity = ConVar('sv_gravity')

    stage_groups = {
        'abort-map-cancelled': ["abort-map-cancelled", ],
        'mapgame-prepare': [
            "mapgame-cancel-falldmg-protection",
            "mapgame-equip-noblock",
            "mapgame-swap-guard",
            "mapgame-teleport-players",
            "mapgame-fire-mapdata-prepare-outputs",
            "mapgame-prepare-entry",
        ],
        'mapgame-start': [
            # "mapgame-equip-weapons",    # If you need mapgame-equip-weapons,
                                          # declare this stage manually in
                                          # your game class.
            "mapgame-register-push-handlers",
            "mapgame-apply-cvars",
            "mapgame-fire-mapdata-outputs",
            "mapgame-entry",
        ],
    }

    class GameLauncher(GameLauncher):
        def __init__(self, game_class, map_data):
            if map_data.caption:
                try:
                    self.caption = get_map_string(map_data.caption)
                except KeyError:
                    try:
                        self.caption = strings_game_captions[map_data.caption]
                    except KeyError:
                        self.caption = game_class._caption
            else:
                self.caption = game_class._caption

            self.game_class = game_class
            self.map_data = map_data

        def __eq__(self, other):
            return (self.game_class, self.map_data) == (
                other.game_class, other.map_data)

        def launch(self, players, **kwargs):
            kwargs['map_data'] = self.map_data
            game_instance = self.game_class(players, **kwargs)
            return game_instance

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self._pushes = {}
        self._cvars = {
            'pushscale': 1,
            'timescale': 1,
            'gravity': DEFAULT_GRAVITY,
        }
        self.map_data = kwargs['map_data']

        for attr_name in dir(self):
            try:  # Be ready for undefined (undefined yet) attributes
                attr = getattr(self, attr_name)
            except AttributeError:
                continue

            if not isinstance(attr, Push):
                continue

            attr.game_instance = self
            self._pushes[(attr.slot_id, attr.push_id)] = attr

    @property
    def caption(self):
        if self.map_data.caption:
            try:
                return get_map_string(self.map_data.caption)
            except KeyError:
                try:
                    return strings_game_captions[self.map_data.caption]
                except KeyError:
                    return self._caption
        return self._caption

    def _weapon_drop_filter(self, player):
        return player not in self._players

    def _weapon_pickup_filter(self, player, weapon_index):
        if player not in self._players:
            return True

        weapon_classname = edict_from_index(weapon_index).classname
        return weapon_classname in self.map_data['ARENA_EQUIPMENT']

    @stage('abort-map-cancelled')
    def stage_abort_map_cancelled(self):
        broadcast(strings_module['abort map_cancelled'])
        self.set_stage_group('destroy')

    @stage('mapgame-swap-guard')
    def stage_mapgame_swap_guard(self):
        lock_teams()
        Entity(self.guard.index).team = PRISONERS_TEAM

    @stage('undo-mapgame-swap-guard')
    def stage_undo_mapgame_swap_guard(self):
        # TODO: Is this the correct way to check if player is connected?
        if self.guard.index != INVALID_ENTITY_INDEX:
            Entity(self.guard.index).team = GUARDS_TEAM

        unlock_teams()

    @stage('mapgame-cancel-falldmg-protection')
    def stage_mapgame_cancel_falldmg_protection(self):
        """Cancel any falldmg protections previous games might have set."""
        for player in self._players:
            with suppress(ValueError):
                unprotect(player)

    @stage('mapgame-register-push-handlers')
    def stage_mapgame_register_push_handlers(self):
        """Register push handlers."""
        for (slot_id, push_id), push_ in self._pushes.items():
            if slot_id is None:
                slot_id = 'slot-gameslot-{}'.format(self.map_data.slot_id)

            register_push_handler(slot_id, push_id, push_)

    @stage('undo-mapgame-register-push-handlers')
    def stage_undo_mapgame_register_push_handlers(self):
        """Unregister push handlers."""
        for (slot_id, push_id), push_ in self._pushes.items():
            if slot_id is None:
                slot_id = 'slot-gameslot-{}'.format(self.map_data.slot_id)

            unregister_push_handler(slot_id, push_id, push_)

    @stage('mapgame-apply-cvars')
    def stage_mapgame_apply_cvars(self):
        """Save current cvar values and apply our own values."""
        self._cvars['pushscale'] = self.cvar_pushscale.get_float()
        self._cvars['timescale'] = self.cvar_timescale.get_float()
        self._cvars['gravity'] = self.cvar_gravity.get_float()

        pushscale = self.map_data['PUSHSCALE']
        timescale = max(0, self.map_data['TIMESCALE'])
        gravity = self.map_data['GRAVITY']

        if self.map_data['PUSHSCALE_OVERRIDE']:
            self.cvar_pushscale.set_float(pushscale)

        if self.map_data['TIMESCALE_OVERRIDE']:
            self.cvar_timescale.set_float(timescale)

        if self.map_data['GRAVITY_OVERRIDE']:
            # Now for sv_graivty we are going to perform a silent change
            silent_set(self.cvar_gravity, 'float', gravity)

    @stage('undo-mapgame-apply-cvars')
    def stage_undo_mapgame_apply_cvars(self):
        """Restore cvars to their original values."""
        self.cvar_pushscale.set_float(self._cvars['pushscale'])
        self.cvar_timescale.set_float(self._cvars['timescale'])
        silent_set(self.cvar_gravity, 'float', self._cvars['gravity'])

    @stage('mapgame-equip-noblock')
    def stage_mapgame_equip_noblock(self):
        """Force noblock on or off if needed."""
        noblock = self.map_data['ENABLE_NOBLOCK'] in (1, -1)
        lock_noblock()

        if noblock:
            for player in self._players:
                set_force_on(player)

        else:
            for player in self._players:
                set_force_off(player)

    @stage('undo-mapgame-equip-noblock')
    def stage_undo_mapgame_equip_noblock(self):
        """Restore noblock setting to its default value."""
        unlock_noblock()
        for player in self._players_all:
            set_default(player)

    @stage('mapgame-fire-mapdata-prepare-outputs')
    def stage_mapgame_fire_mapdata_prepare_outputs(self):
        """Fire OnPrepare output on controller entity."""
        self.map_data.prepare()

    @stage('mapgame-fire-mapdata-outputs')
    def stage_mapgame_fire_mapdata_outputs(self):
        """Fire OnStart and OnLastRequestStart outputs on controller entity."""
        self.map_data.start()
        self.map_data.last_request_start()

    @stage('undo-mapgame-fire-mapdata-outputs')
    def stage_undo_mapgame_fire_mapdata_outputs(self):
        """Fire OnEnd output on controller entity."""
        # TODO: Maybe this should be a standalone stage?
        self.map_data.end()

    @stage('mapgame-teleport-players')
    def stage_mapgame_teleport_players(self):
        """Teleport players and game leader."""
        spawnpoints = list(self.map_data.get_spawnpoints('team1'))
        shuffle(spawnpoints)

        for player in self._players:
            teleport_player(player, spawnpoints.pop())

    @stage('mapgame-equip-weapons')
    def stage_mapgame_equip_weapons(self):
        """Equip players with weapons."""
        if not self.map_data['ENABLE_EQUIPMENT']:
            return

        for player in self._players_all:
            equipment_player = saved_player_manager[player.index]
            equipment_player.save_weapons()

            equipment_player.infinite_weapons.clear()
            for weapon_classname in self.map_data['ARENA_EQUIPMENT']:
                player.give_named_item(weapon_classname)
                equipment_player.infinite_weapons.append(weapon_classname)

            equipment_player.infinite_on()

        register_weapon_drop_filter(self._weapon_drop_filter)
        register_weapon_pickup_filter(self._weapon_pickup_filter)

    @stage('undo-mapgame-equip-weapons')
    def stage_undo_mapgame_equip_weapons(self):
        """Restore player's original equipment."""
        if not self.map_data['ENABLE_EQUIPMENT']:
            return

        unregister_weapon_drop_filter(self._weapon_drop_filter)

        # Important: unregister weapon pickup filter BEFORE
        # restoring player's weapons!
        unregister_weapon_pickup_filter(self._weapon_pickup_filter)

        for player in self._players_all:
            equipment_player = saved_player_manager[player.index]

            if player in self._players:
                equipment_player.restore_weapons()

            equipment_player.infinite_off()

    @stage('prepare-entry')
    def stage_prepare_entry(self):
        self.insert_stage_group('mapgame-prepare')

    @stage('basegame-entry')
    def stage_basegame_entry(self):
        self.set_stage_group('mapgame-start')

    @stage('mapgame-entry')
    def stage_mapgame_entry(self):
        pass

    @stage('mapgame-prepare-entry')
    def stage_mapgame_prepare_entry(self):
        pass

    @classmethod
    def get_available_launchers(cls):
        result = []
        for map_data in get_games(cls.module):
            p_min = map_data['MIN_PLAYERS']
            p_max = map_data['MAX_PLAYERS']

            if (len(map_data.get_spawnpoints('team1')) >= 2 >= p_min and
                    (p_max == -1 or 2 <= p_max)):

                result.append(cls.GameLauncher(cls, map_data))

        return result
