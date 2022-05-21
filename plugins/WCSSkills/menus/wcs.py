# ../WCSSkills/menus/wcs.py
"""
This file is working with wcs radios menu
"""
# =============================================================================
# >> Imports
# =============================================================================
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

# Plugin imports
# DB
from WCSSkills.db.wcs import Skills_info
from WCSSkills.db.wcs import Player_settings
# WCS_Player
from WCSSkills.wcs.WCSP.wcsplayer import WCS_Player, WCS_Players
# Modified default PagedMenu
from .radio import *
from WCSSkills.admin.menu import AdminPlayers_player
# Logging
from ..WCS_Logger import wcs_logger
#
from .functions import RMSound, KeyboardTyping

# =============================================================================
# >> ALL DECLARATION
# =============================================================================

__all__ = ('MainMenu',)

#==============================================================================
# >> WCS
# =============================================================================

def MainMenu(player):
    # Menu that opens on writing command wcs

    menu = SimpleMenu(select_callback=MainMenu_callback)

    # Title
    menu.append(Text("Меню"))

    # First page to menu, where u can look at ur selected skills
    # and/or unselect skill
    menu.append(SimpleOption(1, 'Мои навыки', 'My skills'))

    # Here is shown list of all skills, where u can select skill that u want
    # Of course, if it unlocked
    menu.append(SimpleOption(2, 'Сменить навык', 'Skill change'))
    menu.append(SimpleOption(3, 'Информация о навыках', 'Skills info'))
    menu.append(SimpleOption(4, 'Информация об игроках', 'Players list'))
    menu.append(SimpleOption(5, 'Настройки', 'Settings'))

    menu.send(player.index)

def MainMenu_callback(*args):
    player = WCS_Player.from_index(args[1])
    RMSound.next_menu(player)
    if args[2].value == 'My skills':
        my_skills(player)
        return
    elif args[2].value == 'Skill change':
        skill_change_groups(player)
        return
    elif args[2].value == 'Skills info':
        skills_info_groups(player)
        return
    elif args[2].value == 'Players list':
        players_list(player)
        return
    elif args[2].value == 'Settings':
        player_settings(player)
        return


def my_skills(player):
    # Page of selected skills

    menu = SimpleMenu(select_callback=my_skills_callback)
    lvls_amount = [800*i for i in range(0,5)]
    for num in range(5):
        skill = player.skills_selected[num] if player.skills_change[num] is None else player.skills_change[num]

        if skill == 'Empty':
            menu.append(Text(f"{num + 1}. Пустой слот навыка"))
        elif skill == 'BLOCKED':
            if player.total_lvls > lvls_amount[num]:
                player.skills_selected[num] = 'Empty'
            menu.append(Text(f"{num + 1}. Заблокированный слот ({lvls_amount[num]})"))
        elif player.skills_selected_lvl[num] is None:
            menu.append(SimpleOption(num+1, f"{Skills_info.get_name(skill)}", value = num))
        elif player.skills_selected_lvl[num] is not None:
            menu.append(SimpleOption(num+1, f"{Skills_info.get_name(skill)} ({player.skills_selected_lvl[num]})",
                                     value = num))

    menu.append(Text(' '))
    menu.append(SimpleOption(7, 'Назад', 'Back'))

    menu.send(player.index)

def my_skills_callback(*args):
    player = WCS_Player.from_index(args[1])
    choice = args[2].value
    if choice == 'Back':
        MainMenu(player)
        RMSound.back(player)
        return
    else:
        RMSound.back(player)
        skill_parameters(player, choice)


def skill_parameters(player, choice):
    menu = SimpleMenu(select_callback = skill_parameters_callback)
    skill = player.skills_selected[choice]
    is_not_empty = False if skill is 'Empty' else True

    menu.append(SimpleOption(1,'Изменить уровень навыка', value=('skill_lvl_select', choice),
                             selectable = is_not_empty, highlight = is_not_empty))
    if is_not_empty and len(Skills_info.get_settings_type(skill)) == 0:
        is_not_empty = False
    menu.append(SimpleOption(2,'Параметры навыка', value=('skill_settings', choice),
                             selectable = is_not_empty, highlight = is_not_empty))

    # selectable = False, highlight = False
    menu.append(SimpleOption(3,'Убрать навык', value=('skill_delete', choice),
                             selectable = True, highlight = True))


    menu.append(Text(' '))
    menu.append(SimpleOption(7, 'Назад', 'Back'))

    menu.send(player.index)

def skill_parameters_callback(*args):
    player = WCS_Player.from_index(args[1])
    choice = args[2].value
    if choice == 'Back':
        RMSound.back(player)
        my_skills(player)
    if choice[0] == 'skill_delete':
        RMSound.final(player)

        skill = player.skills_selected[choice[1]]
        player.skills_change[choice[1]] = 'Empty'

        SayText2(f"\4[WCS]\1 Вы убрали навык \5"
        f"{Skills_info.get_name(skill)}"
        f" \1из слота\5 {choice[1]+1}\1").send(player.index)

        # Logging
        wcs_logger('menu', f"{player.name}: {choice[1]+1}. "
            f"{player.skills_selected[choice[1]]} -> Empty")

    if choice[0] == 'skill_lvl_select':
        RMSound.next(player)
        skill_parameter_lvls(player, choice[1])
    if choice[0] == 'skill_settings':
        RMSound.next(player)
        skill_settings(player, choice)


def skill_parameter_lvls(player, choice):
    menu = PagedMenu(title='Уровень:',
                   select_callback=skill_parameter_lvls_callback,
                   parent_menu = skill_parameters,
                   parent_menu_args = (player, choice))

    skill_name = player.skills_selected[choice]
    skill_id = choice
    max_lvl = Skills_info.get_max_lvl(skill_name)
    player_current_lvl = player.skills_selected_lvls[skill_id]
    current_lvl = player_current_lvl if player_current_lvl < max_lvl else max_lvl
    menu.append(PagedOption(f"Последний уровень",
                            value = (skill_id, None)))
    menu.append(PagedOption(f"Ввести с клавиатуры",
                            value = (skill_id, 'Keyboard', current_lvl, max_lvl)))

    for lvl in range(0,current_lvl+1):
        menu.append(PagedOption(lvl, value = (skill_id, lvl)))

    menu.send(player.index)

def skill_parameter_lvls_callback(command, index, choice):
    player = WCS_Player.from_index(index)
    choice = choice.value
    skill = Skills_info.get_name(player.skills_selected[command])

    if choice[1] is None:

        # Sound
        RMSound.final(player)

        # Deleting info about selected lvl
        player.skills_selected_lvl[choice[0]] = None

        # Notify player
        SayText2("\4[WCS]\1 Вы установили уровень навыка "
        f"\5{skill}\1 на \5последний\1").send(player.index)

    # Player requested to enter number from kb
    elif choice[1] is 'Keyboard':

        # Sound
        RMSound.next(player)

        # Saving info to enter_temp
        player.enter_temp = ('skill_parameter_lvls_keyboard',
                             choice[0], choice[2], choice[3])
        # skill_id, Current, max
        KeyboardTyping(
            target = player,
            previous_menu = skill_parameter_lvls,
            previous_menu_args = (player, choice[0]),
            success_function = skill_parameter_lvls_keyboard,
            success_function_args = (choice[0], choice[2], choice[3])
        )


def skill_parameter_lvls_keyboard(player: WCS_Player, entered: str, skill_id: str,
                  current_lvl: int, maximum_skill_lvl: int):

    # Is he truly entered a number?
    try: entered = int(entered)

    # No, say, that input is wrong
    except ValueError:
        return f"{entered} не является числом"

    # Level can't be negative
    entered = abs(entered)

    # Selected lvl above maximum of this skill
    if entered > maximum_skill_lvl:
        return f"{entered} уровень выше максимума навыка {player.enter_temp[3]}"

    # Selected lvl is above his reached limit
    elif entered > current_lvl:
        return f"{entered} уровня вы ещё не достигли"

    # Well, everything is fine, changing skill lvl

    # Sound
    RMSound.final(player)

    # Setting new lvl
    player.skills_selected_lvl[skill_id] = entered

    # Notify player
    SayText2("\4[WCS]\1 Вы установили уровень навыка "
    f"\5{Skills_info.get_name(player.skills_selected[skill_id])}\1"
    f" на \5{entered}\1").send(player.index)

    # Success sound!
    RMSound.final(player)


def skill_settings(player, choice):
    menu = PagedMenu(title='Параметры',
                     select_callback=skill_settings_callback,
                     parent_menu=skill_parameters,
                     parent_menu_args=(player, choice[1]))

    skill = player.skills_selected[choice[1]]
    parameters = Skills_info.get_settings_type(skill)
    names = Skills_info.get_settings_name(skill)
    costs = Skills_info.get_settings_cost(skill)

    for code, parameter_type in parameters.items():

        value = player.skills_selected_settings[choice[1]][code]
        if parameter_type == 'bool':
            menu.append(PagedOption(f"{names[code]}"
            f": {'вкл' if value == True else 'выкл'} [{costs[code]}]",
                    value = (choice[1],code,parameter_type,value)))
        else:
            menu.append(PagedOption(f"{code} idk",
                        value = (choice[1],code,parameter_type,value)))
    menu.send(player.index)

def skill_settings_callback(_, index, choice):

    # Getting starter information
    player = WCS_Player.from_index(index)
    skill_index = choice.value[0]
    name = choice.value[1]
    parameter_type = choice.value[2]
    value = choice.value[3]

    # Checking, if setting type is good
    if parameter_type == 'bool':

        # Sound
        RMSound.final(player)

        # Getting skill
        skill = player.skills_selected[skill_index]

        # Changing value
        player.skills_selected_settings[skill_index][name] = not value

        # Re-open skill settings menu
        skill_settings(player, ('skill_settings',player.skills_selected.index(skill)))

        # Notifying player
        if player.data_info['skill_parameter_change_notify']:
            SayText2("\5[WCS\1 Изменена настройка навыка \5"
                    f"{Skills_info.get_name(skill)}:\1").send(index)
            SayText2(f"Изменение '\5{Skills_info.get_settings_name(skill, name)}\1'"
                     f" на \5{'вкл' if value == False else 'выкл'}\1").send(index)

    # Well, I didn't add any other types
    else: raise ValueError("Selected other parameter_type instead of bool")


def skill_change_groups(player):
    menu = PagedMenu(title='Категории навыков',
                   select_callback=skill_change_groups_callback,
                   parent_menu = MainMenu,
                   parent_menu_args = (player,))

    menu.extend(player_skill_groups())
    menu.send(player.index)

def skill_change_groups_callback(*args):

    # Getting player
    player = WCS_Player.from_index(args[1])

    # Sound
    RMSound.next(player)

    # Sending him to skills menu
    skill_change_skills(player, args[2].value)


def skill_change_skills(player, group: str):
    menu = PagedMenu(title=f'{group} навыки',
                   select_callback=skill_change_skills_callback,
                   parent_menu = skill_change_groups,
                   parent_menu_args = (player,))

    menu.extend(player_skills(player, group))
    menu.send(player.index)

def skill_change_skills_callback(*args):

    # Getting player
    player = WCS_Player.from_index(args[1])

    # Sound
    RMSound.next(player)

    # Sending him to this skills list
    skill_change_skills_list(player, args[2].value)

def skill_change_skills_list(player, skill_name):
    menu = SimpleMenu(select_callback=skill_change_skills_list_callback)
    for num in range(5):
        skill = player.skills_selected[num] if player.skills_change[num] is None else player.skills_change[num]
        if skill == 'Empty':
            menu.append(SimpleOption(num+1, "Пусто", value = (num, skill_name)))
        elif skill == 'BLOCKED':
            menu.append(SimpleOption(num+1, "Заблокировано", value = (num, skill_name),
                                     selectable = False, highlight = False))
        elif skill == skill_name:
            menu.append(SimpleOption(num+1, Skills_info.get_name(skill),
                                     value = (num, skill_name),
                                     selectable = False, highlight = False))
        else:
            menu.append(SimpleOption(num+1, Skills_info.get_name(skill),
                                     value = (num, skill_name)))

    menu.append(Text(' '))
    menu.append(SimpleOption(7, 'Назад', 'Back'))

    menu.send(player.index)

def skill_change_skills_list_callback(*args):
    player = WCS_Player.from_index(args[1])
    choice = args[2].value

    # He wants back :'(
    if choice == 'Back':

        # Sound
        RMSound.back(player)

        # Sending to previous menu
        skill_change_groups(player)

    # He want to change skill
    else:

        # Getting target slot
        slot_value = player.skills_selected[choice[0]]

        # Slot is not empty (then here is 100% skill)
        if slot_value != 'Empty':

            # Getting previous skill name
            previous_skill_name = Skills_info.get_name(player.skills_selected[choice[0]])

            # And future skill name
            chosen_skill_name = Skills_info.get_name(choice[1])

            # Notifying
            SayText2(f"\4[WCS]\1 Вы заменили навык \5{previous_skill_name}\1 на "
                     f"\5{chosen_skill_name}\1").send(args[1])

        # If slot is empty
        else:

            # Getting only future name
            chosen_skill_name = Skills_info.get_name(choice[1])

            # And notifying player
            SayText2(f"\4[WCS]\1 Вы поставили навык \5{chosen_skill_name}\1 в "
                     f"\5{choice[0]+1}\1 слот").send(args[1])

        # Log his change
        wcs_logger('menu', f'{player.name}: {choice[0]+1}. '
                       f'{player.skills_selected[choice[0]]} -> {choice[1]}')

        # Sound
        RMSound.final(player)

        # Actually changing skill (prepare to change)
        player.skills_change[choice[0]] = choice[1]


def skills_info_groups(player):
    menu = PagedMenu(title='Информация о навыках (группы)',
                     select_callback = skills_info_groups_callback,
                     parent_menu = MainMenu,
                     parent_menu_args = (player,))

    menu.extend(player_skill_groups())
    menu.send(player.index)

def skills_info_groups_callback(*args):

    # Getting player and other start info
    player = WCS_Player.from_index(args[1])
    choice = args[2].value

    # Sound
    RMSound.next(player)

    # Sending to skills menu
    skills_info_skills(player, choice)

def skills_info_skills(player, group):
    menu = PagedMenu(title='Информация о навыках',
                     select_callback = skills_info_skills_callback,
                     parent_menu = skills_info_groups,
                     parent_menu_args = (player, group))

    for skill in Skills_info.get_group_skills(group):
        menu.append(PagedOption(f"{Skills_info.get_name(skill)}", value=skill))

    menu.send(player.index)

def skills_info_skills_callback(*args):

    # Getting player and other start info
    player = WCS_Player.from_index(args[1])
    choice = args[2].value

    # Sound
    RMSound.next(player)

    # Sending to skills menu
    skills_info_description(player, choice)


def skills_info_description(player, skill):
    desc = Skills_info.get_description(skill)
    name = Skills_info.get_name(skill)

    menu = PagedMenu(title=f"Навык {name}",
                     parent_menu = skills_info_groups,
                     parent_menu_args = (player, ))
    menu.extend([Text(i) for i in desc])

    menu.send(player.index)

def players_list(player):
    menu = PagedMenu(title='Игроки',
                     select_callback=players_list_callback,
                     parent_menu = MainMenu,
                     parent_menu_args = (player,))


    for player_wcs in WCS_Players.values():
        menu.append(PagedOption(f"{player_wcs.name}", value = player_wcs))

    menu.send(player.index)

def players_list_callback(*args):

    # Getting player
    player = WCS_Player.from_index(args[1])

    # Sound
    RMSound.next(player)

    # Sending player previous menu
    player_info(player,args[2].value)

def player_info(player, target):
    menu = SimpleMenu(select_callback = player_info_callback)

    menu.append(Text(f"Игрок: {target.name[0:10]}"))
    menu.append(Text(' '))
    menu.append(Text(f"Всего уровней: {target.total_lvls}"))
    menu.append(SimpleOption(1, "Открытые "
    "навыки", value = ('Opened skills', target)))
    menu.append(SimpleOption(2, "Установленные "
    "навыки", value = ('Selected skills', target)))
    if 'wcs_admin' in player.permissions:
        menu.append(SimpleOption(3, "Управление",
                         value = ('admin', target)))

    menu.append(Text(' '))
    menu.append(SimpleOption(7, 'Назад', 'Back'))
    menu.send(player.index)

def player_info_callback(*args):

    # Getting starter info
    choice = args[2].value
    player = WCS_Player.from_index(args[1])

    # Is he going back?
    if choice == 'Back':

        # Sound
        RMSound.back(player)

        # Sending previous menu
        players_list(player)

    # Is he looking for skills, that opened victim?
    elif choice[0] == 'Opened skills':

        # Sound
        RMSound.next(player)

        # Sending menu
        player_info_opened(player, choice[1])

    # Is he looking for skills, that selected victim?
    elif choice[0] == 'Selected skills':

        # Sound
        RMSound.next(player)

        # Sending menu
        player_info_selected(player, choice[1])

    # May be he is admin?
    if choice[0] == 'admin':

        # Sound
        RMSound.next(player)

        # Sending admin player-control menu
        AdminPlayers_player(player, choice[1])


def player_info_opened(player, target):
    menu = PagedMenu(title=f'Навыки игрока {target.name[0:10]}',
                     parent_menu = player_info,
                     parent_menu_args = (player, target))
    data_skills = target.data_skills

    data_skills_list = []
    for key, value in data_skills.items():
        temp = [key]
        temp.extend(value)
        data_skills_list.append(temp)

    for data in sorted(data_skills_list, key = lambda x: x[1], reverse = True):
        try:
            menu.append(PagedOption(f"{Skills_info.get_name(data[0])} "
                                    f"[{data[1]}lvl]",
                                    selectable = False, highlight = False))
        except KeyError:
            continue
    menu.send(player.index)

def player_info_selected(player, target):
    menu = SimpleMenu(select_callback = player_info_selected_callback)

    menu.append(Text(f"Игрок: {target.name[0:10]}"))
    menu.append(Text(' '))

    for num, skill in enumerate(target.skills_selected):
        if skill == 'Empty':
            menu.append(f"{num+1}. Не установлено")
        elif skill == 'BLOCKED':
            menu.append(f"{num+1}. Заблокировано")
        else:
            menu.append(f"{num+1}. {Skills_info.get_name(skill)} "
                        f"[{target.skills_selected_lvls[num]}lvl]")

    menu.append(Text(' '))
    menu.append(SimpleOption(7, 'Назад', target))
    menu.send(player.index)

def player_info_selected_callback(*args):

    # Getting starter info
    player = WCS_Player.from_index(args[1])

    # Sound
    RMSound.back(player)

    # Sending previous menu
    player_info(player, args[2].value)


def player_settings(player):
    menu = PagedMenu(title='Настройки',
                     select_callback=player_settings_callback,
                     parent_menu = MainMenu,
                     parent_menu_args = (player,),
                     )
    menu._get_max_item_count = lambda : 5
    for setting in Player_settings.get_values():
        menu.append(PagedOption(f"{Player_settings.get_name(setting)}: "
            f"{'вкл' if player.data_info[setting] == True else 'выкл'}",
            value = setting))

    menu.send(player.index)

def player_settings_callback(_, index, choice):
    # Getting starter info
    player = WCS_Player.from_index(index)
    setting = choice.value

    # Previous setting value (with not)
    value = not player.data_info[setting]

    # Setting new value
    player.data_info[setting] = value

    # Notifying player
    SayText2(f"\4[WCS]\1 Настройка '\5{Player_settings.get_name(setting)}\1"
    f"изменена на \5{'вкл' if value == True else 'выкл'}\1'")

    # Playing sound
    RMSound.final(player)

    # Sending THIS menu
    player_settings(player)


# =============================================================================
# >> LK
# =============================================================================

def LK(player):

    menu = SimpleMenu(select_callback = LK_callback)
    lvls = player.lk_lvls
    is_not_zero = False if lvls == 0 else True
    menu.append(Text(f"У вас {lvls} уровней"))
    menu.append(Text(" "))

    menu.append(SimpleOption(1,"Слить уровни в навык", value = "Waste",
                selectable = is_not_zero, highlight = is_not_zero))
    menu.append(SimpleOption(2,"Передать уровни", value = "Send",
                selectable = is_not_zero, highlight = is_not_zero))

    menu.send(player.index)

def LK_callback(_, index, choice):

    # Getting starter info
    player = WCS_Player.from_index(index)

    # Is he going to waster lvls for himself?
    if choice.value == "Waste":
        # Wow, such a selfish dud

        # Sound
        RMSound.next(player)

        # Sending waste menu
        LK_user_groups(player)

    # He wants to send!
    elif choice.value == "Send":
        # Good man))

        # Sound
        RMSound.next(player)

        # Sending share menu
        LK_send(player)


def LK_user_groups(player):
    menu = PagedMenu(title=f'Навыки игрока {player.name[0:10]}',
                     select_callback=LK_user_groups_callback,
                     parent_menu = LK,
                     parent_menu_args = (player,))

    menu.extend(player_skill_groups())

    menu.send(player.index)

def LK_user_groups_callback(_, index, choice):

    # Getting player
    player = WCS_Player.from_index(index)

    # Sending skills menu
    LK_user_skills(player, choice.value)

def LK_user_skills(player, group):
    menu = PagedMenu(title=f'Навыки игрока {player.name[0:10]}',
                     select_callback=LK_user_skills_callback,
                     parent_menu = LK,
                     parent_menu_args = (player,))

    menu.extend(player_skills(player, group, select_selected=True))

    menu.send(player.index)

def LK_user_skills_callback(_, index, choice):

    # Getting player
    player = WCS_Player.from_index(index)

    # Saving kb info to enter_temp
    player.enter_temp = ('LK_user_keyboard', choice.value)

    # Notifying player
    SayText2("\2Напишите число в чат.\1").send(player.index)
    SayText2("\2Введите STOP для отмены.\1").send(player.index)

    # Sound
    RMSound.next(player)

    # Try to register filter command (he can be registered before)
    try:
        register_say_filter(LK_user_keyboard)
    except ValueError:
        pass

def LK_user_keyboard(command, index, _):

    # Getting starter info
    player = WCS_Player.from_index(index)

    # If enter_temp is None, player is not using kb functions
    if player.enter_temp is None:

        # Then pass him
        return CommandReturn.CONTINUE

    # He's using kb, but not this function
    elif player.enter_temp[0] != 'LK_user_keyboard':

        # Then pass him, to allow other filters work
        return CommandReturn.CONTINUE

    # This is our user

    # Getting his command
    entered = command.command_string

    # Requested stop
    if entered[:4] == 'STOP' or entered[:4] == 'stop':

        # Unregister filter
        unregister_say_filter(LK_user_keyboard)

        # Clearing player temp
        player.enter_temp = None

        # Sending previous menu
        LK_user_groups(player)

        # Blocking command
        return CommandReturn.BLOCK

    # Trying to get in lk
    elif entered == 'lk':

        # Allow
        return CommandReturn.CONTINUE

    # Is his input really a number?
    try:
        entered = int(entered)

    # No
    except ValueError:

        # Notifying user about error
        SayText2(f"\2Введено некорректное значение\1").send(index)

        # Blocking command
        return CommandReturn.BLOCK

    # Lvls can't be negative
    if entered < 0:

        # Notifying user about error
        SayText2(f"\2Нельзя вывести отрицательное количество уровней\1").send(index)

        # Blocking command
        return CommandReturn.BLOCK

    # Not enough lvls
    elif entered > player.lk_lvls:

        # Notifying user about error
        SayText2(f"\2В вашем банке нет столько уровней\1").send(index)

        # Blocking command
        return CommandReturn.BLOCK

    # EveryThing is ok

    # Unregister filter
    unregister_say_filter(LK_user_keyboard)

    # What skill he want to upgrade?
    skill = player.enter_temp[1]

    # Is his skill in selected?
    if skill in player.skills_selected:
        # Yes

        # Getting starter values
        num = player.skills_selected.index(skill)
        before = player.skills_selected_lvls[num]

        # Increasing skill lvl
        player.skills_selected_lvls[num] += entered

        # Notifying user about increase
        SayText2(f"\4[WCS]\1 Вы усилили навык "
        f"\5{Skills_info.get_name(skill)}\1"
                 f" до \5{before+entered}\1 уровня").send(index)

    # Not in selected
    else:

        # Then looking in data_skills
        for num, value in enumerate(player.data_skills):

            # Is this, what are we looking for?
            if value[0] == skill:

                # Yes. Getting value
                data = list(value)

                # Breaking iteration
                break

        # Nothing found!
        else:

            # Then he opened this skill, but not selected even once
            # Adding skill to data_skills

            data = [0, 0, None, {}]

        # Remember previous amount
        before = data[0]

        # Increasing levels amount
        data[0] += entered

        # Replace with new value
        player.data_skills[skill] = data
        SayText2("\4[WCS]\1 Вы усилили навык "
                 f"\5{Skills_info.get_name(skill)}\1 "
                 f"(\5{before}\1 -> \5{str(before+entered)}\1)").send(index)

    # Decreasing lk lvls
    player.lk_lvls -= entered

    # Increasing overall lvls
    player.total_lvls += entered

    # Sound
    RMSound.final(player)

    player.enter_temp = None
    return CommandReturn.BLOCK


def LK_send(player):
    menu = PagedMenu(title='Все игроки',
                     select_callback=LK_send_callback,
                     parent_menu = LK,
                     parent_menu_args = (player,))

    for player_wcs in WCS_Players.values():
        if player_wcs is not player:
            menu.append(PagedOption(f"{player_wcs.name}", value = player_wcs))

    menu.send(player.index)

def LK_send_callback(_, index, choice):

    # Getting starter info
    target = choice.value
    player = WCS_Player.from_index(index)

    # Saving enter_temp info
    player.enter_temp = ('LK_send_keyboard', target)

    # Instructions to user
    SayText2("\2[SYS]\1 Напишите \5число\1 в чат").send(player.index)
    SayText2("\2[SYS]\1 Введите \7STOP\1 для отмены").send(player.index)

    # Register new filter
    register_say_filter(LK_send_keyboard)

def LK_send_keyboard(command, index, _):

    # Getting starter info
    player = WCS_Player.from_index(index)

    # If enter_temp is None, player is not using kb functions
    if player.enter_temp is None:

        # Then pass him
        return CommandReturn.CONTINUE

    # He using kb, but not this function
    elif player.enter_temp[0] != 'LK_user_keyboard':

        # Then pass him, to allow other filters work
        return CommandReturn.CONTINUE

    # This is our user

    # Getting his command
    entered = command.command_string

    # Requested stop
    if entered[:4] == 'STOP' or entered[:4] == 'stop':

        # Unregister filter
        unregister_say_filter(LK_user_keyboard)

        # Clearing player temp
        player.enter_temp = None

        # Sending previous menu
        LK_send(player)

        # Blocking command
        return CommandReturn.BLOCK

    # Trying to get in lk
    elif entered == 'lk':

        # Allow
        return CommandReturn.CONTINUE

    # Is his input really a number?
    try:
        entered = int(entered)

    # No
    except ValueError:

        # Notifying user about error
        SayText2(f"\2Введено некорректное значение\1").send(index)

        # Blocking command
        return CommandReturn.BLOCK

    # Lvls can't be negative
    if entered < 0:

        # Notifying user about error
        SayText2(f"\2Нельзя вывести отрицательное количество уровней\1").send(index)

        # Blocking command
        return CommandReturn.BLOCK

    # Not enough lvls
    elif entered > player.lk_lvls:

        # Notifying user about error
        SayText2(f"\2В вашем банке нет столько уровней\1").send(index)

        # Blocking command
        return CommandReturn.BLOCK

    # Sound
    RMSound.final(player)

    # Unregister filter
    unregister_say_filter(LK_send_keyboard)

    # Changing target amount of lvls
    player.enter_temp[1].lk_lvls += entered

    # Decreasing owner lvls
    player.lk_lvls -= entered

    # Notify owner
    SayText2(f"\4[WCS]\1 Вы передали \5{entered}\1 уровней игроку"
             f" \5{player.enter_temp[1].name}\1").send(player)

    # Clearing owner enter_temp
    player.enter_temp = None

    # Block command
    return CommandReturn.BLOCK