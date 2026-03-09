from dataclasses import dataclass, field

import pygame

from .config import (
    BOMB_COOLDOWN,
    BOMB_DAMAGE,
    DASH_DURATION,
    ENEMY_HIT_FLASH_DURATION,
    GROUND_POUND_COOLDOWN,
    GROUND_POUND_DAMAGE,
    MAX_HP,
    SPEED,
)


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
class WebProjectile:
    x: float
    y: float
    life: float
    radius: int
    speed: float


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
class GroundSpike:
    x: float
    y: float
    life: float
    max_life: float


@dataclass
class GroundDent:
    x: float
    y: float
    life: float
    max_life: float


@dataclass
class RubbleParticle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float


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
    slash_damage: int = 1
    bomb_damage: int = BOMB_DAMAGE
    ground_pound_damage: int = GROUND_POUND_DAMAGE
    bomb_hits_required: float = BOMB_COOLDOWN
    bomb_charge_hits: float = BOMB_COOLDOWN
    ground_pound_hits_required: float = GROUND_POUND_COOLDOWN
    ground_pound_charge_hits: float = GROUND_POUND_COOLDOWN
    move_speed: float = SPEED
    dash_duration: float = DASH_DURATION
    special_stun_duration: float = 0.0
    special_hits_required: float = 0.0
    special_charge_hits: float = 0.0
    hit_flash_time: float = 0.0
    hit_flash_duration: float = ENEMY_HIT_FLASH_DURATION
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
    ground_pound_cooldown_left: float = 0.0
    trail_spawn_timer: float = 0.0
    bomb_trail_spawn_timer: float = 0.0
    dash_trail: list[DustParticle] = field(default_factory=list)
    bomb_trail: list[DustParticle] = field(default_factory=list)
    heal_splashes: list[HealSplash] = field(default_factory=list)
    bombs: list[Bomb] = field(default_factory=list)
    web_projectiles: list[WebProjectile] = field(default_factory=list)
    floating_texts: list[FloatingText] = field(default_factory=list)
    mushroom_clouds: list[MushroomCloud] = field(default_factory=list)
    ground_spikes: list[GroundSpike] = field(default_factory=list)
    ground_dents: list[GroundDent] = field(default_factory=list)
    rubble_particles: list[RubbleParticle] = field(default_factory=list)
    shake_time_left: float = 0.0
    shake_phase: float = 0.0
    ground_pound_active: bool = False


@dataclass
class EnemyAI:
    patrol_min: float = 0.0
    patrol_max: float = 0.0
    patrol_dir: int = -1
    velocity_y: float = 0.0
    is_grounded: bool = True
    jump_cooldown_left: float = 0.0
    knockback_velocity_x: float = 0.0
    speed_scale: float = 1.0
    stun_time_left: float = 0.0
    poison_ticks_left: int = 0
    poison_tick_timer: float = 0.0
    path_sample_timer: float = 0.0
    path_points: list[tuple[float, float]] = field(default_factory=list)
