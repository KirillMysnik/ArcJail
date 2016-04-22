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

from cvars.flags import ConVarFlags


def silent_set(cvar, type_, value):
    if cvar.is_flag_set(ConVarFlags.NOTIFY):
        cvar.remove_flags(ConVarFlags.NOTIFY)
        getattr(cvar, 'set_{}'.format(type_))(value)
        cvar.add_flags(ConVarFlags.NOTIFY)

    else:
        getattr(cvar, 'set_{}'.format(type_))(value)
