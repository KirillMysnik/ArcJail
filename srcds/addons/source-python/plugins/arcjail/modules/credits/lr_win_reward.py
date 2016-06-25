from ...arcjail import InternalEvent

from ...resource.strings import build_module_strings

from . import credits_config, earn_credits


strings_module = build_module_strings('credits/lr_win_reward')


@InternalEvent('jail_lr_won')
def on_jail_lr_won(winner, loser):
    earn_credits(
        winner, credits_config['rewards']['lr_win'], strings_module['reason'])
