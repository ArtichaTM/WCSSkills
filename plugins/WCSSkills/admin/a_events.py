
# Event himself
from events import Event
# Player
from players.helpers import index_from_steamid
from players.entity import Player
# SayText2
from messages import SayText2
# Types of punish
from ..admin.constants import Punishment_types
from ..admin.constants import tell_admin_about_all_demutes as TAAAD
# Logging
from ..WCS_Logger import wcs_logger


@Event('Punishment_expired')
def punishment_expired(ev):

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
        SayText2(f"\2[SYS]\1 Мут игрока {ev['victim_name']} прошёл").send(admin.index)
