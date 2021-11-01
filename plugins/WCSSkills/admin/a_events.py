
# Event himself
from events import Event
# Player
from players.helpers import index_from_steamid
from players.entity import Player
# SayText2
from messages import SayText2
# Types of punish
from WCSSkills.admin.constants import Punishment_types
from WCSSkills.admin.constants import tell_admin_about_all_demutes as TAAAD
# Logging
from WCSSkills.other_functions.functions import wcs_logger


@Event('Punishment_expired')
def something(ev):

    # Logging punishment expire
    wcs_logger('PUNISHMENT', f"{ev['victim_name']} {Punishment_types(ev['etype']).name} expired")

    # Telling to player, that his punishment expired
    try:

        # Getting Player
        player = Player(index_from_steamid(ev['victim_steamid']))

        # Saying to him with index
        SayText2(f"\2[SYS]\1 Ваш мут прошёл").send(player.index)

    except ValueError:

        # Returning otherwise, if turned on
        if TAAAD:
            return

    try:

        # Getting admin player
        admin = Player(index_from_steamid(ev['admin_steamid']))

    except ValueError:

        # If failing, returning
        return

    else:

        # Else telling to admin, that his mute on player passed
        SayText2(f"\2[SYS]\1 Мут игрока {player.name} прошёл").send(admin.index)