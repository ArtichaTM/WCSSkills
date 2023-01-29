# ../WCSSkills/admin/menu.py
"""
This file is working with admin radio menu
"""
# =============================================================================
# >> Imports
# =============================================================================
# Python Imports
# Typing
from typing import Union
# Dates
from datetime import datetime

# Source.Python
# Menu functions
from menus import Text
from menus import SimpleMenu
from menus import SimpleOption
from menus import PagedOption
# SayText2
from messages.base import SayText2
# Commands filters
from commands import CommandReturn
from commands.say import register_say_filter
from commands.say import unregister_say_filter
# Tick repeat
from listeners.tick import Repeat
from listeners.tick import RepeatStatus

# Plugin imports
# Admin action functions
from .admin_actions import *
# Other functions
from .functions import *
# Left players JSON
from ..db.admin import DC_history
# Left player class
from ..db.functions import Disconnected_user
# Punishment Enums
from .constants import Punishment_reasons
from .constants import Punishment_duration
from .constants import MoveTypes
# WCS_Player
from ..wcs.WCSP.wcsplayer import WCS_Player
# Modified default PagedMenu
from ..menus.radio import PagedMenu
from ..menus.functions import RMSound
# To receive player information
from .. import db


# =============================================================================
# >> Admin
# =============================================================================

def AdminMain(player):
    menu = SimpleMenu(select_callback=AdminMain_callback)

    if 'wcss_admin.all' in player.permissions:
        menu.append(Text('Главный админ'))
    elif 'wcss_admin.base' in player.permissions:
        menu.append(Text('Основной Админ'))
    else:
        menu.append(Text('Модифицированный'))

    menu.append(Text(' '))

    menu.append(SimpleOption(1, 'Игроки', 'players'))
    menu.append(SimpleOption(2, 'Вышедшие игроки', 'left'))
    # TODO: Check for player permission
    menu.append(SimpleOption(3, 'Функции', 'functions'))

    menu.send(player.index)

def AdminMain_callback(_, index, choice):
    choice = choice.value
    admin = WCS_Player.from_index(index)
    if choice == 'players':
        AdminPlayers(admin)
    if choice == 'left':
        Admin_left_players(admin)
    if choice == 'functions':
        Admin_functions(admin)


def AdminPlayers(player: Union[Disconnected_user, WCS_Player]):
    menu = PagedMenu(title='Игроки',
                     select_callback=AdminPlayers_callback,
                     parent_menu = AdminMain,
                     parent_menu_args = (player,))

    for player_wcs in WCS_Player.iter():
        menu.append(PagedOption(f"{player_wcs.name}", value = player_wcs))

    menu.send(player.index)

def AdminPlayers_callback(*args):
    AdminPlayers_player(WCS_Player.from_index(args[1]),
                        args[2].value)


def AdminPlayers_player(player: WCS_Player, target: Union[Disconnected_user, WCS_Player]):
    menu = PagedMenu(title = f'Управление {target.name:.10}',
                     select_callback = AdminPlayers_player_callback,
                     parent_menu = AdminPlayers,
                     parent_menu_args = (player,)
                     )

    # Base admin rights
    # View information about him
    if 'wcss_admin.view_information' in player.permissions:
        menu.append(PagedOption('Информация', value=(target ,'info')))
    # Kick
    if 'wcss_admin.kick' in player.permissions and target:
        menu.append(PagedOption('Кик', value=(target ,'kick')))
    # Ban
    if 'wcss_admin.ban' in player.permissions:
        menu.append(PagedOption('Бан', value=(target, 'ban')))
    # Mute
    if 'wcss_admin.mute' in player.permissions:
        menu.append(PagedOption('Мут', value=(target, 'mute')))
    # Slay
    if 'wcss_admin.slay' in player.permissions and target:
        menu.append(PagedOption('Убить', value=(target, 'slay')))

    # WCS admin rights
    # Freeze
    if 'wcss_admin.move_type' in player.permissions and target:
        menu.append(PagedOption('Смена вида движения',
                                value=(target, 'move_type')))
    # Paralyze
    if 'wcss_admin.paralyze' in player.permissions and target:
        menu.append(PagedOption('Паралич', value=(target, 'paralyze')))
    # Skill lvl decrease
    # if 'wcss_admin.set_achieved_skill_lvl' in player.permissions:
    #     menu.append(PagedOption('Уменьшение уровня ',
    #                  value=(target, 'skill lvl decrease')))
    # Block skill for map
    # if 'wcss_admin.block_skill' in player.permissions:
    #     menu.append(PagedOption('Блок навыка',
    #                             value=(target, 'skill block')))
    # Block all skills for a map
    # if 'wcss_admin.block_skills' in player.permissions:
    #     menu.append(PagedOption('Блок навыков',
    #                             value=(target, 'skills block')))
    # Deactivate all skills for a round
    if 'wcss_admin.deactivate_skills' in player.permissions and target:
        menu.append(PagedOption('Отключение навыков на раунд',
                            value=(target, 'skills deactivate')))
    if 'wcss_admin.give_lvls' in player.permissions:
        menu.append(PagedOption('Дать уровней',
                                value=(target, 'give levels')))
    if 'wcss_admin.heal' in player.permissions and target:
        menu.append(PagedOption('Исцелить', value=(target, 'heal')))

    menu.send(player.index)

def AdminPlayers_player_callback(_, index, choice):
    admin = WCS_Player.from_index(index)
    target, command = choice.value

    if command == 'heal':

        # Getting player
        player = WCS_Player.from_index(index)

        # Saving kb info to enter_temp
        player.enter_temp = ('health_request_solver', choice.value)

        # Notifying player
        SayText2("\2Напишите число в чат.\1").send(player.index)
        SayText2("\2Введите STOP для отмены.\1").send(player.index)

        # Sound
        RMSound.next(player)

        # Try to register filter command (function can be registered before)
        try: register_say_filter(health_request_solver)
        except ValueError: pass

        # Returning to avoid double calls
        return

    elif command == 'give levels':

        # Getting player
        player = WCS_Player.from_index(index)

        # Saving kb info to enter_temp
        player.enter_temp = ('give_levels_solver', choice.value)

        # Notifying player
        SayText2("\2Напишите число в чат.\1").send(player.index)
        SayText2("\2Введите STOP для отмены.\1").send(player.index)

        # Sound
        RMSound.next(player)

        # Try to register filter command (function can be registered before)
        try: register_say_filter(give_levels_solver)
        except ValueError: pass

        # Returning to avoid double calls
        return

    if command == 'info':

        # If player requesting info, targeting him to info function
        AdminPlayers_player_info(WCS_Player.from_index(index), target)

        # Returning to avoid double calls
        return

    Admin_reasons(admin, target, command)

def health_request_solver(command, index, _):

    # Getting starter info
    player = WCS_Player.from_index(index)

    # If enter_temp is None, player is not using kb functions
    if player.enter_temp is None:

        # Then pass him
        return CommandReturn.CONTINUE

    # He's using kb, but not this function
    elif player.enter_temp[0] != 'health_request_solver':

        # Then pass him, to allow other filters work
        return CommandReturn.CONTINUE

    # This is our user

    # Getting target to give health
    target: WCS_Player = player.enter_temp[1][0]

    # Getting his command
    entered = command.command_string

    # Requested stop
    if entered[:4] == 'STOP' or entered[:4] == 'stop':

        # Unregister filter
        unregister_say_filter(health_request_solver)

        # Sending previous menu
        AdminPlayers_player(player, target)

        # Clearing player temp
        player.enter_temp = None

        # Blocking command
        return CommandReturn.BLOCK

    # Is his input really a number?
    try: entered = int(entered)

    # No
    except ValueError:

        # Notifying user about error
        SayText2(f"\2Введено некорректное значение\1").send(index)

        # Blocking command
        return CommandReturn.BLOCK

    # Should be above or equal 0
    entered = abs(entered)

    # Adding health to target player
    target.heal(entered, True)

    # Notifying target
    SayText2(f"\2[Admin]\1 Админ \5{player.name}\1 добавил вам \5{entered}\1"
             f" здоровья").send(target.index)

    # Notifying admin
    SayText2(f"\2[Admin]\1 Вы добавили \5{entered}\1 здоровья"
             f" игроку \5{target.name}\1").send(index)

    # Unregistering current function from message check
    unregister_say_filter(health_request_solver)

    # Blocking message
    return CommandReturn.BLOCK

def give_levels_solver(command, index, _):

    # Getting starter info
    player = WCS_Player.from_index(index)

    # If enter_temp is None, player is not using kb functions
    if player.enter_temp is None:

        # Then pass him
        return CommandReturn.CONTINUE

    # He's using kb, but not this function
    elif player.enter_temp[0] != 'give_levels_solver':

        # Then pass him, to allow other filters work
        return CommandReturn.CONTINUE

    # This is our user

    # Getting target to give health
    target: WCS_Player = player.enter_temp[1][0]

    # Getting his command
    entered = command.command_string

    # Requested stop
    if entered[:4] == 'STOP' or entered[:4] == 'stop':

        # Unregister filter
        unregister_say_filter(health_request_solver)

        # Sending previous menu
        AdminPlayers_player(player, target)

        # Clearing player temp
        player.enter_temp = None

        # Blocking command
        return CommandReturn.BLOCK

    # Is his input really a number?
    try: entered = int(entered)

    # No
    except ValueError:

        # Notifying user about error
        SayText2(f"\2Введено некорректное значение\1").send(index)

        # Blocking command
        return CommandReturn.BLOCK

    # Should be above or equal 1
    entered = abs(entered)

    # Validation
    if entered == 0:

        # Notifying admin wrong number
        SayText2(f"\2Невозможно выдать игроку 0 уровней\1").send(index)

        # Blocking command
        return CommandReturn.BLOCK

    # Adding levels to target player
    target.lk_lvls += entered

    # Notifying target
    SayText2(f"\2[Admin]\1 Админ \5{player.name}\1 добавил вам \5{entered}\1"
             f" уровней в банк").send(target.index)

    # Notifying admin
    SayText2(f"\2[Admin]\1 Вы добавили \5{entered}\1 уровней"
             f" игроку \5{target.name}\1 в банк").send(index)

    # Unregistering current function from message check
    unregister_say_filter(give_levels_solver)

    # Blocking message
    return CommandReturn.BLOCK


def AdminPlayers_player_info(admin: WCS_Player,
         target: Union[WCS_Player, Disconnected_user]):
    menu = PagedMenu(title=f'Информация об {target.name:.10}',
                     select_callback=AdminPlayers_player_info_callback,
                     parent_menu=AdminPlayers_player,
                     parent_menu_args=(admin, target, ))

    menu.append(Text(f"Ник: '{target.name}'"))
    menu.append(Text(f"SteamID: '{target.steamid}'"))
    menu.append(Text(f"{'' if target else 'Последний '}IP: '{target.address}'"))

    if target:
        # WCS_Player

        # Lvl of account (Summary of all skills)
        menu.append(Text(f"Общий уровень: {target.total_lvls}"))

        # Levels in lvl bank
        menu.append(Text(f"Уровней в банке: {target.lk_lvls}"))

        # Getting skill list
        skills = target.skills_selected

        # Removing 'BLOCKED' and 'Empty'
        skills = [skill for skill in skills if not any((skill == 'BLOCKED', skill == 'Empty'))]

        # Giving amount of skills with ability to view them
        menu.append(PagedOption(f"Установленные навыки: {len(skills)}",
                value=(target, 'selected_skills', skills)))


    else:
        # Disconnected_user

        # Loading information about player from databases
        data_info: dict = db.wcs.DB_users.info_load(target.steamid)
        data_skills: dict = db.wcs.DB_users.skills_load(target.steamid)

        # Lvl of account (Summary of all skills)
        menu.append(Text(f"Общий уровень: {data_info['total_lvls']}"))

        # Levels in lvl bank
        menu.append(Text(f"Уровней в банке: {data_info['LK_lvls']}"))

        # Getting skill list
        skills = eval(data_info['skills_selected'])

        # Removing 'BLOCKED' and 'Empty'
        skills = [skill for skill in skills if not any((skill == 'BLOCKED', skill == 'Empty'))]

        # Giving amount of skills with ability to view them
        menu.append(PagedOption(f"Установленные навыки: {len(skills)}",
                                value=(target, 'selected_skills', skills, data_skills)))

    menu.send(admin.index)

def AdminPlayers_player_info_callback(_, index, choice):
    admin = WCS_Player.from_index(index)

    choice = choice.value
    target: WCS_Player = choice[0]
    command: str = choice[1]

    if command == 'selected_skills':
        menu = PagedMenu(title=f'Выбранные навыки игрока {target.name:.10}',
                         parent_menu=AdminPlayers_player_info,
                         parent_menu_args=(admin, target, ),
                         top_separator=None
                         )
        skills = choice[2]

        menu.append(Text('Название: лвл'))

        if target:
            # WCS_Player

            for skill in skills:
                name = db.wcs.Skills_info.get_name(skill)

                # Printing name
                menu.append(Text(f'{name}: '
                   f'{target.skills_selected_lvls[target.skills_selected.index(skill)]}'))
        else:
            # Disconnected_user

            # Getting data_skills variable
            data_skills = choice[3]

            # Iterating over selected skills
            for skill in skills:

                # Getting skill name
                name = db.wcs.Skills_info.get_name(skill)

                # Printing values
                menu.append(Text(f'{name}: '
                   f'{data_skills[skill][0]}'))

        menu.send(admin.index)



def Admin_reasons(admin: WCS_Player, target, command):
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


def Admin_time(admin, target, command, reason =None):
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
    if target:
        SayText2(f"\2[SYS]\1 Внимание! Выбранный игрок на сервере").send(admin.index)
        target = WCS_Player.from_index(target.index)

    AdminPlayers_player(admin, target)


def Admin_functions(admin):
    menu = PagedMenu(title='Функции',
                     select_callback=Admin_functions_callback,
                     parent_menu=AdminMain,
                     parent_menu_args=(admin,))

    if 'wcss_admin.functions.show_coordinates_origin':
        menu.append(PagedOption('Показывать координаты', value = 'show_origin'))
    if 'wcss_admin.functions.show_coordinates_eyes':
        menu.append(PagedOption('Показывать координаты глаз', value = 'show_eyes'))
    if 'wcss_admin.functions.show_coordinates_view':
        menu.append(PagedOption('Показывать координаты под прицелом', value = 'show_view'))
    if 'wcss_admin.functions.show_coordinates_view':
        menu.append(PagedOption('Показывать класс существа под прицелом', value = 'show_entity'))

    menu.send(admin.index)

def Admin_functions_callback(_, index, choice):
    admin: WCS_Player = WCS_Player.from_index(index)
    command = choice.value

    if command[:5] == 'show_':

        # Adding admin variable to admin, if not set
        if 'wcss_admin' not in dir(admin):
            admin.wcss_admin = dict()

        if command == 'show_origin':

            # Trying to get repeat
            repeat = admin.wcss_admin.get('show_origin_repeat')

            # Exist?
            if repeat is not None:
                # Yes

                # Then turning it off
                if repeat.status is RepeatStatus.RUNNING: repeat.stop()

                # Clearing from dictionary
                del admin.wcss_admin['show_origin_repeat']

            else:
                # No

                # Creating new repeat
                repeat: Repeat = admin.repeat(hudmsg, kwargs = {
                    'target': admin,
                    'function': print_origin,
                    'y': -0.11,
                    'x': 0.01,
                    'channel': 1450,
                    'color': (255,255,255),
                    'hold_time': 1.2
                    }, cancel_on_level_end = True
                )

                # Starting it
                repeat.start(1, 100, True)

                # Adding to admin variable in WCS_Player
                admin.wcss_admin['show_origin_repeat'] = repeat

        elif command == 'show_eyes':

            # Trying to get repeat
            repeat = admin.wcss_admin.get('show_eyes_repeat')

            # Exist?
            if repeat is not None:
                # Yes

                # Then turning it off
                if repeat.status is RepeatStatus.RUNNING: repeat.stop()

                # Clearing from dictionary
                del admin.wcss_admin['show_eyes_repeat']

            else:
                # No

                # Creating new repeat
                repeat: Repeat = admin.repeat(hudmsg, kwargs = {
                    'target': admin,
                    'function': print_eye_location,
                    'y': -0.08,
                    'x': 0.01,
                    'channel': 1460,
                    'color': (255,255,255),
                    'hold_time': 1.2
                    }, cancel_on_level_end = True
                )

                # Starting it
                repeat.start(1, 100, True)

                # Adding to admin variable in WCS_Player
                admin.wcss_admin['show_eyes_repeat'] = repeat

        elif command == 'show_view':

            # Trying to get repeat
            repeat = admin.wcss_admin.get('show_view_repeat')

            # Exist?
            if repeat is not None:
                # Yes

                # Then turning it off
                if repeat.status is RepeatStatus.RUNNING: repeat.stop()

                # Clearing from dictionary
                del admin.wcss_admin['show_view_repeat']

            else:
                # No

                # Creating new repeat
                repeat: Repeat = admin.repeat(hudmsg, kwargs = {
                    'target': admin,
                    'function': print_view_coordinates,
                    'y': -0.05,
                    'x': 0.01,
                    'channel': 1470,
                    'color': (255,255,255),
                    'hold_time': 1.2
                    }, cancel_on_level_end = True
                )

                # Starting it
                repeat.start(1, 100, True)

                # Adding to admin variable in WCS_Player
                admin.wcss_admin['show_view_repeat'] = repeat

        elif command == 'show_entity':

            # Trying to get repeat
            repeat = admin.wcss_admin.get('show_eyes_repeat')

            # Exist?
            if repeat is not None:
                # Yes

                # Then turning it off
                if repeat.status is RepeatStatus.RUNNING: repeat.stop()

                # Clearing from dictionary
                del admin.wcss_admin['show_eyes_repeat']

            else:
                # No

                # Creating new repeat
                repeat: Repeat = admin.repeat(hudmsg, kwargs = {
                    'target': admin,
                    'function': print_entity,
                    'y': -0.0001,
                    'x': 0.43,
                    'channel': 1460,
                    'color': (255,255,255),
                    'hold_time': 1.2
                    }, cancel_on_level_end = True
                )

                # Starting it
                repeat.start(1, 100, True)

                # Adding to admin variable in WCS_Player
                admin.wcss_admin['show_eyes_repeat'] = repeat

        Admin_functions(admin)
