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

from effects.base import TempEntity
from engines.precache import Model
from entities.constants import DamageTypes
from entities.entity import Entity
from entities.helpers import edict_from_index, index_from_inthandle
from filters.recipients import RecipientFilter
from listeners import on_entity_spawned_listener_manager

from ....resource.strings import build_module_strings

from ...damage_hook import (
    get_hook, is_world, protected_player_manager,
    strings_module as strings_damage_hook)

from ...equipment_switcher import (
    register_weapon_pickup_filter, saved_player_manager,
    unregister_weapon_pickup_filter)

from ...players import main_player_manager

from ...rebels import register_rebel_filter

from ...show_damage import show_damage

from ...teams import GUARDS_TEAM

from .. import add_available_game, stage

from ..antiflash import (
    register_detonation_filter, unregister_detonation_filter)

from .survival import SurvivalPlayerBasedFriendlyFire
from .survival import SurvivalTeamBasedFriendlyFire


FLASHBANG_CLASSNAME = "weapon_flashbang"
BEAM_MODEL = Model('sprites/laserbeam.vmt')


strings_module = build_module_strings('games/survival_flashbang_arena')


class SurvivalFlashbangArenaPlayerBased(SurvivalPlayerBasedFriendlyFire):
    _caption = strings_module['title playerbased']
    module = 'survival_flashbang_arena_playerbased'
    stage_groups = {
                       'mapgame-start': [
                           "mapgame-equip-weapons",
                           "mapgame-register-push-handlers",
                           "mapgame-apply-cvars",
                           "mapgame-fire-mapdata-outputs",
                           "survival-enable-ff",
                           "survival-flashbang-arena-register-filter",
                           "survival-flashbang-arena-register-listener",
                           "mapgame-entry",
                       ],
    }

    def _weapon_pickup_filter(self, player, weapon_index):
        if player not in self._players:
            return True

        weapon_classname = edict_from_index(weapon_index).classname
        return weapon_classname == FLASHBANG_CLASSNAME

    def detonation_filter(self, entity):
        try:
            owner_index = index_from_inthandle(entity.owner)
        except (OverflowError, ValueError):
            return True

        for player in self._players:
            if player.index == owner_index:
                return False

        return True

    def listener_on_entity_spawned(self, index, base_entity):
        if base_entity.classname != 'flashbang_projectile':
            return

        try:
            owner_index = index_from_inthandle(Entity(index).owner)
        except (OverflowError, ValueError):
            return

        for player in self._players:
            if player.index == owner_index:
                break
        else:
            return

        temp_entity = TempEntity('BeamFollow')
        temp_entity.entity_index = index
        temp_entity.model_index = BEAM_MODEL.index
        temp_entity.halo_index = BEAM_MODEL.index
        temp_entity.life_time = 1
        temp_entity.start_width = 3
        temp_entity.end_width = 3
        temp_entity.fade_length = 1
        temp_entity.red = 255
        temp_entity.green = 255
        temp_entity.blue = 255
        temp_entity.alpha = 150

        temp_entity.create(RecipientFilter())

    @stage('survival-flashbang-arena-register-filter')
    def stage_survival_flashbang_arena_register_hooks(self):
        register_detonation_filter(self.detonation_filter)

    @stage('undo-survival-flashbang-arena-register-filter')
    def undo_stage_survival_flashbang_arena_register_hooks(self):
        unregister_detonation_filter(self.detonation_filter)

    @stage('survival-flashbang-arena-register-listener')
    def stage_survival_flashbang_arena_register_listener(self):
        on_entity_spawned_listener_manager.register_listener(
            self.listener_on_entity_spawned)

    @stage('undo-survival-flashbang-arena-register-listener')
    def undo_stage_survival_flashbang_arena_register_listener(self):
        on_entity_spawned_listener_manager.unregister_listener(
            self.listener_on_entity_spawned)

    @stage('survival-equip-damage-hooks')
    def stage_survival_equip_damage_hooks(self):
        def hook_enemy_p(counter, info):
            victim = counter.owner.player

            if info.attacker == victim.index or is_world(info.attacker):
                return False

            attacker = main_player_manager[info.attacker]

            if attacker in self._players:
                show_damage(attacker, info.damage)

                # Initial (DamageTypes.CLUB) type doesn't do any actual damage
                info.type = DamageTypes.BLAST

                return True

            return False

        def hook_sw_enemy_p(counter, info):
            victim = counter.owner.player

            if info.attacker == victim.index or is_world(info.attacker):
                return True

            attacker = main_player_manager[info.attacker]

            if attacker in self._players:
                show_damage(attacker, info.damage)

                # Initial (DamageTypes.CLUB) type doesn't do any actual damage
                info.type = DamageTypes.BLAST

                return True

            return False

        for player in main_player_manager.values():
            if player.dead:
                continue

            p_player = protected_player_manager[player.index]
            self._counters[player.index] = []
            if player in self._players:
                counter1 = p_player.new_counter(
                    display=strings_damage_hook['health against_guards'])

                counter1.hook_hurt = get_hook('G')

                counter2 = p_player.new_counter(
                    display=strings_damage_hook['health game'])

                if self.map_data['ALLOW_SELFDAMAGE']:
                    counter2.hook_hurt = hook_sw_enemy_p

                else:
                    counter2.hook_hurt = hook_enemy_p

                counter2.health = self.map_data['INITIAL_HEALTH']

                self._counters[player.index].append(counter1)
                self._counters[player.index].append(counter2)

            elif player.team == GUARDS_TEAM:
                counter = p_player.new_counter()
                if self.map_data['ALLOW_REBELLING']:
                    counter.hook_hurt = get_hook('SWP')
                    counter.display = strings_damage_hook[
                        'health against_prisoners']

                else:
                    counter.hook_hurt = get_hook('SW')
                    counter.display = strings_damage_hook['health general']

                self._counters[player.index].append(counter)

            p_player.set_protected()

        if not self.map_data['ALLOW_REBELLING']:
            def rebel_filter(player):
                return player not in self._players_all

            self._rebel_filter = rebel_filter
            register_rebel_filter(rebel_filter)

    @stage('mapgame-equip-weapons')
    def stage_mapgame_equip_weapons(self):
        """Equip players with weapons."""

        for player in self._players_all:
            equipment_player = saved_player_manager[player.index]
            equipment_player.save_weapons()

            equipment_player.infinite_weapons.clear()
            player.give_named_item(FLASHBANG_CLASSNAME, 0)
            equipment_player.infinite_weapons.append(FLASHBANG_CLASSNAME)

            equipment_player.infinite_on()

        register_weapon_pickup_filter(self._weapon_pickup_filter)

    @stage('undo-mapgame-equip-weapons')
    def stage_undo_mapgame_equip_weapons(self):
        """Restore player's original equipment."""

        # Important: unregister weapon pickup filter BEFORE
        # restoring player's weapons!
        unregister_weapon_pickup_filter(self._weapon_pickup_filter)

        for player in self._players_all:
            equipment_player = saved_player_manager[player.index]

            if player in self._players:
                equipment_player.restore_weapons()

            equipment_player.infinite_off()

add_available_game(SurvivalFlashbangArenaPlayerBased)
