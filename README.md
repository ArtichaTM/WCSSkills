# Вступление
Мод Warcraft для CS:GO, который даёт возможность игрокам самим выбирать свои способности

## Структура папок
* __WCSSkills__ - Главная папка
    * __../admin/__ - Админ
    * __../commands/__ - функции команд в чате/консоли
    * __../db/__ - Базы данных / JSON
    * __../JSONs/__ - Здесь лежат статичные JSON
    * __../menus/__ - Ради меню
    * __../other_functions/__ - Разные важные функции / файлы
    * __../python/__ - Питонистский код, не связанный с Source.Python
    * __../skills/__ - Здесь лежат классы всех скиллов
    * __../wcs/__ - Папка с главным кодом

В папках (где нужно) добавлены файлы **function**, которые содержать важные функции для той или иной отрасли мода

# Помощь
Здесь описаны способы помочь мне писать WCS

## Добавление новых способностей
Есть несколько способов предложить новую способность
* _Forking_ - Написать код самому. Гайд ниже
    1. Создать ответвление
    2. Написать новую способность в _WCSSkills/skills/skills.py_
    3. Запросить объединение
* _Текстовый_ - Просто написать словами, как скилл работает
    1. Создать новую проблему
    2. Написать название, описание, описание в игре
    3. Примерно описать, как должен работать
* _Со ссылками на литературу_ - текстовый вариант + сторонняя литература
    * Ссылка на игру, в которой используется скилл + название скилла
    * Видео с использованием скилла
    * Текстовый вариант с приложением модельки, спрайта, другого

## Как писать код способностей
База способности.
skills/**skills.py**:
``` python
class skill_unique(BaseSkill):
    __slots__ = (...,)
  
    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)
    
    def close(self) -> None:
        super().close()
```
JSONs/**skills_info.json**:
``` JSON
"skill_unique": {
        "name": "Скилл",
        "description": [
            "Я описание. Чтобы перенести текст на другую",
            "строку используйте следующий string"
        ],
        "max_lvl": 1,
        "min_player_lvl": 0,
        "settings_type": {
            "setting": "bool"
        },
        "settings_name": {
            "setting": "Описание"
        },
        "settings_cost": {
            "setting": 20
        }
    }
```

Название способности произвольное, но оно должно соответствовать названию в skills_json.
Наследование от _BaseSkill_ обязательное.
Можно заменить наследованием от _ActiveSkill_ или _PeriodicSkill_.
В случае добавления новых переменных, создавайте `__slots__` и заносите их туда.
Константы _owner_/_lvl_/_settings_ уже
созданы, и писать их заново не нужно.

После строки `super().__init(lvl, userid, settings)` следует ваш код.
Также, после строки инициализации экземпляр имеет в своём пространстве следующие константы:
* **self.owner** — WCS_Player обладателя способности. `WCS_Player` наследуется от `Player`
* **self.lvl** — Уровень игрока владением способности. Обратите внимание, 
что при выборе способности первым уровнем является 0, а не 1. И не может быть отрицательным
* **self.settings** — настройки, которые можно настроить в Мои скиллы -> скилл -> параметры.
В коде они принимают форму словаря в виде _{"Название": "True/False"}_
____
Описание классов, от которых следует наследовать:
* **BaseSkill** — Добавляет _owner_/_lvl_/_settings_
* **ActiveSkill** — Добавляет _bind_pressed_/_bind_released_, 
а также добавляет навык в owner.Buttons.
* **PeriodicSkill** — Добавляет /infect_dict/repeat_delay/token/cd_passed. 
Поражённые противники получают `{token}`, система снимает их каждую `{repeat_delay}` и
запускает функцию `infect_activate`.
  * _infect_dict_ — Содержит записи о поражённых противниках в виде 
`{"ИД игрока": "количество токенов"}`
  * _repeat_delay_ — "тик" урона в секундах (через какой промежуток срабатывает тик)
  * _token_ — количество токенов, (сколько раз сработает тик), выдаваемые

# В планах добавить
* **Общее**
  - [X] Категории способностей
  - [ ] Усиления, которые располагаются в рандомных частях карты
  - [ ] Секреты на картах, которые дают доступ к уникальным способностям
  - [ ] [Admin] Возможность посмотреть предыдущие наказания, снять их
* **Способности**
  - [ ] Поджёг
  - [ ] Заморозка
  - [ ] Массовый телепорт
  - [ ] Смена местами
  - [ ] Ауры
  - [ ] Строительство
  - [X] Выдача оружия
  - [ ] Молния с небес
  - [ ] Тотемы (пока просто нет модельки)
  - [X] Разворот
  - [X] Обратный паралич
  - [ ] Зеркальный урон
  - [ ] Светящиеся гранаты
  - [ ] Уникальная техника установка предмета (сначала выбирается радиус, а потом место блока)
  - [ ] Висячие в воздухе мины (основано на технике выше)
  - [ ] Смена режима (вкл. режим призрака) при взятие ножа
  - [ ] Мини радар на земле, отображающий противников и союзников
  - [ ] Блок какой-то моделькой при наведении на пользователя
