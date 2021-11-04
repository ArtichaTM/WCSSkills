# ../WCSSkills/other_functions/constants.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
from datetime import datetime
from enum import IntFlag

# Source.Python Imports
# DamageTypes
from entities.constants import DamageTypes
# Plugin path
from paths import PLUGIN_DATA_PATH
from paths import EVENT_PATH
from paths import PLUGIN_PATH
from paths import SOUND_PATH

# Plugin Imports
# Folder name
from WCSSkills.WCSSkills import WCS_FOLDER

# =============================================================================
# >> Constants
# =============================================================================

WCSSKILLS_DEBUG = False

# WCS_magic_damage ID
WCS_DAMAGE_ID = DamageTypes.PHYSGUN
ADMIN_DAMAGE_ID = DamageTypes.DISSOLVE

# Skills unload timings. Returns tuple, where [0] delay, [1] interval
SKILL_TIMINGS = (0, 0)

# Default skill setting value
SKILL_SETTING_DEFAULT_BOOL = False

# Sprites for wcs_effects
orb_sprites = (
    'sprites/glow'
    'sprites/glow01'
    'sprites/glow03'
    'sprites/glow04'
    'sprites/glow04_noz'
    'sprites/glow06'
    'sprites/glow07')

# =============================================================================
# >> Paths
# =============================================================================

# Files
PATH_FILE_DATABASE_USERS = PLUGIN_DATA_PATH / WCS_FOLDER / 'db' / 'users.db'
PATH_FILE_DATABASE_ADMIN = PLUGIN_DATA_PATH / WCS_FOLDER / 'db' / 'SourceBan.db'
PATH_FILE_JSON_DISCONNECTED_PLAYERS = PLUGIN_DATA_PATH / WCS_FOLDER / 'json' / 'disconnected_players.json'
PATH_FILE_JSON_SKILLS_INFO = PLUGIN_PATH / WCS_FOLDER / 'JSONs' / 'skills_info.json'
PATH_FILE_JSON_PLAYER_SETTINGS = PLUGIN_PATH / WCS_FOLDER / 'JSONs' / 'player_settings.json'
PATH_FOLDER_EVENTS = EVENT_PATH / WCS_FOLDER
PATH_FOLDER_SOUNDS = SOUND_PATH.parent / WCS_FOLDER

# Making Dirs if they don't exist
for local in locals().copy().items():

    # Iterating over all locals and locking for 'PATH_' constants
    if local[0][:5] == 'PATH_':

        # Is path - folder?
        if local[0][5:11] == 'FOLDER':

            # Yes, creating for dirs, if needed
            if not local[1].isdir(): local[1].makedirs()

        elif local[0][5:9] == 'FILE':

            # Found. Going backwards to folder
            parent = local[1].parent

            # If dir doesn't exist, create
            if not parent.isdir(): parent.makedirs()

# Logs
if WCSSKILLS_DEBUG:
    PATH_TO_LOG = f"{WCS_FOLDER}/log.log"
else:
    PATH_TO_LOG = f"{WCS_FOLDER}/{datetime.today().strftime('%Y-%m-%d')}.log"


# =============================================================================
# >> Sound volume
# =============================================================================

VOLUME_MENU = 0.2

# =============================================================================
# >> Enumeratings
# =============================================================================

class Immune_types(IntFlag):
    """ Types of immune to skills

    You must be cautious with Ultimate_deflect, bcz Ultimate_deflect
    should be used ONLY for parts of ultimate. Example:

    skill with damage and paralyze. Check for skill immune should
    be in damage, and paralyze -> If victim has
    •Immune_types.Nothing paralyze
    •Immune_types.Ultimate_deflect for damage
    Victim should deflect damage, and be paralyzed.

    Always check resistance partly in this situation!
    """

    # None immune
    Nothing = 0

    # Immune to default skills (attack)
    Default = 1
    Default_deflect = 2

    # Mirror skills
    Mirror = 4
    Mirror_deflect = 8

    # Ultimate
    Ultimate = 16
    Ultimate_deflect = 32

    # Aura immune
    Aura = 64
    Aura_deflect = 128

    def __contains__(self, item):

        # Items is enum
        if isinstance(item, IntFlag):

            # If with adding new value nothing changed -> value
            # already contains in enum
            if self.value | item.value == self.value: return True

            # Changed -> value didn't contains in enum
            else: return False


        # Item is int
        elif isinstance(item, int):

            # If with adding new value nothing changed -> value
            # already contains in enum
            if self.value | item == self.value: return True

            # Changed -> value didn't contains in enum
            else:  return False

        # No? Then we can't compare item with enum
        else:
            raise TypeError(f"Can't compare '{type(item)}' and 'enum'")