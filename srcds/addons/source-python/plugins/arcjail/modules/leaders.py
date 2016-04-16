from commands.say import SayCommand
from events import Event

from controlled_cvars import InvalidValue
from controlled_cvars.handlers import bool_handler

from ..arcjail import InternalEvent

from ..resource.strings import build_module_strings

from .admin import section

from .jail_menu import new_available_option

from .max_health import upgrade_health

from .players import broadcast, main_player_manager, tell

from .teams import GUARDS_TEAM

from . import build_module_config


DEFAULT_GAME_HP_AMOUNT = 100


strings_module = build_module_strings('leaders')
config_manager = build_module_config('leaders')

config_manager.controlled_cvar(
    bool_handler,
    name="enabled",
    default=1,
    description="Enable/Disable leadership features",
)


def _leader_hp_handler(cvar):
    try:
        hp = int(cvar.get_string())
    except ValueError:
        raise InvalidValue

    if hp <= 0:
        raise InvalidValue

    return hp

config_manager.controlled_cvar(
    _leader_hp_handler,
    name="leader_hp",
    default=115,
    description="Maximum amount of health a leader can have",
)


_round_end = False
_hp_bonuses = set()
_leader = None


def _give_leadership(player):
    global _leader
    _leader = player

    InternalEvent.fire('jail_leadership_given', player=player)

    if player.userid in _hp_bonuses:
        return

    upgrade_health(player, config_manager['leader_hp'])
    _hp_bonuses.add(player.userid)


def _drop_leadership():
    global _leader
    player = _leader
    _leader = None

    InternalEvent.fire('jail_leadership_dropped', player=player)

    if player.dead:
        return

    if DEFAULT_GAME_HP_AMOUNT < player.health <= config_manager['leader_hp']:
        player.health = DEFAULT_GAME_HP_AMOUNT


def is_leader(player):
    return _leader is not None and _leader == player


def iter_leaders():
    if _leader is not None:
        yield _leader


def get_leadership_denial_reason(player):
    if not config_manager['enabled']:
        return strings_module['fail_disabled']

    if _leader is not None:
        return strings_module['fail_leader_already_set']

    if player.dead:
        return strings_module['fail_dead']

    if player.team != GUARDS_TEAM:
        return strings_module['fail_wrong_team']

    if _round_end:
        return strings_module['fail_round_end']


@Event('player_death_real')
def on_player_death_real(game_event):
    player = main_player_manager[game_event.get_int('userid')]
    if _leader is not None and player == _leader:
        broadcast(strings_module['leader_died'].tokenize(player=player.name))

        _drop_leadership()


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    if _leader is not None and event_var['main_player'] == _leader:
        broadcast(strings_module['leader_disconnected'].tokenize(
            player=_leader.name))

        _drop_leadership()


@Event('round_start')
def on_round_start(game_event):
    global _round_end, _leader
    _round_end = False
    _leader = None

    _hp_bonuses.clear()


@Event('round_end')
def on_round_end(game_event):
    global _round_end
    _round_end = True


@SayCommand('!lead')
def chat_on_lead(command, index, team_only):
    player = main_player_manager.get_by_index(index)
    if _leader is not None and _leader == player:
        _drop_leadership()
        broadcast(strings_module['leader_drop'].tokenize(player=player.name))

    else:
        reason = get_leadership_denial_reason(player)
        if reason is None:
            _give_leadership(player)
            broadcast(strings_module['new_leader'].tokenize(
                player=player.name))

        else:
            tell(player, reason)


@SayCommand('!leaders')
def chat_on_leaders(command, index, team_only):
    player = main_player_manager.get_by_index(index)

    if _leader is None:
        tell(player, strings_module['no_current_leader'])
    else:
        tell(player, strings_module['current_leader'].tokenize(
            player=_leader.name))


# =============================================================================
# >> JAIL MENU ENTRIES
# =============================================================================
def jailmenu_obtain_leadership(player):
    chat_on_lead(None, player.index, False)


def jailmenu_refuse_leadership(player):
    chat_on_lead(None, player.index, False)


def jailmenu_obtain_leadership_handler_active(player):
    return get_leadership_denial_reason(player) is None


def jailmenu_refuse_leadership_handler_active(player):
    return _leader is not None and _leader == player


new_available_option(
    'leadership',
    strings_module['jailmenu_entry_obtain'],
    jailmenu_obtain_leadership,
    jailmenu_obtain_leadership_handler_active,
    jailmenu_obtain_leadership_handler_active,
)


new_available_option(
    'leadership',
    strings_module['jailmenu_entry_refuse'],
    jailmenu_refuse_leadership,
    jailmenu_refuse_leadership_handler_active,
    jailmenu_refuse_leadership_handler_active,
)


# =============================================================================
# >> ARCADMIN ENTRIES
# =============================================================================
if section is not None:
    from arcadmin.classes.menu import PlayerBasedCommand, Section

    class GiveLeadershipCommand(PlayerBasedCommand):
        base_filter = 'alive'
        include_equal_priorities = True
        include_self = True
        allow_multiple_choices = False

        @staticmethod
        def player_name(player):
            if is_leader(player):
                return strings_module['arcadmin name_prefix'].tokenize(
                    base=player.name)
            return player.name

        @staticmethod
        def player_select_callback(admin, players):
            player = players.pop()

            if _leader is not None:
                _drop_leadership()

            if is_leader(player):
                admin.announce(strings_module['arcadmin dropped'].tokenize(
                    leader=player.name))

            else:
                _give_leadership(player)
                admin.announce(strings_module['arcadmin given'].tokenize(
                    leader=player.name))

    leaders_section = section.add_child(
        Section, strings_module['arcadmin section'])

    leaders_section.add_child(
        GiveLeadershipCommand,
        strings_module['arcadmin option give_leadership'],
        'jail.leaders.give', 'give'
    )
