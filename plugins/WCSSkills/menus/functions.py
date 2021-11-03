
# Constants
from WCSSkills.other_functions.constants import WCS_FOLDER
from WCSSkills.other_functions.constants import VOLUME_MENU

class _RSound:

    @staticmethod
    def back(target):
        target.emit_sound(f'{WCS_FOLDER}/menus/back.mp3', attenuation=1.6, volume=VOLUME_MENU)

    @staticmethod
    def next(target):
        target.emit_sound(f'{WCS_FOLDER}/menus/next.mp3', attenuation=1.6, volume=VOLUME_MENU)

    @staticmethod
    def final(target):
        target.emit_sound(f'{WCS_FOLDER}/menus/final.mp3', attenuation=1.6, volume=VOLUME_MENU)

    @staticmethod
    def next_menu(target):
        target.emit_sound(f'{WCS_FOLDER}/menus/continue.mp3', attenuation=1.6, volume=VOLUME_MENU)

RSound = _RSound