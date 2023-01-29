# ../skills/immunities.py

# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python
from messages import SayText2

# Plugin Imports
# Immune types
from ..other_functions.constants import ImmuneTypes
# Skills information
from ..db.wcs import Skills_info
# WCS_Player
from ..wcs.WCSP.wcsplayer import WCS_Player
# chance
from .functions import chance

# =============================================================================
# >> ALL DECLARATION
# =============================================================================

__all__ = (
'paralyze',
'screen_rotate',
'active_weapon_drop',
'toss',
'aimbot',
'teleport'
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

        # Setting name of skill
        self.name = f"immune.{type(self).__name__}"

        # Saving owner
        owner = WCS_Player.from_userid(userid)

        # Getting maximum lvl
        max_lvl = Skills_info.get_max_lvl(self.name)

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

        # If level < 1000, then we apply only immune
        if lvl < 1000:

            # Going through all forms of immune
            for form in self.form:

                # Iterating over all selected forms of immune
                for key in forms:

                    # Chance check
                    if chance(trigger_chance, 100):

                        # Applying Immune_type to owner immunes
                        owner.immunes[form] = getattr(ImmuneTypes, key)

        # But if lvl over 1000, then we can apply deflect 2
        else:

            # Going through all forms of immune
            for form in self.form:

                # Applying starter ImmuneType
                owner.immunes[form] = ImmuneTypes.Nothing

                # Iterating over all selected forms of immune
                for key in forms:

                    # Chance check
                    if chance(trigger_chance, 1000):

                        # Applying deflecting to owner.immunes
                        owner.immunes[form] |= (getattr(ImmuneSkill, key) << 1)

                    # Not worked. Applying simple immune
                    else:

                        # Applying deflecting to owner.immunes
                        owner.immunes[form] |= (getattr(ImmuneSkill, key))

        # Notifying player
        SayText2(f"\4[WCS]\1 Вы получите защиту от {self.text} c шансом \5"
             f"{trigger_chance/2.5 if trigger_chance < 100 else 100:.1f}"
             f"\1%").send(owner.index)

    def __repr__(self):
        return f"{self.name}(form={self.form}, text={self.text})"

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

class teleport(ImmuneSkill):
    form = ('position_swap',)
    text = 'любого вида принудительной телепортации'

class presence(ImmuneSkill):
    form = ('aimbot', 'detect', 'reveal')
    text = 'от любого вида обнаружения'
