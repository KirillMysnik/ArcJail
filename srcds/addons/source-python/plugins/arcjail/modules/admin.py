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

from warnings import warn

from core.manager import core_plugin_manager

from ..internal_events import InternalEvent
from ..resource.strings import build_module_strings


class ArcAdminNotInstalledWarning(Warning):
    pass


strings_module = build_module_strings('admin')


if core_plugin_manager.is_loaded('arcadmin'):
    from arcadmin.classes.menu import popup_main, Section
    section = popup_main.add_child(Section, strings_module['popup title'])

    @InternalEvent('unload')
    def on_unload():
        popup_main.remove(section)

else:
    warn(ArcAdminNotInstalledWarning("ArcAdmin has not been available by the "
                                     "time ArcJail loads, jail admin features "
                                     "won't be available too"))

    section = None
