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

from time import time

from listeners.tick import TickRepeat

from controlled_cvars.handlers import int_handler

from ...resource.strings import build_module_strings

from .. import build_module_config
from ..arcjail.arcjail_user import arcjail_user_manager
from ..arcjail.item_classes import get_item_instance
from ..players import tell


CHECK_INTERVAL = 30


strings_module = build_module_strings('shop/online_rewards')
config_manager = build_module_config('shop/online_rewards')

config_manager.controlled_cvar(
    int_handler,
    'timeout',
    default=1800,
    description="Reward constantly playing players every X seconds"
)


def check_rewards():
    current_time = time()
    for arcjail_user in arcjail_user_manager.values():
        if not arcjail_user.loaded:
            continue

        if (current_time - arcjail_user.last_online_reward <
                config_manager['timeout']):

            continue

        arcjail_user.last_online_reward = current_time
        arcjail_user.give_item('gift', 'online_reward', amount=1, async=True)

        item_instance = get_item_instance('gift', 'online_reward')
        tell(arcjail_user.player, strings_module['reward_received'],
             caption=item_instance.caption)

_tick_repeat = TickRepeat(check_rewards).start(CHECK_INTERVAL, limit=0)
