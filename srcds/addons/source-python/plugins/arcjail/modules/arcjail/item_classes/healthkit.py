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

from ..item_instance import BaseItemInstance

from . import register_item_instance_class


strings_module = build_module_strings('arcjail/items/healthkit')


class Healthkit(BaseItemInstance):
    manual_activation = True

    def try_activate(self, player, amount, async=True):
        if self['health_mode'] == "set":
            if player.health >= self['health_restored']:
                return strings_module['fail youre_full_health']

            player.health = self['health_restored']

        elif self['health_mode'] == "add":
            player.health += self['health_restored']

        return super().try_activate(player, amount, async)

register_item_instance_class('healthkit', Healthkit)
