import pygame

from .config import (
    BOMB_COOLDOWN,
    DASH_COOLDOWN,
    FLOOR_HEIGHT,
    GROUND_POUND_COOLDOWN,
    HEALTH_BAR_HEIGHT,
    HEALTH_BAR_WIDTH,
    HEAL_COOLDOWN,
    HEIGHT,
    TEXT_COLOR,
)
from .models import FloatingText


def draw_health_bar(surface: pygame.Surface, entity_rect: pygame.Rect, hp: int, max_hp: int) -> None:
    health_ratio = max(0.0, min(1.0, hp / max_hp))
    bar_x = entity_rect.centerx - HEALTH_BAR_WIDTH // 2
    bar_y = entity_rect.top - 16
    pygame.draw.rect(surface, (60, 20, 20), (bar_x, bar_y, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT))
    pygame.draw.rect(
        surface,
        (40, 200, 70),
        (bar_x, bar_y, int(HEALTH_BAR_WIDTH * health_ratio), HEALTH_BAR_HEIGHT),
    )
    pygame.draw.rect(surface, (20, 20, 20), (bar_x, bar_y, HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT), 2)


def draw_debug_hud(
    surface: pygame.Surface,
    font: pygame.font.Font,
    player_pos: tuple[int, int],
    dash_cooldown: float,
    heal_cooldown: float,
    bomb_cooldown: float,
    player_slash_cd: float,
    enemy_slash_cd: float,
    player_hp: int,
    enemy_hp: int,
    player_alive: bool,
    enemy_alive: bool,
    player_respawn_timer: float,
    enemy_respawn_timer: float,
) -> None:
    lines = [
        f"Cube position: x={player_pos[0]}, y={player_pos[1]}",
        f"Dash cooldown: {dash_cooldown:.2f}s",
        f"Heal cooldown: {heal_cooldown:.2f}s",
        f"Bomb cooldown: {bomb_cooldown:.2f}s",
        f"Player slash cd: {player_slash_cd:.2f}s",
        f"Enemy slash cd: {enemy_slash_cd:.2f}s",
        f"Player HP: {player_hp}",
        f"Enemy HP: {enemy_hp}",
        f"Player respawn: {player_respawn_timer:.1f}s" if not player_alive else "Player respawn: ready",
        f"Enemy respawn: {enemy_respawn_timer:.1f}s" if not enemy_alive else "Enemy respawn: ready",
    ]

    y = 16
    for line in lines:
        text = font.render(line, True, TEXT_COLOR)
        surface.blit(text, (16, y))
        y += 32


def create_pixel_font(size: int = 18) -> pygame.font.Font:
    for name in ("pressstart2p", "silkscreen", "pixelmix"):
        path = pygame.font.match_font(name)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


def draw_floating_texts(surface: pygame.Surface, font: pygame.font.Font, texts: list[FloatingText]) -> None:
    for text in texts:
        alpha = int(255 * (text.life / text.max_life))
        glyph = font.render(text.text, False, text.color)
        glyph.set_alpha(alpha)
        surface.blit(glyph, (int(text.x), int(text.y)))


def draw_ability_boxes(
    surface: pygame.Surface,
    dash_cooldown_left: float,
    heal_cooldown_left: float,
    bomb_cooldown_left: float,
    ground_pound_cooldown_left: float,
) -> None:
    box_size = 52
    padding = 12
    base_x = 18
    base_y = HEIGHT - FLOOR_HEIGHT + (FLOOR_HEIGHT - box_size) // 2

    dash_ratio = 1.0 - max(0.0, min(1.0, dash_cooldown_left / DASH_COOLDOWN))
    heal_ratio = 1.0 - max(0.0, min(1.0, heal_cooldown_left / HEAL_COOLDOWN))
    bomb_ratio = 1.0 - max(0.0, min(1.0, bomb_cooldown_left / BOMB_COOLDOWN))
    pound_ratio = 1.0 - max(0.0, min(1.0, ground_pound_cooldown_left / GROUND_POUND_COOLDOWN))

    dash_rect = pygame.Rect(base_x, base_y, box_size, box_size)
    bomb_rect = pygame.Rect(base_x + box_size + padding, base_y, box_size, box_size)
    heal_rect = pygame.Rect(base_x + (box_size + padding) * 2, base_y, box_size, box_size)
    pound_rect = pygame.Rect(base_x + (box_size + padding) * 3, base_y, box_size, box_size)

    _draw_box(surface, dash_rect)
    _draw_box(surface, bomb_rect)
    _draw_box(surface, heal_rect)
    _draw_box(surface, pound_rect)

    _draw_icon_with_recharge(surface, dash_rect, dash_ratio, _draw_dash_icon)
    _draw_icon_with_recharge(surface, bomb_rect, bomb_ratio, _draw_bomb_icon)
    _draw_icon_with_recharge(surface, heal_rect, heal_ratio, _draw_potion_icon)
    _draw_icon_with_recharge(surface, pound_rect, pound_ratio, _draw_ground_pound_icon)


def _draw_box(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, (93, 67, 47), rect)
    pygame.draw.rect(surface, (34, 24, 17), rect, 3)
    # Subtle bevel so slots look like framed inventory boxes.
    pygame.draw.line(surface, (132, 101, 74), rect.topleft, (rect.right - 1, rect.top), 2)
    pygame.draw.line(surface, (132, 101, 74), rect.topleft, (rect.left, rect.bottom - 1), 2)
    pygame.draw.line(surface, (58, 42, 30), (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1), 2)
    pygame.draw.line(surface, (58, 42, 30), (rect.right - 1, rect.top), (rect.right - 1, rect.bottom - 1), 2)
    inner = rect.inflate(-8, -8)
    pygame.draw.rect(surface, (112, 86, 64), inner, 1)


def _draw_icon_with_recharge(
    surface: pygame.Surface,
    rect: pygame.Rect,
    recharge_ratio: float,
    icon_drawer,
) -> None:
    size = rect.width - 12
    icon_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    gray_surface = pygame.Surface((size, size), pygame.SRCALPHA)

    icon_drawer(icon_surface, colored=True)
    icon_drawer(gray_surface, colored=False)

    surface.blit(gray_surface, (rect.x + 6, rect.y + 6))

    color_height = int(size * recharge_ratio)
    if color_height > 0:
        clip_rect = pygame.Rect(0, size - color_height, size, color_height)
        colored_part = icon_surface.subsurface(clip_rect)
        surface.blit(colored_part, (rect.x + 6, rect.y + 6 + size - color_height))


def _draw_pixel_pattern(
    target: pygame.Surface,
    pattern: list[str],
    palette: dict[str, tuple[int, int, int, int]],
    scale: int = 4,
) -> None:
    for row_idx, row in enumerate(pattern):
        for col_idx, ch in enumerate(row):
            if ch == ".":
                continue
            color = palette.get(ch)
            if color:
                pygame.draw.rect(
                    target,
                    color,
                    pygame.Rect(col_idx * scale, row_idx * scale, scale, scale),
                )


def _draw_bomb_icon(target: pygame.Surface, colored: bool) -> None:
    pattern = [
        "...2222...",
        "..233332..",
        "..211112..",
        ".21111112.",
        ".11111111.",
        ".11111111.",
        ".11111111.",
        "..111111..",
        "...1111.4.",
        ".....444..",
    ]
    palette = {
        "1": (27, 27, 30, 255) if colored else (92, 92, 92, 255),
        "2": (95, 95, 100, 255) if colored else (118, 118, 118, 255),
        "3": (180, 180, 188, 255) if colored else (132, 132, 132, 255),
        "4": (255, 173, 59, 255) if colored else (125, 125, 125, 255),
    }
    _draw_pixel_pattern(target, pattern, palette)


def _draw_potion_icon(target: pygame.Surface, colored: bool) -> None:
    pattern = [
        "....33....",
        "....33....",
        "...3223...",
        "...2112...",
        "..211112..",
        "..211112..",
        "..211112..",
        "...1111...",
        "...1111...",
        "....11....",
    ]
    palette = {
        "1": (60, 221, 111, 255) if colored else (108, 108, 108, 255),
        "2": (192, 238, 255, 255) if colored else (145, 145, 145, 255),
        "3": (176, 125, 74, 255) if colored else (125, 125, 125, 255),
    }
    _draw_pixel_pattern(target, pattern, palette)


def _draw_dash_icon(target: pygame.Surface, colored: bool) -> None:
    pattern = [
        "..........",
        "....1.....",
        "...11.....",
        "..1111....",
        ".11111111.",
        "..1111....",
        "...11.....",
        "....1.....",
        ".....22...",
        "....2222..",
    ]
    palette = {
        "1": (255, 255, 255, 255) if colored else (150, 150, 150, 255),
        "2": (210, 240, 255, 255) if colored else (130, 130, 130, 255),
    }
    _draw_pixel_pattern(target, pattern, palette)


def _draw_ground_pound_icon(target: pygame.Surface, colored: bool) -> None:
    pattern = [
        "...4444...",
        "...4224...",
        "...4224...",
        "...4444...",
        "....11....",
        "...1111...",
        "..111111..",
        "...1111...",
        "....11....",
        "...3333...",
    ]
    palette = {
        "1": (248, 248, 248, 255) if colored else (145, 145, 145, 255),
        "2": (180, 82, 55, 255) if colored else (120, 120, 120, 255),
        "3": (142, 88, 54, 255) if colored else (115, 115, 115, 255),
        "4": (206, 168, 122, 255) if colored else (135, 135, 135, 255),
    }
    _draw_pixel_pattern(target, pattern, palette)
