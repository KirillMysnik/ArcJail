import os

from colors import Color

from advanced_ts import BaseLangStrings

from ..info import info


# Map color variables in translation files to actual Color instances
COLOR_SCHEME = {
    'color_tag': Color(242, 242, 242),
    'color_highlight': Color(255, 191, 0),
    'color_default': Color(242, 242, 242),
    'color_error': Color(255, 54, 54),
}


strings_common = BaseLangStrings(os.path.join(info.basename, "common"))


def build_module_strings(module):
    return BaseLangStrings(os.path.join(info.basename, 'modules', module))
