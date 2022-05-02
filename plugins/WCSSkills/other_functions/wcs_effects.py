# ../WCSSkills/other_functions/wcs_effects.py
# =============================================================================
# >> Imports
# =============================================================================
# Python Imports
# Type helpers
from collections.abc import Iterable
# Random
from random import randint as ri

# Source.Python Imports
# RecipientFilter
from filters.recipients import RecipientFilter
# Model PreCache
from engines.precache import engine_server, Model
# Effects entity
from effects.base import TempEntity
# Entity
from entities.entity import Entity
# Render modes constant
from entities.constants import RenderMode
# Vector
from mathlib import Vector

# Plugin Imports
from WCSSkills.other_functions.constants import orb_sprites

# =============================================================================
# >> All
# =============================================================================

__all__ = (
    'effects'
)

# =============================================================================
# >> TempEnt creator
# =============================================================================

class temporary_entity:
    __slots__ = ('users', 'tempEnt')

    def __init__(self, ent_type, users):
        self.tempEnt = TempEntity(ent_type)
        self.users = users

    def __enter__(self):
        return self.tempEnt

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tempEnt.create(RecipientFilter(*self.users))

class persistent_entity:
    __slots__ = ('entity',)

    def __init__(self, class_name):
        self.entity = Entity.create(class_name)

    def __enter__(self):
        return self.entity

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.entity.spawn()

# =============================================================================
# >> Effects
# =============================================================================

class effect:

    @staticmethod
    def beam_laser(users: Iterable, # Entity indexes that receive this effect
             start: Vector,         # Start position of beam
             end: Vector,           # End position of beam
             width: float = 1,      # Radius of tube
             lifetime: float = 1,   # Amount of time in seconds to disappear
             amplitude: float = 1,  # Wiggling in the end
             red: int = 0,          # Amount of red in beam (0-255)
             green: int = 0,        # Amount of green in beam (0-255)
             blue: int = 0,         # Amount of blue in beam (0-255)
             a: int = 255,          # Overall alpha of beam
             model: str = 'sprites/laserbeam.vmt' # Model
             ) -> None:

        with temporary_entity('BeamLaser', users) as tempEnt:
            modelIndex = engine_server.precache_model(model)

            tempEnt.red = red
            tempEnt.green = green
            tempEnt.blue = blue
            tempEnt.alpha = a
            tempEnt.start_point = start
            tempEnt.end_point = end
            tempEnt.life_time = lifetime
            tempEnt.start_width = width
            tempEnt.amplitude = amplitude
            tempEnt.halo_index = modelIndex
            tempEnt.model_index = modelIndex

    @staticmethod
    def explosion(users: Iterable,
                  origin,
                  smoke = True # Only sparks or add smoke
                  ) -> None:
        tempEnt = TempEntity('Explosion')

        # Position
        tempEnt.origin = origin

        # By default, spawn with smoke, but if needed
        # can remove smoke
        tempEnt.scale = 1 if smoke else 0
        tempEnt.create(RecipientFilter(*users))

    @staticmethod
    def energy_splash(users: Iterable,
                      origin,
                      explosion = False
                      ) -> None:
        with temporary_entity('Energy Splash', users) as tempEnt:
            tempEnt.position = origin
            if explosion:
                tempEnt.direction = origin

    @staticmethod
    def shards(users: Iterable,
               origin,
               width: float,
               height: float,
               front_color: tuple,           # Vector of 3 colors: (0-255,0-255,0-255)
               back_color: tuple,            # Shards have 2 sides. Same as front_color
               angle: Vector = Vector(90,0), # Angle. 2 Values: (0-360,0-360)
               shard_size: float = 1,        # Size of each shard
               ) -> None:

        with temporary_entity('Surface Shatter', users) as tempEnt:
            # Spawn position
            tempEnt.origin = origin

            # Size of shards (scale, doesn't add new shards)
            tempEnt.shard_size = shard_size

            # Spawner width
            tempEnt.width = width

            # Spawner height
            tempEnt.height = height

            # Spawner angle
            tempEnt.angles = angle

            # Colors
            tempEnt.set_property_int('m_uchFrontColor[0]', front_color[0])
            tempEnt.set_property_int('m_uchFrontColor[1]', front_color[1])
            tempEnt.set_property_int('m_uchFrontColor[2]', front_color[2])
            tempEnt.set_property_int('m_uchBackColor[0]', back_color[0])
            tempEnt.set_property_int('m_uchBackColor[1]', back_color[1])
            tempEnt.set_property_int('m_uchBackColor[2]', back_color[2])

    @staticmethod
    def orb(users: Iterable,
            origin: Vector,
            life: float = 1,         # LifeTime in seconds
            brightness: float = 255, # Alpha (0-255)
            scale: float = 1,
            sprite: int = 0,         # Variant of sprite (0-13)
            persistent: bool = False
            ) -> None:

        # Sprite model loading.
        # String: custom path
        # Int: number from list of sprites
        if isinstance(sprite, int):     model_name = orb_sprites[sprite % len(orb_sprites)]
        elif isinstance(sprite, str):   model_name = sprite
        else:                           raise ValueError("sprite should be int or str")

        if persistent:

            with persistent_entity('env_glow') as Ent:

                # Setting model
                Ent.model = Model(model_name)

                # Position to spawn
                Ent.origin = origin

                # —
                Ent.scale = scale

                # Making transparent and make entity differes glowing radius based on distance
                Ent.render_mode = RenderMode.GLOW

                # Returning entity
                return Ent

        else:

            with temporary_entity('GlowSprite', users) as tempEnt:

                # Sprite model
                model_index = engine_server.precache_model(model_name)
                tempEnt.model_index = model_index

                # Position to spawn
                tempEnt.origin = origin

                # Length of life in seconds
                tempEnt.life_time = life

                # Alpha
                tempEnt.brightness = brightness

                # —
                tempEnt.scale = scale

    @staticmethod
    def muzzle_flash(users: Iterable,
                     origin: Vector,
                     angle: Vector,      # Angle of muzzle_flash
                     scale: float = 1,
                     dark: bool = False  # Choose dark model
                     ) -> None:

        with temporary_entity('MuzzleFlash', users) as tempEnt:
            # Position to spawn
            tempEnt.origin = origin

            # —
            tempEnt.scale = scale

            # Vector with TWO numbers
            tempEnt.angles = angle

            # There's 2 types of muzzle_flash btw
            tempEnt.type = 4 if dark else 1

    @staticmethod
    def smoke(users: Iterable,  # Entity indexes to show effect
             origin: Vector,    # Position at which smoke will be spawned
             scale: float = 1   # Scale of model
             ) -> None:
        with temporary_entity('Smoke', users) as tempEnt:
            # Position to spawn
            tempEnt.origin = origin

            # —
            tempEnt.scale = scale

    @staticmethod
    def sparks(users: Iterable,     # Entity indexes to show effect
               origin: Vector,      # Start position
               end: Vector,         # End position, to which sparks will be fired
               height: float = 0,   # Coefficient to add some height
               trails: int = 1,     # Amount of sparks
               length: int = 1      # Length of sparks
               ) -> None:
        with temporary_entity('Sparks', users) as tempEnt:
            # Position to spawn
            tempEnt.origin = origin

            # Direction in which force applies
            proportions = (origin - end)/origin.get_distance(end)
            proportions[2] -= height
            tempEnt.direction = proportions*-1

            # Length of sparks
            tempEnt.trail_length = length

            # Amount of sparks
            tempEnt.magnitude = trails

    @staticmethod
    def sprite(users: Iterable,                    # Entity indexes to show effect
               origin: Vector = Vector(0,0,0), # Start position
               scale: float = 1,               # Scale of model
               brightness: int = 255,          # Alpha (0-255)
               model: str = 'sprites/glow.vmt' # Link to .vmt
               ) -> None:

        if not isinstance(users, Iterable) :
            raise TypeError('Wrong users argument')

        if isinstance(model, str):
            pass
        else:
            raise TypeError('Wrong model argument')

        with temporary_entity('Sprite', users) as tempEnt:
            model_index = engine_server.precache_model(model)

            tempEnt.origin = origin
            tempEnt.model_index = model_index
            tempEnt.scale = scale
            tempEnt.brightness = brightness

    @staticmethod
    def sprite_spray(users: Iterable,          # Entity indexes to show effect
                     origin: Vector,           # Start position
                     model: str,               # Link to .vmt
                     end: Vector = None,       # Position, where particle will be thrown to
                     count: int = 1,           # Amount of particles
                     height_align: float = 0,  # Height align
                     power: float = 0,         # Throw power
                     speed: int = 5,           # Speed of noising
                     noise: float = 5          # Distortion in Vector
                     ):
        with temporary_entity('Sprite Spray', users) as tempEnt:
            model_index = engine_server.precache_model(model)

            tempEnt.origin = origin
            tempEnt.model_index = model_index

            if end is not None:
                tempEnt.count = count
                proportions = (origin - end) / origin.get_distance(end)
                proportions[2] -= height_align
                tempEnt.direction = proportions * -power
                tempEnt.speed = speed
                tempEnt.noise = noise

    @staticmethod
    def shot(users: Iterable,             # Entity indexes to show effect
             origin: Vector,              # Start position
             inaccuracy: float = 0,       # Accuracy (0 — 100%, 1 — 0%)
             angle: Vector = Vector(0,0), # Angle of fire
             weapon_id: int = 7           # Index of weapon (Use WeaponID enum)
             ) -> None:

        with temporary_entity('Shotgun Shot', users) as tempEnt:
            tempEnt.origin = origin
            tempEnt.seed = ri(0,500000)
            tempEnt.spread = tempEnt.inaccuracy = inaccuracy
            tempEnt.angles = angle
            tempEnt.item_defition_index = weapon_id

    @staticmethod
    def text(origin: Vector,
             message: str,
             show_radius: int = 100,
             ):

        with persistent_entity('point_message') as Ent:
            Ent.message = message.replace('"', '_')
            Ent.radius = show_radius
            Ent.origin = origin
            return Ent