import pygame
import math
import random

from .combat import build_slash_rect
from .config import (
    BACKGROUND,
    BOMB_COOLDOWN,
    BOMB_DAMAGE,
    BOMB_GRAVITY,
    BOMB_HITBOX_RADIUS,
    BOMB_HOMING_SPEED,
    BOMB_LIFETIME,
    BOMB_RADIUS,
    BOMB_SPEED_X,
    BOMB_SPEED_Y,
    BOMB_TRAIL_SPAWN_INTERVAL,
    DASH_COOLDOWN,
    DASH_DURATION,
    DASH_SPEED,
    ENEMY_COLOR,
    ENEMY_CHASE_SPEED,
    ENEMY_JUMP_COOLDOWN,
    ENEMY_JUMP_VELOCITY,
    ENEMY_SIZE,
    ENEMY_SLASH_COOLDOWN,
    ENEMY_SPEED,
    GRAVITY,
    HEIGHT,
    HEAL_AMOUNT,
    HEAL_COOLDOWN,
    FLOATING_TEXT_LIFETIME,
    FLOATING_TEXT_RISE_SPEED,
    MAX_HP,
    PLATFORM_COLOR,
    PLAYER_SLASH_COOLDOWN,
    RESPAWN_ANIM_TIME,
    RESPAWN_DELAY,
    SLASH_ACTIVE_TIME,
    SLASH_RANGE_X,
    SQUARE_COLOR,
    SQUARE_SIZE,
    SPEED,
    TRAIL_SPAWN_INTERVAL,
    WIDTH,
    JUMP_VELOCITY,
)
from .effects import (
    draw_crescent_slash,
    draw_dash_trail,
    draw_dust_particles,
    draw_respawn_particles,
    make_dust_particles,
    make_heal_splash,
    make_respawn_particles,
    make_trail_particle,
    update_heal_splashes,
    update_dust_particles,
    update_respawn_particles,
    draw_heal_splashes,
)
from .models import Actor, Bomb, EnemyAI, FloatingText, PlayerState
from .ui import create_pixel_font, draw_debug_hud, draw_floating_texts, draw_health_bar
from .world import make_platforms, resolve_platform_landing


def run_game() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bomb Bugs - Movement Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    floating_text_font = create_pixel_font(18)

    platforms = make_platforms()

    player_spawn = (int((WIDTH - SQUARE_SIZE) / 2), int(platforms[0].top - SQUARE_SIZE))
    enemy_spawn = (680, int(platforms[0].top - ENEMY_SIZE))

    player = Actor(
        rect=pygame.Rect(player_spawn[0], player_spawn[1], SQUARE_SIZE, SQUARE_SIZE),
        color=SQUARE_COLOR,
        facing_dir=1,
    )
    enemy = Actor(
        rect=pygame.Rect(enemy_spawn[0], enemy_spawn[1], ENEMY_SIZE, ENEMY_SIZE),
        color=ENEMY_COLOR,
        facing_dir=-1,
    )

    player_state = PlayerState()
    enemy_ai = EnemyAI(
        patrol_min=float(enemy_spawn[0] - 180),
        patrol_max=float(enemy_spawn[0] + 180),
        patrol_dir=-1,
    )

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        _tick_timers(player, enemy, player_state, dt)
        _update_particles(player, enemy, player_state, dt)
        _handle_respawns(player, enemy, player_state, enemy_ai, player_spawn, enemy_spawn, dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                _handle_input_event(event, player, enemy, player_state, platforms)

        keys = pygame.key.get_pressed()

        _update_player(player, player_state, keys, platforms, dt)
        _update_enemy(enemy, enemy_ai, player, platforms, dt)
        _resolve_combat(player, enemy, player_state)

        _render(screen, font, floating_text_font, platforms, player, enemy, player_state)

    pygame.quit()


def _tick_timers(player: Actor, enemy: Actor, player_state: PlayerState, dt: float) -> None:
    player_state.dash_time_left = max(0.0, player_state.dash_time_left - dt)
    player_state.dash_cooldown_left = max(0.0, player_state.dash_cooldown_left - dt)
    player_state.heal_cooldown_left = max(0.0, player_state.heal_cooldown_left - dt)
    player_state.bomb_cooldown_left = max(0.0, player_state.bomb_cooldown_left - dt)
    player_state.trail_spawn_timer = max(0.0, player_state.trail_spawn_timer - dt)
    player_state.bomb_trail_spawn_timer = max(0.0, player_state.bomb_trail_spawn_timer - dt)

    player.slash_time_left = max(0.0, player.slash_time_left - dt)
    player.slash_cooldown_left = max(0.0, player.slash_cooldown_left - dt)
    enemy.slash_time_left = max(0.0, enemy.slash_time_left - dt)
    enemy.slash_cooldown_left = max(0.0, enemy.slash_cooldown_left - dt)


def _update_particles(player: Actor, enemy: Actor, player_state: PlayerState, dt: float) -> None:
    player_state.dash_trail = update_dust_particles(player_state.dash_trail, dt)
    player_state.bomb_trail = update_dust_particles(player_state.bomb_trail, dt)
    player_state.heal_splashes = update_heal_splashes(player_state.heal_splashes, dt)
    player.death_particles = update_dust_particles(player.death_particles, dt)
    enemy.death_particles = update_dust_particles(enemy.death_particles, dt)
    player.respawn_particles = update_respawn_particles(player.respawn_particles, dt)
    enemy.respawn_particles = update_respawn_particles(enemy.respawn_particles, dt)
    player_state.floating_texts = _update_floating_texts(player_state.floating_texts, dt)
    _update_bombs(player, enemy, player_state, dt)


def _handle_respawns(
    player: Actor,
    enemy: Actor,
    player_state: PlayerState,
    enemy_ai: EnemyAI,
    player_spawn: tuple[int, int],
    enemy_spawn: tuple[int, int],
    dt: float,
) -> None:
    if not player.alive:
        player.respawn_timer = max(0.0, player.respawn_timer - dt)
        if player.respawn_timer <= RESPAWN_ANIM_TIME and not player.respawn_particles:
            player.respawn_particles = make_respawn_particles(
                pygame.Rect(player_spawn[0], player_spawn[1], player.rect.width, player.rect.height),
                player.color,
            )
        if player.respawn_timer <= 0.0:
            player.alive = True
            player.hp = player.max_hp
            player.rect.topleft = player_spawn
            player_state.velocity_y = 0.0
            player_state.is_grounded = True
            player.death_particles.clear()
            player.respawn_particles.clear()
            player.slash_time_left = 0.0
            player.slash_cooldown_left = 0.0
            player_state.dash_time_left = 0.0
            player_state.bombs.clear()
            player_state.bomb_trail.clear()
            player_state.floating_texts.clear()

    if not enemy.alive:
        enemy.respawn_timer = max(0.0, enemy.respawn_timer - dt)
        if enemy.respawn_timer <= RESPAWN_ANIM_TIME and not enemy.respawn_particles:
            enemy.respawn_particles = make_respawn_particles(
                pygame.Rect(enemy_spawn[0], enemy_spawn[1], enemy.rect.width, enemy.rect.height),
                enemy.color,
            )
        if enemy.respawn_timer <= 0.0:
            enemy.alive = True
            enemy.hp = enemy.max_hp
            enemy.rect.topleft = enemy_spawn
            enemy.death_particles.clear()
            enemy.respawn_particles.clear()
            enemy.slash_time_left = 0.0
            enemy.slash_cooldown_left = 0.0
            enemy_ai.velocity_y = 0.0
            enemy_ai.is_grounded = True
            enemy_ai.jump_cooldown_left = 0.0


def _handle_input_event(
    event: pygame.event.Event,
    player: Actor,
    enemy: Actor,
    player_state: PlayerState,
    platforms: list[pygame.Rect],
) -> None:
    if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
        if player.alive and player_state.is_grounded:
            player_state.velocity_y = JUMP_VELOCITY
            player_state.is_grounded = False
        return

    if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
        if player.alive and player_state.bomb_cooldown_left <= 0.0:
            player_state.bomb_cooldown_left = BOMB_COOLDOWN
            player_state.bombs.append(
                Bomb(
                    x=float(player.rect.centerx + player.facing_dir * 18),
                    y=float(player.rect.centery - 12),
                    vx=float(player.facing_dir * BOMB_SPEED_X),
                    vy=float(BOMB_SPEED_Y),
                    life=float(BOMB_LIFETIME),
                    radius=BOMB_RADIUS,
                    trail_timer=0.0,
                )
            )
        return

    if event.type == pygame.KEYDOWN and event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
        if player.alive and player_state.dash_time_left <= 0.0 and player_state.dash_cooldown_left <= 0.0:
            keys = pygame.key.get_pressed()
            input_dir = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                input_dir -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                input_dir += 1
            player_state.dash_dir = input_dir if input_dir != 0 else player.facing_dir
            if player_state.dash_dir != 0:
                player_state.dash_time_left = DASH_DURATION
                player_state.dash_cooldown_left = DASH_COOLDOWN
                player_state.trail_spawn_timer = 0.0
        return

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if player.alive and player.slash_cooldown_left <= 0.0:
            player_slash_rect = build_slash_rect(player.rect, player.facing_dir)
            player.slash_time_left = SLASH_ACTIVE_TIME
            player.slash_cooldown_left = PLAYER_SLASH_COOLDOWN

            if enemy.alive and player_slash_rect.colliderect(enemy.rect):
                old_hp = enemy.hp
                enemy.hp = max(0, enemy.hp - 1)
                _spawn_floating_text(player_state, enemy.rect, old_hp - enemy.hp, is_heal=False)
                if enemy.hp == 0:
                    enemy.alive = False
                    enemy.respawn_timer = RESPAWN_DELAY + RESPAWN_ANIM_TIME
                    enemy.death_particles = make_dust_particles(enemy.rect)
                    enemy.respawn_particles.clear()
                    enemy.slash_time_left = 0.0
        return

    if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
        if player.alive and player_state.heal_cooldown_left <= 0.0:
            old_hp = player.hp
            player.hp = min(player.max_hp, player.hp + HEAL_AMOUNT)
            player_state.heal_cooldown_left = HEAL_COOLDOWN
            splash_y = _find_floor_below(player.rect, platforms)
            player_state.heal_splashes.append(make_heal_splash(float(player.rect.centerx), float(splash_y)))
            _spawn_floating_text(player_state, player.rect, player.hp - old_hp, is_heal=True)


def _find_floor_below(rect: pygame.Rect, platforms: list[pygame.Rect]) -> int:
    floor_y = HEIGHT - 4
    for platform in platforms:
        overlaps_x = rect.right > platform.left and rect.left < platform.right
        is_below = platform.top >= rect.bottom
        if overlaps_x and is_below:
            floor_y = min(floor_y, platform.top)
    return floor_y


def _update_bombs(player: Actor, enemy: Actor, player_state: PlayerState, dt: float) -> None:
    active_bombs: list[Bomb] = []
    for bomb in player_state.bombs:
        bomb.life -= dt
        if bomb.homing and enemy.alive:
            dx = enemy.rect.centerx - bomb.x
            dy = enemy.rect.centery - bomb.y
            distance = math.hypot(dx, dy)
            if distance > 0:
                step = BOMB_HOMING_SPEED * dt
                if distance <= step:
                    bomb.x = float(enemy.rect.centerx)
                    bomb.y = float(enemy.rect.centery)
                else:
                    bomb.x += (dx / distance) * step
                    bomb.y += (dy / distance) * step
        else:
            bomb.vy += BOMB_GRAVITY * dt
            bomb.x += bomb.vx * dt
            bomb.y += bomb.vy * dt
        bomb.trail_timer -= dt
        if bomb.trail_timer <= 0.0:
            player_state.bomb_trail.append(make_trail_particle(bomb.x - bomb.radius, bomb.y - bomb.radius))
            bomb.trail_timer = BOMB_TRAIL_SPAWN_INTERVAL

        if bomb.life <= 0.0:
            continue
        if bomb.x < -30 or bomb.x > WIDTH + 30 or bomb.y > HEIGHT + 30:
            continue

        if enemy.alive:
            radius = BOMB_HITBOX_RADIUS
            bomb_rect = pygame.Rect(int(bomb.x - radius), int(bomb.y - radius), radius * 2, radius * 2)
            if bomb_rect.colliderect(enemy.rect):
                old_hp = enemy.hp
                enemy.hp = max(0, enemy.hp - BOMB_DAMAGE)
                _spawn_floating_text(player_state, enemy.rect, old_hp - enemy.hp, is_heal=False)
                if enemy.hp == 0:
                    enemy.alive = False
                    enemy.respawn_timer = RESPAWN_DELAY + RESPAWN_ANIM_TIME
                    enemy.death_particles = make_dust_particles(enemy.rect)
                    enemy.respawn_particles.clear()
                    enemy.slash_time_left = 0.0
                continue

        active_bombs.append(bomb)
    player_state.bombs = active_bombs


def _update_player(
    player: Actor,
    player_state: PlayerState,
    keys: pygame.key.ScancodeWrapper,
    platforms: list[pygame.Rect],
    dt: float,
) -> None:
    if not player.alive:
        return

    direction = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        direction -= 1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        direction += 1
    if direction != 0:
        player.facing_dir = direction

    if player_state.dash_time_left > 0.0:
        player.rect.x += int(player_state.dash_dir * DASH_SPEED * dt)
        if player_state.trail_spawn_timer <= 0.0:
            player_state.dash_trail.append(make_trail_particle(float(player.rect.x), float(player.rect.y)))
            player_state.trail_spawn_timer = TRAIL_SPAWN_INTERVAL
    else:
        player.rect.x += int(direction * SPEED * dt)
    player.rect.x = max(0, min(player.rect.x, WIDTH - player.rect.width))

    previous_bottom = player.rect.bottom
    player_state.velocity_y += GRAVITY * dt
    player.rect.y += int(player_state.velocity_y * dt)
    player_state.is_grounded = False

    new_y, new_velocity, grounded = resolve_platform_landing(player.rect, previous_bottom, player_state.velocity_y, platforms)
    player.rect.y = new_y
    player_state.velocity_y = new_velocity
    player_state.is_grounded = grounded


def _update_enemy(enemy: Actor, enemy_ai: EnemyAI, player: Actor, platforms: list[pygame.Rect], dt: float) -> None:
    if not enemy.alive:
        return

    if player.alive:
        dx = player.rect.centerx - enemy.rect.centerx
        if abs(dx) > 8:
            enemy.facing_dir = 1 if dx > 0 else -1
            enemy.rect.x += int(enemy.facing_dir * ENEMY_CHASE_SPEED * dt)

        enemy_ai.jump_cooldown_left = max(0.0, enemy_ai.jump_cooldown_left - dt)
        player_is_higher = player.rect.centery + 12 < enemy.rect.centery
        close_enough = abs(dx) < 260
        if enemy_ai.is_grounded and enemy_ai.jump_cooldown_left <= 0.0 and player_is_higher and close_enough:
            enemy_ai.velocity_y = ENEMY_JUMP_VELOCITY
            enemy_ai.is_grounded = False
            enemy_ai.jump_cooldown_left = ENEMY_JUMP_COOLDOWN
    else:
        enemy.rect.x += int(enemy_ai.patrol_dir * ENEMY_SPEED * dt)
        if enemy.rect.x < int(enemy_ai.patrol_min):
            enemy.rect.x = int(enemy_ai.patrol_min)
            enemy_ai.patrol_dir = 1
        elif enemy.rect.x > int(enemy_ai.patrol_max):
            enemy.rect.x = int(enemy_ai.patrol_max)
            enemy_ai.patrol_dir = -1

    previous_bottom = enemy.rect.bottom
    enemy_ai.velocity_y += GRAVITY * dt
    enemy.rect.y += int(enemy_ai.velocity_y * dt)
    enemy_ai.is_grounded = False

    new_y, new_velocity, grounded = resolve_platform_landing(enemy.rect, previous_bottom, enemy_ai.velocity_y, platforms)
    enemy.rect.y = new_y
    enemy_ai.velocity_y = new_velocity
    enemy_ai.is_grounded = grounded

    enemy.rect.x = max(0, min(enemy.rect.x, WIDTH - enemy.rect.width))


def _resolve_combat(player: Actor, enemy: Actor, player_state: PlayerState) -> None:
    if not (player.alive and enemy.alive):
        return

    dx = player.rect.centerx - enemy.rect.centerx
    in_attack_x = abs(dx) <= (SLASH_RANGE_X + 10)
    in_attack_y = abs(player.rect.centery - enemy.rect.centery) <= 70
    if in_attack_x and in_attack_y and enemy.slash_cooldown_left <= 0.0:
        enemy_slash_rect = build_slash_rect(enemy.rect, enemy.facing_dir)
        enemy.slash_time_left = SLASH_ACTIVE_TIME
        enemy.slash_cooldown_left = ENEMY_SLASH_COOLDOWN

        if enemy_slash_rect.colliderect(player.rect):
            old_hp = player.hp
            player.hp = max(0, player.hp - 1)
            _spawn_floating_text(player_state, player.rect, old_hp - player.hp, is_heal=False)
            if player.hp == 0:
                player.alive = False
                player.respawn_timer = RESPAWN_DELAY + RESPAWN_ANIM_TIME
                player.death_particles = make_dust_particles(player.rect)
                player.respawn_particles.clear()
                player.slash_time_left = 0.0
                player_state.dash_time_left = 0.0
                player_state.bombs.clear()
                player_state.bomb_trail.clear()
                player_state.floating_texts.clear()
            player_state.heal_splashes.clear()


def _render(
    screen: pygame.Surface,
    font: pygame.font.Font,
    floating_text_font: pygame.font.Font,
    platforms: list[pygame.Rect],
    player: Actor,
    enemy: Actor,
    player_state: PlayerState,
) -> None:
    screen.fill(BACKGROUND)
    for platform in platforms:
        pygame.draw.rect(screen, PLATFORM_COLOR, platform)

    draw_dash_trail(screen, player_state.dash_trail, player.rect.width, player.color)
    draw_dash_trail(screen, player_state.bomb_trail, BOMB_RADIUS * 2, (45, 45, 45))
    draw_heal_splashes(screen, player_state.heal_splashes)
    for bomb in player_state.bombs:
        radius = int(bomb.radius)
        pygame.draw.circle(screen, (28, 28, 28), (int(bomb.x), int(bomb.y)), radius)
        pygame.draw.circle(screen, (250, 160, 40), (int(bomb.x - radius * 0.2), int(bomb.y - radius * 0.6)), 2)

    if player.alive:
        pygame.draw.rect(screen, player.color, player.rect)
        draw_health_bar(screen, player.rect, player.hp, MAX_HP)
    if enemy.alive:
        pygame.draw.rect(screen, enemy.color, enemy.rect)
        draw_health_bar(screen, enemy.rect, enemy.hp, MAX_HP)

    draw_dust_particles(screen, player.death_particles, (170, 150, 130))
    draw_dust_particles(screen, enemy.death_particles, (170, 150, 130))
    draw_respawn_particles(screen, player.respawn_particles)
    draw_respawn_particles(screen, enemy.respawn_particles)

    if player.alive and player.slash_time_left > 0.0:
        draw_crescent_slash(screen, player.rect, player.facing_dir, player.slash_time_left)
    if enemy.alive and enemy.slash_time_left > 0.0:
        draw_crescent_slash(screen, enemy.rect, enemy.facing_dir, enemy.slash_time_left)
    draw_floating_texts(screen, floating_text_font, player_state.floating_texts)

    draw_debug_hud(
        screen,
        font,
        (player.rect.x, player.rect.y),
        player_state.dash_cooldown_left,
        player_state.heal_cooldown_left,
        player_state.bomb_cooldown_left,
        player.slash_cooldown_left,
        enemy.slash_cooldown_left,
        player.hp,
        enemy.hp,
        player.alive,
        enemy.alive,
        player.respawn_timer,
        enemy.respawn_timer,
    )

    pygame.display.flip()


def _update_floating_texts(texts: list[FloatingText], dt: float) -> list[FloatingText]:
    active_texts: list[FloatingText] = []
    for text in texts:
        text.life -= dt
        text.y -= text.vy * dt
        if text.life > 0.0:
            active_texts.append(text)
    return active_texts


def _spawn_floating_text(player_state: PlayerState, rect: pygame.Rect, value: int, is_heal: bool) -> None:
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
