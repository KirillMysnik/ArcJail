from ...damage_hook import protected_player_manager

from .. import stage

from .jail_game import JailGame


class NoOffenseGame(JailGame):
    stage_groups = {
        'nooffensegame-start': [
            "equip-damage-hooks",
            'nooffensegame-entry',
        ],
    }

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self._counters = {}

    @stage('basegame-entry')
    def stage_basegame_entry(self):
        self.set_stage_group('nooffensegame-start')

    @stage('nooffensegame-entry')
    def stage_nooffensegame_entry(self):
        pass

    @stage('equip-damage-hooks')
    def stage_equip_damage_hooks(self):
        for player in self._players:
            p_player = protected_player_manager[player.index]

            counter = self._counters[player.userid] = p_player.new_counter()
            counter.hook_hurt = lambda counter, info: False

            p_player.set_protected()

    @stage('undo-equip-damage-hooks')
    def stage_undo_equip_damage_hooks(self):
        for player in self._players_all:
            p_player = protected_player_manager[player.index]
            p_player.delete_counter(self._counters[player.userid])
            p_player.unset_protected()
