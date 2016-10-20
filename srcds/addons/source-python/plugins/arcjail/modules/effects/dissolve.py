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
from entities.constants import DissolveType
from memory import Convention, DataType


if PLATFORM == 'windows':
    DISSOLVE_INDEX = 230
else:
    DISSOLVE_INDEX = 231


def dissolve(entity, type_=DissolveType.NORMAL):
    entity.pointer.make_virtual_function(
        DISSOLVE_INDEX,
        Convention.THISCALL,
        (
            DataType.POINTER,
            DataType.STRING,
            DataType.FLOAT,
            DataType.BOOL,
            DataType.INT,
            DataType.POINTER,
            DataType.INT
        ),
        DataType.BOOL
    )(entity.pointer, "", global_vars.current_time, False, type_,
      entity.origin, 2)
