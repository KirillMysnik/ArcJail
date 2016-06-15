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
from entities.helpers import index_from_inthandle
from filters.recipients import RecipientFilter
from listeners import on_entity_created_listener_manager
from listeners import on_entity_spawned_listener_manager
from memory import make_object
from memory.hooks import HookType

from ....arcjail import InternalEvent

from ....resource.strings import build_module_strings

from ...effects.dissolve import dissolve

from ...players import tell

from ..base_classes.combat_game import CombatGame

from .. import (
    add_available_game, HiddenSetting, Setting, SettingOption, stage,
    strings_module as strings_common)


BEAM_MODEL = Model('sprites/laserbeam.vmt')


strings_module = build_module_strings('lrs/flashbang_battle')


class FlashbangBattle(CombatGame):
    caption = strings_module['title']
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
            self.prisoner.userid: False,
            self.guard.userid: False,
        }

        add_hook_or_wait(self.pre_detonate)

        if self._settings['trails']:
            on_entity_spawned_listener_manager.register_listener(
                self.listener_on_entity_spawned)

    @stage('undo-combatgame-entry')
    def stage_undo_combatgame_entry(self):
        remove_hook_or_stop_waiting(self.pre_detonate)

        if self._settings['trails']:
            on_entity_spawned_listener_manager.unregister_listener(
                self.listener_on_entity_spawned)

    def pre_detonate(self, args):
        entity = make_object(Entity, args[0])
        if entity.classname != 'flashbang_projectile':
            return

        try:
            owner_index = index_from_inthandle(entity.owner)
        except (OverflowError, ValueError):
            return

        if owner_index not in (self.prisoner.index, self.guard.index):
            return

        dissolve(entity)
        return True

    def listener_on_entity_spawned(self, index, base_entity):
        if base_entity.classname != 'flashbang_projectile':
            return

        try:
            owner_index = index_from_inthandle(Entity(index).owner)
        except (OverflowError, ValueError):
            return

        if owner_index not in (self.prisoner.index, self.guard.index):
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

add_available_game(FlashbangBattle)


_listener_registered = False
_detonate_func = None
_waiting_hooks = []
_attached_hooks = []


def add_hook_or_wait(hook):
    if _detonate_func is None:
        _waiting_hooks.append(hook)
    else:
        add_hook(hook)


def remove_hook_or_stop_waiting(hook):
    if _detonate_func is None:
        _waiting_hooks.remove(hook)
    else:
        remove_hook(hook)


def add_hook(hook):
    _detonate_func.add_hook(HookType.PRE, hook)
    _attached_hooks.append(hook)


def remove_hook(hook):
    _detonate_func.remove_hook(HookType.PRE, hook)
    _attached_hooks.remove(hook)


@InternalEvent('load')
def on_load(event_var):
    on_entity_created_listener_manager.register_listener(
        listener_on_entity_created)

    global _listener_registered
    _listener_registered = True


@InternalEvent('unload')
def on_unload(event_var):
    global _listener_registered
    if _listener_registered:
        on_entity_created_listener_manager.unregister_listener(
            listener_on_entity_created)

        _listener_registered = False

    if _detonate_func is not None:
        for attached_hook in tuple(_attached_hooks):
            remove_hook(attached_hook)


def listener_on_entity_created(index, base_entity):
    if base_entity.classname != 'flashbang_projectile':
        return

    global _detonate_func
    _detonate_func = Entity(index).detonate

    for waiting_hook in _waiting_hooks:
        add_hook(waiting_hook)

    _waiting_hooks.clear()

    on_entity_created_listener_manager.unregister_listener(
        listener_on_entity_created)

    global _listener_registered
    _listener_registered = False
