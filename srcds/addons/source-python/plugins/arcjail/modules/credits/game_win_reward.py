from ...arcjail import InternalEvent

from ...resource.strings import build_module_strings

from . import credits_config, earn_credits


strings_module = build_module_strings('credits/game_win_reward')


@InternalEvent('jail_game_cock_fight_winners')
def on_jail_game_cock_fight_winners(event_var):
    payout = int(
        int(credits_config['rewards']['cock_fight_win']) *
        (1 - len(event_var['winners']) / event_var['starting_player_number'])
    )

    for winner in event_var['winners']:
        earn_credits(winner, payout, strings_module['reason cock_fight'])


@InternalEvent('jail_game_chat_game_winner')
def on_jail_game_chat_game_winner(event_var):
    earn_credits(
        event_var['winner'], int(credits_config['rewards']['chat_game_win']),
        strings_module['reason chat_game'])


@InternalEvent('jail_game_map_game_team_based_winners')
def on_jail_game_map_game_team_based_win(event_var):
    winners = event_var['winners']
    payout = int(credits_config['rewards']['map_game_team_based_win'])

    for winner in winners:
        earn_credits(
            winner, payout, strings_module['reason map_game_team_based'])


@InternalEvent('jail_game_map_game_winners')
def on_jail_game_map_game_winners(event_var):
    winners = event_var['winners']
    starting_player_number = event_var['starting_player_number']

    payout = int(
        int(credits_config['rewards']['cock_fight_win']) *
        (1 - len(winners) / starting_player_number)
    )

    for winner in winners:
        earn_credits(winner, payout, strings_module['reason map_game'])
