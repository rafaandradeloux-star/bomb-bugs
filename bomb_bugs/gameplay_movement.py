import pygame

from .config import (
    BOMB_LIFETIME,
    BOMB_RADIUS,
    BOMB_RECOIL_DISTANCE,
    BOMB_SPEED_X,
    BOMB_SPEED_Y,
    DASH_SPEED,
    ENEMY_CHASE_SPEED,
    ENEMY_BOMB_COOLDOWN,
    ENEMY_BOMB_HOMING_SPEED,
    ENEMY_HIT_SLOW_RECOVERY,
    ENEMY_JUMP_COOLDOWN,
    ENEMY_JUMP_VELOCITY,
    ENEMY_KNOCKBACK_DECEL,
    ENEMY_SPEED,
    GRAVITY,
    GROUND_POUND_FALL_SPEED,
    RESPAWN_ANIM_TIME,
    RESPAWN_DELAY,
    SPIDER_POISON_TICK_INTERVAL,
    TRAIL_SPAWN_INTERVAL,
    WEB_UNWRAP_BLIP_DURATION,
    WIDTH,
)
from .effects import make_dust_particles, make_ground_dent, make_ground_spike, make_rubble_particles, make_trail_particle
from .gameplay_common import grant_hit_charges, spawn_floating_text
from .models import Actor, Bomb, EnemyAI, PlayerState
from .world import resolve_platform_landing


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
    enemy_ai.bomb_cooldown_left = max(0.0, enemy_ai.bomb_cooldown_left - dt)

    if enemy_ai.poison_ticks_left > 0:
        enemy_ai.poison_tick_timer -= dt
        if enemy_ai.poison_tick_timer <= 0.0:
            old_hp = enemy.hp
            enemy.hp = max(0, enemy.hp - 1)
            enemy.hit_flash_time = enemy.hit_flash_duration
            spawn_floating_text(player_state, enemy.rect, old_hp - enemy.hp, is_heal=False)
            grant_hit_charges(player, 1.0)
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
        if enemy_ai.bomb_cooldown_left <= 0.0 and abs(dx) <= 460:
            enemy.facing_dir = 1 if dx > 0 else -1
            player_state.bombs.append(
                Bomb(
                    x=float(enemy.rect.centerx + enemy.facing_dir * 18),
                    y=float(enemy.rect.centery - 12),
                    vx=float(enemy.facing_dir * BOMB_SPEED_X),
                    vy=float(BOMB_SPEED_Y),
                    life=float(BOMB_LIFETIME),
                    radius=BOMB_RADIUS,
                    trail_timer=0.0,
                    homing_speed=ENEMY_BOMB_HOMING_SPEED,
                    owner_is_enemy=True,
                )
            )
            enemy.rect.x -= int(enemy.facing_dir * BOMB_RECOIL_DISTANCE)
            enemy.rect.x = max(0, min(enemy.rect.x, WIDTH - enemy.rect.width))
            enemy_ai.bomb_cooldown_left = ENEMY_BOMB_COOLDOWN

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
