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

from ....resource.strings import build_module_strings

from .. import (
    add_available_game, HiddenSetting, Setting, SettingOption,
    strings_module as strings_common)
from ..base_classes.combat_game import CombatGame


strings_module = build_module_strings('lrs/knife_battle')


class KnifeBattle(CombatGame):
    _caption = strings_module['title']
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
