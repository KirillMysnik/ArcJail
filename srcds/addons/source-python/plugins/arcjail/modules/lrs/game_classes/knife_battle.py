from ....resource.strings import build_module_strings

from .. import (
    add_available_game, HiddenSetting, Setting, SettingOption,
    strings_module as strings_common)

from ..base_classes.combat_game import CombatGame


strings_module = build_module_strings('lrs/knife_battle')


class KnifeBattle(CombatGame):
    caption = strings_module['title']
    module = "knife_battle"
    settings = [
        Setting('health', strings_module['settings hp'],
                SettingOption(35, strings_module['setting 35hp']),
                SettingOption(100, strings_module['setting 100hp'], True),
                ),
        Setting('using_map_data', strings_common['settings map_data'],
                SettingOption(
                    True, strings_common['setting map_data yes'], True),
                SettingOption(False, strings_common['setting map_data no']),
                ),
        HiddenSetting('weapons', ('weapon_knife', )),
    ]


add_available_game(KnifeBattle)
