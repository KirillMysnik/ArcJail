from filters.players import PlayerIter


from ..arcjail import InternalEvent


PRISONERS_TEAM = 2
GUARDS_TEAM = 3


@InternalEvent('load')
def on_load(event_var):
    is_prisoner = lambda player: player.team == PRISONERS_TEAM
    is_guard = lambda player: player.team == GUARDS_TEAM

    PlayerIter.register_filter('jail_prisoner', is_prisoner)
    PlayerIter.register_filter('jail_guard', is_guard)


@InternalEvent('unload')
def on_unload(event_var):
    PlayerIter.unregister_filter('jail_prisoner')
    PlayerIter.unregister_filter('jail_guard')
