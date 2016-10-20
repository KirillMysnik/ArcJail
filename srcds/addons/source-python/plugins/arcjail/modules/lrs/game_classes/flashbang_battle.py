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
from entities.entity import Entity
from filters.recipients import RecipientFilter
from listeners import on_entity_spawned_listener_manager

from ....resource.strings import build_module_strings

from ...games.antiflash import (
    register_detonation_filter, unregister_detonation_filter)
from ...players import tell

from .. import (
    add_available_game, HiddenSetting, Setting, SettingOption, stage,
    strings_module as strings_common)
from ..base_classes.combat_game import CombatGame


BEAM_MODEL = Model('sprites/laserbeam.vmt')


strings_module = build_module_strings('lrs/flashbang_battle')


class FlashbangBattle(CombatGame):
    _caption = strings_module['title']
    module = "flashbang_battle"
    settings = [
        HiddenSetting('health', 1),
        HiddenSetting('weapons', ('weapon_flashbang', )),
        Setting('trails', strings_module['settings trails'],
                SettingOption(
                    True, strings_module['setting trails yes'], True),
                SettingOption(False, strings_module['setting trails no']),
                ),
        Setting('using_map_data', strings_common['settings map_data'],
                SettingOption(
                    True, strings_common['setting map_data yes'], True),
                SettingOption(False, strings_common['setting map_data no']),
                ),
    ]

    @stage('combatgame-entry')
    def stage_combatgame_entry(self):
        tell(self.prisoner, strings_module['aim'].tokenize(
            player=self.guard.name))

        tell(self.guard, strings_module['aim'].tokenize(
            player=self.prisoner.name))

        # We don't need no flawless effects in a 1-hit game
        self._flawless = {
            self.prisoner.index: False,
            self.guard.index: False,
        }

        register_detonation_filter(self.detonation_filter)

        if self._settings['trails']:
            on_entity_spawned_listener_manager.register_listener(
                self.listener_on_entity_spawned)

    @stage('undo-combatgame-entry')
    def stage_undo_combatgame_entry(self):
        unregister_detonation_filter(self.detonation_filter)

        if self._settings['trails']:
            on_entity_spawned_listener_manager.unregister_listener(
                self.listener_on_entity_spawned)

    def detonation_filter(self, entity):
        return entity.owner_handle not in (
            self.prisoner.inthandle, self.guard.inthandle)

    def listener_on_entity_spawned(self, base_entity):
        if base_entity.classname != 'flashbang_projectile':
            return

        index = base_entity.index
        entity = Entity(index)

        if entity.owner_handle not in (
                self.prisoner.inthandle, self.guard.inthandle):

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
        temp_entity.blue  = 255
        temp_entity.alpha = 150

        temp_entity.create(RecipientFilter())

add_available_game(FlashbangBattle)
