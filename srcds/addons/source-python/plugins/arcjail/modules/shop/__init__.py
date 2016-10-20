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

from controlled_cvars.handlers import sound_nullable_handler

from ...arcjail import load_downloadables
from ...resource.strings import build_module_strings

from .. import build_module_config


strings_module = build_module_strings('shop/common')
_downloadables = load_downloadables('shop-sounds.res')
config_manager = build_module_config('shop')

config_manager.controlled_cvar(
    sound_nullable_handler,
    "checkout_sound",
    default="arcjail/checkout.mp3",
    description="Checkout sound",
)


import os

from .. import parse_modules


current_dir = os.path.dirname(__file__)
__all__ = parse_modules(current_dir)


from . import *
