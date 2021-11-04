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
from listeners.tick import Delay
from entities import TakeDamageInfo
from entities.entity import Entity
from entities.helpers import index_from_pointer
# Hooks
from entities.hooks import EntityPreHook, EntityCondition
# WCS_damage id:
from WCSSkills.other_functions.constants import WCS_DAMAGE_ID
from WCSSkills.other_functions.constants import ADMIN_DAMAGE_ID

# =============================================================================
# >> All
# =============================================================================

__all__ = (
    'paralyze',
    'on_take_physical_damage',
    'on_take_magic_damage',
    'active_weapon_drop',
    'screen_angle_distortion'
)

# =============================================================================
# >> Global variables
# =============================================================================

on_take_physical_damage = set()
on_take_magic_damage = set()


# =============================================================================
# >> Functions
# =============================================================================

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


def paralyze(victim: wcs_player_entity,
             length: float,
             form) -> bool:
    try: victim.paralyze_length
    except AttributeError:
        setattr(victim, 'frozen_length', Delay(0, lambda: None))

    # Immune check
    if form in victim.immunes['paralyze']: return False

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

    return True

def active_weapon_drop(victim: wcs_player_entity, form):

    # Immune check
    if form in victim.immunes['active_weapon_drop']: return False

    # Dropping weapon
    victim.drop_weapon(victim.active_weapon)

    # Success return
    return True

def screen_angle_distortion(victim: wcs_player_entity, form, amount):

    # Immune check
    if form in victim.immunes['screen_rotate']: return False

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
    return True