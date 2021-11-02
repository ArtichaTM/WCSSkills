# ../WCSSkills/admin/admin_actions.py
"""
This file is working with wcs radios menu
"""

# =============================================================================
# >> Imports
# =============================================================================
# Source.Python
# SayText2
from messages.base import SayText2
# Delay
from listeners.tick import Delay
# Mute manager
from players.voice import mute_manager

# Plugin imports
# Punishment types
from WCSSkills.admin.constants import Punishment_types
from WCSSkills.admin.constants import MoveTypes
from entities.constants import MoveType
# DB
from WCSSkills.db.admin import DB_admin
# Logging
from WCSSkills.other_functions.functions import wcs_logger

# =============================================================================
# >> All
# =============================================================================
__all__ = ('admin_kick',
           'admin_slay',
           'admin_heal',
           'admin_skills_deactivate',
           'admin_paralyze',
           'admin_move_type',
           'admin_ban',
           'admin_mute'
           )

# =============================================================================
# >> Functions
# =============================================================================

def admin_kick(admin, target, reason):

    # Messaging kick to admin
    SayText2("\2[Admin]\1 Вы кикнули игрока "
             f"\5{target.name}\1").send(admin.index)

    # Adding kick to database
    DB_admin.add_entry(ptype=Punishment_types.KICK.value[0],
                       victim_name=target.name,
                       victim_steamid=target.steamid,
                       victim_ip=target.address,
                       admin_name=admin.name,
                       admin_steamid=admin.steamid,
                       reason=reason.value[0])
    # Kicking
    if reason.value[1] == '—':
        target.kick("Вас кикнули без причины")
    else:
        target.kick(f"Вы кикнуты по причине {reason.value[1].lower()}")

    # Logging
    wcs_logger('admin', f"{admin.name} kicked "
                            f"{target.name} for {reason.name.lower()}")

def admin_slay(admin, target, reason):
    # Messaging kick to admin
    SayText2("\2[Admin]\1 Вы убили игрока "
             f"\5{target.name}\1").send(admin.index)

    # Slaying
    target.take_damage(999999)

    # Notifying admin
    if reason.value[1] == '—':
        SayText2(f"\2[Admin]\1 Вы убиты админом "
                 f"\5{admin.name}\1").send(target.index)
    else:
        SayText2(f"\2[Admin]\1 Вы убиты админом \5{admin.name}\1"
                 f" по причине \5{reason.value[1].lower()}\1").send(target.index)

    # Logging
    wcs_logger('admin', f"{admin.name} slayed "
                            f"{target.name} for {reason.name.lower()}")

def admin_heal(admin, target, reason, amount: int = 100):

    # Messaging skill deactivate to admin
    SayText2("\2[Admin]\1 Вы исцелили игрока "
             f"\5{target.name}\1").send(admin.index)

    # Deactivating
    target.heal(amount, ignore=True)

    # Messaging skill deactivate to target
    if reason.value[1] == '—':
        SayText2(f"\2[Admin]\1 Вы были исцелены админом"
                 f"\5{admin.name}\1").send(target.index)
    else:
        SayText2(f"\2[Admin]\1 Вы были исцелены админом \5{admin.name}\1"
                 f" по причине \5{reason.value[1].lower()}\1").send(target.index)

    # Logging
    wcs_logger('admin', f"{admin.name} healed "
                            f"{target.name} for {reason.name.lower()}")

def admin_skills_deactivate(admin, target, reason):
    # Messaging skill deactivate to admin
    SayText2("\2[Admin]\1 Вы отключили способности игрока "
             f"\5{target.name}\1").send(admin.index)

    # Deactivating
    target.skills_deactivate()

    # Slaying
    if reason.value[1] == '—':
        SayText2(f"\2[Admin]\1 Ваши навыки отключены админом "
                 f"\5{admin.name}\1").send(target.index)
    else:
        SayText2(f"\2[Admin]\1 Ваши навыки отключены админом \5{admin.name}\1"
                 f" по причине \5{reason.value[1].lower()}\1").send(target.index)

    # Logging
    wcs_logger('admin', f"{admin.name} disabled "
                        f"{target.name} skills for {reason.name.lower()}")

def admin_paralyze(admin, target, reason):
    paralyze = target.get_frozen()

    # Target already paralyzed. Abolishing paralyze
    if paralyze:

        # Messaging Abolishment to admin
        SayText2("\2[Admin]\1 Вы сняли паралич с игрока "
                 f"\5{target.name}\1").send(admin.index)

        # Messaging Abolishment to target
        if reason.value[1] == '—':
            SayText2(f"\2[Admin]\1 Паралич снят админом "
                     f"\5{admin.name}\1").send(target.index)
        else:
            SayText2(f"\2[Admin]\1 Паралич снят админом \5{admin.name}\1"
                 f" по причине \5{reason.value[1].lower()}\1").send(target.index)

        # Abolishing
        target.set_frozen(False)

        # Checking for skill paralyze length variable
        if 'paralyze_length' in dir(target):

            # Exist.
            if target.paralyze_length.running is True:

                # Paralyze from it. Cancel it
                target.paralyze_length.cancel()

        # Logging
        wcs_logger('admin', f"{admin.name} denied"
                    f" {target.name} paralyze for {reason.name.lower()}")

    # Target not paralyzed. Paralyzing.
    else:

        # Messaging paralyze to admin
        SayText2("\2[Admin]\1 Вы парализовали "
                 f"\5{target.name}\1").send(admin.index)

        # Messaging paralyze to target
        if reason.value[1] == '—':
            SayText2(f"\2[Admin]\1 Вас парализовал админ "
                     f"\5{admin.name}\1").send(target.index)
        else:
            SayText2(f"\2[Admin]\1 Вас парализовал админ \5{admin.name}\1"
                 f" по причине \5{reason.value[1].lower()}\1").send(target.index)

        # Checking for skill paralyze length variable
        if 'paralyze_length' in dir(target):
            # Adding cooldown, that DeParalyze victim
            target.frozen_length = Delay(30, target.set_frozen, args=(False,))
        target.set_frozen(True)

        # Logging
        wcs_logger('admin', f"{admin.name} paralyzed"
                            f" {target.name} for {reason.name.lower()}")

def admin_move_type(admin, target, move_type):
    name_previous = MoveTypes(target.move_type).value[1].lower()
    name_new = MoveTypes(move_type).value[1].lower()

    # Messaging paralyze to admin
    SayText2("\2[Admin]\1 Вы сменили режим движения игрока "
             f"\5{target.name}\1 с {name_previous} на "
             f"{name_new}").send(admin.index)

    # Messaging paralyze to target
    SayText2("\2[Admin]\1 Ваш режим движения изменён с "
            f"\5{name_previous}\1 на \5{name_new}\1 админом "
            f"\5{admin.name}\1").send(target.index)

    # Logging
    wcs_logger('admin', f"{admin.name} changed "
                            f"{target.name} movement type from "
                            f"{MoveTypes(target.move_type).name} to "
                            f"{MoveTypes(move_type).name}")

    # Changing movement type
    target.move_type = MoveType(move_type)

def admin_ban(admin, target, reason, duration):

    # Messaging kick to admin
    SayText2("\2[Admin]\1 Вы забанили игрока "
             f"\5{target.name}\1 по причине {reason.value[1]} "
             f"{duration}").send(admin.index)

    # Adding kick to database
    DB_admin.add_entry(ptype=Punishment_types.BAN.value[0],
                       victim_name=target.name,
                       victim_steamid=target.steamid,
                       victim_ip=target.address,
                       admin_name=admin.name,
                       admin_steamid=admin.steamid,
                       reason=reason.value[0],
                       duration=duration.value[0])

    reason_temp = reason.value[1]
    duration_temp = duration.value[1]

    # Kicking
    if reason_temp == '—':
        target.kick(f"Вы забанены {'' if duration_temp.lower() == 'навсегда' else 'на '}"
                    f"{duration_temp.lower()}")
    else:
        target.kick(f"Вы забанены по причине "
                f"{reason_temp.lower()} {'' if duration_temp.lower() == 'навсегда' else 'на '}{duration_temp.lower()}")

    # Logging
    wcs_logger('ban admin', f"{admin.name} banned "
                f"{target.name} for {reason.name.lower()} for {duration.name}")

def admin_mute(admin, target, reason, duration):

    # Messaging mute to admin
    SayText2("\2[Admin]\1 Вы замутили игрока "
             f"\5{target.name}\1 по причине {reason.value[1]} "
             f"{duration}").send(admin.index)

    # Adding mute to database
    DB_admin.add_entry(ptype=Punishment_types.KICK.value[0],
                       victim_name=target.name,
                       victim_steamid=target.steamid,
                       victim_ip=target.address,
                       admin_name=admin.name,
                       admin_steamid=admin.steamid,
                       reason=reason.value[0])

    # Muting player
    mute_manager.mute_player(target.index)

    # Logging
    wcs_logger('admin', f"{admin.name} muted "
                            f"{target.name} for {reason.name.lower()}")