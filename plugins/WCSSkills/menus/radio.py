# ../WCSSkills/menus/radio.py
"""
This file contains:
1. Modified 'PagedMenu' -- Changed parent_menu behaviour,
    changed language to russian
2. 'player_skills' skills -- returns list of player-target skills.
    Code moved to function bcz of many repeats
"""

# =============================================================================
# >> ALL DECLARATION
# =============================================================================
from menus import PagedMenu as PagedRadioMenu
from menus import PagedOption

from WCSSkills.db.wcs import Skills_info

# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = ('PagedMenu',
           'player_skills',
           'player_skill_groups')

# =============================================================================
# >> Functions
# =============================================================================
class PagedMenu(PagedRadioMenu):

    def __init__(
            self, data=None, select_callback=None,
            build_callback=None, close_callback=None, description=None,
            title=None, top_separator=' ', bottom_separator=' ',
            fill=True, parent_menu =None, parent_menu_args=None):
        super().__init__(data, select_callback, build_callback, close_callback)

        self.title = title
        self.description = description
        self.top_separator = top_separator
        self.bottom_separator = bottom_separator
        self.fill = fill
        self.parent_menu = parent_menu
        self.parent_menu_args = parent_menu_args

    def _format_footer(self, player_index, page, slots):
        buffer = ''

        # Set the bottom separator if present
        if self.bottom_separator is not None:
            buffer += self.bottom_separator + '\n'

        # Add "Back" option
        back_selectable = page.index > 0 or self.parent_menu is not None
        buffer += PagedOption(
            "Назад", highlight=back_selectable)._render(
            player_index, 7)
        if back_selectable:
            slots.add(7)

        # Add "Next" option
        next_selectable = page.index < self.last_page_index
        buffer += PagedOption(
            "Вперёд", highlight=next_selectable)._render(
            player_index, 8)
        if next_selectable:
            slots.add(8)

        # Add "Close" option
        buffer += PagedOption(
            "Закрыть", highlight=False)._render(player_index, 9)

        # Return the buffer
        return buffer

    def _select(self, player_index, choice_index):
        """See :meth:`menus.base._BaseMenu._select`."""
        if choice_index == 9:
            del self._player_pages[player_index]
            return self._select_close(player_index)

        # Get the player's current page
        page = self._player_pages[player_index]

        # Display previous page?
        if choice_index == 7:
            # Is the player on the first page, and do we have a parent menu?
            if not page.index and self.parent_menu is not None:
                del self._player_pages[player_index]
                if len(self.parent_menu_args) == 1:
                    self.parent_menu(self.parent_menu_args[0])
                elif len(self.parent_menu_args) == 2:
                    self.parent_menu(self.parent_menu_args[0], self.parent_menu_args[1])
                elif len(self.parent_menu_args) == 3:
                    self.parent_menu(self.parent_menu_args[0], self.parent_menu_args[1], self.parent_menu_args[2])
                return self._select_close(player_index)

            self.set_player_page(player_index, page.index - 1)
            return self

        # Display next page?
        if choice_index == 8:
            self.set_player_page(player_index, page.index + 1)
            return self

        return super()._select(player_index, choice_index)

def player_skill_groups():
    menu = []
    for group in Skills_info.get_groups():
        menu.append(PagedOption(f"{group}", value=group))
    return menu

def player_skills(player, group, select_selected: bool = False):
    menu = []
    for num, skill in enumerate(Skills_info.get_group_skills(group)):
        try:
            player_lvl = player.data_skills[skill][0]
        except KeyError:
            player_lvl = None

        name = Skills_info.get_name(skill)
        max_lvl = Skills_info.get_max_lvl(skill)
        min_lvl = Skills_info.get_min_lvl(skill)

        if skill in player.skills_selected:
            if player_lvl > max_lvl:
                menu.append(PagedOption(f"[S] {name} [{player_lvl}ур]", value = skill,
                                        selectable = select_selected, highlight = select_selected))
            else:
                menu.append(PagedOption(f"[S] {name} [{player_lvl}/{max_lvl}]", value = skill,
                                        selectable = select_selected, highlight = select_selected))
        elif player.total_lvls < min_lvl:
            menu.append(PagedOption(f"{name} [{min_lvl}ур]",
                                    selectable = False, highlight = False))
        elif player_lvl is None:
            menu.append(PagedOption(f"{name} [0/{max_lvl}]", value = skill))
        elif player_lvl > max_lvl:
            menu.append(PagedOption(f"{name} [{player_lvl}ур]", value = skill))
        else:
            menu.append(PagedOption(f"{name} [{player_lvl}/{max_lvl}]", value = skill))

    return menu
