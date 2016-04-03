from json import dumps
from warnings import warn

from core import echo_console
from events.manager import event_manager

from ....arcjail import internal_event_manager, InternalEvent

from ...players import broadcast

from .. import GameLauncher, GameMeta, set_instance, stage, strings_module


class UnknownStageWarning(Warning):
    pass


class BaseGame(metaclass=GameMeta):
    class GameLauncher(GameLauncher):
        def launch(self, leader_player, players, **kwargs):
            return self.game_class(leader_player, players, **kwargs)

    module = None
    caption = strings_module['title basegame']
    stage_groups = {
        'init': [
            "register-event-handlers",
            "start-notify",
            "basegame-entry",
        ],
        'destroy': [
            "destroy",
        ]
    }

    def __init__(self, leader_player, players, **kwargs):
        self.leader = leader_player
        self._players = list(players)
        self._players_all = list(players)
        self._lock_stage_queue = False
        self._cur_stage_id = None
        self._stage_queue = []
        self._executed_stages = []
        self._settings = kwargs

        for stage_ in self._stages_map.values():
            stage_.game_instance = self

        for game_event_handler_ in self._events.values():
            game_event_handler_.game_instance = self

    @property
    def players(self):
        return tuple(self._players)

    @property
    def players_all(self):
        return tuple(self._players_all)

    def launch_stages(self):
        while self._stage_queue:
            stage_id = self._stage_queue.pop(0)
            self._cur_stage_id = stage_id

            self._stages_map[stage_id]()

            self._executed_stages.append(self._stages_map[stage_id])

        self._cur_stage_id = None

    def set_stage_group(self, stage_group_id):
        if self._lock_stage_queue:
            return

        if stage_group_id not in self._stage_groups:
            warn(UnknownStageWarning(
                "{}: Unknown stage group id '{}', destroying".format(
                    self.__class__.__name__, stage_group_id)))

            self.set_stage_group('destroy')

        else:
            self._stage_queue = list(self._stage_groups[stage_group_id])
            if self._cur_stage_id is None:
                self.launch_stages()

    def insert_stage_group(self, stage_group_id):
        if self._lock_stage_queue:
            return

        if stage_group_id not in self._stage_groups:
            warn(UnknownStageWarning(
                "{}: Unknown stage group id '{}', destroying".format(
                    self.__class__.__name__, stage_group_id)))

            self.set_stage_group('destroy')

        else:
            self._stage_queue = (self._stage_groups[stage_group_id] +
                                 self._stage_queue)

            if self._cur_stage_id is None:
                self.launch_stages()

    def undo_stages(self, stage_group_ids=None):
        if stage_group_ids is None:
            stage_group_ids = self._stage_groups.keys()
        else:
            if isinstance(stage_group_ids, str):
                stage_group_ids = (stage_group_ids, )

        for stage_group_id in stage_group_ids:
            for stage_id in self._stage_groups[stage_group_id]:
                stage_ = self._stages_map[stage_id]
                if stage_ not in self._executed_stages:
                    continue

                self._executed_stages.remove(stage_)

                undo_stage_id = 'undo-{}'.format(stage_id)
                if undo_stage_id not in self._stages_map:
                    continue

                self._stages_map[undo_stage_id]()

    @property
    def current_stage_id(self):
        return self._cur_stage_id

    @classmethod
    def get_available_launchers(cls, leader_player, players):
        return (cls.GameLauncher(cls), )

    def print_stages(self):
        echo_console(dumps(self._stage_groups, indent=2))

    @stage('destroy')
    def stage_destroy(self):
        self.undo_stages()
        self._lock_stage_queue = True
        set_instance(None)

    @stage('register-event-handlers')
    def stage_register_event_handlers(self):
        for game_event_handler_ in self._events.values():
            event_manager.register_for_event(
                game_event_handler_.event, game_event_handler_)

        for game_internal_event_handler_ in self._internal_events.values():
            internal_event_manager.register_event_handler(
                game_internal_event_handler_.event,
                game_internal_event_handler_
            )

    @stage('undo-register-event-handlers')
    def stage_undo_register_event_handlers(self):
        for game_event_handler_ in self._events.values():
            event_manager.unregister_for_event(
                game_event_handler_.event, game_event_handler_)

        for game_internal_event_handler_ in self._internal_events.values():
            internal_event_manager.unregister_event_handler(
                game_internal_event_handler_.event,
                game_internal_event_handler_
            )

    @stage('start-notify')
    def stage_start_notify(self):
        InternalEvent.fire('arcjail_games_game_started', instance=self)
        broadcast(strings_module['game_started'].tokenize(game=self.caption))

    @stage('basegame-entry')
    def stage_basegame_entry(self):
        pass
