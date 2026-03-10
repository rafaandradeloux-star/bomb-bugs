from dataclasses import dataclass

from .config import SQUARE_COLOR
from .models import Actor


@dataclass(frozen=True)
class CharacterProfile:
    color: tuple[int, int, int]
    slash_damage: int
    move_speed: float
    dash_duration: float
    bomb_damage: int
    ground_pound_damage: int
    heal_amount: int
    special_stun_duration: float
    special_invincible_duration: float
    special_counter_enabled: bool
    special_hits_required: float
    max_hp: int


CHARACTER_PROFILES: dict[str, CharacterProfile] = {
    "mantis": CharacterProfile(
        color=SQUARE_COLOR,
        slash_damage=2,
        move_speed=420.0,
        dash_duration=0.22,
        bomb_damage=3,
        ground_pound_damage=3,
        heal_amount=2,
        special_stun_duration=0.0,
        special_invincible_duration=0.0,
        special_counter_enabled=True,
        special_hits_required=10.0,
        max_hp=10,
    ),
    "spider": CharacterProfile(
        color=(180, 142, 97),
        slash_damage=1,
        move_speed=360.0,
        dash_duration=0.18,
        bomb_damage=4,
        ground_pound_damage=4,
        heal_amount=2,
        special_stun_duration=1.5,
        special_invincible_duration=0.0,
        special_counter_enabled=False,
        special_hits_required=10.0,
        max_hp=10,
    ),
    "rhino_beetle": CharacterProfile(
        color=(34, 60, 126),
        slash_damage=1,
        move_speed=300.0,
        dash_duration=0.14,
        bomb_damage=5,
        ground_pound_damage=5,
        heal_amount=1,
        special_stun_duration=0.0,
        special_invincible_duration=2.0,
        special_counter_enabled=False,
        special_hits_required=10.0,
        max_hp=15,
    ),
}


def apply_character_profile(player: Actor, character_id: str, refill_hp: bool = False) -> None:
    profile = CHARACTER_PROFILES[character_id]
    player.max_hp = profile.max_hp
    player.hp = player.max_hp if refill_hp else min(player.hp, player.max_hp)

    player.color = profile.color
    player.slash_damage = profile.slash_damage
    player.move_speed = profile.move_speed
    player.dash_duration = profile.dash_duration
    player.bomb_damage = profile.bomb_damage
    player.ground_pound_damage = profile.ground_pound_damage
    player.heal_amount = profile.heal_amount

    player.bomb_charge_hits = player.bomb_hits_required
    player.ground_pound_charge_hits = player.ground_pound_hits_required

    player.special_stun_duration = profile.special_stun_duration
    player.special_invincible_duration = profile.special_invincible_duration
    player.special_counter_enabled = profile.special_counter_enabled
    player.special_counter_active = False
    player.special_hits_required = profile.special_hits_required
    player.special_charge_hits = player.special_hits_required
