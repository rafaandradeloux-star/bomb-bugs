import pygame

from .combat import build_slash_rect
from .config import (
    BOMB_LIFETIME,
    BOMB_RECOIL_DISTANCE,
    BOMB_RADIUS,
    BOMB_SPEED_X,
    BOMB_SPEED_Y,
    DASH_COOLDOWN,
    ENEMY_HIT_SLOW_MIN,
    GROUND_POUND_FALL_SPEED,
    HEAL_COOLDOWN,
    JUMP_VELOCITY,
    PLAYER_SLASH_COOLDOWN,
    PLAYER_SLASH_KNOCKBACK_SPEED,
    RESPAWN_ANIM_TIME,
    RESPAWN_DELAY,
    SLASH_ACTIVE_TIME,
    SPIDER_POISON_TICK_INTERVAL,
    SPIDER_POISON_TOTAL_HITS,
    WIDTH,
    WEB_PROJECTILE_LIFETIME,
    WEB_PROJECTILE_RADIUS,
    WEB_PROJECTILE_SPEED,
)
from .effects import make_dust_particles, make_heal_splash
from .gameplay_common import can_jump_from_platform, find_floor_below, grant_hit_charges, spawn_floating_text
from .models import Actor, Bomb, EnemyAI, PlayerState, WebProjectile


def handle_input_event(
    event: pygame.event.Event,
    player: Actor,
    enemy: Actor,
    enemy_ai: EnemyAI,
    player_state: PlayerState,
    platforms: list[pygame.Rect],
) -> None:
    rhino_invincible_active = player.special_invincible_duration > 0.0 and player.invincible_time_left > 0.0

    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and player.special_counter_enabled:
        if (
            player.alive
            and not player.special_counter_active
            and player.special_charge_hits >= player.special_hits_required
        ):
            player.special_counter_active = True
            if player.special_hits_required > 0.0:
                player.special_charge_hits = 0.0
        return

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
        if player.alive and can_jump_from_platform(player.rect, player_state.is_grounded, platforms):
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
            # Bomb recoil pushes the player opposite their throw direction.
            player.rect.x -= int(player.facing_dir * BOMB_RECOIL_DISTANCE)
            player.rect.x = max(0, min(player.rect.x, WIDTH - player.rect.width))
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
                grant_hit_charges(player, 1.0)
                if player.special_stun_duration > 0.0:
                    enemy_ai.poison_ticks_left = max(enemy_ai.poison_ticks_left, SPIDER_POISON_TOTAL_HITS - 1)
                    enemy_ai.poison_tick_timer = SPIDER_POISON_TICK_INTERVAL
                enemy.hit_flash_time = enemy.hit_flash_duration
                enemy_ai.knockback_velocity_x = float(player.facing_dir * PLAYER_SLASH_KNOCKBACK_SPEED)
                enemy_ai.speed_scale = ENEMY_HIT_SLOW_MIN
                spawn_floating_text(player_state, enemy.rect, old_hp - enemy.hp, is_heal=False)
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
            splash_y = find_floor_below(player.rect, platforms)
            player_state.heal_splashes.append(make_heal_splash(float(player.rect.centerx), float(splash_y)))
            spawn_floating_text(player_state, player.rect, player.hp - old_hp, is_heal=True)
