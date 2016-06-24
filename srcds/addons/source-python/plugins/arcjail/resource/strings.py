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

import os

from colors import Color
from core import GAME_NAME

from advanced_ts import BaseLangStrings

from ..info import info


if GAME_NAME in ('csgo', ):
    COLOR_SCHEME = {
        'color_tag': "\x01",
        'color_highlight': "\x10",
        'color_default': "\x01",
        'color_error': "\x02",
        'color_warning': "\x02",
        'color_credits': "\x04",
    }

else:
    # Map color variables in translation files to actual Color instances
    COLOR_SCHEME = {
        'color_tag': Color(242, 242, 242),
        'color_highlight': Color(255, 137, 0),
        'color_default': Color(242, 242, 242),
        'color_error': Color(255, 54, 54),
        'color_warning': Color(255, 54, 54),
        'color_credits': Color(0, 220, 55),
    }


strings_common = BaseLangStrings(os.path.join(info.basename, "common"))


def build_module_strings(module):
    return BaseLangStrings(os.path.join(info.basename, 'modules', module))
