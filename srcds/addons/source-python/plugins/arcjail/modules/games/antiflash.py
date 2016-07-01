from entities.entity import Entity
from listeners import on_entity_created_listener_manager
from memory import make_object
from memory.hooks import HookType
from events import Event

from ...arcjail import InternalEvent

from ..effects.dissolve import dissolve


_detonate_func = None
_waiting = False
_attached = False
_detonation_filters = []
_filtered_indexes = set()


def register_detonation_filter(filter_):
    if filter_ in _detonation_filters:
        raise ValueError("Detonation filter '{}' is already "
                         "registered".format(filter_))

    if not _detonation_filters:
        _add_hook_or_wait()

    _detonation_filters.append(filter_)


def unregister_detonation_filter(filter_):
    _detonation_filters.remove(filter_)

    if not _detonation_filters:
        _remove_hook_or_stop_waiting()


def _pre_detonate(args):
    entity = make_object(Entity, args[0])
    if entity.index not in _filtered_indexes:
        return None

    dissolve(entity)
    return True


def _add_hook_or_wait():
    if _detonate_func is None:
        global _waiting
        _waiting = True
    else:
        _add_hook()


def _remove_hook_or_stop_waiting():
    if _detonate_func is None:
        global _waiting
        _waiting = False
    else:
        _remove_hook()


def _add_hook():
    global _attached
    _detonate_func.add_hook(HookType.PRE, _pre_detonate)
    _attached = True


def _remove_hook():
    global _attached
    _detonate_func.remove_hook(HookType.PRE, _pre_detonate)
    _attached = False


@InternalEvent('load')
def on_load(event_var):
    on_entity_created_listener_manager.register_listener(
        listener_on_entity_created)


@InternalEvent('unload')
def on_unload(event_var):
    on_entity_created_listener_manager.unregister_listener(
        listener_on_entity_created)

    if _detonate_func is not None:
        _remove_hook()


def listener_on_entity_created(index, base_entity):
    if base_entity.classname != 'flashbang_projectile':
        return

    entity = Entity(index)

    if _detonate_func is None:
        global _detonate_func
        _detonate_func = entity.detonate

        global _waiting
        if _waiting:
            _add_hook()
            _waiting = False

    for filter_ in _detonation_filters:
        if not filter_(entity):
            _filtered_indexes.add(entity.index)
            break


@Event('round_start')
def on_round_start(game_event):
    _filtered_indexes.clear()
