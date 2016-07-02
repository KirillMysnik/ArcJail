from core import GAME_NAME


if GAME_NAME in ("csgo", ):
    def give_named_item(player, classname, subtype=0):
        player.give_named_item(classname, subtype, None, True)

else:
    def give_named_item(player, classname, subtype=0):
        player.give_named_item(classname, subtype)
