# ../WCSSkills/skills/functions.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python imports
from typing import Union

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
    'on_take_magic_damage'
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


def paralyze(owner, victim, length: float) -> bool:
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

    return True