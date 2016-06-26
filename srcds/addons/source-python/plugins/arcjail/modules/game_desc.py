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

from engines.server import server_game_dll

from memory import get_virtual_function
from memory.hooks import PreHook

from ..info import info


ARCJAIL_DESCRIPTION = "{} {}".format(info.name, info.version)


@PreHook(get_virtual_function(server_game_dll, 'GetGameDescription'))
def pre_get_game_description(args):
    return ARCJAIL_DESCRIPTION
