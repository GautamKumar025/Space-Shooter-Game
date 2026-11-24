import arcade
import math
import random
import os

# ============================================================
# GAME SETTINGS
# ============================================================

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Space Shooter - Neon Boss Edition"

# Player
PLAYER_SPEED = 5.5
PLAYER_RADIUS = 20
PLAYER_MAX_HEALTH = 100

# Player bullets
BULLET_SPEED = 13
BULLET_RADIUS = 4
NORMAL_SHOOT_COOLDOWN = 0.18
RAPID_SHOOT_COOLDOWN = 0.07

# Enemy
NORMAL_ENEMY_RADIUS = 18
NORMAL_ENEMY_MIN_SPEED = 1.2
NORMAL_ENEMY_MAX_SPEED = 3.0

SHOOTER_ENEMY_RADIUS = 22
SHOOTER_ENEMY_MIN_SPEED = 0.8
SHOOTER_ENEMY_MAX_SPEED = 1.6

ENEMY_SPAWN_RATE = 0.85

# Enemy bullets
ENEMY_BULLET_SPEED = 5.5
ENEMY_BULLET_RADIUS = 5
ENEMY_SHOOT_COOLDOWN = 1.5

# Boss
BOSS_RADIUS = 65
BOSS_MAX_HEALTH = 600
BOSS_SPEED = 1.5
BOSS_BULLET_SPEED = 4.5

# Power-ups
POWERUP_RADIUS = 14
POWERUP_SPEED = 2.2
RAPID_FIRE_DURATION = 8.0
SHIELD_DURATION = 7.0
TRIPLE_SHOT_DURATION = 8.0

# Stars
STAR_COUNT = 180
STAR_SPEED_MIN = 0.4
STAR_SPEED_MAX = 3.2


# ============================================================
# ASSET DIRECTORY & SAFE LOADING
# ============================================================

ASSET_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets"
)
BACKGROUND_PATH = os.path.join(ASSET_DIR, "background.png")


def load_background_texture():
    """Load the space backdrop safely without crashing if missing."""
    if not os.path.exists(BACKGROUND_PATH):
        return None
    try:
        return arcade.load_texture(BACKGROUND_PATH)
    except Exception:
        return None


BACKGROUND_IMAGE = load_background_texture()


# ============================================================
# SOUND MANAGER
# ============================================================

class SoundManager:
    def __init__(self):
        self.shoot = self.load("shoot.w.mp3")
        self.enemy_shoot = self.load("enemy_shoot.mp3")
        self.explosion = self.load("explosion.wav")
        self.hit = self.load("hit.wav")
        self.powerup = self.load("powerup.wav")
        self.boss = self.load("boss.wav")
        self.music = self.load("background_music.mp3")
        self.music_player = None

    def load(self, filename):
        path = os.path.join(ASSET_DIR, filename)
        if not os.path.exists(path):
            return None
        try:
            return arcade.load_sound(path)
        except Exception:
            return None

    def play(self, sound, volume=1.0):
        if sound is None:
            return
        try:
            arcade.play_sound(sound, volume=volume)
        except Exception:
            pass

    def play_music(self):
        if self.music is None:
            return
        try:
            self.music_player = arcade.play_sound(
                self.music, volume=0.25, loop=True
            )
        except Exception:
            pass


# ============================================================
# STAR (PARALLAX DEPTH)
# ============================================================

class Star:
    def __init__(self):
        self.x = random.uniform(0, SCREEN_WIDTH)
        self.y = random.uniform(0, SCREEN_HEIGHT)
        self.speed = random.uniform(STAR_SPEED_MIN, STAR_SPEED_MAX)
        self.radius = 1 if self.speed < 2.0 else 2
        self.brightness = int(100 + (self.speed / STAR_SPEED_MAX) * 155)
        self.tint = random.choice([
            (self.brightness, self.brightness, self.brightness),
            (int(self.brightness * 0.8), int(self.brightness * 0.9), self.brightness),
            (self.brightness, int(self.brightness * 0.85), int(self.brightness * 0.7)),
        ])

    def update(self):
        self.y -= self.speed
        if self.y < 0:
            self.y = SCREEN_HEIGHT
            self.x = random.uniform(0, SCREEN_WIDTH)

    def draw(self):
        arcade.draw_circle_filled(self.x, self.y, self.radius, self.tint)


# ============================================================
# PARTICLE & FLOATING TEXT EFFECTS
# ============================================================

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 6.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.25, 0.65)
        self.max_life = self.life
        self.radius = random.uniform(2, 4.5)
        self.color = color

    def update(self, delta_time):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= delta_time

    def draw(self):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        r, g, b = self.color[:3]
        arcade.draw_circle_filled(
            self.x, self.y, self.radius * (self.life / self.max_life), (r, g, b, alpha)
        )

    def finished(self):
        return self.life <= 0


class FloatingText:
    def __init__(self, x, y, text, color=arcade.color.YELLOW):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 0.8

    def update(self, delta_time):
        self.y += 35 * delta_time
        self.life -= delta_time

    def draw(self):
        if self.life <= 0:
            return
        arcade.draw_text(
            self.text,
            self.x,
            self.y,
            self.color,
            13,
            bold=True,
            anchor_x="center"
        )

    def finished(self):
        return self.life <= 0


# ============================================================
# PLAYER BULLET (NEON LASER)
# ============================================================

class PlayerBullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = BULLET_SPEED
        self.radius = BULLET_RADIUS

    def update(self):
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed

    def draw(self):
        rad = math.radians(self.angle)
        tail_x = self.x - math.cos(rad) * 14
        tail_y = self.y - math.sin(rad) * 14

        # Outer glow
        arcade.draw_line(
            tail_x, tail_y, self.x, self.y, (0, 255, 255, 110), 6
        )
        # Inner bright core
        arcade.draw_line(
            tail_x, tail_y, self.x, self.y, arcade.color.WHITE, 2.5
        )
        arcade.draw_circle_filled(self.x, self.y, self.radius, arcade.color.CYAN)

    def off_screen(self):
        return (
            self.x < -30
            or self.x > SCREEN_WIDTH + 30
            or self.y < -30
            or self.y > SCREEN_HEIGHT + 30
        )


# ============================================================
# ENEMY BULLET
# ============================================================

class EnemyBullet:
    def __init__(self, x, y, angle, speed=ENEMY_BULLET_SPEED):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.radius = ENEMY_BULLET_RADIUS

    def update(self):
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed

    def draw(self):
        arcade.draw_circle_filled(
            self.x, self.y, self.radius + 3, (255, 60, 0, 90)
        )
        arcade.draw_circle_filled(
            self.x, self.y, self.radius, arcade.color.ORANGE_RED
        )
        arcade.draw_circle_filled(
            self.x, self.y, 2, arcade.color.YELLOW
        )

    def off_screen(self):
        return (
            self.x < -30
            or self.x > SCREEN_WIDTH + 30
            or self.y < -30
            or self.y > SCREEN_HEIGHT + 30
        )


# ============================================================
# EXPLOSION RING
# ============================================================

class Explosion:
    def __init__(self, x, y, size=35):
        self.x = x
        self.y = y
        self.radius = 5
        self.max_radius = size
        self.life = 0.40
        self.max_life = 0.40

    def update(self, delta_time):
        self.life -= delta_time
        self.radius += self.max_radius * 2.5 * delta_time

    def draw(self):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        arcade.draw_circle_outline(
            self.x, self.y, self.radius, (255, 165, 0, alpha), 3
        )
        arcade.draw_circle_filled(
            self.x, self.y, max(1, self.radius / 3), (255, 255, 100, alpha)
        )

    def finished(self):
        return self.life <= 0


# ============================================================
# NORMAL ENEMY
# ============================================================

class NormalEnemy:
    def __init__(self, speed_bonus=0):
        self.x, self.y = spawn_position()
        self.speed = (
            random.uniform(NORMAL_ENEMY_MIN_SPEED, NORMAL_ENEMY_MAX_SPEED)
            + speed_bonus
        )
        self.radius = NORMAL_ENEMY_RADIUS
        self.angle = 0
        self.health = 30
        self.hit_flash = 0

    def update(self, player_x, player_y, delta_time=0.016):
        dx = player_x - self.x
        dy = player_y - self.y
        self.angle = math.degrees(math.atan2(dy, dx))

        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed

        if self.hit_flash > 0:
            self.hit_flash -= delta_time

    def draw(self):
        color = arcade.color.WHITE if self.hit_flash > 0 else arcade.color.CRIMSON
        draw_enemy_ship(self.x, self.y, self.radius, self.angle, color, arcade.color.ORANGE)


# ============================================================
# SHOOTER ENEMY
# ============================================================

class ShooterEnemy:
    def __init__(self, speed_bonus=0):
        self.x, self.y = spawn_position()
        self.speed = (
            random.uniform(SHOOTER_ENEMY_MIN_SPEED, SHOOTER_ENEMY_MAX_SPEED)
            + speed_bonus
        )
        self.radius = SHOOTER_ENEMY_RADIUS
        self.angle = 0
        self.health = 60
        self.hit_flash = 0
        self.shoot_timer = random.uniform(0.6, ENEMY_SHOOT_COOLDOWN)

    def update(self, player_x, player_y, delta_time):
        dx = player_x - self.x
        dy = player_y - self.y
        self.angle = math.degrees(math.atan2(dy, dx))

        # Keep a tactical distance instead of crashing immediately
        dist = math.hypot(dx, dy)
        if dist > 220:
            rad = math.radians(self.angle)
            self.x += math.cos(rad) * self.speed
            self.y += math.sin(rad) * self.speed

        if self.hit_flash > 0:
            self.hit_flash -= delta_time

        self.shoot_timer -= delta_time
        if self.shoot_timer <= 0:
            self.shoot_timer = ENEMY_SHOOT_COOLDOWN
            return True
        return False

    def draw(self):
        color = arcade.color.WHITE if self.hit_flash > 0 else arcade.color.ELECTRIC_PURPLE
        draw_enemy_ship(self.x, self.y, self.radius, self.angle, color, arcade.color.MAGENTA)


# ============================================================
# POWER-UP
# ============================================================

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.power_type = power_type
        self.radius = POWERUP_RADIUS
        self.speed = POWERUP_SPEED
        self.pulse = 0

    def update(self, delta_time=0.016):
        self.y -= self.speed
        self.pulse += delta_time * 6

    def draw(self):
        if self.power_type == "rapid":
            color = arcade.color.GOLD
            letter = "R"
        elif self.power_type == "shield":
            color = arcade.color.CYAN
            letter = "S"
        elif self.power_type == "triple":
            color = arcade.color.ORANGE
            letter = "T"
        else:
            color = arcade.color.LIME_GREEN
            letter = "H"

        glow_r = self.radius + 4 + math.sin(self.pulse) * 2
        r, g, b = color[:3]
        arcade.draw_circle_outline(self.x, self.y, glow_r, (r, g, b, 150), 2)
        arcade.draw_circle_filled(self.x, self.y, self.radius, color)
        arcade.draw_text(
            letter,
            self.x,
            self.y - 6,
            arcade.color.BLACK,
            12,
            bold=True,
            anchor_x="center"
        )

    def off_screen(self):
        return self.y < -30


# ============================================================
# BOSS
# ============================================================

class Boss:
    def __init__(self, level=5):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT + 100
        self.radius = BOSS_RADIUS
        scale = 1 + (level // 5 - 1) * 0.4
        self.health = int(BOSS_MAX_HEALTH * scale)
        self.max_health = self.health
        self.angle = -90
        self.shoot_timer = 1.0
        self.direction = 1
        self.hit_flash = 0
        self.attack_pattern = 0

    def update(self, player_x, player_y, delta_time):
        if self.y > SCREEN_HEIGHT - 125:
            self.y -= BOSS_SPEED

        self.x += self.direction * (BOSS_SPEED * 1.4)
        if self.x > SCREEN_WIDTH - self.radius - 30:
            self.direction = -1
        if self.x < self.radius + 30:
            self.direction = 1

        dx = player_x - self.x
        dy = player_y - self.y
        self.angle = math.degrees(math.atan2(dy, dx))

        if self.hit_flash > 0:
            self.hit_flash -= delta_time

        self.shoot_timer -= delta_time
        if self.shoot_timer <= 0:
            self.shoot_timer = 0.85
            self.attack_pattern = (self.attack_pattern + 1) % 2
            return True
        return False

    def draw(self):
        body_color = arcade.color.WHITE if self.hit_flash > 0 else arcade.color.DARK_RED

        # Outer aura
        arcade.draw_circle_outline(
            self.x, self.y, self.radius + 8, (255, 40, 40, 100), 3
        )

        # Wings
        arcade.draw_triangle_filled(
            self.x - 50, self.y + 10,
            self.x - 105, self.y - 35,
            self.x - 65, self.y + 35,
            arcade.color.CRIMSON
        )
        arcade.draw_triangle_filled(
            self.x + 50, self.y + 10,
            self.x + 105, self.y - 35,
            self.x + 65, self.y + 35,
            arcade.color.CRIMSON
        )

        # Main hull
        arcade.draw_circle_filled(self.x, self.y, self.radius, body_color)
        arcade.draw_circle_outline(self.x, self.y, self.radius, arcade.color.ORANGE_RED, 3)

        # Glowing core
        arcade.draw_circle_filled(self.x, self.y, 28, arcade.color.ORANGE_RED)
        arcade.draw_circle_filled(self.x, self.y, 12, arcade.color.YELLOW)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def spawn_position():
    side = random.choice(["top", "top", "right", "left"])
    if side == "top":
        return random.uniform(30, SCREEN_WIDTH - 30), SCREEN_HEIGHT + 30
    if side == "right":
        return SCREEN_WIDTH + 30, random.uniform(SCREEN_HEIGHT * 0.4, SCREEN_HEIGHT)
    return -30, random.uniform(SCREEN_HEIGHT * 0.4, SCREEN_HEIGHT)


def draw_enemy_ship(x, y, radius, angle, color, core_color):
    rad = math.radians(angle)
    front_x = x + math.cos(rad) * (radius * 1.4)
    front_y = y + math.sin(rad) * (radius * 1.4)

    left_rad = math.radians(angle + 140)
    left_x = x + math.cos(left_rad) * radius
    left_y = y + math.sin(left_rad) * radius

    right_rad = math.radians(angle - 140)
    right_x = x + math.cos(right_rad) * radius
    right_y = y + math.sin(right_rad) * radius

    arcade.draw_triangle_filled(
        front_x, front_y, left_x, left_y, right_x, right_y, color
    )
    arcade.draw_circle_filled(x, y, radius * 0.35, core_color)


def distance_between(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)


# ============================================================
# GAME WINDOW
# ============================================================

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color((6, 8, 20))

        self.stars = [Star() for _ in range(STAR_COUNT)]
        self.sounds = SoundManager()
        self.sounds.play_music()

        self.init_game_state()

    def init_game_state(self):
        self.player_x = SCREEN_WIDTH / 2
        self.player_y = 120
        self.player_angle = 90

        self.bullets = []
        self.enemy_bullets = []
        self.normal_enemies = []
        self.shooter_enemies = []
        self.explosions = []
        self.particles = []
        self.floating_texts = []
        self.powerups = []

        self.score = 0
        self.high_score = getattr(self, "high_score", 0)
        self.health = PLAYER_MAX_HEALTH
        self.level = 1
        self.game_over = False
        self.paused = False

        self.combo = 0
        self.combo_timer = 0

        self.boss = None
        self.boss_spawned_for_level = 0

        self.shoot_timer = 0
        self.enemy_spawn_timer = 0
        self.level_timer = 0
        self.powerup_timer = 0

        self.rapid_fire_timer = 0
        self.shield_timer = 0
        self.triple_shot_timer = 0

        self.shake_timer = 0
        self.shake_intensity = 0

        self.auto_fire = False
        self.keys_pressed = set()

    # ========================================================
    # DRAW
    # ========================================================

    def on_draw(self):
        self.clear()

        # Screen shake offset
        shake_x = 0
        shake_y = 0
        if self.shake_timer > 0:
            shake_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            shake_y = random.uniform(-self.shake_intensity, self.shake_intensity)

        self.draw_background(shake_x, shake_y)

        for powerup in self.powerups:
            powerup.draw()

        for bullet in self.bullets:
            bullet.draw()

        for bullet in self.enemy_bullets:
            bullet.draw()

        for enemy in self.normal_enemies:
            enemy.draw()

        for enemy in self.shooter_enemies:
            enemy.draw()

        if self.boss:
            self.boss.draw()
            self.draw_boss_health()

        for particle in self.particles:
            particle.draw()

        for explosion in self.explosions:
            explosion.draw()

        if not self.game_over:
            self.draw_player()

        for ft in self.floating_texts:
            ft.draw()

        self.draw_hud()

        if self.paused and not self.game_over:
            self.draw_pause_overlay()

        if self.game_over:
            self.draw_game_over()

    def draw_background(self, shake_x=0, shake_y=0):
        if BACKGROUND_IMAGE is not None:
            if hasattr(arcade, "draw_texture_rect"):
                arcade.draw_texture_rect(
                    BACKGROUND_IMAGE,
                    arcade.LBWH(shake_x, shake_y, SCREEN_WIDTH, SCREEN_HEIGHT)
                )
            else:
                arcade.draw_lrwh_rectangle_textured(
                    shake_x, shake_y, SCREEN_WIDTH, SCREEN_HEIGHT, BACKGROUND_IMAGE
                )
        else:
            # Deep space nebula glow circles
            arcade.draw_circle_filled(740 + shake_x, 490 + shake_y, 130, (25, 12, 55, 140))
            arcade.draw_circle_filled(160 + shake_x, 150 + shake_y, 160, (10, 30, 65, 140))

        for star in self.stars:
            star.draw()

    def draw_player(self):
        rad = math.radians(self.player_angle)

        # Energy Shield
        if self.shield_timer > 0:
            pulse = math.sin(self.shield_timer * 10) * 2
            arcade.draw_circle_filled(
                self.player_x, self.player_y, PLAYER_RADIUS + 12, (0, 255, 255, 35)
            )
            arcade.draw_circle_outline(
                self.player_x,
                self.player_y,
                PLAYER_RADIUS + 12 + pulse,
                arcade.color.CYAN,
                2.5
            )

        # Animated Thruster Flame
        back_rad = math.radians(self.player_angle + 180)
        flame_len = random.uniform(18, 28)
        flame_x = self.player_x + math.cos(back_rad) * flame_len
        flame_y = self.player_y + math.sin(back_rad) * flame_len

        arcade.draw_circle_filled(
            self.player_x + math.cos(back_rad) * 14,
            self.player_y + math.sin(back_rad) * 14,
            7,
            arcade.color.ORANGE_RED
        )
        arcade.draw_circle_filled(flame_x, flame_y, 4, arcade.color.YELLOW)

        # Ship Hull Vertices
        front_x = self.player_x + math.cos(rad) * (PLAYER_RADIUS * 1.45)
        front_y = self.player_y + math.sin(rad) * (PLAYER_RADIUS * 1.45)

        left_rad = math.radians(self.player_angle + 145)
        left_x = self.player_x + math.cos(left_rad) * (PLAYER_RADIUS * 1.1)
        left_y = self.player_y + math.sin(left_rad) * (PLAYER_RADIUS * 1.1)

        right_rad = math.radians(self.player_angle - 145)
        right_x = self.player_x + math.cos(right_rad) * (PLAYER_RADIUS * 1.1)
        right_y = self.player_y + math.sin(right_rad) * (PLAYER_RADIUS * 1.1)

        # Outer Neon Trim
        arcade.draw_triangle_filled(
            front_x, front_y, left_x, left_y, right_x, right_y, arcade.color.WHITE
        )
        arcade.draw_triangle_outline(
            front_x, front_y, left_x, left_y, right_x, right_y, arcade.color.CYAN, 2
        )

        # Glowing Cockpit
        cockpit_x = self.player_x + math.cos(rad) * 4
        cockpit_y = self.player_y + math.sin(rad) * 4
        arcade.draw_circle_filled(cockpit_x, cockpit_y, 5, arcade.color.DEEP_SKY_BLUE)

    def draw_hud(self):
        # Score & High Score
        arcade.draw_text(
            f"SCORE: {self.score}",
            20, SCREEN_HEIGHT - 35, arcade.color.WHITE, 18, bold=True
        )
        arcade.draw_text(
            f"BEST: {max(self.score, self.high_score)}",
            20, SCREEN_HEIGHT - 58, arcade.color.LIGHT_GRAY, 12
        )

        # Combo Multiplier
        if self.combo > 1:
            arcade.draw_text(
                f"COMBO x{self.combo}!",
                200, SCREEN_HEIGHT - 38, arcade.color.ORANGE, 16, bold=True
            )

        # Level
        arcade.draw_text(
            f"LEVEL {self.level}",
            SCREEN_WIDTH - 130, SCREEN_HEIGHT - 35, arcade.color.GOLD, 18, bold=True
        )

        # Health Bar
        bar_x = 20
        bar_y = SCREEN_HEIGHT - 92
        bar_width = 200
        bar_height = 16

        health_ratio = max(0.0, self.health / PLAYER_MAX_HEALTH)
        health_width = bar_width * health_ratio

        bar_color = (
            arcade.color.LIME_GREEN if health_ratio > 0.5
            else arcade.color.ORANGE if health_ratio > 0.25
            else arcade.color.RED
        )

        arcade.draw_lbwh_rectangle_filled(
            bar_x, bar_y, bar_width, bar_height, (40, 15, 20)
        )
        if health_width > 0:
            arcade.draw_lbwh_rectangle_filled(
                bar_x, bar_y, health_width, bar_height, bar_color
            )
        arcade.draw_lbwh_rectangle_outline(
            bar_x, bar_y, bar_width, bar_height, arcade.color.WHITE, 1.5
        )
        arcade.draw_text(
            f"{self.health}/{PLAYER_MAX_HEALTH}",
            bar_x + bar_width + 10, bar_y + 1, arcade.color.WHITE, 13, bold=True
        )

        # Active Power-up Timers
        status_y = SCREEN_HEIGHT - 125
        if self.rapid_fire_timer > 0:
            arcade.draw_text(
                f"⚡ RAPID FIRE: {self.rapid_fire_timer:.1f}s",
                20, status_y, arcade.color.GOLD, 13, bold=True
            )
            status_y -= 22

        if self.triple_shot_timer > 0:
            arcade.draw_text(
                f"🔱 TRIPLE SHOT: {self.triple_shot_timer:.1f}s",
                20, status_y, arcade.color.ORANGE, 13, bold=True
            )
            status_y -= 22

        if self.shield_timer > 0:
            arcade.draw_text(
                f"🛡️ SHIELD: {self.shield_timer:.1f}s",
                20, status_y, arcade.color.CYAN, 13, bold=True
            )

        # Controls Hint
        auto_status = "ON" if self.auto_fire else "OFF"
        arcade.draw_text(
            f"WASD/Arrows: Move | Mouse: Aim & Fire | F: Auto-Fire ({auto_status}) | P: Pause",
            20, 14, arcade.color.LIGHT_GRAY, 12
        )

    def draw_boss_health(self):
        if self.boss is None:
            return

        width = 460
        height = 18
        x = SCREEN_WIDTH / 2 - width / 2
        y = SCREEN_HEIGHT - 45

        health_width = width * max(0.0, self.boss.health / self.boss.max_health)

        arcade.draw_text(
            "⚠️ DREADNOUGHT BOSS ⚠️",
            SCREEN_WIDTH / 2, y + 24, arcade.color.RED, 15, bold=True, anchor_x="center"
        )
        arcade.draw_lbwh_rectangle_filled(x, y, width, height, (50, 0, 0))
        if health_width > 0:
            arcade.draw_lbwh_rectangle_filled(x, y, health_width, height, arcade.color.CRIMSON)
        arcade.draw_lbwh_rectangle_outline(x, y, width, height, arcade.color.WHITE, 2)

    def draw_pause_overlay(self):
        arcade.draw_lbwh_rectangle_filled(
            0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 150)
        )
        arcade.draw_text(
            "PAUSED",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 10,
            arcade.color.CYAN, 44, bold=True, anchor_x="center"
        )
        arcade.draw_text(
            "Press P to Resume",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 35,
            arcade.color.WHITE, 18, anchor_x="center"
        )

    def draw_game_over(self):
        arcade.draw_lbwh_rectangle_filled(
            0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 200)
        )
        arcade.draw_text(
            "GAME OVER",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 80,
            arcade.color.CRIMSON, 52, bold=True, anchor_x="center"
        )
        arcade.draw_text(
            f"Final Score: {self.score}",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20,
            arcade.color.WHITE, 24, bold=True, anchor_x="center"
        )
        arcade.draw_text(
            f"High Score: {max(self.score, self.high_score)}  |  Reached Level: {self.level}",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20,
            arcade.color.GOLD, 18, anchor_x="center"
        )
        arcade.draw_text(
            "Press R to Play Again",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 75,
            arcade.color.CYAN, 22, bold=True, anchor_x="center"
        )

    # ========================================================
    # UPDATE LOOP
    # ========================================================

    def on_update(self, delta_time):
        if self.paused:
            return

        if self.shake_timer > 0:
            self.shake_timer -= delta_time

        for particle in self.particles[:]:
            particle.update(delta_time)
            if particle.finished():
                self.particles.remove(particle)

        for explosion in self.explosions[:]:
            explosion.update(delta_time)
            if explosion.finished():
                self.explosions.remove(explosion)

        for ft in self.floating_texts[:]:
            ft.update(delta_time)
            if ft.finished():
                self.floating_texts.remove(ft)

        if self.game_over:
            return

        # Timers
        self.shoot_timer -= delta_time
        self.enemy_spawn_timer -= delta_time
        self.level_timer += delta_time
        self.powerup_timer += delta_time
        self.rapid_fire_timer -= delta_time
        self.shield_timer -= delta_time
        self.triple_shot_timer -= delta_time

        if self.combo_timer > 0:
            self.combo_timer -= delta_time
            if self.combo_timer <= 0:
                self.combo = 0

        # Stars
        for star in self.stars:
            star.update()

        # Level progression (pause timer during Boss fight)
        if self.boss is None and self.level_timer >= 18:
            self.level_timer = 0
            self.level += 1
            self.floating_texts.append(
                FloatingText(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50, f"LEVEL {self.level}!", arcade.color.GOLD)
            )

        # Boss Spawn every 5 levels
        if self.level % 5 == 0 and self.boss is None and self.boss_spawned_for_level != self.level:
            self.boss = Boss(self.level)
            self.boss_spawned_for_level = self.level
            self.sounds.play(self.sounds.boss, 0.7)

        # Player Movement (WASD + Arrow Keys)
        move_x = 0
        move_y = 0
        if arcade.key.W in self.keys_pressed or arcade.key.UP in self.keys_pressed:
            move_y += 1
        if arcade.key.S in self.keys_pressed or arcade.key.DOWN in self.keys_pressed:
            move_y -= 1
        if arcade.key.A in self.keys_pressed or arcade.key.LEFT in self.keys_pressed:
            move_x -= 1
        if arcade.key.D in self.keys_pressed or arcade.key.RIGHT in self.keys_pressed:
            move_x += 1

        if move_x != 0 and move_y != 0:
            move_x *= 0.7071
            move_y *= 0.7071

        self.player_x += move_x * PLAYER_SPEED
        self.player_y += move_y * PLAYER_SPEED

        self.player_x = max(PLAYER_RADIUS, min(SCREEN_WIDTH - PLAYER_RADIUS, self.player_x))
        self.player_y = max(PLAYER_RADIUS, min(SCREEN_HEIGHT - PLAYER_RADIUS, self.player_y))

        # Shooting
        if arcade.key.SPACE in self.keys_pressed or self.auto_fire:
            self.shoot()

        # Enemy Spawning
        if self.enemy_spawn_timer <= 0 and self.boss is None:
            speed_bonus = self.level * 0.1
            shooter_chance = min(0.40, 0.12 + self.level * 0.025)

            if random.random() < shooter_chance:
                self.shooter_enemies.append(ShooterEnemy(speed_bonus))
            else:
                self.normal_enemies.append(NormalEnemy(speed_bonus))

            self.enemy_spawn_timer = max(0.25, ENEMY_SPAWN_RATE - self.level * 0.035)

        # Periodic Power-ups
        if self.powerup_timer >= 11:
            self.powerup_timer = 0
            self.spawn_powerup(random.uniform(60, SCREEN_WIDTH - 60), SCREEN_HEIGHT + 20)

        # Update Bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.off_screen():
                self.bullets.remove(bullet)

        for bullet in self.enemy_bullets[:]:
            bullet.update()
            if bullet.off_screen():
                self.enemy_bullets.remove(bullet)

        # Update Normal Enemies
        for enemy in self.normal_enemies[:]:
            enemy.update(self.player_x, self.player_y, delta_time)
            if distance_between(enemy.x, enemy.y, self.player_x, self.player_y) < (enemy.radius + PLAYER_RADIUS):
                self.damage_player()
                self.create_explosion(enemy.x, enemy.y, 28, arcade.color.CRIMSON)
                if enemy in self.normal_enemies:
                    self.normal_enemies.remove(enemy)

        # Update Shooter Enemies
        for enemy in self.shooter_enemies[:]:
            should_shoot = enemy.update(self.player_x, self.player_y, delta_time)
            if should_shoot:
                angle = math.degrees(math.atan2(self.player_y - enemy.y, self.player_x - enemy.x))
                self.enemy_bullets.append(EnemyBullet(enemy.x, enemy.y, angle))
                self.sounds.play(self.sounds.enemy_shoot, 0.25)

            if distance_between(enemy.x, enemy.y, self.player_x, self.player_y) < (enemy.radius + PLAYER_RADIUS):
                self.damage_player()
                self.create_explosion(enemy.x, enemy.y, 32, arcade.color.PURPLE)
                if enemy in self.shooter_enemies:
                    self.shooter_enemies.remove(enemy)

        # Enemy Bullets vs Player
        for bullet in self.enemy_bullets[:]:
            if distance_between(bullet.x, bullet.y, self.player_x, self.player_y) < (bullet.radius + PLAYER_RADIUS):
                if bullet in self.enemy_bullets:
                    self.enemy_bullets.remove(bullet)
                self.damage_player()

        # Bullet Collisions
        self.check_bullets_vs_normal()
        self.check_bullets_vs_shooter()
        self.check_bullets_vs_boss()

        # Boss Update
        if self.boss:
            if self.boss.update(self.player_x, self.player_y, delta_time):
                self.boss_attack()

            if distance_between(self.boss.x, self.boss.y, self.player_x, self.player_y) < (self.boss.radius + PLAYER_RADIUS):
                self.damage_player()

        # Power-ups Update
        for powerup in self.powerups[:]:
            powerup.update(delta_time)
            if distance_between(powerup.x, powerup.y, self.player_x, self.player_y) < (powerup.radius + PLAYER_RADIUS):
                self.collect_powerup(powerup)
                if powerup in self.powerups:
                    self.powerups.remove(powerup)
            elif powerup.off_screen():
                if powerup in self.powerups:
                    self.powerups.remove(powerup)

    # ========================================================
    # COLLISIONS & COMBAT
    # ========================================================

    def add_score(self, base_points, x, y):
        self.combo += 1
        self.combo_timer = 2.5
        multiplier = min(5, 1 + (self.combo // 4))
        gained = base_points * multiplier
        self.score += gained
        if self.score > self.high_score:
            self.high_score = self.score

        label = f"+{gained}" if multiplier == 1 else f"+{gained} (x{multiplier})"
        self.floating_texts.append(FloatingText(x, y, label, arcade.color.YELLOW))

    def spawn_powerup(self, x, y):
        power_type = random.choice(["rapid", "shield", "health", "triple"])
        self.powerups.append(PowerUp(x, y, power_type))

    def check_bullets_vs_normal(self):
        for bullet in self.bullets[:]:
            for enemy in self.normal_enemies[:]:
                if distance_between(bullet.x, bullet.y, enemy.x, enemy.y) < (bullet.radius + enemy.radius):
                    enemy.health -= 30
                    enemy.hit_flash = 0.08
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)

                    if enemy.health <= 0:
                        if enemy in self.normal_enemies:
                            self.normal_enemies.remove(enemy)
                        self.add_score(10, enemy.x, enemy.y)
                        self.create_explosion(enemy.x, enemy.y, 35, arcade.color.ORANGE_RED)
                        if random.random() < 0.12:
                            self.spawn_powerup(enemy.x, enemy.y)
                    break

    def check_bullets_vs_shooter(self):
        for bullet in self.bullets[:]:
            for enemy in self.shooter_enemies[:]:
                if distance_between(bullet.x, bullet.y, enemy.x, enemy.y) < (bullet.radius + enemy.radius):
                    enemy.health -= 30
                    enemy.hit_flash = 0.08
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)

                    if enemy.health <= 0:
                        if enemy in self.shooter_enemies:
                            self.shooter_enemies.remove(enemy)
                        self.add_score(25, enemy.x, enemy.y)
                        self.create_explosion(enemy.x, enemy.y, 42, arcade.color.MAGENTA)
                        if random.random() < 0.20:
                            self.spawn_powerup(enemy.x, enemy.y)
                    break

    def check_bullets_vs_boss(self):
        if self.boss is None:
            return

        for bullet in self.bullets[:]:
            if distance_between(bullet.x, bullet.y, self.boss.x, self.boss.y) < (bullet.radius + self.boss.radius):
                self.boss.health -= 12
                self.boss.hit_flash = 0.06
                if bullet in self.bullets:
                    self.bullets.remove(bullet)

                # Small spark on hit
                for _ in range(4):
                    self.particles.append(Particle(bullet.x, bullet.y, arcade.color.YELLOW))

                if self.boss.health <= 0:
                    self.add_score(500, self.boss.x, self.boss.y)
                    self.create_explosion(self.boss.x, self.boss.y, 95, arcade.color.RED, particle_count=75)
                    self.trigger_shake(0.5, 10)
                    self.sounds.play(self.sounds.boss, 0.85)
                    self.spawn_powerup(self.boss.x - 25, self.boss.y)
                    self.spawn_powerup(self.boss.x + 25, self.boss.y)
                    self.boss = None
                    self.level += 1
                    self.level_timer = 0
                break

    def boss_attack(self):
        if self.boss is None:
            return

        base_angle = math.degrees(
            math.atan2(self.player_y - self.boss.y, self.player_x - self.boss.x)
        )

        if self.boss.attack_pattern == 0:
            # 5-way spread shot
            for offset in [-24, -12, 0, 12, 24]:
                self.enemy_bullets.append(
                    EnemyBullet(self.boss.x, self.boss.y, base_angle + offset, BOSS_BULLET_SPEED)
                )
        else:
            # Radial ring burst
            for angle in range(0, 360, 30):
                self.enemy_bullets.append(
                    EnemyBullet(self.boss.x, self.boss.y, angle, BOSS_BULLET_SPEED * 0.85)
                )

        self.sounds.play(self.sounds.enemy_shoot, 0.45)

    def damage_player(self):
        if self.shield_timer > 0:
            self.floating_texts.append(FloatingText(self.player_x, self.player_y + 25, "BLOCKED!", arcade.color.CYAN))
            return

        self.health -= 12
        self.combo = 0
        self.trigger_shake(0.25, 7)
        self.sounds.play(self.sounds.hit, 0.5)
        self.create_explosion(self.player_x, self.player_y, 28, arcade.color.CYAN, particle_count=15)

        if self.health <= 0:
            self.health = 0
            self.game_over = True
            self.create_explosion(self.player_x, self.player_y, 70, arcade.color.ORANGE, particle_count=60)
            self.sounds.play(self.sounds.explosion, 0.85)

    def collect_powerup(self, powerup):
        self.sounds.play(self.sounds.powerup, 0.7)
        self.score += 25

        if powerup.power_type == "rapid":
            self.rapid_fire_timer = RAPID_FIRE_DURATION
            msg = "RAPID FIRE!"
            col = arcade.color.GOLD
        elif powerup.power_type == "shield":
            self.shield_timer = SHIELD_DURATION
            msg = "SHIELD ACTIVE!"
            col = arcade.color.CYAN
        elif powerup.power_type == "triple":
            self.triple_shot_timer = TRIPLE_SHOT_DURATION
            msg = "TRIPLE SHOT!"
            col = arcade.color.ORANGE
        else:
            self.health = min(PLAYER_MAX_HEALTH, self.health + 35)
            msg = "+35 HEALTH!"
            col = arcade.color.LIME_GREEN

        self.floating_texts.append(FloatingText(self.player_x, self.player_y + 25, msg, col))

    def create_explosion(self, x, y, size=35, color=arcade.color.ORANGE, particle_count=22):
        self.explosions.append(Explosion(x, y, size))
        for _ in range(particle_count):
            self.particles.append(Particle(x, y, color))
        self.sounds.play(self.sounds.explosion, 0.35)

    def trigger_shake(self, duration, intensity):
        self.shake_timer = duration
        self.shake_intensity = intensity

    def shoot(self):
        if self.shoot_timer > 0:
            return

        self.shoot_timer = (
            RAPID_SHOOT_COOLDOWN if self.rapid_fire_timer > 0 else NORMAL_SHOOT_COOLDOWN
        )

        rad = math.radians(self.player_angle)
        nose_x = self.player_x + math.cos(rad) * (PLAYER_RADIUS * 1.4)
        nose_y = self.player_y + math.sin(rad) * (PLAYER_RADIUS * 1.4)

        if self.triple_shot_timer > 0:
            for spread in [-12, 0, 12]:
                self.bullets.append(PlayerBullet(nose_x, nose_y, self.player_angle + spread))
        else:
            self.bullets.append(PlayerBullet(nose_x, nose_y, self.player_angle))

        self.sounds.play(self.sounds.shoot, 0.3)

    # ========================================================
    # INPUT EVENTS
    # ========================================================

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)

        if key == arcade.key.F:
            self.auto_fire = not self.auto_fire

        if key == arcade.key.P and not self.game_over:
            self.paused = not self.paused

        if key == arcade.key.R and self.game_over:
            self.init_game_state()

    def on_key_release(self, key, modifiers):
        self.keys_pressed.discard(key)

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.paused and not self.game_over:
            self.player_angle = math.degrees(
                math.atan2(y - self.player_y, x - self.player_x)
            )

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT and not self.paused and not self.game_over:
            self.shoot()


# ============================================================
# MAIN
# ============================================================

def main():
    GameWindow()
    arcade.run()


if __name__ == "__main__":
    main()

