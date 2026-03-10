import pygame

from .config import RESPAWN_ANIM_TIME, WIDTH
from .models import Actor, EnemyAI, PlayerState


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
            eased = 1.0 - pow(1.0 - progress, 3.0)
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
            player.special_counter_active = False
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
            eased = 1.0 - pow(1.0 - progress, 3.0)
            player_start_center_x = WIDTH * 0.125
            player_start_x = int(player_start_center_x - player.rect.width * 0.5)
            travel_distance = player_spawn[0] - player_start_x
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
            enemy_ai.bomb_cooldown_left = 0.0
