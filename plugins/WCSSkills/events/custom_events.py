# ../WCSSkills/events/custom_events.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
# Variable types
from events.variable import ShortVariable
from events.variable import FloatVariable
from events.variable import StringVariable
from events.variable import LongVariable
from events.variable import BoolVariable
# Resource
from events.resource import ResourceFile
# CustomEvent
from events.custom import CustomEvent

# Plugin Imports
# PATHs
from WCSSkills.other_functions.constants import PATH_FOLDER_EVENTS

# =============================================================================
# >> Custom events
# =============================================================================

class Player_setting_changed(CustomEvent):
    """ Fired when player changed setting in menu settings """
    code = StringVariable('Name of the setting in the code')
    name = StringVariable('Translated name')
    value = BoolVariable('New value of setting')

class Punishment_expired(CustomEvent):
    """ Fired when player punishment expired """
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

resource_file = ResourceFile(PATH_FOLDER_EVENTS, Punishment_expired, Player_setting_changed)
resource_file.write()
resource_file.load_events()