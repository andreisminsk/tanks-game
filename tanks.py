import pygame, math, random, sys

# ── Configurable Balancer Engine ──────────────────────────────────────────────

class Balancer:
    """Adjusts enemy parameters based on how many are alive. Fully configurable."""
    def __init__(self, max_enemies=5, enemy_speed=1.4, enemy_health=2,
                 enemy_fire_rate=90, enemy_accuracy=0.55, player_speed=3.0,
                 player_health=5, player_fire_rate=18, bullet_speed=7,
                 scale_with_remaining=True, scale_factor=0.12):
        self.max_enemies       = max_enemies
        self.enemy_speed       = enemy_speed
        self.enemy_health      = enemy_health
        self.enemy_fire_rate   = enemy_fire_rate
        self.enemy_accuracy    = enemy_accuracy
        self.player_speed      = player_speed
        self.player_health     = player_health
        self.player_fire_rate  = player_fire_rate
        self.bullet_speed      = bullet_speed
        self.scale_with_remaining = scale_with_remaining
        self.scale_factor      = scale_factor

    def enemy_params(self, alive_count):
        """Return (speed, accuracy) for enemies, scaling up as fewer remain."""
        s, a = self.enemy_speed, self.enemy_accuracy
        if self.scale_with_remaining and alive_count > 0:
            mult = 1 + (self.max_enemies - alive_count) * self.scale_factor
            s *= mult
            a  = min(0.95, a * mult)
        return s, a

# ── Bullet ───────────────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5)
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(15, 40)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.96
        self.vy *= 0.96
        self.life -= 1

    def draw(self, surf):
        alpha = self.life / self.max_life
        r = min(255, int(self.color[0] * alpha + 255 * (1 - alpha)))
        g = min(255, int(self.color[1] * alpha + 80 * (1 - alpha)))
        b = min(255, int(self.color[2] * alpha))
        sz = max(1, int(self.size * alpha))
        pygame.draw.circle(surf, (r, g, b), (int(self.x), int(self.y)), sz)


class Bullet:
    RADIUS = 3

    def __init__(self, x, y, angle, speed, owner):
        self.x, self.y = x, y
        self.angle = angle
        self.speed = speed
        self.owner = owner          # 'player' | 'enemy'
        self.alive = True

    def update(self, w, h):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        if not (0 < self.x < w and 0 < self.y < h):
            self.alive = False

    def draw(self, surf):
        c = (180, 255, 180) if self.owner == 'player' else (255, 160, 160)
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), self.RADIUS)

# ── Tank (base) ──────────────────────────────────────────────────────────────

class Tank:
    SIZE = 24

    def __init__(self, x, y, color, speed, health, fire_rate):
        self.x, self.y = float(x), float(y)
        self.color = color
        self.speed = speed
        self.health = health
        self.max_health = health
        self.fire_rate = fire_rate
        self.cooldown = 0
        self.angle = 0.0
        self.alive = True

    def move(self, dx, dy):
        self.x = max(self.SIZE//2, min(800 - self.SIZE//2, self.x + dx * self.speed))
        self.y = max(self.SIZE//2, min(600 - self.SIZE//2, self.y + dy * self.speed))

    def try_shoot(self, bullet_speed, owner):
        if self.cooldown <= 0:
            self.cooldown = self.fire_rate
            bx = self.x + math.cos(self.angle) * (self.SIZE//2 + 5)
            by = self.y + math.sin(self.angle) * (self.SIZE//2 + 5)
            return Bullet(bx, by, self.angle, bullet_speed, owner)
        return None

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            self.alive = False

    def draw(self, surf):
        r = pygame.Rect(self.x - self.SIZE//2, self.y - self.SIZE//2, self.SIZE, self.SIZE)
        pygame.draw.rect(surf, self.color, r)
        pygame.draw.rect(surf, (220, 220, 220), r, 1)
        ex = self.x + math.cos(self.angle) * (self.SIZE//2 + 7)
        ey = self.y + math.sin(self.angle) * (self.SIZE//2 + 7)
        pygame.draw.line(surf, (200, 200, 200), (int(self.x), int(self.y)), (int(ex), int(ey)), 3)
        # health bar
        bw = self.SIZE
        bx, by = self.x - bw//2, self.y - self.SIZE//2 - 7
        pygame.draw.rect(surf, (50, 50, 50), (bx, by, bw, 4))
        fill = int(bw * self.health / self.max_health)
        hc = (0, 200, 0) if self.health > self.max_health // 2 else (220, 200, 0) if self.health > 1 else (220, 0, 0)
        pygame.draw.rect(surf, hc, (bx, by, fill, 4))

# ── Enemy Tank ────────────────────────────────────────────────────────────────

class EnemyTank(Tank):
    def __init__(self, x, y, speed, health, fire_rate, accuracy):
        super().__init__(x, y, (200, 50, 50), speed, health, fire_rate)
        self.accuracy = accuracy
        self.think_cd = random.randint(20, 80)
        self.move_dir = (0, 0)

    def think(self, player, bullets, balancer):
        self.think_cd -= 1
        if self.think_cd <= 0:
            self.think_cd = random.randint(30, 90)
            a = math.atan2(player.y - self.y, player.x - self.x) + random.uniform(-0.6, 0.6)
            self.move_dir = (math.cos(a), math.sin(a))

        self.move(*self.move_dir)

        # aim & shoot
        target_a = math.atan2(player.y - self.y, player.x - self.x)
        diff = abs((self.angle - target_a + math.pi) % (2 * math.pi) - math.pi)
        if diff < 0.45 and random.random() < self.accuracy * 0.04:
            self.angle = target_a
            b = self.try_shoot(5, 'enemy')
            if b:
                bullets.append(b)

# ── Game ─────────────────────────────────────────────────────────────────────

class Game:
    W, H, FPS = 800, 600, 60

    def __init__(self, balancer=None):
        pygame.init()
        self.screen = pygame.display.set_mode((self.W, self.H))
        pygame.display.set_caption("Tanks!")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.balancer = balancer or Balancer()
        self.reset()

    def reset(self):
        b = self.balancer
        self.player = Tank(self.W // 2, self.H // 2, (50, 200, 50),
                           b.player_speed, b.player_health, b.player_fire_rate)
        self.enemies = []
        self.bullets = []
        self.round = 1
        self.won = False
        self.particles = []
        self._spawn_wave()

    def _spawn_wave(self):
        b = self.balancer
        count = min(self.round, 10)
        sp, acc = b.enemy_params(count)
        for _ in range(count):
            for _ in range(50):
                x = random.randint(40, self.W - 40)
                y = random.randint(40, self.H - 40)
                if math.hypot(x - self.player.x, y - self.player.y) > 140:
                    break
            self.enemies.append(EnemyTank(x, y, sp, b.enemy_health, b.enemy_fire_rate, acc))

    def run(self):
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN and not self.player.alive:
                    b = self.balancer
                    self.player = Tank(self.W // 2, self.H // 2, (50, 200, 50),
                                       b.player_speed, b.player_health, b.player_fire_rate)
                    self.enemies = []
                    self.bullets = []
                    self._spawn_wave()

            keys = pygame.key.get_pressed()
            # Arrows = move body
            dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            dy = keys[pygame.K_DOWN]  - keys[pygame.K_UP]
            if dx and dy:
                dx *= 0.707; dy *= 0.707
            self.player.move(dx, dy)
            # WASD = aim turret
            tx = keys[pygame.K_d] - keys[pygame.K_a]
            ty = keys[pygame.K_s] - keys[pygame.K_w]
            if tx or ty:
                self.player.angle = math.atan2(ty, tx)

            if keys[pygame.K_SPACE]:
                b = self.player.try_shoot(self.balancer.bullet_speed, 'player')
                if b:
                    self.bullets.append(b)
            self.player.update()

            alive = sum(e.alive for e in self.enemies)
            for e in self.enemies:
                if e.alive:
                    sp, acc = self.balancer.enemy_params(alive)
                    e.speed, e.accuracy = sp, acc
                    e.think(self.player, self.bullets, self.balancer)
                    e.update()

            for b in self.bullets:
                b.update(self.W, self.H)

            # collisions
            for b in self.bullets:
                if not b.alive: continue
                if b.owner == 'player':
                    for e in self.enemies:
                        if e.alive and math.hypot(b.x - e.x, b.y - e.y) < e.SIZE // 2:
                            e.hit()
                            if not e.alive:
                                self.particles += [Particle(e.x, e.y, (220, 80, 20)) for _ in range(25)]
                            b.alive = False; break
                elif b.owner == 'enemy':
                    if math.hypot(b.x - self.player.x, b.y - self.player.y) < self.player.SIZE // 2:
                        self.player.hit()
                        if not self.player.alive:
                            self.particles += [Particle(self.player.x, self.player.y, (50, 200, 50)) for _ in range(30)]
                        b.alive = False

            self.bullets = [b for b in self.bullets if b.alive]

            # update particles
            for p in self.particles: p.update()
            self.particles = [p for p in self.particles if p.life > 0]

            if not any(e.alive for e in self.enemies):
                if self.round >= 10:
                    self.won = True
                else:
                    self.round += 1
                    self._spawn_wave()

            # ── draw ──
            self.screen.fill((25, 25, 30))
            for i in range(0, self.W, 50):
                pygame.draw.line(self.screen, (35, 35, 40), (i, 0), (i, self.H))
            for i in range(0, self.H, 50):
                pygame.draw.line(self.screen, (35, 35, 40), (0, i), (self.W, i))

            for p in self.particles: p.draw(self.screen)
            for b in self.bullets: b.draw(self.screen)
            for e in self.enemies:
                if e.alive: e.draw(self.screen)
            if self.player.alive: self.player.draw(self.screen)

            alive = sum(e.alive for e in self.enemies)
            hud = self.font.render(f"Round: {self.round}   Enemies: {alive}   HP: {self.player.health}   [R] Restart", True, (180, 180, 180))
            self.screen.blit(hud, (10, 10))

            if not self.player.alive:
                msg = self.font.render(f"YOU DIED on Round {self.round} — Press ENTER to respawn", True, (255, 70, 70))
                self.screen.blit(msg, (self.W//2 - msg.get_width()//2, self.H//2 - 10))
                sub = self.font.render("Press R to restart from Round 1", True, (150, 150, 150))
                self.screen.blit(sub, (self.W//2 - sub.get_width()//2, self.H//2 + 25))
            elif self.won:
                t = pygame.time.get_ticks()
                pulse = abs(math.sin(t * 0.003)) * 55 + 200
                big = pygame.font.SysFont(None, 64)
                msg = big.render("🏆 YOU CONQUERED ALL 10 ROUNDS! 🏆", True, (int(pulse), 255, int(pulse)))
                self.screen.blit(msg, (self.W//2 - msg.get_width()//2, self.H//2 - 40))
                sub = self.font.render("Press R to play again", True, (180, 180, 180))
                self.screen.blit(sub, (self.W//2 - sub.get_width()//2, self.H//2 + 30))

            pygame.display.flip()
            self.clock.tick(self.FPS)

if __name__ == '__main__':
    Game().run()
