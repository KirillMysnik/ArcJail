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

from filters.players import PlayerIter
from listeners.tick import Delay

from controlled_cvars.handlers import sound_nullable_handler

from ....resource.strings import build_module_strings

from ... import build_module_config

from ...players import broadcast

from ..item_instance import BaseItemInstance

from . import register_item_instance_class


strings_module = build_module_strings('arcjail/items/party_for_everybody')
config_manager = build_module_config('arcjail/items/party_for_everybody')

config_manager.controlled_cvar(
    sound_nullable_handler,
    "sound",
    default="arcjail/party_for_everybody.mp3",
    description="Party For Everybody sound",
)


class PartyForEverybody(BaseItemInstance):
    manual_activation = True

    def try_activate(self, player, amount, async=True):
        reason = super().try_activate(player, amount, async)
        if reason is not None:
            return reason

        broadcast(strings_module['announcement'].tokenize(
            player=player.name,
            caption=self.caption,
        ))

        config_manager['sound'].play()

        def party():
            for player_ in PlayerIter(['alive'], ['spec', 'un']):
                player_.give_named_item(self['entity_to_give'], 0)

        Delay(self.get('delay', 0), party)

        return None

register_item_instance_class('party_for_everybody', PartyForEverybody)
