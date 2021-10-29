# ../WCSSkills/__init__.py

# Main mod
# Events
from . import admin
# WCS_Player
from . import wcs
# Databases
from . import db
# Commands
from . import commands
# Radio menu
from . import menus
from .other_functions import xp

# Logging plugin load
from .other_functions.functions import wcs_logger

# Downloadables
from stringtables.downloads import Downloadables
from .WCSSkills import WCS_FOLDER
from WCSSkills.other_functions.constants import SOUND_PATH
# Sounds
Downloadables().add_directory(f'sound/{WCS_FOLDER}/')