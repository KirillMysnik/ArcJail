from warnings import warn

from core.manager import core_plugin_manager

from ..arcjail import InternalEvent

from ..resource.strings import build_module_strings


class ArcAdminNotInstalledWarning(Warning):
    pass


strings_module = build_module_strings('admin')


if core_plugin_manager.is_loaded('arcadmin'):
    from arcadmin.classes.menu import popup_main, Section
    section = popup_main.add_child(Section, strings_module['popup title'])

    @InternalEvent('unload')
    def on_unload(event_var):
        popup_main.remove(section)

else:
    warn(ArcAdminNotInstalledWarning("ArcAdmin has not been available by the "
                                     "time ArcJail loads, jail admin features "
                                     "won't be available too"))

    section = None
