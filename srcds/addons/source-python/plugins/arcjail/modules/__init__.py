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

from controlled_cvars import ControlledConfigManager

from ..info import info


def parse_packages(dir_):
    packages = []
    for name in os.listdir(dir_):
        if name.startswith('__') and name.endswith('__'):
            continue

        if os.path.isdir(os.path.join(dir_, name)):
            packages.append(name)

    return packages


def parse_modules(dir_):
    modules = []
    for name in os.listdir(dir_):
        if not name.endswith('.py'):
            continue

        if name.startswith('__') and name.endswith('__.py'):
            continue

        if os.path.isfile(os.path.join(dir_, name)):
            modules.append(os.path.splitext(name)[0])

    return modules


configs = []


def build_module_config(path):
    config_file = info.basename + '/' + info.basename + '_' + path
    config_manager = ControlledConfigManager(
        config_file, cvar_prefix='arcjail_{}_'.format(path.replace('/', '_')))

    configs.append(config_manager)
    return config_manager


current_dir = os.path.dirname(__file__)
__all__ = parse_packages(current_dir) + parse_modules(current_dir)


from . import *


for config_manager in configs:
    config_manager.write()
    config_manager.execute()
