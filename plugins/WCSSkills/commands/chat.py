# ../WCSSkills/commands/chat.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
# randint
from random import randint

# Source.Python Imports
# Commands
from commands import CommandReturn
from commands.client import ClientCommand
from commands.typed import TypedSayCommand
# EntityIter
from filters.entities import EntityIter
# SayText2
from messages import SayText2

# Plugin imports
# Player
from WCSSkills.wcs.WCSP.wcsplayer import WCS_Player
# Main Radio Menu
from WCSSkills.menus.wcs import MainMenu, LK
from WCSSkills.admin.menu import AdminMain
# Logger
from WCSSkills.WCS_Logger import wcs_logger


def increase():
    for x in range(0,10000):
        yield x
sc = increase()

@ClientCommand('rtd')
def test(_, index):
    player = WCS_Player.from_index(index)
    wcs_logger(prefix='info', msg=f'rtd called by {player.name}')
    return CommandReturn.BLOCK

@TypedSayCommand('t')
def wcs(comm):
    player = WCS_Player.from_index(comm.index)
    wcs_logger(prefix='info', msg=f't called by {player.name}')
    return CommandReturn.BLOCK

# =============================================================================
# >> WCS
# =============================================================================

@TypedSayCommand('wcs')
def wcs(comm):
    MainMenu(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

@TypedSayCommand('цсы')
def wcs(comm):
    MainMenu(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

@TypedSayCommand('цс')
def wcs(comm):
    MainMenu(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

@TypedSayCommand('wc')
def wcs(comm):
    MainMenu(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

@TypedSayCommand('!wcs')
def wcs(comm):
    MainMenu(WCS_Player.from_index(comm.index))
    return CommandReturn.CONTINUE

@TypedSayCommand('/wcs')
def wcs(comm):
    MainMenu(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

@TypedSayCommand('/цсы')
def wcs(comm):
    MainMenu(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

@TypedSayCommand('/цс')
def wcs(comm):
    MainMenu(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

# =============================================================================
# >> LK
# =============================================================================

@TypedSayCommand('lk')
def lk(comm):
    LK(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

@TypedSayCommand('/lk')
def lk(comm):
    LK(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

@TypedSayCommand('!lk')
def lk(comm):
    LK(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

# =============================================================================
# >> Admin
# =============================================================================

@TypedSayCommand('admin', 'wcs_admin_base')
def admin(comm):
    AdminMain(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

@TypedSayCommand('админ', 'wcs_admin_base')
def admin(comm):
    AdminMain(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

@TypedSayCommand('!админ', 'wcs_admin_base')
def admin(comm):
    AdminMain(WCS_Player.from_index(comm.index))
    return CommandReturn.CONTINUE

@TypedSayCommand('!admin', 'wcs_admin_base')
def admin(comm):
    AdminMain(WCS_Player.from_index(comm.index))
    return CommandReturn.CONTINUE

@TypedSayCommand('/admin', 'wcs_admin_base')
def admin(comm):
    AdminMain(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

@TypedSayCommand('/админ', 'wcs_admin_base*')
def admin(comm):
    AdminMain(WCS_Player.from_index(comm.index))
    return CommandReturn.BLOCK

# =============================================================================
# >> Other
# =============================================================================

# =============================================================================
# >> Debug commands
# =============================================================================
from WCSSkills.other_functions.constants import WCSSKILLS_DEBUG

if WCSSKILLS_DEBUG:
    @ClientCommand('tp')
    def self_tp(_, index):
        player = WCS_Player.from_index(index)
        origin = player.origin
        origin[0] = 308
        origin[1] = 2318
        origin[2] = -117
        player.teleport(origin=origin)
        return CommandReturn.BLOCK

    @ClientCommand('bot_tp')
    def bot_tp(_, index):
        player = WCS_Player.from_index(index)
        for entity in EntityIter():
            if entity.class_name == 'player' and entity.index != player.index:
                origin = player.view_coordinates
                origin[0] += randint(-100,100)
                origin[1] += randint(-100,100)
                origin[2] += 10
                entity.teleport(origin = origin)

        return CommandReturn.BLOCK

    @TypedSayCommand('cash')
    def cash(comm):
        player = WCS_Player.from_index(comm.index)
        player.cash += 5000
        return CommandReturn.BLOCK

    @ClientCommand('dmg')
    def dmg(_, index):
        player = WCS_Player.from_index(index)
        player.take_damage(20)
        return CommandReturn.BLOCK

    @TypedSayCommand('wcsplists')
    def wcsp_lists(comm):
        player = WCS_Player.from_index(comm.index)

        print(f"lvls: {player.skills_selected_lvls}")
        print(f"lvl:  {player.skills_selected_lvl}")
        print(f"xp:   {player.skills_selected_xp}")
        print(f"ne_l:  {player.skills_selected_next_lvl}")
        print(f"sett: {player.skills_selected_settings}")