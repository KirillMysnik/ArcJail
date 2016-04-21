from entities.entity import Entity
from listeners import on_entity_created_listener_manager
from memory import make_object
from memory.hooks import HookType

from ....arcjail import InternalEvent

from ....resource.strings import build_module_strings

from ...effects.dissolve import dissolve

from ...players import tell

from ..base_classes.combat_game import CombatGame

from .. import (
    add_available_game, config_manager, HiddenSetting, Setting, SettingOption,
    stage, strings_module as strings_common)


strings_module = build_module_strings('lrs/flashbang_battle')


class FlashbangBattle(CombatGame):
    caption = strings_module['title']
    module = "flashbang_battle"
    settings = [
        HiddenSetting('health', 1),
        HiddenSetting('weapons', ('weapon_flashbang', )),
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

    @stage('undo-combatgame-entry')
    def stage_undo_combatgame_entry(self):
        remove_hook_or_stop_waiting(self.pre_detonate)

    @staticmethod
    def pre_detonate(args):
        entity = make_object(Entity, args[0])
        if entity.classname != 'flashbang_projectile':
            return

        dissolve(entity)
        return True


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
