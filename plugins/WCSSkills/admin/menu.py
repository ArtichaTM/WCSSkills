# ../WCSSkills/admin/menu.py
"""
This file is working with admin radio menu
"""
# =============================================================================
# >> Imports
# =============================================================================
# Python Imports
from datetime import datetime

# Source.Python
# Menu functions
from menus import Text
from menus import SimpleMenu
from menus import SimpleOption
from menus import PagedOption
# SayText2
from messages.base import SayText2

# Plugin imports
# Admin action functions
from WCSSkills.admin.admin_actions import *
# Left players JSON
from WCSSkills.db.admin import DC_history
# Left player class
from WCSSkills.db.functions import Disconnected_user
# Punishment Enums
from WCSSkills.admin.constants import Punishment_reasons
from WCSSkills.admin.constants import Punishment_duration
from WCSSkills.admin.constants import MoveTypes
# WCS_Player
from WCSSkills.wcs.WCSP.wcsplayer import WCS_Player, WCS_Players
# Modified default PagedMenu
from WCSSkills.menus.radio import PagedMenu

# =============================================================================
# >> Admin
# =============================================================================

def AdminMain(player):
    menu = SimpleMenu(select_callback=AdminMain_callback)

    if 'wcs_admin_all' in player.permissions:
        menu.append(Text('Админ'))
    elif 'wcs_admin_wcs_admin' in player.permissions:
        menu.append(Text('WCS Админ'))
    elif 'wcs_admin_base' in player.permissions:
        menu.append(Text('Основной Админ'))
    else:
        menu.append(Text('Модифицированный'))

    menu.append(Text(' '))

    menu.append(SimpleOption(1, 'Игроки', 'players'))
    menu.append(SimpleOption(2, 'Вышедшие игроки', 'left'))

    menu.send(player.index)

def AdminMain_callback(*args):
    choice = args[2].value
    choice_player = WCS_Player.from_index(args[1])
    if choice == 'players':
        AdminPlayers(choice_player)
    if choice == 'left':
        Admin_left_players(choice_player)

# noinspection PyTypeChecker
def AdminPlayers(player):
    menu = PagedMenu(title='Игроки',
                     select_callback=AdminPlayers_callback,
                     parent_menu = AdminMain,
                     parent_menu_args = (player,))

    for player_wcs in WCS_Players.values():
        menu.append(PagedOption(f"{player_wcs.name}", value = player_wcs))

    menu.send(player.index)

def AdminPlayers_callback(*args):
    AdminPlayers_player(WCS_Player.from_index(args[1]),
                        args[2].value, AdminPlayers)

# noinspection PyTypeChecker
def AdminPlayers_player(player, target, parent=None):
    menu = PagedMenu(title=f'Управление {target.name:.10}',
                     select_callback=AdminPlayers_player_callback)
    if parent is not None:
        menu.parent_menu = parent
        menu.parent_menu_args = (player, )

    # Base admin rights
    # Kick
    if 'wcs_admin_kick' in player.permissions and target.is_player:
        menu.append(PagedOption('Кик', value=(target ,'kick')))
    # Ban
    if 'wcs_admin_ban' in player.permissions:
        menu.append(PagedOption('Бан', value=(target, 'ban')))
    # Mute
    if 'wcs_admin_mute' in player.permissions:
        menu.append(PagedOption('Мут', value=(target, 'mute')))
    # Slay
    if 'wcs_admin_slay' in player.permissions and target.is_player:
        menu.append(PagedOption('Убить', value=(target, 'slay')))

    # WCS admin rights
    # Freeze
    if 'wcs_admin_move_type' in player.permissions and target.is_player:
        menu.append(PagedOption('Смена вида движения',
                                value=(target, 'move_type')))
    # Paralyze
    if 'wcs_admin_paralyze' in player.permissions and target.is_player:
        menu.append(PagedOption('Паралич', value=(target, 'paralyze')))
    # Skill lvl decrease
    # if 'wcs_admin_set_achieved_skill_lvl' in player.permissions:
    #     menu.append(PagedOption('Уменьшение уровеня ',
    #                  value=(target, 'skill lvl decrease')))
    # Block skill for map
    # if 'wcs_admin_block_skill' in player.permissions:
    #     menu.append(PagedOption('Блок навыка',
    #                             value=(target, 'skill block')))
    # Block all skills for a map
    # if 'wcs_admin_block_skills' in player.permissions:
    #     menu.append(PagedOption('Блок навыков',
    #                             value=(target, 'skills block')))
    # Deactivate all skills for a round
    if 'wcs_admin_deactivate_skills' in player.permissions and target.is_player:
        menu.append(PagedOption('Отключение навыков на раунд',
                            value=(target, 'skills deactivate')))
    # if 'wcs_admin_give_lvls' in player.permissions:
    #     menu.append(PagedOption('Дать уровней',
    #                             value=(target, 'give lvls')))
    if 'wcs_admin_heal' in player.permissions and target.is_player:
        menu.append(PagedOption('Исцелить', value=(target, 'heal')))

    menu.send(player.index)

def AdminPlayers_player_callback(_, index, choice):
    admin = WCS_Player.from_index(index)
    target, command = choice.value

    Admin_reasons(admin, target, command)

# noinspection PyTypeChecker
def Admin_reasons(admin, target, command):
    menu = PagedMenu(title='Причина',
                     select_callback=Admin_reasons_callback,
                     parent_menu=AdminPlayers_player,
                     parent_menu_args=(admin, target, ))

    if command == 'move_type':
        Admin_move_types(admin, target)
    else:
        for reason in Punishment_reasons:
            menu.append(PagedOption(f"{reason.value[1]}",
                                value = (target, command, reason)))
        menu.send(admin.index)

def Admin_reasons_callback(_, index, choice):
    admin = WCS_Player.from_index(index)
    target, command, reason = choice.value
    Admin_time(admin, target, command, reason)

# noinspection PyTypeChecker
def Admin_time(admin, target, command, reason  = None):
    menu = PagedMenu(title='Длительность',
                     select_callback=Admin_time_callback,
                     parent_menu=Admin_reasons,
                     parent_menu_args=(admin, target, reason))


    if command == 'skills deactivate':
        admin_skills_deactivate(admin, target, reason)
    elif command == 'heal':
        admin_heal(admin, target, reason)
    elif command == 'slay':
        admin_slay(admin, target, reason)
    elif command == 'kick':
        admin_kick(admin, target, reason)
    elif command == 'paralyze':
        admin_paralyze(admin, target, reason)
    else:
        for time in Punishment_duration:
            menu.append(PagedOption(f"{time.value[1]}",
                                value=(target, command, reason, time)))

    menu.send(admin.index)

def Admin_time_callback(_, index, choice):
    admin = WCS_Player.from_index(index)
    target, command, reason, time = choice.value

    if command == 'ban':
        admin_ban(admin, target, reason, time)
        return
    elif command == 'mute':
        admin_mute(admin, target, reason, time)
        return

    SayText2(f"{reason}, {time}").send()

# noinspection PyTypeChecker
def Admin_move_types(admin, target):
    menu = PagedMenu(title='Виды движения',
                     select_callback=Admin_move_types_callback,
                     parent_menu=AdminPlayers_player,
                     parent_menu_args=(admin, target))
    current = target.move_type
    for movetype in MoveTypes:
        if movetype.value[0] == current:
            menu.append(PagedOption(f"{movetype.value[1]}",
                value=(target, movetype.value[0]),
                highlight=False, selectable=False))
        else:
            menu.append(PagedOption(f"{movetype.value[1]}",
                value=(target, movetype.value[0])))

    menu.send(admin.index)

def Admin_move_types_callback(_, index, choice):
    admin = WCS_Player.from_index(index)
    target, move_type = choice.value
    admin_move_type(admin, target, move_type)

# noinspection PyTypeChecker
def Admin_left_players(admin):
    menu = PagedMenu(title='Игроки',
                     select_callback=Admin_left_players_callback,
                     parent_menu = AdminMain,
                     parent_menu_args = (admin,))

    for player_data in DC_history:
        date = datetime.fromtimestamp(player_data[0])
        date = date.strftime("%m.%d %H:%M")
        name = player_data[1]
        menu.append(PagedOption(f"[{date}] {name:.10}", value = player_data))

    menu.send(admin.index)

def Admin_left_players_callback(*args):
    admin = WCS_Player.from_index(args[1])
    target_data = args[2].value
    target = Disconnected_user.create(target_data[1], target_data[2], target_data[3])
    if target.is_player:
        SayText2(f"\2[SYS]\1 Внимание! Выбранный игрок на сервере").send(admin.index)
    AdminPlayers_player(admin, target, Admin_left_players)