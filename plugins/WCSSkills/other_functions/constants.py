# ../WCSSkills/other_functions/constants.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
from datetime import datetime
from enum import Enum
from enum import IntFlag
from enum import IntEnum
from enum import auto

# Source.Python Imports
# DamageTypes
from entities.constants import DamageTypes as DamTyp
# Plugin path
from paths import PLUGIN_DATA_PATH
from paths import EVENT_PATH
from paths import PLUGIN_PATH
from paths import SOUND_PATH

# Plugin Imports
# Folder name
from WCSSkills.WCSSkills import WCS_FOLDER

# =============================================================================
# >> Enumeratings
# =============================================================================

class ImmuneTypes(IntFlag):
    """ Types of immune to skills

    You must be cautious with Ultimate_deflect, bcz Ultimate_deflect
    should be used ONLY for parts of ultimate. Example:

    skill with damage and paralyze. Check for skill immune should
    be in damage, and paralyze -> If victim has
    •ImmuneTypes.Nothing paralyze
    •ImmuneTypes.Ultimate_deflect for damage
    Victim should deflect damage, and be paralyzed.

    Always check resistance partly in this situation!
    """

    # None immune
    Nothing = auto()

    # Immune to all
    Any = auto()

    # Penetrate all immunes
    Penetrate = auto()

    # Immune to default skills (attack)
    Default = auto()
    Default_deflect = auto()

    # Mirror skills
    Mirror = auto()
    Mirror_deflect = auto()

    # Ultimate
    Ultimate = auto()
    Ultimate_deflect = auto()

    # Aura immune
    Aura = auto()
    Aura_deflect = auto()

    # Light
    Light = auto()
    Light_deflect = auto()

    # Dark
    Dark = auto()
    Dark_deflect = auto()

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
            raise TypeError(f"Can't compare '{type(item)}' and 'IntFlag'")

class ImmuneReactionTypes(IntEnum):
    Passed = 0
    Immune = 1
    Deflect = 2

DamTyp.__contains__ = ImmuneTypes.__contains__
DamageTypes = DamTyp
# class DamageTypes(DamTyp):
#
#     def __contains__(self, item):
#
#         # Items is enum
#         if isinstance(item, IntFlag):
#
#             # If with adding new value nothing changed -> value
#             # already contains in enum
#             if self.value | item.value == self.value: return True
#
#             # Changed -> value didn't contains in enum
#             else: return False
#
#
#         # Item is int
#         elif isinstance(item, int):
#
#             # If with adding new value nothing changed -> value
#             # already contains in enum
#             if self.value | item == self.value: return True
#
#             # Changed -> value didn't contains in enum
#             else:  return False
#
#         # No? Then we can't compare item with enum
#         else:
#             raise TypeError(f"Can't compare '{type(item)}' and 'IntFlag'")

# =============================================================================
# >> Constants
# =============================================================================

WCSSKILLS_DEBUG = True

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
# >> Dictionaries
# =============================================================================
# Translate weapons to russian
weapon_translations = {
'weapon_nova': 'Нова',
'weapon_xm1014': 'XM1014',
'weapon_sawedoff': 'Sawed-off',
'weapon_mag7': 'Mag7',
'weapon_m249': 'M249',
'weapon_negev': 'Негев',
'weapon_mac10': 'Mac10',
'weapon_mp5sd': 'MP5SD',
'weapon_mp7': 'MP7',
'weapon_mp9': 'MP9',
'weapon_ump45': 'Юмп',
'weapon_p90': 'Петух',
'weapon_bizon': 'Бизон',
'weapon_galilar': 'Галина',
'weapon_famas': 'Фамас',
'weapon_ak47': 'Калаш',
'weapon_m4a1': 'Мка',
'weapon_m4a1_silencer': 'Мка с глушителем',
'weapon_aug': 'Ауг',
'weapon_sg556': 'СГ',
'weapon_ssg08': 'Муха',
'weapon_awp': 'АВП',
'weapon_g3sg1': 'Плётка Т',
'weapon_scar20': 'Плётка КТ',
'weapon_glock': 'Глок',
'weapon_usp_silencer': 'Юсп',
'weapon_hkp2000': 'P2000',
'weapon_fiveseven': 'Five seven',
'weapon_elite': 'Двойные берреты',
'weapon_p250': 'P250',
'weapon_tec9': 'Tec 9',
'weapon_cz75a': 'Чешка',
'weapon_deagle': 'Дигл',
'weapon_revolver': 'Револьвер',
'weapon_knife': 'Нож',
'weapon_fists': 'Кулаки',
'weapon_hammer': 'Молоток',
'weapon_spanner': 'Гаечный ключ',
'weapon_axe': 'Топор',
'weapon_taser': 'Шокер',
'weapon_molotov': 'Молик',
'weapon_incgrenade': 'Поджигательная граната',
'weapon_decoy': 'Декой',
'weapon_flashbang': 'Флешка',
'weapon_hegrenade': 'Хаешка',
'weapon_smokegrenade': 'Смок',
'weapon_tagrenade': 'ВХ граната',
'weapon_frag_grenade': 'weapon_frag_grenade',
'weapon_diversion': 'weapon_diversion',
'weapon_firebomb': 'weapon_firebomb',
'weapon_snowball': 'Снежок',
'weapon_breachcharge': 'Пробивной заряд',
'weapon_c4': 'Бомба',
'weapon_tablet': 'Планшет',
'weapon_healthshot': 'Хилка',
'item_cutters': 'Дефуза',
'item_assaultsuit': 'item_assaultsuit',
'item_heavyassaultsuit': 'Тяжёлая броня',
'item_cash': 'Деньги',
'item_drone': 'Дрон',
'item_dronegun': 'Оружие дрона'
}

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