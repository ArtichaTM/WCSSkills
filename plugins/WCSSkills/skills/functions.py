# ../WCSSkills/skills/functions.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
from listeners.tick import Delay
# =============================================================================
# >> All
# =============================================================================

__all__ = (
    'paralyze',
)

# =============================================================================
# >> Functions
# =============================================================================

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