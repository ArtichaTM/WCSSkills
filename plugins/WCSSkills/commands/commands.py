# ../WCSSkills/commands/commands.py
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
from commands.typed import *
# userid_from_index
from players.helpers import userid_from_index
# SayText2
from messages.base import SayText2
# EntityIter
from filters.entities import EntityIter

# Plugin imports
# Player
from WCSSkills.wcs.wcsplayer import WCS_Players
# Main Radio Menu
from WCSSkills.menus.wcs import MainMenu, LK
from WCSSkills.menus.admin import AdminMain
# Logger
from WCSSkills.other_functions.functions import wcs_logger

def increase():
    for x in range(0,10000):
        yield x
sc = increase()

# from engines.precache import Model
# from entities.entity import Entity
# from colors import RED

# entitys = [Entity.create('env_beam') for i in range(0,0)]

@ClientCommand('rtd')
def test(_, index):
    player = WCS_Players[userid_from_index(index)]
    wcs_logger(prefix='info', msg='rtd called')

    return CommandReturn.BLOCK

@TypedSayCommand('t')
def wcs(comm):
    return CommandReturn.BLOCK

# =============================================================================
# >> WCS
# =============================================================================

@TypedSayCommand('wcs')
def wcs(comm):
    MainMenu(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

@TypedSayCommand('цсы')
def wcs(comm):
    MainMenu(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

@TypedSayCommand('цс')
def wcs(comm):
    MainMenu(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

@TypedSayCommand('wc')
def wcs(comm):
    MainMenu(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

@TypedSayCommand('!wcs')
def wcs(comm):
    MainMenu(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.CONTINUE

@TypedSayCommand('/wcs')
def wcs(comm):
    MainMenu(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

@TypedSayCommand('/цсы')
def wcs(comm):
    MainMenu(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

@TypedSayCommand('/цс')
def wcs(comm):
    MainMenu(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

# =============================================================================
# >> LK
# =============================================================================

@TypedSayCommand('lk')
def lk(comm):
    LK(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

@TypedSayCommand('/lk')
def lk(comm):
    LK(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

@TypedSayCommand('!lk')
def lk(comm):
    LK(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

# =============================================================================
# >> Admin
# =============================================================================

@TypedSayCommand('admin', 'wcs_admin_base')
def admin(comm):
    AdminMain(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

@TypedSayCommand('админ', 'wcs_admin_base')
def admin(comm):
    AdminMain(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

@TypedSayCommand('!админ', 'wcs_admin_base')
def admin(comm):
    AdminMain(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.CONTINUE

@TypedSayCommand('!admin', 'wcs_admin_base')
def admin(comm):
    AdminMain(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.CONTINUE

@TypedSayCommand('/admin', 'wcs_admin_base')
def admin(comm):
    AdminMain(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

@TypedSayCommand('/админ', 'wcs_admin_base*')
def admin(comm):
    AdminMain(WCS_Players[userid_from_index(comm.index)])
    return CommandReturn.BLOCK

# =============================================================================
# >> Other
# =============================================================================

@ClientCommand('tp')
def self_tp(_, index):
    player = WCS_Players[userid_from_index(index)]
    origin = player.origin
    origin[0] = 308
    origin[1] = 2318
    origin[2] = -117
    player.teleport(origin=origin)
    return CommandReturn.BLOCK

@ClientCommand('bot_tp')
def bot_tp(_, index):
    player = WCS_Players[userid_from_index(index)]
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
    player = WCS_Players[userid_from_index(comm.index)]
    player.cash += 5000
    return CommandReturn.BLOCK

@ClientCommand('dmg')
def dmg(_, index):
    player = WCS_Players[userid_from_index(index)]
    player.take_damage(20)
    return CommandReturn.BLOCK