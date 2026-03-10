import math

import pygame

from .config import (
    BOMB_GRAVITY,
    BOMB_HITBOX_RADIUS,
    BOMB_KNOCKBACK_SPEED,
    BOMB_TRAIL_SPAWN_INTERVAL,
    ENEMY_HIT_SLOW_MIN,
    RESPAWN_ANIM_TIME,
    RESPAWN_DELAY,
    SCREEN_SHAKE_DURATION,
    WEB_PROJECTILE_HITBOX_RADIUS,
    WIDTH,
    HEIGHT,
)
from .effects import (
    make_dust_particles,
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
from .gameplay_common import spawn_status_text, spawn_floating_text
from .models import Actor, Bomb, EnemyAI, FloatingText, PlayerState, WebProjectile


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


def _update_bombs(player: Actor, enemy: Actor, enemy_ai: EnemyAI, player_state: PlayerState, dt: float) -> None:
    active_bombs: list[Bomb] = []
    for bomb in player_state.bombs:
        target = player if bomb.owner_is_enemy else enemy
        bomb.life -= dt
        if bomb.homing and target.alive:
            dx = target.rect.centerx - bomb.x
            dy = target.rect.centery - bomb.y
            distance = math.hypot(dx, dy)
            if distance > 0:
                step = bomb.homing_speed * dt
                if distance <= step:
                    bomb.x = float(target.rect.centerx)
                    bomb.y = float(target.rect.centery)
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

        if bomb.owner_is_enemy and player.alive:
            radius = BOMB_HITBOX_RADIUS
            bomb_rect = pygame.Rect(int(bomb.x - radius), int(bomb.y - radius), radius * 2, radius * 2)
            if bomb_rect.colliderect(player.rect):
                if player.special_counter_active:
                    player.special_counter_active = False
                    # Turn the same bomb around so it visibly travels back to the enemy.
                    bomb.owner_is_enemy = False
                    bomb.homing = True
                    bomb.homing_speed = max(bomb.homing_speed, 1300.0)
                    bomb.life = max(bomb.life, 0.55)
                    bomb.trail_timer = 0.0
                    dx = enemy.rect.centerx - player.rect.centerx
                    dy = enemy.rect.centery - player.rect.centery
                    distance = math.hypot(dx, dy)
                    if distance > 0.0:
                        launch_offset = float(player.rect.width * 0.6 + bomb.radius + 4)
                        bomb.x = float(player.rect.centerx + (dx / distance) * launch_offset)
                        bomb.y = float(player.rect.centery + (dy / distance) * launch_offset)
                    else:
                        bomb.x = float(player.rect.centerx + player.facing_dir * (bomb.radius + 20))
                        bomb.y = float(player.rect.centery)
                    active_bombs.append(bomb)
                    continue
                if player.invincible_time_left > 0.0:
                    continue
                old_hp = player.hp
                player.hp = max(0, player.hp - enemy.bomb_damage)
                player.hit_flash_time = player.hit_flash_duration
                player_state.mushroom_clouds.append(make_mushroom_cloud(float(player.rect.centerx), float(player.rect.bottom)))
                player_state.shake_time_left = SCREEN_SHAKE_DURATION
                spawn_floating_text(player_state, player.rect, old_hp - player.hp, is_heal=False)
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
                continue

        if not bomb.owner_is_enemy and enemy.alive:
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
                spawn_floating_text(player_state, enemy.rect, old_hp - enemy.hp, is_heal=False)
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
                spawn_status_text(player_state, enemy.rect, "STUNNED", (255, 235, 120))
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
