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

from core import PLATFORM
from engines.server import global_vars
from memory import Convention, DataType, find_binary, NULL


if PLATFORM == 'windows':
    DISSOLVE_IDENTIFIER = b'\x55\x8B\xEC\x80\x7D\x10\x00\x56\x57\x8B\xF1\x74\x14'
else:
    DISSOLVE_IDENTIFIER = "_ZN14CBaseAnimating8DissolveEPKcfbi6Vectori"

server = find_binary('server')

dissolve_srv = server[DISSOLVE_IDENTIFIER].make_function(
    Convention.THISCALL,
    (
        DataType.POINTER,
        DataType.POINTER,
        DataType.FLOAT,
        DataType.BOOL,
        DataType.INT,
        DataType.POINTER,
        DataType.INT
    ),
    DataType.BOOL
)


def dissolve(entity, type_=0):
    dissolve_srv(
        entity.pointer, NULL,
        global_vars.current_time,
        False, type_, entity.origin, 2
    )
