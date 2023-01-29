# ../WCSSkills/skills/functions.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python imports
import random
from typing import Union, Callable
from random import uniform

# Source.Python Imports
# MathLib
from mathlib import Vector
# Delay
from listeners.tick import Delay
# Entities
from entities import TakeDamageInfo
from entities.entity import Entity, BaseEntity
from entities.helpers import index_from_pointer
from entities.hooks import EntityPreHook, EntityCondition
# Entity constants
from entities.constants import WORLD_ENTITY_INDEX
# Engine trace
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import engine_trace
from engines.trace import ContentMasks

# Plugin Imports
# Typing
from ..python.types import *
# Constants
from ..other_functions.constants import WCS_DAMAGE_ID
from ..other_functions.constants import ADMIN_DAMAGE_ID
from ..other_functions.constants import ImmuneTypes
from ..other_functions.constants import ImmuneReactionTypes
from ..other_functions.constants import AffinityTypes

# =============================================================================
# >> All
# =============================================================================

__all__ = (
    'immunes_check',
    'chance',
    'on_take_physical_damage',
    'on_take_magic_damage',
    'paralyze',
    'active_weapon_drop',
    'screen_angle_distortion',
    'throw_player_upwards',
    'will_be_stuck',
    'affinity_check'
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


@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def skills_on_take_damage(args) -> Union[None, bool]:
    """ Take damage hook """

    # Getting TameDamageInfo
    # info = make_object(TakeDamageInfo, args[1])
    info = TakeDamageInfo._obj(args[1])

    # Checking if damage was dealt by admin
    if info.type == ADMIN_DAMAGE_ID:

        # Yes, it is. Canceling skill checks
        return

    # If damage dealt by magic dmg, iter over magic_damage functions
    if info.type == info.type | WCS_DAMAGE_ID:

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


def immunes_check(victim: wcs_player_entity,
                  form: ImmuneTypes,
                  immune_type: str,
                  deflect_target: Callable,
                  deflect_arguments: tuple,
                  ):
    """ Decides, which immune (deflect/immune) is worked, if any
    :param victim: victim's WCS_Player
    :param form: ImmuneTypes form of attack
    :param immune_type: Which immune to check (paralyze/toss/...)
    :param deflect_target: function, the works on deflect
    :param deflect_arguments: arguments passed to deflect function
    :return: ImmuneReactionTypes
    """

    # Immunities check

    # If form is penetrate, return passed
    if form is ImmuneTypes.Penetrate: return ImmuneReactionTypes.Passed

    # If type of attack in immunities
    if form in victim.immunes[immune_type]: return ImmuneReactionTypes.Immune
    # Or victim has counter to all types
    if ImmuneTypes.Any in victim.immunes[immune_type]: return ImmuneReactionTypes.Immune

    # Else if victim deflect attack
    if form << 1 in victim.immunes[immune_type]:

        # Passing to deflect function with args
        deflect_target(*deflect_arguments)

        # Returning Deflect
        return ImmuneReactionTypes.Deflect

    # If no immunities triggered, return Passed
    return ImmuneReactionTypes.Passed


def paralyze(
        owner: wcs_player_entity,
        victim: wcs_player_entity,
        length: float,
        form) -> ImmuneReactionTypes:
    """ Stops player camera rotate and movement

    :param owner: Initiator of paralyze
    :param victim: Target of paralyze
    :param length: Amount of time to freeze player
        movement and camera rotate
    :param form: Type of paralyze (Aura/Default/...) (ImmuneTypes)
    :return: ImmuneReactionTypes type.
        1 - passed
        2 - immune
        3 - deflect
    """

    result = immunes_check(victim, form, 'paralyze',
                   # Deflect func and args
                   paralyze, victim, owner, length, ImmuneTypes.Any)

    # Returning result, if skill is not passed
    if result is not ImmuneReactionTypes.Passed: return result

    try: victim.paralyze_length
    except AttributeError:
        setattr(victim, 'frozen_length', Delay(0, lambda: None))

    # Paralyzed?
    if victim.get_frozen() is False:

        # No, then paralyzing
        victim.set_frozen(True)

        # And adding cooldown, that DeParalyze victim
        victim.paralyze_length = Delay(length, victim.set_frozen, args=(False,))

    # Paralyzed => have frozen_length
    else:

        # Adding time to paralyze
        victim.paralyze_length.exec_time += length

    return ImmuneReactionTypes.Passed


def active_weapon_drop(
        owner: wcs_player_entity,
        victim: wcs_player_entity,
        form
        ):

    result = immunes_check(victim, form, 'active_weapon_drop',
                   # Deflect func and args
                   active_weapon_drop, victim, owner, ImmuneTypes.Any)

    # Returning result, if skill is not passed
    if result is not ImmuneReactionTypes.Passed: return result

    # Dropping weapon
    victim.drop_weapon(victim.active_weapon)

    # Success return
    return ImmuneReactionTypes.Passed


def screen_angle_distortion(
        owner: wcs_player_entity,
        victim: wcs_player_entity,
        amount: float,
        form):

    result = immunes_check(victim, form, 'screen_rotate',
                   # Deflect func and args
                   screen_angle_distortion, victim, owner, amount, ImmuneTypes.Any)
    # Returning result, if skill is not passed
    if result is not ImmuneReactionTypes.Passed: return result

    # Normalize amount
    amount = 180 if amount > 180 else abs(int(amount))

    # Creating different values
    amount1 = random.randint(0, amount)
    amount2 = (amount - amount1)/2

    # Getting initial angle
    angle = victim.view_angle

    # Making distortion to horizontal rotate
    angle[0] += uniform(-amount1, +amount1)
    # Making distortion to vertical rotate
    angle[1] += uniform(-amount2, +amount2)

    # Applying angle
    victim.view_angle = angle

    # Success return
    return ImmuneReactionTypes.Passed


def throw_player_upwards(
        owner: wcs_player_entity,
        victim: wcs_player_entity,
        power: float,
        form):

    result = immunes_check(victim, form, 'toss_upwards',
                   # Deflect func and args
                   throw_player_upwards, victim, owner, power, ImmuneTypes.Any)
    # Returning result, if skill is not passed
    if result is not ImmuneReactionTypes.Passed: return result

    # Getting velocity
    vel = victim.velocity

    # Applying power to the upwards dimension
    vel[2] += power

    # Applying new velocity to player
    victim.teleport(velocity=vel)

    # Success return
    return ImmuneReactionTypes.Passed


def will_be_stuck(entity: Entity_entity, position: Vector) -> bool:
    """ Checks, will be entity stuck if teleported to this position

    :param entity: Entity that we check for solid in
    :param position: Position where we check for stuck
    :return: Bool, will entity be stuck in this position
    """

    # Get a dot ray object of the entity physic box
    ray = Ray(position, position, entity.mins, entity.maxs)

    # Get a new GameTrace instance
    trace = GameTrace()

    # Trace in point
    engine_trace.clip_ray_to_entity(
        ray, ContentMasks.ALL, BaseEntity(WORLD_ENTITY_INDEX), trace)

    # Return False if hit something
    if trace.did_hit(): return True

    # Otherwise return True
    else: return False


def affinity_check(player, affinity: AffinityTypes) -> bool:
    """Checks for owner affinity. Return False, if owner affinity is other"""

    # User doesn't have any affinity. Add current, return "success"
    if player.affinity == AffinityTypes.NONE:
        player.affinity = affinity
        return True

    # User under current affinity. Return "success"
    elif player.affinity == affinity: return True

    # User belongs to another group. Return "error"
    else: return False
