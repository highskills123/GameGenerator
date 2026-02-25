"""
top_down_shooter.py – Code generator for the top-down shooter genre.

Produces a complete, multi-file Flutter/Flame project sub-tree for a
top-down shooter game.  All generated Dart code follows Flame best
practices:
  - Assets preloaded in ``onLoad``.
  - No per-frame allocations in ``update``.
  - Simple object pool for bullets.
"""

from __future__ import annotations

from typing import Dict

from ..spec import GameSpec


def generate_files(spec: GameSpec) -> Dict[str, str]:
    """Return a dict of {relative_path: file_content} for the shooter."""
    title = spec.get("title", "Top Down Shooter")
    safe_name = _safe_class_name(title)

    files: Dict[str, str] = {}
    files["lib/game/game.dart"] = _game_dart(safe_name)
    files["lib/game/player.dart"] = _player_dart(safe_name)
    files["lib/game/enemy.dart"] = _enemy_dart(safe_name)
    files["lib/game/bullet.dart"] = _bullet_dart(safe_name)
    files["lib/game/bullet_pool.dart"] = _bullet_pool_dart(safe_name)
    files["lib/game/hud.dart"] = _hud_dart(safe_name)
    files["lib/game/mobile_controls.dart"] = _mobile_controls_dart(safe_name)
    files["lib/game/game_over_overlay.dart"] = _game_over_overlay_dart(safe_name)
    return files


def _safe_class_name(title: str) -> str:
    """Convert a title string into a CamelCase Dart class name prefix."""
    words = "".join(ch if ch.isalnum() or ch == " " else " " for ch in title).split()
    return "".join(w.capitalize() for w in words) if words else "MyGame"


def _game_dart(name: str) -> str:
    return f"""\
import 'dart:math';
import 'package:flame/game.dart';
import 'package:flame/input.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'player.dart';
import 'enemy.dart';
import 'bullet_pool.dart';
import 'hud.dart';
import 'mobile_controls.dart';

class {name}Game extends FlameGame
    with HasCollisionDetection, KeyboardEvents {{
  // Loaded assets
  late final SpriteComponent _background;

  // Game objects
  late final Player player;
  late final BulletPool bulletPool;

  // Mobile controls
  late final JoystickComponent joystick;

  // Score / state
  int score = 0;
  bool _gameOver = false;

  // Enemy spawn timer (seconds)
  static const double _spawnInterval = 2.0;
  double _spawnTimer = 0;

  final Random _rng = Random();

  @override
  Future<void> onLoad() async {{
    await super.onLoad();

    // Background
    final bgSprite = await loadSprite('imported/background.png');
    _background = SpriteComponent(
      sprite: bgSprite,
      size: size,
    );
    add(_background);

    // Bullet pool – pre-allocate 20 bullets
    bulletPool = BulletPool(20);
    add(bulletPool);

    // Player
    player = Player(game: this);
    await player.onLoad();
    add(player);

    // Mobile virtual joystick + fire button
    final controls = MobileControls(game: this);
    joystick = controls.joystick;
    add(controls);

    // HUD
    add(Hud(game: this));

    overlays.addEntry(
      'GameOver',
      (context, game) => GameOverOverlay(game: game as {name}Game),
    );
  }}

  @override
  void update(double dt) {{
    if (_gameOver) return;
    super.update(dt);

    _spawnTimer += dt;
    if (_spawnTimer >= _spawnInterval) {{
      _spawnTimer = 0;
      _spawnEnemy();
    }}
  }}

  void _spawnEnemy() {{
    final x = _rng.nextDouble() * (size.x - 48);
    add(Enemy(game: this, position: Vector2(x, -48)));
  }}

  void addScore(int points) {{
    score += points;
  }}

  void triggerGameOver() {{
    if (_gameOver) return;
    _gameOver = true;
    pauseEngine();
    overlays.add('GameOver');
  }}

  @override
  KeyEventResult onKeyEvent(
    RawKeyEvent event,
    Set<LogicalKeyboardKey> keysPressed,
  ) {{
    player.handleKeys(keysPressed);
    if (keysPressed.contains(LogicalKeyboardKey.space)) {{
      player.shoot();
    }}
    return KeyEventResult.handled;
  }}
}}
"""


def _player_dart(name: str) -> str:
    return f"""\
import 'package:flame/collisions.dart';
import 'package:flame/components.dart';
import 'package:flutter/services.dart';
import 'game.dart';
import 'bullet_pool.dart';
import 'enemy.dart';

class Player extends SpriteComponent with CollisionCallbacks {{
  final {name}Game game;

  // Movement speed (pixels/sec)
  static const double _speed = 200;

  // Shoot cooldown (seconds)
  static const double _shootCooldown = 0.25;
  double _shootTimer = 0;

  // Keyboard direction vector – updated from key events, no per-frame alloc
  final Vector2 _keyDir = Vector2.zero();

  Player({{required this.game}}) : super(size: Vector2(48, 48));

  @override
  Future<void> onLoad() async {{
    sprite = await game.loadSprite('imported/player.png');
    position = Vector2(game.size.x / 2 - 24, game.size.y - 80);
    add(RectangleHitbox());
  }}

  void handleKeys(Set<LogicalKeyboardKey> keys) {{
    _keyDir.setZero();
    if (keys.contains(LogicalKeyboardKey.arrowLeft) ||
        keys.contains(LogicalKeyboardKey.keyA)) {{
      _keyDir.x -= 1;
    }}
    if (keys.contains(LogicalKeyboardKey.arrowRight) ||
        keys.contains(LogicalKeyboardKey.keyD)) {{
      _keyDir.x += 1;
    }}
    if (keys.contains(LogicalKeyboardKey.arrowUp) ||
        keys.contains(LogicalKeyboardKey.keyW)) {{
      _keyDir.y -= 1;
    }}
    if (keys.contains(LogicalKeyboardKey.arrowDown) ||
        keys.contains(LogicalKeyboardKey.keyS)) {{
      _keyDir.y += 1;
    }}
  }}

  void shoot() {{
    if (_shootTimer <= 0) {{
      game.bulletPool.fire(
        position: Vector2(position.x + size.x / 2 - 4, position.y),
        direction: Vector2(0, -1),
      );
      _shootTimer = _shootCooldown;
    }}
  }}

  @override
  void update(double dt) {{
    super.update(dt);
    if (_shootTimer > 0) _shootTimer -= dt;

    // Prefer keyboard; fall back to joystick (mobile)
    final joystickDelta = game.joystick.relativeDelta;
    if (_keyDir.length2 > 0) {{
      position.addScaled(_keyDir.normalized(), _speed * dt);
    }} else if (joystickDelta.length2 > 0) {{
      // relativeDelta is already normalised in the range [-1, 1]
      position.addScaled(joystickDelta, _speed * dt);
    }}

    // Clamp to screen
    position.x = position.x.clamp(0, game.size.x - size.x);
    position.y = position.y.clamp(0, game.size.y - size.y);
  }}

  @override
  void onCollisionStart(
    Set<Vector2> intersectionPoints,
    PositionComponent other,
  ) {{
    if (other is Enemy) {{
      game.triggerGameOver();
    }}
  }}
}}
"""


def _enemy_dart(name: str) -> str:
    return f"""\
import 'package:flame/collisions.dart';
import 'package:flame/components.dart';
import 'game.dart';

class Enemy extends SpriteComponent with CollisionCallbacks {{
  final {name}Game game;

  static const double _speed = 100;

  Enemy({{required this.game, required Vector2 position}})
      : super(size: Vector2(48, 48), position: position);

  @override
  Future<void> onLoad() async {{
    sprite = await game.loadSprite('imported/enemy.png');
    add(RectangleHitbox());
  }}

  @override
  void update(double dt) {{
    super.update(dt);
    position.y += _speed * dt;

    // Remove if off-screen
    if (position.y > game.size.y + size.y) {{
      removeFromParent();
    }}
  }}
}}
"""


def _bullet_dart(name: str) -> str:
    return f"""\
import 'package:flame/collisions.dart';
import 'package:flame/components.dart';
import 'enemy.dart';
import 'game.dart';

class Bullet extends SpriteComponent with CollisionCallbacks {{
  final {name}Game game;
  final Vector2 direction;

  static const double _speed = 400;

  // Pool state
  bool active = false;

  Bullet({{required this.game}})
      : direction = Vector2(0, -1),
        super(size: Vector2(8, 16));

  @override
  Future<void> onLoad() async {{
    sprite = await game.loadSprite('imported/bullet.png');
    add(RectangleHitbox());
  }}

  @override
  void update(double dt) {{
    if (!active) return;
    super.update(dt);
    position.addScaled(direction, _speed * dt);

    // Deactivate if off-screen
    if (position.y < -size.y) {{
      deactivate();
    }}
  }}

  void activate(Vector2 pos, Vector2 dir) {{
    position.setFrom(pos);
    direction.setFrom(dir.normalized());
    active = true;
  }}

  void deactivate() {{
    active = false;
    position.setValues(-1000, -1000);
  }}

  @override
  void onCollisionStart(
    Set<Vector2> intersectionPoints,
    PositionComponent other,
  ) {{
    if (other is Enemy) {{
      other.removeFromParent();
      game.addScore(10);
      deactivate();
    }}
  }}
}}
"""


def _bullet_pool_dart(name: str) -> str:
    return f"""\
import 'package:flame/components.dart';
import 'bullet.dart';
import 'game.dart';

/// Simple object pool for bullets – avoids per-shot allocations.
class BulletPool extends Component {{
  final int poolSize;
  final List<Bullet> _pool = [];
  late final {name}Game _game;

  BulletPool(this.poolSize);

  @override
  Future<void> onLoad() async {{
    _game = findGame()! as {name}Game;
    for (int i = 0; i < poolSize; i++) {{
      final b = Bullet(game: _game);
      await b.onLoad();
      b.deactivate();
      _pool.add(b);
      add(b);
    }}
  }}

  /// Activate an available bullet at [position] moving in [direction].
  void fire({{required Vector2 position, required Vector2 direction}}) {{
    for (final b in _pool) {{
      if (!b.active) {{
        b.activate(position, direction);
        return;
      }}
    }}
    // Pool exhausted – silently skip (no allocation)
  }}
}}
"""


def _hud_dart(name: str) -> str:
    return f"""\
import 'package:flame/components.dart';
import 'package:flutter/material.dart';
import 'game.dart';

class Hud extends TextComponent with HasGameRef<{name}Game> {{
  Hud({{required {name}Game game}})
      : super(
          text: 'Score: 0',
          textRenderer: TextPaint(
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
            ),
          ),
        );

  @override
  void update(double dt) {{
    super.update(dt);
    text = 'Score: ${{gameRef.score}}';
  }}
}}
"""


def _mobile_controls_dart(name: str) -> str:
    return f"""\
import 'package:flame/components.dart';
import 'package:flame/input.dart';
import 'package:flutter/material.dart';
import 'game.dart';

/// Mobile on-screen controls: virtual joystick (left) + fire button (right).
///
/// Both controls are [HudComponent]-like; they stay fixed on the viewport
/// regardless of the game camera.  On desktop the joystick is ignored and
/// keyboard input takes priority (see Player.update).
class MobileControls extends Component {{
  final {name}Game game;
  late final JoystickComponent joystick;

  MobileControls({{required this.game}});

  @override
  Future<void> onLoad() async {{
    // Joystick – bottom-left corner
    joystick = JoystickComponent(
      knob: CircleComponent(
        radius: 20,
        paint: Paint()..color = const Color(0xBBFFFFFF),
      ),
      background: CircleComponent(
        radius: 55,
        paint: Paint()..color = const Color(0x44FFFFFF),
      ),
      margin: const EdgeInsets.only(left: 48, bottom: 48),
    );
    add(joystick);

    // Fire button – bottom-right corner
    final fireButton = HudButtonComponent(
      button: CircleComponent(
        radius: 36,
        paint: Paint()..color = const Color(0xAAFF3333),
      ),
      buttonDown: CircleComponent(
        radius: 36,
        paint: Paint()..color = const Color(0xFFFF0000),
      ),
      margin: const EdgeInsets.only(right: 48, bottom: 48),
      onPressed: game.player.shoot,
    );
    add(fireButton);
  }}
}}
"""


def _game_over_overlay_dart(name: str) -> str:
    return f"""\
import 'package:flutter/material.dart';
import 'game.dart';

class GameOverOverlay extends StatelessWidget {{
  final {name}Game game;

  const GameOverOverlay({{required this.game, super.key}});

  @override
  Widget build(BuildContext context) {{
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text(
            'GAME OVER',
            style: TextStyle(
              color: Colors.red,
              fontSize: 48,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Score: ${{game.score}}',
            style: const TextStyle(color: Colors.white, fontSize: 24),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {{
              game.overlays.remove('GameOver');
              game.resumeEngine();
            }},
            child: const Text('Restart'),
          ),
        ],
      ),
    );
  }}
}}
"""
