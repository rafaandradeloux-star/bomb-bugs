import math
import random

import pygame

from .combat import build_slash_rect
from .config import (
    BOMB_KNOCKBACK_SPEED,
    BOMB_GRAVITY,
    BOMB_HITBOX_RADIUS,
    BOMB_HOMING_SPEED,
    BOMB_LIFETIME,
    BOMB_RADIUS,
    BOMB_SPEED_X,
    BOMB_SPEED_Y,
    BOMB_TRAIL_SPAWN_INTERVAL,
    DASH_COOLDOWN,
    DASH_SPEED,
    ENEMY_CHASE_SPEED,
    ENEMY_HIT_SLOW_MIN,
    ENEMY_HIT_SLOW_RECOVERY,
    ENEMY_JUMP_COOLDOWN,
    ENEMY_JUMP_VELOCITY,
    ENEMY_KNOCKBACK_DECEL,
    ENEMY_PATH_MAX_POINTS,
    ENEMY_PATH_SAMPLE_INTERVAL,
    ENEMY_SLASH_COOLDOWN,
    ENEMY_SPEED,
    FLOATING_TEXT_LIFETIME,
    FLOATING_TEXT_RISE_SPEED,
    GRAVITY,
    GROUND_POUND_FALL_SPEED,
    HEAL_AMOUNT,
    HEAL_COOLDOWN,
    HEIGHT,
    JUMP_VELOCITY,
    PLAYER_SLASH_COOLDOWN,
    PLAYER_SLASH_KNOCKBACK_SPEED,
    RESPAWN_ANIM_TIME,
    RESPAWN_DELAY,
    SCREEN_SHAKE_DURATION,
    SLASH_ACTIVE_TIME,
    SLASH_RANGE_X,
    SPIDER_POISON_TICK_INTERVAL,
    SPIDER_POISON_TOTAL_HITS,
    TRAIL_SPAWN_INTERVAL,
    WEB_PROJECTILE_HITBOX_RADIUS,
    WEB_PROJECTILE_LIFETIME,
    WEB_PROJECTILE_RADIUS,
    WEB_PROJECTILE_SPEED,
    WEB_UNWRAP_BLIP_DURATION,
    WIDTH,
)
from .effects import (
    make_dust_particles,
    make_ground_dent,
    make_ground_spike,
    make_rubble_particles,
    make_heal_splash,
    make_mushroom_cloud,
    make_trail_particle,
    update_dust_particles,
    update_ground_dents,
    update_ground_spikes,
    update_heal_splashes,
    update_mushroom_clouds,
    update_respawn_particles,
    update_rubble_particles,
)
from .models import Actor, Bomb, EnemyAI, FloatingText, PlayerState, WebProjectile
from .world import resolve_platform_landing


def tick_timers(player: Actor, enemy: Actor, player_state: PlayerState, dt: float) -> None:
    player_state.dash_time_left = max(0.0, player_state.dash_time_left - dt)
    player_state.dash_cooldown_left = max(0.0, player_state.dash_cooldown_left - dt)
    player_state.heal_cooldown_left = max(0.0, player_state.heal_cooldown_left - dt)
    player_state.shake_time_left = max(0.0, player_state.shake_time_left - dt)
    if player_state.shake_time_left > 0.0:
        player_state.shake_phase += dt * 34.0
    player_state.trail_spawn_timer = max(0.0, player_state.trail_spawn_timer - dt)
    player_state.bomb_trail_spawn_timer = max(0.0, player_state.bomb_trail_spawn_timer - dt)

    player.slash_time_left = max(0.0, player.slash_time_left - dt)
    player.slash_cooldown_left = max(0.0, player.slash_cooldown_left - dt)
    player.invincible_time_left = max(0.0, player.invincible_time_left - dt)
    player.hit_flash_time = max(0.0, player.hit_flash_time - dt)
    enemy.slash_time_left = max(0.0, enemy.slash_time_left - dt)
    enemy.slash_cooldown_left = max(0.0, enemy.slash_cooldown_left - dt)
    enemy.hit_flash_time = max(0.0, enemy.hit_flash_time - dt)


def update_particles(player: Actor, enemy: Actor, enemy_ai: EnemyAI, player_state: PlayerState, dt: float) -> None:
    player_state.dash_trail = update_dust_particles(player_state.dash_trail, dt)
    player_state.bomb_trail = update_dust_particles(player_state.bomb_trail, dt)
    player_state.heal_splashes = update_heal_splashes(player_state.heal_splashes, dt)
    player_state.ground_spikes = update_ground_spikes(player_state.ground_spikes, dt)
    player_state.ground_dents = update_ground_dents(player_state.ground_dents, dt)
    player_state.rubble_particles = update_rubble_particles(player_state.rubble_particles, dt)
    player.death_particles = update_dust_particles(player.death_particles, dt)
    enemy.death_particles = update_dust_particles(enemy.death_particles, dt)
    player.respawn_particles = update_respawn_particles(player.respawn_particles, dt)
    enemy.respawn_particles = update_respawn_particles(enemy.respawn_particles, dt)
    player_state.mushroom_clouds = update_mushroom_clouds(player_state.mushroom_clouds, dt)
    player_state.floating_texts = _update_floating_texts(player_state.floating_texts, dt)
    _update_bombs(player, enemy, enemy_ai, player_state, dt)
    _update_web_projectiles(player, enemy, enemy_ai, player_state, dt)


def handle_respawns(
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
        if 0.0 < player.respawn_timer <= RESPAWN_ANIM_TIME:
            progress = 1.0 - (player.respawn_timer / RESPAWN_ANIM_TIME)
            eased = 1.0 - pow(1.0 - progress, 3.0)  # Ease-out: fast start, slow finish.
            start_center_x = WIDTH * 0.125
            start_x = int(start_center_x - player.rect.width * 0.5)
            player.rect.x = int(start_x + (player_spawn[0] - start_x) * eased)
            player.rect.y = player_spawn[1]
            player.facing_dir = 1
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
            player.invincible_time_left = 0.0
            player_state.dash_time_left = 0.0
            player_state.ground_pound_active = False
            player_state.bombs.clear()
            player_state.web_projectiles.clear()
            player_state.bomb_trail.clear()
            player_state.floating_texts.clear()

    if not enemy.alive:
        enemy.respawn_timer = max(0.0, enemy.respawn_timer - dt)
        if 0.0 < enemy.respawn_timer <= RESPAWN_ANIM_TIME:
            progress = 1.0 - (enemy.respawn_timer / RESPAWN_ANIM_TIME)
            eased = 1.0 - pow(1.0 - progress, 3.0)  # Ease-out: fast start, slow finish.
            player_start_center_x = WIDTH * 0.125
            player_start_x = int(player_start_center_x - player.rect.width * 0.5)
            travel_distance = player_spawn[0] - player_start_x
            # Mirror player walk-in distance so enemy uses the same pacing feel.
            start_x = int(enemy_spawn[0] + travel_distance)
            enemy.rect.x = int(start_x + (enemy_spawn[0] - start_x) * eased)
            enemy.rect.y = enemy_spawn[1]
            enemy.facing_dir = -1
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
            enemy_ai.knockback_velocity_x = 0.0
            enemy_ai.speed_scale = 1.0
            enemy_ai.stun_time_left = 0.0
            enemy_ai.web_unwrap_blip_time = 0.0
            enemy_ai.poison_ticks_left = 0
            enemy_ai.poison_tick_timer = 0.0
            enemy_ai.path_sample_timer = 0.0
            enemy_ai.path_points.clear()


def handle_input_event(
    event: pygame.event.Event,
    player: Actor,
    enemy: Actor,
    enemy_ai: EnemyAI,
    player_state: PlayerState,
    platforms: list[pygame.Rect],
) -> None:
    rhino_invincible_active = player.special_invincible_duration > 0.0 and player.invincible_time_left > 0.0

    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and player.special_invincible_duration > 0.0:
        if (
            player.alive
            and player.invincible_time_left <= 0.0
            and player.special_charge_hits >= player.special_hits_required
        ):
            player.invincible_time_left = player.special_invincible_duration
            if player.special_hits_required > 0.0:
                player.special_charge_hits = 0.0
        return

    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and player.special_stun_duration > 0.0:
        if player.alive and enemy.alive and player.special_charge_hits >= player.special_hits_required:
            player_state.web_projectiles.append(
                WebProjectile(
                    x=float(player.rect.centerx),
                    y=float(player.rect.centery - 6),
                    life=float(WEB_PROJECTILE_LIFETIME),
                    radius=WEB_PROJECTILE_RADIUS,
                    speed=float(WEB_PROJECTILE_SPEED),
                )
            )
            player.special_charge_hits = 0.0
        return

    if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
        if rhino_invincible_active:
            return
        above_enemy = player.rect.bottom <= enemy.rect.top + 10
        if (
            player.alive
            and enemy.alive
            and not player_state.is_grounded
            and player.ground_pound_charge_hits >= player.ground_pound_hits_required
            and above_enemy
        ):
            player_state.ground_pound_active = True
            player.ground_pound_charge_hits = 0.0
            player_state.dash_time_left = 0.0
            player_state.velocity_y = max(player_state.velocity_y, GROUND_POUND_FALL_SPEED)
        return

    if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
        if rhino_invincible_active:
            return
        if player.alive and _can_jump_from_platform(player.rect, player_state.is_grounded, platforms):
            player_state.velocity_y = JUMP_VELOCITY
            player_state.is_grounded = False
        return

    if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
        if player.alive and player.bomb_charge_hits >= player.bomb_hits_required:
            player.bomb_charge_hits = 0.0
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
        if rhino_invincible_active:
            return
        if player.alive and player_state.dash_time_left <= 0.0 and player_state.dash_cooldown_left <= 0.0:
            keys = pygame.key.get_pressed()
            input_dir = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                input_dir -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                input_dir += 1
            player_state.dash_dir = input_dir if input_dir != 0 else player.facing_dir
            if player_state.dash_dir != 0:
                player_state.dash_time_left = player.dash_duration
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
                enemy.hp = max(0, enemy.hp - player.slash_damage)
                _grant_hit_charges(player, 1.0)
                if player.special_stun_duration > 0.0:
                    enemy_ai.poison_ticks_left = max(enemy_ai.poison_ticks_left, SPIDER_POISON_TOTAL_HITS - 1)
                    enemy_ai.poison_tick_timer = SPIDER_POISON_TICK_INTERVAL
                enemy.hit_flash_time = enemy.hit_flash_duration
                enemy_ai.knockback_velocity_x = float(player.facing_dir * PLAYER_SLASH_KNOCKBACK_SPEED)
                enemy_ai.speed_scale = ENEMY_HIT_SLOW_MIN
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
            player.hp = min(player.max_hp, player.hp + player.heal_amount)
            player_state.heal_cooldown_left = HEAL_COOLDOWN
            splash_y = _find_floor_below(player.rect, platforms)
            player_state.heal_splashes.append(make_heal_splash(float(player.rect.centerx), float(splash_y)))
            _spawn_floating_text(player_state, player.rect, player.hp - old_hp, is_heal=True)


def update_player(
    player: Actor,
    player_state: PlayerState,
    keys: pygame.key.ScancodeWrapper,
    platforms: list[pygame.Rect],
    dt: float,
) -> None:
    if not player.alive:
        return

    if player.special_invincible_duration > 0.0 and player.invincible_time_left > 0.0:
        # Rhino invincibility is a planted stance: no movement while active.
        player_state.dash_time_left = 0.0
        player_state.velocity_y = 0.0
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
        player.rect.x += int(direction * player.move_speed * dt)
    player.rect.x = max(0, min(player.rect.x, WIDTH - player.rect.width))

    previous_bottom = player.rect.bottom
    if player_state.ground_pound_active:
        player_state.velocity_y = max(player_state.velocity_y, GROUND_POUND_FALL_SPEED)
    player_state.velocity_y += GRAVITY * dt
    player.rect.y += int(player_state.velocity_y * dt)
    player_state.is_grounded = False

    landing_platforms = platforms[:1] if player_state.ground_pound_active else platforms
    new_y, new_velocity, grounded = resolve_platform_landing(
        player.rect,
        previous_bottom,
        player_state.velocity_y,
        landing_platforms,
    )
    player.rect.y = new_y
    player_state.velocity_y = new_velocity
    player_state.is_grounded = grounded
    if grounded:
        if player_state.ground_pound_active:
            player_state.ground_spikes.append(make_ground_spike(float(player.rect.centerx), float(player.rect.bottom)))
            player_state.ground_dents.append(make_ground_dent(float(player.rect.centerx), float(player.rect.bottom)))
            player_state.rubble_particles.extend(
                make_rubble_particles(float(player.rect.centerx), float(player.rect.bottom))
            )
        player_state.ground_pound_active = False


def update_enemy(
    enemy: Actor,
    enemy_ai: EnemyAI,
    player: Actor,
    player_state: PlayerState,
    platforms: list[pygame.Rect],
    dt: float,
) -> None:
    if not enemy.alive:
        return

    enemy_ai.web_unwrap_blip_time = max(0.0, enemy_ai.web_unwrap_blip_time - dt)

    if enemy_ai.poison_ticks_left > 0:
        enemy_ai.poison_tick_timer -= dt
        if enemy_ai.poison_tick_timer <= 0.0:
            old_hp = enemy.hp
            enemy.hp = max(0, enemy.hp - 1)
            enemy.hit_flash_time = enemy.hit_flash_duration
            _spawn_floating_text(player_state, enemy.rect, old_hp - enemy.hp, is_heal=False)
            _grant_hit_charges(player, 1.0)
            enemy_ai.poison_ticks_left -= 1
            enemy_ai.poison_tick_timer = SPIDER_POISON_TICK_INTERVAL
            if enemy.hp == 0:
                enemy.alive = False
                enemy.respawn_timer = RESPAWN_DELAY + RESPAWN_ANIM_TIME
                enemy.death_particles = make_dust_particles(enemy.rect)
                enemy.respawn_particles.clear()
                enemy.slash_time_left = 0.0
                enemy_ai.poison_ticks_left = 0
                enemy_ai.poison_tick_timer = 0.0
                return

    prev_stun_time = enemy_ai.stun_time_left
    enemy_ai.stun_time_left = max(0.0, enemy_ai.stun_time_left - dt)
    if prev_stun_time > 0.0 and enemy_ai.stun_time_left <= 0.0:
        enemy_ai.web_unwrap_blip_time = WEB_UNWRAP_BLIP_DURATION
    enemy_ai.speed_scale = min(1.0, enemy_ai.speed_scale + ENEMY_HIT_SLOW_RECOVERY * dt)
    if abs(enemy_ai.knockback_velocity_x) > 0.0:
        enemy.rect.x += int(enemy_ai.knockback_velocity_x * dt)
        if enemy_ai.knockback_velocity_x > 0.0:
            enemy_ai.knockback_velocity_x = max(0.0, enemy_ai.knockback_velocity_x - ENEMY_KNOCKBACK_DECEL * dt)
        else:
            enemy_ai.knockback_velocity_x = min(0.0, enemy_ai.knockback_velocity_x + ENEMY_KNOCKBACK_DECEL * dt)

    if enemy_ai.stun_time_left > 0.0:
        enemy_ai.jump_cooldown_left = max(0.0, enemy_ai.jump_cooldown_left - dt)
    elif player.alive:
        dx = player.rect.centerx - enemy.rect.centerx
        if abs(dx) > 8:
            enemy.facing_dir = 1 if dx > 0 else -1
            enemy.rect.x += int(enemy.facing_dir * ENEMY_CHASE_SPEED * enemy_ai.speed_scale * dt)

        enemy_ai.jump_cooldown_left = max(0.0, enemy_ai.jump_cooldown_left - dt)
        player_is_higher = player.rect.centery + 12 < enemy.rect.centery
        close_enough = abs(dx) < 260
        if enemy_ai.is_grounded and enemy_ai.jump_cooldown_left <= 0.0 and player_is_higher and close_enough:
            enemy_ai.velocity_y = ENEMY_JUMP_VELOCITY
            enemy_ai.is_grounded = False
            enemy_ai.jump_cooldown_left = ENEMY_JUMP_COOLDOWN
    else:
        enemy.rect.x += int(enemy_ai.patrol_dir * ENEMY_SPEED * enemy_ai.speed_scale * dt)
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


def resolve_combat(player: Actor, enemy: Actor, enemy_ai: EnemyAI, player_state: PlayerState) -> None:
    if not (player.alive and enemy.alive):
        return

    if player_state.ground_pound_active and player.rect.colliderect(enemy.rect):
        old_hp = enemy.hp
        enemy.hp = max(0, enemy.hp - player.ground_pound_damage)
        enemy.hit_flash_time = enemy.hit_flash_duration
        _spawn_floating_text(player_state, enemy.rect, old_hp - enemy.hp, is_heal=False)
        player_state.shake_time_left = SCREEN_SHAKE_DURATION
        player_state.ground_pound_active = False
        player_state.velocity_y = -220.0
        if enemy.hp == 0:
            enemy.alive = False
            enemy.respawn_timer = RESPAWN_DELAY + RESPAWN_ANIM_TIME
            enemy.death_particles = make_dust_particles(enemy.rect)
            enemy.respawn_particles.clear()
            enemy.slash_time_left = 0.0
        return

    dx = player.rect.centerx - enemy.rect.centerx
    in_attack_x = abs(dx) <= (SLASH_RANGE_X + 10)
    in_attack_y = abs(player.rect.centery - enemy.rect.centery) <= 70
    if enemy_ai.stun_time_left <= 0.0 and in_attack_x and in_attack_y and enemy.slash_cooldown_left <= 0.0:
        enemy_slash_rect = build_slash_rect(enemy.rect, enemy.facing_dir)
        enemy.slash_time_left = SLASH_ACTIVE_TIME
        enemy.slash_cooldown_left = ENEMY_SLASH_COOLDOWN

        if enemy_slash_rect.colliderect(player.rect):
            if player.invincible_time_left > 0.0:
                return
            old_hp = player.hp
            player.hp = max(0, player.hp - 1)
            player.hit_flash_time = player.hit_flash_duration
            _spawn_floating_text(player_state, player.rect, old_hp - player.hp, is_heal=False)
            if player.hp == 0:
                player.alive = False
                player.respawn_timer = RESPAWN_DELAY + RESPAWN_ANIM_TIME
                player.death_particles = make_dust_particles(player.rect)
                player.respawn_particles.clear()
                player.slash_time_left = 0.0
                player_state.dash_time_left = 0.0
                player_state.ground_pound_active = False
                player_state.bombs.clear()
                player_state.bomb_trail.clear()
                player_state.floating_texts.clear()
            player_state.heal_splashes.clear()


# Internal helpers

def _find_floor_below(rect: pygame.Rect, platforms: list[pygame.Rect]) -> int:
    floor_y = HEIGHT - 4
    for platform in platforms:
        overlaps_x = rect.right > platform.left and rect.left < platform.right
        is_below = platform.top >= rect.bottom
        if overlaps_x and is_below:
            floor_y = min(floor_y, platform.top)
    return floor_y


def _is_on_floating_platform(rect: pygame.Rect, platforms: list[pygame.Rect]) -> bool:
    if len(platforms) <= 1:
        return False
    feet_y = rect.bottom
    for platform in platforms[1:]:
        touches_top = abs(feet_y - platform.top) <= 2
        overlaps_x = rect.right > platform.left and rect.left < platform.right
        if touches_top and overlaps_x:
            return True
    return False


def _can_jump_from_platform(rect: pygame.Rect, grounded: bool, platforms: list[pygame.Rect]) -> bool:
    if grounded:
        return True
    feet_y = rect.bottom
    for platform in platforms:
        touches_top = abs(feet_y - platform.top) <= 3
        overlaps_x = rect.right > platform.left and rect.left < platform.right
        if touches_top and overlaps_x:
            return True
    return False


def _update_bombs(player: Actor, enemy: Actor, enemy_ai: EnemyAI, player_state: PlayerState, dt: float) -> None:
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
                enemy.hp = max(0, enemy.hp - player.bomb_damage)
                enemy.hit_flash_time = enemy.hit_flash_duration
                knockback_dir = 1 if enemy.rect.centerx >= bomb.x else -1
                enemy_ai.knockback_velocity_x = float(knockback_dir * BOMB_KNOCKBACK_SPEED)
                enemy_ai.speed_scale = ENEMY_HIT_SLOW_MIN
                player_state.mushroom_clouds.append(make_mushroom_cloud(float(enemy.rect.centerx), float(enemy.rect.bottom)))
                player_state.shake_time_left = SCREEN_SHAKE_DURATION
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


def _update_web_projectiles(
    player: Actor,
    enemy: Actor,
    enemy_ai: EnemyAI,
    player_state: PlayerState,
    dt: float,
) -> None:
    active_projectiles: list[WebProjectile] = []
    for web in player_state.web_projectiles:
        web.life -= dt
        if web.life <= 0.0:
            continue

        if enemy.alive:
            dx = enemy.rect.centerx - web.x
            dy = enemy.rect.centery - web.y
            distance = math.hypot(dx, dy)
            if distance > 0:
                step = web.speed * dt
                if distance <= step:
                    web.x = float(enemy.rect.centerx)
                    web.y = float(enemy.rect.centery)
                else:
                    web.x += (dx / distance) * step
                    web.y += (dy / distance) * step
        else:
            web.y -= web.speed * dt * 0.35

        if web.x < -30 or web.x > WIDTH + 30 or web.y < -30 or web.y > HEIGHT + 30:
            continue

        if enemy.alive:
            radius = WEB_PROJECTILE_HITBOX_RADIUS
            hitbox = pygame.Rect(int(web.x - radius), int(web.y - radius), radius * 2, radius * 2)
            if hitbox.colliderect(enemy.rect):
                enemy_ai.stun_time_left = max(enemy_ai.stun_time_left, player.special_stun_duration)
                enemy_ai.web_unwrap_blip_time = 0.0
                enemy_ai.knockback_velocity_x = 0.0
                enemy_ai.speed_scale = 0.0
                enemy.hit_flash_time = enemy.hit_flash_duration
                _spawn_status_text(player_state, enemy.rect, "STUNNED", (255, 235, 120))
                continue

        active_projectiles.append(web)
    player_state.web_projectiles = active_projectiles


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


def _spawn_status_text(
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


def _grant_hit_charges(player: Actor, amount: float) -> None:
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
