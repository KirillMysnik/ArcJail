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
