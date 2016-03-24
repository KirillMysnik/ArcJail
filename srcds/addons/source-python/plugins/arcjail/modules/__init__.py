import os


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


current_dir = os.path.dirname(__file__)
__all__ = parse_packages(current_dir) + parse_modules(current_dir)


from . import *
