# ../WCSSkills/__init__.py

# Main mod
# Events
from .events import custom_events
# Admin
from .admin import admin_events
# WCS_Player
from . import wcs
# Databases
from .db import wcs, admin
# Commands
from .commands import chat
# Radio menu
from .menus import wcs
# XP
from .other_functions import xp

# Logging plugin load
from .other_functions.functions import wcs_logger

# Downloadables
from stringtables.downloads import Downloadables
from .WCSSkills import WCS_FOLDER
# Sounds
Downloadables().add_directory(f'sound/{WCS_FOLDER}/')

wcs_logger('info', 'Plugin loaded successfully')