# ../WCSSkills/admin/functions.py
# =============================================================================
# >> Imports
# =============================================================================

# Source.Python
# HudMsg
from messages.base import HudMsg
# Colors
from colors import Color

# =============================================================================
# >> All
# =============================================================================

__all__ = (
    'print_origin',
    'print_eye_location',
    'print_view_coordinates',
    'print_entity',
    'hudmsg'
)

# =============================================================================
# >> Functions
# =============================================================================

def print_origin(target):
    return f"Origin {target.origin[0]:.0f} {target.origin[1]:.0f} {target.origin[2]:.0f}"
def print_eye_location(target):
    return f"Eyes   {target.eye_location[0]:.0f} {target.eye_location[1]:.0f} {target.eye_location[2]:.0f}"
def print_view_coordinates(target):
    return f"View   {target.eye_location[0]:.0f} {target.eye_location[1]:.0f} {target.eye_location[2]:.0f}"
def print_entity(target):
    ent = target.view_entity
    if ent is None: ent = '—'
    else: ent = ent.classname
    return f"Entity {ent}"

def hudmsg(target, function: callable, y, x, channel: int, color: tuple, hold_time: float):
    HudMsg(function(target), y=y, x=x, channel=channel, color1=Color(*color),
           hold_time=hold_time).send(target.index)