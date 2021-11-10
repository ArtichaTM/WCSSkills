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
from typing import Union, Any, List

# Source.Python imports
from hooks.exceptions import ExceptHook
# Helpers
# Entities
from entities.entity import BaseEntity
from entities.constants import WORLD_ENTITY_INDEX
# Engine trace
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import engine_trace
from engines.trace import ContentMasks
# Iters
from filters.players import PlayerIter
# Repeat
from listeners.tick import RepeatStatus
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
# Constants
from WCSSkills.other_functions.constants import PATH_TO_LOG
# from WCSSkills.wcs.wcsplayer import WCS_Players
# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = ('player_indexes',
           'open_players',
           'force_buttons',
           'repeat_functions',
           'wcs_logger',
           'skill_timings_calculate'
           )

# =============================================================================
# >> Functions
# =============================================================================

# Return all players indexes
player_indexes = lambda : [player.index for player in PlayerIter()]

required_xp = lambda lvl: ((80 * lvl+1 ** 0.5) ** 2) ** 0.5
next_lvl_xp_calculate = lambda lvl: required_xp(lvl) - random.randint(0, int(required_xp(lvl) // 2))
#
# @EntityPreHook(EntityCondition.is_player, 'emit_sound')
# def xz(*args):
#     pass


def open_players(entity: Player_entity,
                 form,
                 only_one: bool = False,
                 same_team: bool = False) -> List[Entity_entity]:
    """ This function checks for other players, that can be hit by entity

    :param entity: Origin enitity, from whom are going rays
    :param form: ImmuneType
    :param only_one: List all entity's or return on gathering one
    :param same_team: List only entitys in seperate teams
    :return: List with Entity's
    """

    # Creating list
    can_hit_players = []

    # Iterating over all alive players
    for user in PlayerIter('alive'):

        # Checking, if selected entity isn't our player
        if user.index == entity.index:
            continue

        # Checking for team equality
        elif user.team_index == entity.team_index and not same_team:
            continue

        # # Abort, if player is not WCS_Player
        # try: wcs_user = WCS_Players[user.userid]
        # except KeyError: continue

        # # Checking for immune
        # if form in wcs_user.immunes['aimbot'] and not ignore_immune:
        #     continue

        # Get the entity's origin
        try: origin: Vector = entity.eye_location
        except AttributeError: origin: Vector = entity.origin

        # Get a Ray object of the entity physic box
        ray = Ray(origin, user.origin)

        # Get a new GameTrace instance
        trace = GameTrace()

        # Trace to player
        engine_trace.clip_ray_to_entity(
            ray, ContentMasks.ALL, BaseEntity(WORLD_ENTITY_INDEX), trace)

        # Hit something?
        if not trace.did_hit():

            # Not hit! Player can be shot
            can_hit_players.append(user)

            if only_one:
                break

    # Returns list
    return can_hit_players

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

    def close(self):
        self._repeat_stop()


def skill_timings_calculate() -> float:
    """
    Skill timings calculate function

    :return: float = delay in float
    """

    # Delay round end -> restart
    restart_delay = ConVar('mp_round_restart_delay').get_float()

    # Getting live players
    amount_of_players = server.num_players

    if restart_delay < 2:
        return 0
    else:
        delay = 1 + amount_of_players // 5
        return restart_delay - random.uniform(0, delay)


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
def exception_log(exc_type, _, trace_back):
    PtH = trace_back.tb_frame.f_code.co_filename
    index = PtH.find('WCSSkills')
    if index != -1:
        PtH = '..\\'+PtH[PtH.find('WCSSkills')+10:]

    first_line = trace_back.tb_frame.f_code.co_firstlineno
    try: wcs_logger('exception', f'{exc_type.__qualname__} in "{PtH}", line {first_line}')
    except ValueError: return
