# ../WCSSkills/other_functions/typing_types.py

# Python Imports
from typing import NewType

# Plugin Imports
from WCSSkills.skills.skill import BaseSkill
from WCSSkills.skills.immune import ImmuneSkill

__all__ = (
    'Skill',
    'Immune'
)

Skill = NewType('Skill', BaseSkill)
Immune = NewType('Immune', ImmuneSkill)