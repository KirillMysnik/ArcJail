from entities.classes import server_classes
from entities.datamaps import FieldType
from events import Event
from filters.entities import BaseEntityIter
from filters.players import PlayerIter
from listeners.tick import Delay
from memory import make_object


_input_types = {
    FieldType.BOOLEAN: lambda arg: arg == '1',
    FieldType.FLOAT: float,
    FieldType.INTEGER: int,
    FieldType.STRING: str,
    FieldType.VOID: None,
}


class Fire:
    def __call__(self, target_pattern, input_name, parameter=None, caller=None,
                 activator=None):

        """
        Find target entities using the given pattern and try to
        call an input on each of them.
        """
        targets = self._get_targets(target_pattern, caller, activator)
        for target in targets:
            self._call_input(target, input_name, parameter, caller, activator)

    def _get_targets(self, target_pattern, caller, activator):
        """
        Return iterable of targets depending on given pattern,
        caller and activator.
        """
        if target_pattern.startswith('!'):
            return self._get_special_name_target(
                target_pattern, caller, activator)

        filter_ = self._get_entity_filter(target_pattern, caller, activator)
        return filter(filter_, BaseEntityIter())

    @staticmethod
    def _get_special_name_target(target_pattern, caller, activator):
        """Find target by a special (starting with '!') target name."""
        if target_pattern == "!self":
            return (caller, )

        if target_pattern == "!player":
            for player in PlayerIter():
                return (player, )
            return ()

        if target_pattern in ("!caller", "!activator"):
            return (activator, )

    @staticmethod
    def _get_entity_filter(target_pattern, caller, activator):
        """
        Return a filter that will be applied to all entities on the server.
        """
        if target_pattern.endswith('*'):
            def filter_(entity):
                targetname = entity.get_key_value_string('targetname')
                return (targetname.startswith(target_pattern[:-1]) or
                        entity.classname.startswith(target_pattern[:-1]))
            return filter_

        if not target_pattern:
            return lambda entity: False

        def filter_(entity):
            targetname = entity.get_key_value_string('targetname')
            return target_pattern in (targetname, entity.classname)
        return filter_

    @staticmethod
    def _get_input(target, input_name):
        """Return input function based on target and input name."""
        for server_class in server_classes.get_entity_server_classes(target):
            if input_name in server_class.inputs:
                return getattr(
                    make_object(
                        server_class._inputs, target.pointer
                    ),
                    input_name
                )

        return None

    def _call_input(self, target, input_name, parameter, caller, activator):
        """Fire an input of a particular entity."""
        input_function = self._get_input(target, input_name)

        # If entity doesn't support the input, we don't work with this entity
        if input_function is None:
            return

        caller_index = None if caller is None else caller.index
        activator_index = None if activator is None else activator.index

        # Check if type is unsupported, but we actually support all types
        # that can possibly be passed as a string to input:
        # int, float, bool, str
        # TODO: Implement support for entity arguments
        # (passed as a special name like !activator, !caller etc)
        if input_function._argument_type not in _input_types:
            return

        type_ = _input_types[input_function._argument_type]

        # Case: input does not require parameter
        if type_ is None:
            parameter = None

        # Case: input does require parameter
        else:
            # Try to cast the parameter to the given type
            try:
                parameter = type_(parameter)

            # We don't give up the target if the value can't be casted;
            # Instead, we fire its input with a default value
            # just like ent_fire does
            except ValueError:
                parameter = type_()

        # Fire an input
        input_function(parameter, caller_index, activator_index)


fire = Fire()


class OutputConnection:
    def __init__(
            self, fire_func, destroy_func, json, caller=None, activator=None):

        delay = max(0.0, json['delay'])
        times_to_fire = max(-1, json['times_to_fire'])

        self._fire_func = fire_func
        self._destroy_func = destroy_func

        self.target_pattern = json['target_pattern']
        self.input_name = json['input_name']
        self.parameter = json['parameter']
        self.parameter_raw = json['parameter_raw']
        self.delay = delay
        self.times_to_fire = times_to_fire
        self.caller = caller
        self.activator = activator

        self._delayed_callbacks = []
        self._times_fired = 0

    def reset(self):
        """Cancel all pending callbacks and set fire count to zero."""
        for delayed_callback in self._delayed_callbacks:
            if delayed_callback.running:
                delayed_callback.cancel()

        self._delayed_callbacks.clear()
        self._times_fired = 0

    def fire(self):
        """Fire this output connection."""
        if self.times_to_fire > -1 and self._times_fired >= self.times_to_fire:
            return

        def callback():
            self._fire_func(self.target_pattern,
                            self.input_name,
                            self.parameter_raw,
                            self.caller,
                            self.activator)

        if self.delay == 0.0:
            callback()

        else:
            self._delayed_callbacks.append(Delay(self.delay, callback))

    def destroy(self):
        """
        Remove a reference to the connection and stop resetting
        connection on every round start.
        """
        self._destroy_func(self)

    def __str__(self):
        return "OutputConnection('{0},{1},{2},{3},{4}')".format(
            self.target_pattern,
            self.input_name,
            self.parameter_raw,
            self.delay,
            self.times_to_fire,
        )


output_connections = []


def new_output_connection(json, caller=None, activator=None):
    """
    Create and register a new OutputConnection instance using given values.
    """
    output_connection = OutputConnection(
        fire, destroy_output_connection, json, caller, activator)

    output_connections.append(output_connection)
    return output_connection


def destroy_output_connection(output_connection):
    """
    Remove connection reference thus stopping
    resetting the connection every round.
    """
    output_connections.remove(output_connection)


@Event('round_start')
def on_round_start(game_event):
    for output_connection in output_connections:
        output_connection.reset()


@Event('server_spawn')
def on_server_spawn(game_event):
    for output_connection in output_connections:
        output_connection.destroy()
