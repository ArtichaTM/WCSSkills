# ../WCSSkills/skills/functions.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python imports
import random
from typing import Union
from WCSSkills.python.types import wcs_player_entity
from random import uniform

# Source.Python Imports
# Delay
from listeners.tick import Delay
# Entities
from entities import TakeDamageInfo
from entities.entity import Entity
from entities.helpers import index_from_pointer
from entities.hooks import EntityPreHook, EntityCondition
# Constants
from WCSSkills.other_functions.constants import WCS_DAMAGE_ID
from WCSSkills.other_functions.constants import ADMIN_DAMAGE_ID
from WCSSkills.other_functions.constants import ImmuneTypes
from WCSSkills.other_functions.constants import ImmuneReactionTypes

# =============================================================================
# >> All
# =============================================================================

__all__ = (
    'chance',
    'on_take_physical_damage',
    'on_take_magic_damage',
    'paralyze',
    'active_weapon_drop',
    'screen_angle_distortion',
    'Throw_player_upwards'
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

# Take damage hook
@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def skills_on_take_damage(args) -> Union[None, bool]:

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

def immunes_check(victim, form, immune_type, deflect_target, *args):

    # # Immune check

    # If type of attack in immunes
    if form in victim.immunes[immune_type]: return ImmuneReactionTypes.Immune

    # Or victim has counter to all types
    elif ImmuneTypes.Any in victim.immunes[immune_type]: return ImmuneReactionTypes.Immune

    # Else if victim deflect attack
    elif form << 1 in victim.immunes[immune_type]:

        # Passing to deflect function with args
        deflect_target(*args)

        # Returning Deflect
        return ImmuneReactionTypes.Deflect

    # If no immunes triggered, return Passed
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
        1 - worked
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

def Throw_player_upwards(
        owner: wcs_player_entity,
        victim: wcs_player_entity,
        power: float,
        form):

    result = immunes_check(victim, form, 'toss_upwards',
                   # Deflect func and args
                   Throw_player_upwards, victim, owner, power, ImmuneTypes.Any)
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