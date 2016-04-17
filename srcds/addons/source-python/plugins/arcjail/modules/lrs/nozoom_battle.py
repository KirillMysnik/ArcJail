from entities.entity import Entity
from entities.helpers import index_from_inthandle
from listeners.tick import on_tick_listener_manager

from ...resource.strings import build_module_strings

from . import (
    add_available_game, config_manager, Setting, SettingOption, stage,
    strings_module as strings_common)

from .base_classes.combat_game import CombatGame


strings_module = build_module_strings('lrs/nozoom_battle')


class NozoomBattle(CombatGame):
    caption = strings_module['title']
    module = "nozoom_battle"
    settings = [
        Setting('health', strings_module['settings hp'],
                SettingOption(1, strings_module['setting 1hp']),
                SettingOption(100, strings_module['setting 100hp'], True),
                ),
        Setting('weapons', strings_module['settings weapons'],
                SettingOption(("weapon_awp", ), "AWP", True),
                SettingOption(("weapon_scout", ), "Scout"),
                SettingOption(("weapon_sg550", ), "SG-550"),
                SettingOption(("weapon_g3sg1", ), "G3/SG-1"),
                ),
        Setting('using_map_data', strings_common['settings map_data'],
                SettingOption(
                    True, strings_common['setting map_data yes'], True),
                SettingOption(False, strings_common['setting map_data no']),
                ),
    ]

    @stage('mapgame-entry')
    def stage_mapgame_entry(self):
        if config_manager['combat_lr_start_sound'] is not None:
            indexes = (self.prisoner.index, self.guard.index)
            config_manager['combat_lr_start_sound'].play(*indexes)

        on_tick_listener_manager.register_listener(self._nozoom_tick_handler)

    @stage('undo-mapgame-entry')
    def stage_undo_mapgame_entry(self):
        on_tick_listener_manager.unregister_listener(self._nozoom_tick_handler)

    def _nozoom_tick_handler(self):
        for player in self._players:
            try:
                weapon_index = index_from_inthandle(player.active_weapon)
            except (OverflowError, ValueError):
                continue

            weapon = Entity(weapon_index)
            weapon.next_secondary_fire_attack += 1


add_available_game(NozoomBattle)
