from .combat import build_slash_rect
from .config import ENEMY_SLASH_COOLDOWN, RESPAWN_ANIM_TIME, RESPAWN_DELAY, SCREEN_SHAKE_DURATION, SLASH_ACTIVE_TIME, SLASH_RANGE_X
from .effects import make_dust_particles
from .gameplay_common import spawn_floating_text
from .models import Actor, EnemyAI, PlayerState


def resolve_combat(player: Actor, enemy: Actor, enemy_ai: EnemyAI, player_state: PlayerState) -> None:
    if not (player.alive and enemy.alive):
        return

    if player_state.ground_pound_active and player.rect.colliderect(enemy.rect):
        old_hp = enemy.hp
        enemy.hp = max(0, enemy.hp - player.ground_pound_damage)
        enemy.hit_flash_time = enemy.hit_flash_duration
        spawn_floating_text(player_state, enemy.rect, old_hp - enemy.hp, is_heal=False)
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
            if player.special_counter_active:
                player.special_counter_active = False
                old_enemy_hp = enemy.hp
                enemy.hp = max(0, enemy.hp - 1)
                enemy.hit_flash_time = enemy.hit_flash_duration
                spawn_floating_text(player_state, enemy.rect, old_enemy_hp - enemy.hp, is_heal=False)
                if enemy.hp == 0:
                    enemy.alive = False
                    enemy.respawn_timer = RESPAWN_DELAY + RESPAWN_ANIM_TIME
                    enemy.death_particles = make_dust_particles(enemy.rect)
                    enemy.respawn_particles.clear()
                    enemy.slash_time_left = 0.0
                return
            if player.invincible_time_left > 0.0:
                return
            old_hp = player.hp
            player.hp = max(0, player.hp - 1)
            player.hit_flash_time = player.hit_flash_duration
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
            player_state.heal_splashes.clear()
