# ../WCSSkills/other_functions/functions.py
"""
File with various useful functions.
1. open_players: return player(-s), that open to first one
2. force_buttons: force button, than returns back to normal
3. wcs_player: returns WCS_Player if exist, else None
4. chance: returns True if chance passed
5. repeat_functions: class that simplifies actions with
    repeat. Inherit to use
6. pre_take_damage: function, that not in all, bcz not using directly.
    add function pointer to on_take_damage_set. On damage take
    function iterate over all functions in set
7. player_indexes:
"""
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
# Random
import random
from datetime import datetime
from typing import Union, Any

# Source.Python imports
# Hooks
from entities.hooks import EntityPreHook, EntityCondition
from hooks.exceptions import ExceptHook
# Helpers
# Entities
from entities.entity import BaseEntity, Entity
from entities.constants import WORLD_ENTITY_INDEX
from entities import TakeDamageInfo
from entities.helpers import index_from_pointer
# Engine trace
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import engine_trace
from engines.trace import ContentMasks
# Iters
from filters.players import PlayerIter
# Repeat
from listeners.tick import RepeatStatus
# Memory
from memory import make_object
# CVars
from cvars import ConVar
# server
from engines.server import server
# Vector
from mathlib import Vector
# Paths
from paths import LOG_PATH

# WCS_Players
from WCSSkills.python.types import *
# WCS_damage id:
from WCSSkills.other_functions.constants import WCS_DAMAGE_ID
from WCSSkills.other_functions.constants import ADMIN_DAMAGE_ID
from WCSSkills.other_functions.constants import PATH_TO_LOG
# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = ('on_take_physical_damage',
           'on_take_magic_damage',
           'chance',
           'player_indexes',
           'open_players',
           'force_buttons',
           'repeat_functions',
           'wcs_logger'
           )

# =============================================================================
# >> Global variables
# =============================================================================

on_take_physical_damage = set()
on_take_magic_damage = set()

# =============================================================================
# >> Functions
# =============================================================================

# Chance function to check if skill worked or not
chance = lambda value1, value2 : value1 >= random.randint(0, value2)

# Return all players indexes
player_indexes = lambda : [player.index for player in PlayerIter()]

#
# @EntityPreHook(EntityCondition.is_player, 'emit_sound')
# def xz(*args):
#     pass

@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def skills_on_take_damage(args) -> Union[None, bool]:
    info = make_object(TakeDamageInfo, args[1])

    # Checking if damage was dealt by admin
    if info.type == ADMIN_DAMAGE_ID:

        # Yes, it is. Canceling skill checks
        return

    # If damage dealt by magic dmg, iter over magic_damage functions
    if info.type == WCS_DAMAGE_ID:

        # Getting player from index arg
        player = Entity(index_from_pointer(args[0]))

        # Loading magic damage set
        global on_take_magic_damage

        # Iterating over all entry's in set
        for func in on_take_magic_damage:

            # Getting his return
            value: bool = func(player, info)

            # Checking, if function returns False
            if value is False:

                # Then canceling hit
                return False

    # In other condition, iterate over physical dmg
    else:

        # Getting player from index arg
        player = Entity(index_from_pointer(args[0]))

        # Loading magic damage set
        global on_take_physical_damage

        # Iterating over all entry's in set
        for func in on_take_physical_damage:

            # Getting his return
            value: bool = func(player, info)

            # Checking, if function returns False
            if value is False:

                # Then canceling hit
                return False

def open_players(player: Player_entity, only_one=False, same_team = False) -> Entity_entity:
    """ This function checks for other players, that can be hitted by player """

    # Creating list
    hitted = []

    # Iterating over all alive players
    for user in PlayerIter('alive'):

        # Checking, if selected player isn't our player
        if user.index == player.index:
            continue

        # Checking for team equality
        elif user.team == player.team and not same_team:
            continue

        # Get the entity's origin
        origin: Vector = player.eye_location

        # Get a Ray object of the entity physic box
        ray = Ray(origin, user.origin)

        # Get a new GameTrace instance
        trace = GameTrace()

        # Trace to player
        engine_trace.clip_ray_to_entity(
            ray, ContentMasks.ALL, BaseEntity(WORLD_ENTITY_INDEX), trace)

        # Hitted something?
        if not trace.did_hit():

            # Not hitted! Player can be shot
            hitted.append(user)

            if only_one:
                break

    # Returns list
    return hitted

def force_buttons(player: Player_entity, buttons: int, once: bool = True, time: float = 0) -> Union[None, int]:
    """Forces the given buttons on the given player for the given time."""

    # Save the current forced buttons
    forced_buttons: int = player.get_datamap_property_int('m_afButtonForced')

    # Apply the given buttons
    player.set_datamap_property_int('m_afButtonForced', forced_buttons|buttons)

    if once:
        # Restore the original buttons after the given time
        player.delay(
            time,
            player.set_datamap_property_int,
            ('m_afButtonForced', forced_buttons))
        return None
    else:
        return forced_buttons

class repeat_functions:
    """
    Class that MUST be implemented.
    Creates repeat functions for class
    """

    repeat_delay = 0
    repeat = RepeatStatus


    def _repeat_start(self) -> bool:
        if self.repeat.status != RepeatStatus.RUNNING:
            self.repeat.start(self.repeat_delay)
            return True
        return False

    def _repeat_stop(self) -> bool:
        if self.repeat.status == RepeatStatus.RUNNING:
            self.repeat.stop()
            return True
        return False


def skill_timings_calculate():
    """ Skill timings reload function """

    global SKILL_TIMINGS

    # Delay round end -> restart
    restart_delay = ConVar('mp_round_restart_delay').get_float()

    # Getting live players
    amount_of_players = server.num_clients()

    if restart_delay < 2:
        SKILL_TIMINGS = (0, 0)
    else:
        delay = restart_delay - 1 - amount_of_players // 5
        SKILL_TIMINGS = (delay, restart_delay-delay)


class WCS_Logger:
    __slots__ = ('file',)

    def __init__(self, path):
        log_path = LOG_PATH / path

        # Does the parent directory exist?
        if not log_path.parent.isdir():

            # Create the parent directory
            log_path.parent.makedirs()

        # Opening file
        self.file = open(log_path, mode='a', encoding='utf-8')

    def unload_instance(self):

        # Closing logs on exit
        self.file.close()

    def __call__(self, prefix: str, msg: Any, console: bool = False):

        msg = msg.replace('\n', '\n---> ')

        # Writing to file with prefix-s
        self.file.write(f"[{datetime.today().strftime('%H:%M:%S')}"
                        f" {prefix.upper().rjust(12):.12}] {msg}\n")

        # Quickly append
        self.file.flush()

        # Echo to console if needed
        if console:
            print(f'[WCSSkills {prefix.upper().rjust(7):.7}] {msg}')

wcs_logger = WCS_Logger(PATH_TO_LOG)


# Logging exceptions
@ExceptHook
def exception_log(exc_type, value, trace_back):
    PtH = trace_back.tb_frame.f_code.co_filename
    index = PtH.find('WCSSkills')
    if index != -1:
        PtH = '..\\'+PtH[PtH.find('WCSSkills')+10:]

    first_line = trace_back.tb_frame.f_code.co_firstlineno
    try: wcs_logger('exception', f'{exc_type.__qualname__} in "{PtH}", line {first_line}')
    except ValueError: return
