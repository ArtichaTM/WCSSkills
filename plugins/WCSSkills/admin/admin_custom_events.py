# ../WCSSkills/admin/admin_custom_events.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
from contextlib import suppress

# Source.Python Imports
# Variable types
from events.variable import ShortVariable
from events.variable import FloatVariable
from events.variable import StringVariable
from events.variable import LongVariable
# Resource
from events.resource import ResourceFile
# CustomEvent
from events.custom import CustomEvent
# Event himself
from events import Event
# Player
from players.helpers import index_from_steamid
from players.entity import Player
# SayText2
from messages import SayText2

# Plugin Imports
from WCSSkills.other_functions.constants import PATH_EVENTS
# Types of punish
from WCSSkills.admin.constants import Punishment_types
from WCSSkills.admin.constants import tell_admin_about_all_demutes as TAAAD
# Logging
from WCSSkills.other_functions.functions import wcs_logger

# =============================================================================
# >> Events
# =============================================================================

class Punishment_expired(CustomEvent):
    date_issued = FloatVariable('Date when punishment issued')
    date_expired = FloatVariable('Date when punishment expired')
    etype = ShortVariable('Type of punishment')
    victim_name = StringVariable('Victim name')
    victim_steamid = StringVariable('Victim steamID')
    victim_ip = StringVariable('Victim IP')
    admin_name = StringVariable('Admin name that issued punishment (if any)')
    admin_steamid = StringVariable('Admin steamID that issued punishment (if any)')
    reason = ShortVariable('Reason of punishment')
    duration = LongVariable('Length of issued punishment')

resource_file = ResourceFile(PATH_EVENTS, Punishment_expired)
resource_file.write()
resource_file.load_events()

# =============================================================================
# >> Events-using functions
# =============================================================================

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