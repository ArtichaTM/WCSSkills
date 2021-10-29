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
# Converter from index to userid
from players.helpers import userid_from_index
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
from WCSSkills.wcs.wcsplayer import WCS_Players
# Modified default PagedMenu
from .radio import PagedMenu
from .radio import player_skills
from WCSSkills.admin.menus import AdminPlayers_player
# Logging
from WCSSkills.other_functions.functions import wcs_logger

# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = ('MainMenu', 'MainMenu_callback',
           'my_skills', 'my_skills_callback',
           'skill_parameters', 'skill_parameters_callback',
           'skill_parameter_lvls', 'skill_parameter_lvls_callback',
           'skill_parameter_lvls_keyboard',
           'skill_change', 'skill_change_callback',
           'skill_change_skills_list', 'skill_change_skills_list_callback',
           'skills_info',
           'skills_info_description', 'skills_info_description_callback',
           'players_list', 'players_list_callback',
           'player_info', 'player_info_callback',
           'player_info_opened',
           'player_info_selected', 'player_info_selected_callback',
           'LK', 'LK_callback',
           'LK_user', 'LK_user_callback',
           'LK_user_keyboard',
           'LK_send', 'LK_send_callback',
           'LK_send_keyboard')

# =============================================================================
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
    if args[2].value == 'My skills':
        # my_skills(WCS_Player.from_index(args[1]))
        my_skills(WCS_Players[userid_from_index(args[1])])
        return
    elif args[2].value == 'Skill change':
        skill_change(WCS_Players[userid_from_index(args[1])])
        return
    elif args[2].value == 'Skills info':
        skills_info(WCS_Players[userid_from_index(args[1])])
        return
    elif args[2].value == 'Players list':
        players_list(WCS_Players[userid_from_index(args[1])])
        return
    elif args[2].value == 'Settings':
        player_settings(WCS_Players[userid_from_index(args[1])])
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
    player = WCS_Players[userid_from_index(args[1])]
    choice = args[2].value
    if choice == 'Back':
        MainMenu(player)
        return
    else:
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
    player = WCS_Players[userid_from_index(args[1])]
    choice = args[2].value
    if choice == 'Back':
        my_skills(player)
    if choice[0] == 'skill_delete':
        player.skills_change[choice[1]] = 'Empty'

        SayText2(f"\4[WCS]\1 Вы убрали навык \5"
        f"{Skills_info.get_name(player.skills_selected[choice[1]])}"
        f" \1из слота\5 {choice[1]+1}\1").send(player.index)

        # Logging
        wcs_logger('menu', f"{player.name}: {choice[1]+1}. "
            f"{player.skills_selected[choice[1]]} -> Empty")

    if choice[0] == 'skill_lvl_select':
        skill_parameter_lvls(player, choice[1])
    if choice[0] == 'skill_settings':
        skill_settings(player, choice)


# noinspection PyTypeChecker
def skill_parameter_lvls(player, choice):
    menu = PagedMenu(title='Уровень:',
                   select_callback=skill_parameter_lvls_callback,
                   parent_menu = skill_parameters,
                   parent_menu_args = (player, choice))

    skill_name = player.skills_selected[choice]
    skill_id = choice
    max_lvl = Skills_info.get_max_lvl(skill_name)
    current_lvl = player.skills_selected_lvls[skill_id] if player.skills_selected_lvls[skill_id] < max_lvl else max_lvl
    menu.append(PagedOption(f"Последний уровень", value = (skill_id, None)))
    menu.append(PagedOption(f"Ввести с клавиатуры", value = (skill_id, 'Keyboard', current_lvl)))
    for lvl in range(0,current_lvl+1):
        menu.append(PagedOption(lvl, value = (skill_id, lvl)))

    menu.send(player.index)

def skill_parameter_lvls_callback(*args):
    player = WCS_Players[userid_from_index(args[1])]
    if type(args[2]) == type(tuple()): choice = args[2]
    else: choice = args[2].value
    skill = Skills_info.get_name(player.skills_selected[choice[0]])

    if choice[1] is None:
        player.skills_selected_lvl[choice[0]] = None
        SayText2("\4[WCS]\1 Вы установили уровень навыка "
        f"\5{skill}\1 на \5последний\1").send(player.index)
    elif choice[1] is 'Keyboard':
        SayText2("\2Напишите число в чат.\1").send(player.index)
        SayText2("\2Введите STOP для отмены.\1").send(player.index)
        player.enter_temp = ('skill_parameter_lvls_keyboard',
                             choice[0], choice[2])

        register_say_filter(skill_parameter_lvls_keyboard)
    else:
        player.skills_selected_lvl[choice[0]] = choice[1]
        SayText2("\4[WCS]\1 Вы установили уровень навыка "
        f"\4{skill}\1 на \4{choice[1]}\1").send(player.index)

def skill_parameter_lvls_keyboard(command, index, _):
    player = WCS_Players[userid_from_index(index)]
    if player.enter_temp is None:
        return CommandReturn.CONTINUE
    elif player.enter_temp[0] != 'skill_parameter_lvls_keyboard':
        return CommandReturn.CONTINUE
    else:
        entered = command.command_string
        if entered[:4] == 'STOP' or entered[:4] == 'stop':
            unregister_say_filter(skill_parameter_lvls_keyboard)
            skill_parameter_lvls(player, player.enter_temp[1])
            return CommandReturn.BLOCK
        elif entered == 'wcs':
            return CommandReturn.CONTINUE

        try:
            entered = int(entered)
        except ValueError:
            SayText2(f"\2Введено некорректное значение\1").send(index)
            return CommandReturn.BLOCK
        if entered < 0:
            SayText2(f"\2Уровень не может быть отрицательным\1").send(index)
            return CommandReturn.BLOCK
        elif entered > player.enter_temp[2]:
            SayText2(f"\2Такого уровня вы ещё не достигли\1").send(index)
            return CommandReturn.BLOCK


        unregister_say_filter(skill_parameter_lvls_keyboard)
        skill_parameter_lvls_callback('', index, (player.enter_temp[1], entered))
        player.enter_temp = None
        return CommandReturn.BLOCK

# noinspection PyTypeChecker
def skill_settings(player, choice):
    menu = PagedMenu(title='Параметры',
                     select_callback=skill_settings_callback,
                     parent_menu=skill_parameters,
                     parent_menu_args=(player, choice[1]))

    skill = player.skills_selected[choice[1]]
    parameters = Skills_info.get_settings_type(skill)

    for name, parameter_type in parameters.items():

        value = player.skills_selected_settings[choice[1]][name]
        if parameter_type == 'bool':
            menu.append(PagedOption(f"{Skills_info.get_settings_name(skill,setting = name)}"
            f": {'вкл' if value == True else 'выкл'}", value = (choice[1],name,parameter_type,value)))
        else:
            menu.append(PagedOption(f"{name} idk", value = (choice[1],name,parameter_type,value)))
    menu.send(player.index)

def skill_settings_callback(_, index, choice):
    player = WCS_Players[userid_from_index(index)]
    skill_index = choice.value[0]
    name = choice.value[1]
    parameter_type = choice.value[2]
    value = choice.value[3]

    if parameter_type == 'bool':
        skill = player.skills_selected[skill_index]
        player.skills_selected_settings[skill_index][name] = not value
        skill_settings(player, ('skill_settings',player.skills_selected.index(skill)))

        if player.data_info['skill_parameter_change_notify']:
            # Notifying player
            SayText2("\5[WCS\1 Изменена настройка навыка \5"
                    f"{Skills_info.get_name(skill)}:\1").send(index)
            SayText2(f"Изменение '\5{Skills_info.get_settings_name(skill, name)}\1'"
                     f" на \5{'вкл' if value == False else 'выкл'}\1").send(index)
    else: raise ValueError("Selected other parameter_type instead of bool")

# noinspection PyTypeChecker
def skill_change(player):
    menu = PagedMenu(title='Все навыки',
                   select_callback=skill_change_callback,
                   parent_menu = MainMenu,
                   parent_menu_args = (player,))

    menu.extend(player_skills(player))
    menu.send(player.index)

def skill_change_callback(*args):
    player = WCS_Players[userid_from_index(args[1])]
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
    player = WCS_Players[userid_from_index(args[1])]
    choice = args[2].value

    if choice == 'Back':
        skill_change(player)
        return
    else:
        slot_value = player.skills_selected[choice[0]]
        if slot_value != 'Empty':
            previous_skill_name = Skills_info.get_name(player.skills_selected[choice[0]])
            chosen_skill_name = Skills_info.get_name(choice[1])
            SayText2(f"\4[WCS]\1 Вы заменили навык \5{previous_skill_name}\1 на "
                     f"\5{chosen_skill_name}\1").send(args[1])
        else:
            chosen_skill_name = Skills_info.get_name(choice[1])
            SayText2(f"\4[WCS]\1 Вы поставили навык \5{chosen_skill_name}\1 в "
                     f"\5{choice[0]+1}\1 слот").send(args[1])
        wcs_logger('menu', f'{player.name}: {choice[0]+1}. '
                       f'{player.skills_selected[choice[0]]} -> {choice[1]}')
        player.skills_change[choice[0]] = choice[1]

# noinspection PyTypeChecker
def skills_info(player):
    menu = PagedMenu(title='Информация',
                     select_callback=skills_info_callback,
                     parent_menu = MainMenu,
                     parent_menu_args = (player,))

    for num, skill in enumerate(Skills_info.get_classes()):
        menu.append(PagedOption(f"{Skills_info.get_name(skill)}", value = skill))

    menu.send(player.index)

def skills_info_callback(*args):
    player = WCS_Players[userid_from_index(args[1])]
    choice = args[2].value

    skills_info_description(player, choice)

# noinspection PyTypeChecker
def skills_info_description(player, skill):
    desc = Skills_info.get_description(skill)
    name = Skills_info.get_name(skill)

    if len(desc) <= 6:
        menu = SimpleMenu(select_callback=skills_info_description_callback)
        menu.append(Text(name))
        menu.append(Text(' '))
        menu.extend([Text(i) for i in desc])
        menu.append(Text(' '))

        menu.append(SimpleOption(7, 'Назад', 'Back'))
    else:
        menu = PagedMenu(title='Информация',
                         select_callback=skills_info_callback,
                         parent_menu = skills_info,
                         parent_menu_args = (player, ))
        menu.append(Text(name))
        menu.extend([Text(i) for i in desc])

    menu.send(player.index)

def skills_info_description_callback(*args):
    player = WCS_Players[userid_from_index(args[1])]
    choice = args[2].value

    if choice == 'Back':
        skills_info(player)

# noinspection PyTypeChecker
def players_list(player):
    menu = PagedMenu(title='Игроки',
                     select_callback=players_list_callback,
                     parent_menu = MainMenu,
                     parent_menu_args = (player,))

    for player_wcs in WCS_Players.values():
        menu.append(PagedOption(f"{player_wcs.name}", value = player_wcs))

    menu.send(player.index)

def players_list_callback(*args):
    player_info(WCS_Players[userid_from_index(args[1])],args[2].value)

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
    choice = args[2].value
    player = WCS_Players[userid_from_index(args[1])]
    if choice == 'Back':
        players_list(player)
    elif choice[0] == 'Opened skills':
        player_info_opened(player, choice[1])
    elif choice[0] == 'Selected skills':
        player_info_selected(player, choice[1])
    if choice[0] == 'admin':
        AdminPlayers_player(player, choice[1], lambda *args : 0)

# noinspection PyTypeChecker
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
    player_info(WCS_Players[userid_from_index(args[1])],
                args[2].value)

# noinspection PyTypeChecker
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
    player = WCS_Players[userid_from_index(index)]
    setting = choice.value
    value = not player.data_info[setting]
    player.data_info[setting] = value
    SayText2(f"\4[WCS]\1 Настройка '\5{Player_settings.get_name(setting)}\1"
    f"изменена на \5{'вкл' if value == True else 'выкл'}\1'")
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
    player = WCS_Players[userid_from_index(index)]

    if choice.value == "Waste":
        LK_user(player)
    elif choice.value == "Send":
        LK_send(player)


# noinspection PyTypeChecker
def LK_user(player):
    menu = PagedMenu(title=f'Навыки игрока {player.name[0:10]}',
                     select_callback=LK_user_callback,
                     parent_menu = LK,
                     parent_menu_args = (player,))

    menu.extend(player_skills(player, select_selected=True))

    menu.send(player.index)

def LK_user_callback(_, index, choice):
    player = WCS_Players[userid_from_index(index)]
    player.enter_temp = ('LK_user_keyboard',choice.value)

    SayText2("\2Напишите число в чат.\1").send(player.index)
    SayText2("\2Введите STOP для отмены.\1").send(player.index)
    try:
        register_say_filter(LK_user_keyboard)
    except ValueError:
        pass

def LK_user_keyboard(command, index, _):
    player = WCS_Players[userid_from_index(index)]
    if player.enter_temp is None:
        return CommandReturn.CONTINUE
    elif player.enter_temp[0] != 'LK_user_keyboard':
        return CommandReturn.CONTINUE
    else:
        entered = command.command_string
        if entered[:4] == 'STOP' or entered[:4] == 'stop':
            unregister_say_filter(LK_user_keyboard)
            LK_user(player)
            return CommandReturn.BLOCK
        elif entered == 'lk':
            return CommandReturn.CONTINUE

        try:
            entered = int(entered)
        except ValueError:
            SayText2(f"\2Введено некорректное значение\1").send(index)
            return CommandReturn.BLOCK
        if entered < 0:
            SayText2(f"\2Нельзя вывести отрицательное количество уровней\1").send(index)
            return CommandReturn.BLOCK
        elif entered > player.lk_lvls:
            SayText2(f"\2В вашем банке нет столько уровней\1").send(index)
            return CommandReturn.BLOCK

        unregister_say_filter(LK_user_keyboard)
        if player.enter_temp[1] in player.skills_selected:
            num = player.skills_selected.index(player.enter_temp[1])
            before = player.skills_selected_lvls[num]
            player.skills_selected_lvls[num] += entered

            player.lk_lvls -= entered
            player.total_lvls += entered
            SayText2(f"\4[WCS]\1 Вы усилили навык "
            f"\5{Skills_info.get_name(player.enter_temp[1])}\1"
                     f" до \5{before+entered}\1 уровня").send(index)
        else:
            for num, value in enumerate(player.data_skills):
                if value[0] == player.enter_temp[1]:
                    data = list(value)
                    break
            else:
                SayText2("\4[WCS]\1 Вы ещё не устанавливали этот навык!"
                         ).send(player.index)
                SayText2("\4[WCS]\1 Установите навык в слот и попробуйте ещё раз"
                         ).send(player.index)
                return
            before = data[1]
            data[1] += entered
            player.data_skills[num] = data

            player.lk_lvls -= entered
            player.total_lvls += entered
            SayText2("\4[WCS]\1 Вы усилили навык "
                     f"\5{Skills_info.get_name(player.enter_temp[1])}\1 "
                     f"до \5{str(before+entered)}\1 уровня").send(index)

        player.enter_temp = None
        return CommandReturn.BLOCK

# noinspection PyTypeChecker
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
    target = choice.value
    player = WCS_Players[userid_from_index(index)]
    player.enter_temp = ('LK_send_keyboard', target)
    SayText2("\2Напишите число в чат.\1").send(player.index)
    SayText2("\2Введите STOP для отмены.\1").send(player.index)
    register_say_filter(LK_send_keyboard)

def LK_send_keyboard(command, index, _):
    player = WCS_Players[userid_from_index(index)]
    if player.enter_temp is None:
        return CommandReturn.CONTINUE
    elif player.enter_temp[0] != 'LK_send_keyboard':
        return CommandReturn.CONTINUE
    else:
        entered = command.command_string
        if entered[:4] == 'STOP' or entered[:4] == 'stop':
            unregister_say_filter(LK_send_keyboard)
            LK_send(player)
            return CommandReturn.BLOCK
        elif entered == 'lk':
            return CommandReturn.CONTINUE

        try:
            entered = int(entered)
        except ValueError:
            SayText2(f"\2Введено некорректное значение\1").send(index)
            return CommandReturn.BLOCK
        if entered < 0:
            SayText2(f"\2Нельзя вывести отрицательное количество уровней\1").send(index)
            return CommandReturn.BLOCK
        elif entered > player.lk_lvls:
            SayText2(f"\2В вашем банке нет столько уровней\1").send(index)
            return CommandReturn.BLOCK

        unregister_say_filter(LK_send_keyboard)
        player.enter_temp[1].lk_lvls += entered
        player.lk_lvls -= entered
        SayText2(f"\4[WCS]\1 Вы передали \5{entered}\1 уровней игроку"
                 f" \5{player.enter_temp[1].name}\1").send(player)
        player.enter_temp = None
        return CommandReturn.BLOCK