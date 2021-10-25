# ../WCSSkills/admin/constants.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
from enum import Enum
from WCSSkills.python.enumeratings import Tuple_Enum_Meta

amount_of_players_in_history: int = 20
tell_admin_about_all_demutes: bool = False

class Punishment_types(Enum, metaclass = Tuple_Enum_Meta):
    BAN = (1, 'Бан')
    MUTE = (2, 'Мут')
    KICK = (3, 'Кик')
    SKILLS = (4, 'Блок способностей')

class Punishment_reasons(Enum, metaclass = Tuple_Enum_Meta):
    Nothing = (1, '—')
    AFK = (2, 'AFK')
    CHEATS = (3, 'Читы')
    FRIENDLY_FIRE = (4, 'Стрельба по своим')
    GRIEFING = (5, 'Вредительство команде')
    SKILL_ABUSE = (6, 'Абуз скиллов')
    AGREEMENT = (7, 'По обоюдному соглашению')

class Punishment_duration(Enum, metaclass = Tuple_Enum_Meta):
    Permanent = (-1, 'Навсегда')
    Seconds_30 = (30, '30 секунд')
    Minute_1 = (60, 'Минута')
    Minute_10 = (600, '10 Минут')
    Minute_30 = (1800, '30 Минут')
    Hour_1 = (3600, 'Час')
    Hour_6 = (21600, '6 часов')
    Day = (86400, 'День')
    Day_3 = (259200, '3 дня')
    Week = (604800, 'Неделя')
    Week_2 = (1209600, '2 недели')

class MoveTypes(Enum, metaclass = Tuple_Enum_Meta):
    NONE = (0, 'Заморозка')
    ISOMETRIC = (1, 'Изометрический')
    WALK = (2, 'Ходьба')
    STEP = (3, 'Шаг')
    FLY = (4, 'Полёт')
    FLYGRAVITY = (5, 'Полёт с гравитацией')
    VPHYSICS = (6, 'Физика')
    PUSH = (7, 'Толкать')
    NOCLIP = (8, 'НоКлип')
    LADDER = (9, 'Лестница')
    OBSERVER = (10, 'Обозреватель')
    CUSTOM = (11, 'Кастомные')