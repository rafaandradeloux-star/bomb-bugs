import random

import pygame

from .config import FLOATING_TEXT_LIFETIME, FLOATING_TEXT_RISE_SPEED, HEIGHT
from .models import Actor, FloatingText, PlayerState


def find_floor_below(rect: pygame.Rect, platforms: list[pygame.Rect]) -> int:
    floor_y = HEIGHT - 4
    for platform in platforms:
        overlaps_x = rect.right > platform.left and rect.left < platform.right
        is_below = platform.top >= rect.bottom
        if overlaps_x and is_below:
            floor_y = min(floor_y, platform.top)
    return floor_y


def can_jump_from_platform(rect: pygame.Rect, grounded: bool, platforms: list[pygame.Rect]) -> bool:
    if grounded:
        return True
    feet_y = rect.bottom
    for platform in platforms:
        touches_top = abs(feet_y - platform.top) <= 3
        overlaps_x = rect.right > platform.left and rect.left < platform.right
        if touches_top and overlaps_x:
            return True
    return False


def spawn_floating_text(player_state: PlayerState, rect: pygame.Rect, value: int, is_heal: bool) -> None:
    if value <= 0:
        return
    player_state.floating_texts.append(
        FloatingText(
            x=float(rect.centerx + random.randint(-8, 8)),
            y=float(rect.top - 14),
            vy=FLOATING_TEXT_RISE_SPEED,
            life=FLOATING_TEXT_LIFETIME,
            max_life=FLOATING_TEXT_LIFETIME,
            text=f"+{value}" if is_heal else f"-{value}",
            color=(80, 250, 120) if is_heal else (255, 90, 90),
        )
    )


def spawn_status_text(
    player_state: PlayerState,
    rect: pygame.Rect,
    text: str,
    color: tuple[int, int, int],
) -> None:
    player_state.floating_texts.append(
        FloatingText(
            x=float(rect.centerx + random.randint(-8, 8)),
            y=float(rect.top - 14),
            vy=FLOATING_TEXT_RISE_SPEED,
            life=FLOATING_TEXT_LIFETIME,
            max_life=FLOATING_TEXT_LIFETIME,
            text=text,
            color=color,
        )
    )


def grant_hit_charges(player: Actor, amount: float) -> None:
    player.bomb_charge_hits = min(player.bomb_hits_required, player.bomb_charge_hits + amount)
    player.ground_pound_charge_hits = min(
        player.ground_pound_hits_required,
        player.ground_pound_charge_hits + amount,
    )
    if player.special_hits_required > 0.0:
        player.special_charge_hits = min(
            player.special_hits_required,
            player.special_charge_hits + amount,
        )
