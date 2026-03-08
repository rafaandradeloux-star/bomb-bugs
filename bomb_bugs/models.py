from dataclasses import dataclass, field

import pygame

from .config import MAX_HP


@dataclass
class DustParticle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float


@dataclass
class RespawnParticle:
    sx: float
    sy: float
    tx: float
    ty: float
    life: float
    max_life: float
    size: float
    r: float
    g: float
    b: float


@dataclass
class HealSplash:
    x: float
    y: float
    life: float
    max_life: float
    max_radius: float


@dataclass
class Bomb:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    radius: int
    trail_timer: float = 0.0
    homing: bool = True


@dataclass
class FloatingText:
    x: float
    y: float
    vy: float
    life: float
    max_life: float
    text: str
    color: tuple[int, int, int]


@dataclass
class MushroomCloud:
    x: float
    y: float
    life: float
    max_life: float


@dataclass
class Actor:
    rect: pygame.Rect
    color: tuple[int, int, int]
    hp: int = MAX_HP
    max_hp: int = MAX_HP
    alive: bool = True
    respawn_timer: float = 0.0
    slash_time_left: float = 0.0
    slash_cooldown_left: float = 0.0
    facing_dir: int = 1
    death_particles: list[DustParticle] = field(default_factory=list)
    respawn_particles: list[RespawnParticle] = field(default_factory=list)


@dataclass
class PlayerState:
    velocity_y: float = 0.0
    is_grounded: bool = True
    dash_dir: int = 0
    dash_time_left: float = 0.0
    dash_cooldown_left: float = 0.0
    heal_cooldown_left: float = 0.0
    bomb_cooldown_left: float = 0.0
    trail_spawn_timer: float = 0.0
    bomb_trail_spawn_timer: float = 0.0
    dash_trail: list[DustParticle] = field(default_factory=list)
    bomb_trail: list[DustParticle] = field(default_factory=list)
    heal_splashes: list[HealSplash] = field(default_factory=list)
    bombs: list[Bomb] = field(default_factory=list)
    floating_texts: list[FloatingText] = field(default_factory=list)
    mushroom_clouds: list[MushroomCloud] = field(default_factory=list)
    shake_time_left: float = 0.0
    shake_phase: float = 0.0


@dataclass
class EnemyAI:
    patrol_min: float = 0.0
    patrol_max: float = 0.0
    patrol_dir: int = -1
    velocity_y: float = 0.0
    is_grounded: bool = True
    jump_cooldown_left: float = 0.0
