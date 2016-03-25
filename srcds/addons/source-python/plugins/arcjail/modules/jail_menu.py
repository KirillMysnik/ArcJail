from commands.client import ClientCommand
from commands.say import SayCommand
from events import Event
from menus import PagedMenu, PagedOption

from ..arcjail import InternalEvent

from ..resource.strings import build_module_strings

from .players import main_player_manager, tell


strings_module = build_module_strings('jail_menu')


class AvailableOption:
    alias = ''
    caption = ""
    handler_visible = lambda self, player: True
    handler_active = lambda self, player: True
    callback = lambda self, player: None


class PopupOptionData:
    alias = ''
    caption = ""
    active = True
    callback = lambda self, player: None


_popups = {}
_available_options = []


def new_available_option(
        alias, caption, callback, handler_visible=None, handler_active=None):

    available_option = AvailableOption()
    available_option.alias = alias
    available_option.caption = caption
    available_option.callback = callback

    if handler_visible is not None:
        available_option.handler_visible = handler_visible

    if handler_active is not None:
        available_option.handler_active = handler_active

    _available_options.append(available_option)
    return available_option


def delete_available_option(available_option):
    _available_options.remove(available_option)


def send_popup(player):
    options = []
    for available_option in _available_options:
        if available_option.handler_visible(player):
            text = available_option.caption
            selectable = available_option.handler_active(player)

            option = PagedOption(
                                 text=text,
                                 value=available_option.callback,
                                 highlight=selectable,
                                 selectable=selectable)

            options.append(option)

    if options:
        if player.userid in _popups:
            _popups[player.userid].close()

        def select_callback(popup, player_index, option):
            callback = option.value
            callback(player)

        menu = _popups[player.userid] = PagedMenu(
            select_callback=select_callback, title=strings_module['title'])

        for option in options:
            menu.append(option)

        menu.send(player.index)

    else:
        tell(player, strings_module['empty'])


@Event('round_start')
def on_round_start(game_event):
    for popup in _popups.values():
        popup.close()

    _popups.clear()


@InternalEvent('unload')
def on_unload(event_var):
    for popup in _popups.values():
        popup.close()

    _popups.clear()


@SayCommand('!jmenu')
def chat_on_jmenu(command, index, team_only):
    send_popup(main_player_manager.get_by_index(index))


@ClientCommand('jmenu')
def cmd_on_jmenu(command, index):
    send_popup(main_player_manager.get_by_index(index))
