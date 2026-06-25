# 🎮 Tanks!

A minimal top-down tank battle game built with Pygame.

## Controls

| Key | Action |
|-----|--------|
| Arrows | Move tank |
| WASD | Aim turret |
| Space | Shoot |
| Enter | Respawn (same round) |
| R | Restart from Round 1 |

## Gameplay

- You (green tank) fight waves of red enemy tanks
- **Round 1** → 1 enemy, **Round 2** → 2 enemies, up to **Round 10** → 10 enemies
- Survive all 10 rounds to win!
- Health carries over between rounds — play smart early
- Destroyed tanks explode into particles 💥

## Balancer Engine

Difficulty is controlled by the `Balancer` class with sensible defaults. Customize it:

```python
from tanks import Game, Balancer

Game(Balancer(
    max_enemies=10,
    enemy_speed=1.4,
    enemy_health=2,
    enemy_fire_rate=90,
    enemy_accuracy=0.55,
    player_speed=3.0,
    player_health=5,
    player_fire_rate=18,
    bullet_speed=7,
    scale_with_remaining=True,
    scale_factor=0.12,
)).run()
```

Key feature: `scale_with_remaining` makes surviving enemies faster and more accurate as their numbers thin, keeping every round tense to the end.

## Install & Run

```bash
pip install pygame
python tanks.py
```

## License

MIT
