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

from ...arcjail import InternalEvent

from ...resource.strings import build_module_strings

from . import credits_config, earn_credits


strings_module = build_module_strings('credits/lr_win_reward')


@InternalEvent('jail_lr_won')
def on_jail_lr_won(event_var):
    earn_credits(event_var['winner'], int(credits_config['rewards']['lr_win']),
                 strings_module['reason'])
