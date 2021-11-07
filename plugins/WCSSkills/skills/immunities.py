# ../skills/immunities.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python
from messages import SayText2

# Plugin Imports
# Immune types
from WCSSkills.other_functions.constants import ImmuneTypes
# Skills information
from WCSSkills.db.wcs import Skills_info
# WCS_Player
from WCSSkills.wcs.wcsplayer import WCS_Players
# chance
from .functions import chance
# =============================================================================
# >> ALL DECLARATION
# =============================================================================

__all__ = (
'paralyze',
'screen_rotate',
'active_weapon_drop',
)

# =============================================================================
# >> Immunities
# =============================================================================

class ImmuneSkill:

    form = None
    text = ''

    def __init__(self, userid: int, lvl: int, settings: dict):

        # form and text check
        if self.form is None:
            raise NotImplemented("When inherit ImmuneSkill, "
                                 "change 'form' constant'")
        if self.text == '':
            raise NotImplemented("When inherit ImmuneSkill, "
                                 "change 'text' constant'")

        owner = WCS_Players[userid]
        max_lvl = Skills_info.get_max_lvl(f"Immune.{type(self).__name__}")

        # Lvl above maximum -> Change lvl to max
        lvl = max_lvl if lvl > max_lvl else lvl

        forms = []

        # Iterating over all settings
        for key, value in settings.items():

            # Getting value
            if value is True:

                # Adding 1 to counter
                forms.append(key)

        # Avoid division by zero
        try:
            # Division chance by all types of immune
            trigger_chance = lvl / len(forms)
        except ZeroDivisionError:
            SayText2(f"\4[WCS]\1 Не выбраны типы защиты от "
                     f"\5{self.text}\1").send(owner.index)
            return

        # Going through all forms of immune
        for form in self.form:

            # Iterating over all selected forms of immune
            for key in forms:

                # Chance check
                if chance(trigger_chance, 100):

                    # Applying Immune_type to owner.immunes
                    owner.immunes[form] = eval(f"ImmuneTypes.{key}")

        # Notifying player
        SayText2(f"\4[WCS]\1 Вы получите защиту от {self.text} c шансом \5"
             f"{trigger_chance/2.5 if trigger_chance < 100 else 100:.1f}"
             f"\1%").send(owner.index)

    def __repr__(self):
        return f"{self.__class__.__name__}(form={self.form}, text={self.text})"

    def close(self):
        pass

class paralyze(ImmuneSkill):
    form = ('paralyze', )
    text = 'паралича'

class screen_rotate(ImmuneSkill):
    form = ('screen_rotate', )
    text = 'разворота экрана'

class active_weapon_drop(ImmuneSkill):
    form = ('active_weapon_drop', )
    text = 'выброса оружия'

class aimbot(ImmuneSkill):
    form = ('aimbot',)
    text = 'аимбота'

class toss(ImmuneSkill):
    form = ('toss', )
    text = 'подкидывания'