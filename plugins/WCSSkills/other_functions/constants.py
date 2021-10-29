# ../WCSSkills/other_functions/constants.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
from datetime import datetime

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

WCSSkills_DEBUG = True

# WCS_magic_damage ID
WCS_DAMAGE_ID = DamageTypes.PHYSGUN
ADMIN_DAMAGE_ID = DamageTypes.DISSOLVE

# Skills unload timings. Returns tuple, where [0] delay, [1] interval
SKILL_TIMINGS = (0,0)

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
if WCSSkills_DEBUG:
    PATH_TO_LOG = f"{WCS_FOLDER}/log.log"
else:
    PATH_TO_LOG = f"{WCS_FOLDER}/{datetime.today().strftime('%Y-%m-%d')}.log"