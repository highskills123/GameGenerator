"""
top_down_shooter.py – Code generator for the top-down shooter genre.

Produces a complete, multi-file Flutter/Flame project sub-tree for a
top-down shooter game.  Features generated:
  - Main menu with high-score display
  - Sprite loading with coloured-shape fallback (works without asset files)
  - Wave progression system (kill N enemies → next wave, faster spawns)
  - Object-pooled bullets (no per-shot allocations)
  - Powerup drops (RapidFire / Shield)
  - Explosion visual feedback on enemy death
  - High-score persistence via SharedPreferences
  - Proper game-restart (full state reset, no page reload required)
  - Mobile virtual joystick + fire button
"""

from __future__ import annotations

from typing import Dict

from ..spec import GameSpec


def generate_files(spec: GameSpec) -> Dict[str, str]:
    """Return a dict of {relative_path: file_content} for the shooter."""
    title = spec.get("title", "Top Down Shooter")
    safe_name = _safe_class_name(title)

    files: Dict[str, str] = {}
    files["lib/game/game.dart"] = _game_dart(safe_name, title)
    files["lib/game/player.dart"] = _player_dart(safe_name)
    files["lib/game/enemy.dart"] = _enemy_dart(safe_name)
    files["lib/game/bullet.dart"] = _bullet_dart(safe_name)
    files["lib/game/bullet_pool.dart"] = _bullet_pool_dart(safe_name)
    files["lib/game/hud.dart"] = _hud_dart(safe_name)
    files["lib/game/mobile_controls.dart"] = _mobile_controls_dart(safe_name)
    files["lib/game/game_over_overlay.dart"] = _game_over_overlay_dart(safe_name)
    files["lib/game/save_manager.dart"] = _save_manager_dart()
    files["lib/game/powerup.dart"] = _powerup_dart(safe_name)
    files["lib/game/explosion.dart"] = _explosion_dart()
    # Override main.dart: embed main menu + game in one file (keeps GameWidget)
    files["lib/main.dart"] = _main_dart(safe_name, title,
                                        spec.get("orientation", "landscape"))
    return files


def _safe_class_name(title: str) -> str:
    """Convert a title string into a CamelCase Dart class name prefix."""
    words = "".join(ch if ch.isalnum() or ch == " " else " " for ch in title).split()
    return "".join(w.capitalize() for w in words) if words else "MyGame"


# ---------------------------------------------------------------------------
# main.dart  (embeds main menu + game; keeps GameWidget for test coverage)
# ---------------------------------------------------------------------------

def _main_dart(name: str, title: str, orientation: str) -> str:
    if orientation == "landscape":
        orient_str = (
            "DeviceOrientation.landscapeLeft,\n"
            "    DeviceOrientation.landscapeRight,"
        )
    else:
        orient_str = (
            "DeviceOrientation.portraitUp,\n"
            "    DeviceOrientation.portraitDown,"
        )
    return f"""\
import 'package:flame/game.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'game/game.dart';
import 'game/save_manager.dart';

void main() async {{
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([
    {orient_str}
  ]);
  runApp(const {name}App());
}}

class {name}App extends StatelessWidget {{
  const {name}App({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{title}',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark(),
      home: const _Shell(),
    );
  }}
}}

/// Root shell: shows main menu OR the live game based on [_playing].
class _Shell extends StatefulWidget {{
  const _Shell();

  @override
  State<_Shell> createState() => _ShellState();
}}

class _ShellState extends State<_Shell> {{
  bool _playing = false;
  int _highScore = 0;
  late {name}Game _game;

  @override
  void initState() {{
    super.initState();
    _loadHighScore();
  }}

  Future<void> _loadHighScore() async {{
    final sm = SaveManager();
    await sm.load();
    if (mounted) setState(() => _highScore = sm.highScore);
  }}

  void _startGame() {{
    _game = {name}Game(onReturnToMenu: _returnToMenu);
    setState(() => _playing = true);
  }}

  void _returnToMenu() {{
    _loadHighScore(); // refresh high score after game ends
    setState(() => _playing = false);
  }}

  @override
  Widget build(BuildContext context) {{
    if (_playing) {{
      return Scaffold(
        backgroundColor: Colors.black,
        body: GameWidget<{name}Game>(game: _game),
      );
    }}
    return _MainMenu(highScore: _highScore, onPlay: _startGame);
  }}
}}

class _MainMenu extends StatelessWidget {{
  final int highScore;
  final VoidCallback onPlay;

  const _MainMenu({{required this.highScore, required this.onPlay}});

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              '{title}',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 40,
                fontWeight: FontWeight.bold,
                letterSpacing: 2,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              'Best Score: $highScore',
              style: const TextStyle(color: Colors.amber, fontSize: 22),
            ),
            const SizedBox(height: 52),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.deepPurple,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(
                    horizontal: 52, vertical: 18),
                textStyle: const TextStyle(
                    fontSize: 22, fontWeight: FontWeight.bold),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: onPlay,
              child: const Text('▶  PLAY'),
            ),
          ],
        ),
      ),
    );
  }}
}}
"""


# ---------------------------------------------------------------------------
# lib/game/game.dart
# ---------------------------------------------------------------------------

def _game_dart(name: str, title: str) -> str:
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
import 'game_over_overlay.dart';
import 'powerup.dart';
import 'save_manager.dart';
import 'explosion.dart';

class {name}Game extends FlameGame
    with HasCollisionDetection, KeyboardEvents {{
  // Callback to return to main menu (set by _ShellState)
  final VoidCallback? onReturnToMenu;

  // Persistence
  late final SaveManager saveManager;

  // Entities
  late Player player;
  late BulletPool bulletPool;
  late JoystickComponent joystick;

  // State
  int score = 0;
  int wave = 1;
  int _killCount = 0;
  bool _gameOver = false;

  // Spawn timing
  static const int _killsPerWave = 5;
  static const double _baseSpawnInterval = 2.0;
  double _spawnTimer = 0;
  double get _spawnInterval =>
      (_baseSpawnInterval - (wave - 1) * 0.15).clamp(0.5, _baseSpawnInterval);

  final Random _rng = Random();

  {name}Game({{this.onReturnToMenu}});

  @override
  Future<void> onLoad() async {{
    await super.onLoad();

    saveManager = SaveManager();
    await saveManager.load();

    // Background – colored rect fallback when no sprite found
    try {{
      final bg = await loadSprite('imported/background.png');
      add(SpriteComponent(sprite: bg, size: size));
    }} catch (_) {{
      add(RectangleComponent(
        size: size,
        paint: Paint()..color = const Color(0xFF080c1a),
      ));
    }}

    bulletPool = BulletPool(30);
    add(bulletPool);

    player = Player(game: this);
    await player.onLoad();
    add(player);

    final controls = MobileControls(game: this);
    joystick = controls.joystick;
    add(controls);

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
    add(Enemy(game: this, position: Vector2(x, -48), wave: wave));
  }}

  /// Called by Enemy when it is destroyed.
  void onEnemyKilled(Vector2 pos) {{
    score += 10 * wave;
    _killCount++;
    if (_killCount >= _killsPerWave) {{
      _killCount = 0;
      wave++;
    }}
    // 25 % chance to drop a powerup
    if (_rng.nextDouble() < 0.25) {{
      final type = _rng.nextBool() ? PowerupType.rapidFire : PowerupType.shield;
      add(Powerup(game: this, position: pos.clone(), type: type));
    }}
    add(ExplosionComponent(position: pos.clone()));
  }}

  void triggerGameOver() {{
    if (_gameOver) return;
    _gameOver = true;
    saveManager.save(score: score);
    pauseEngine();
    overlays.add('GameOver');
  }}

  /// Full state reset – called by GameOverOverlay "Play Again" button.
  void restart() {{
    overlays.remove('GameOver');
    score = 0;
    wave = 1;
    _killCount = 0;
    _gameOver = false;
    _spawnTimer = 0;
    children.whereType<Enemy>().toList().forEach((e) => e.removeFromParent());
    children.whereType<Powerup>().toList().forEach((p) => p.removeFromParent());
    children.whereType<ExplosionComponent>().toList()
        .forEach((e) => e.removeFromParent());
    player.reset();
    resumeEngine();
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


# ---------------------------------------------------------------------------
# lib/game/player.dart
# ---------------------------------------------------------------------------

def _player_dart(name: str) -> str:
    return f"""\
import 'package:flame/collisions.dart';
import 'package:flame/components.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'game.dart';
import 'enemy.dart';
import 'powerup.dart';

/// Player ship.  Tries to load a sprite from assets/imported/player.png;
/// falls back to a blue rectangle when the file does not exist.
class Player extends PositionComponent with CollisionCallbacks {{
  final {name}Game game;

  static const double _speed = 200;
  static const double _baseCooldown = 0.25;

  double _shootTimer = 0;
  final Vector2 _keyDir = Vector2.zero();

  // Power-up state
  bool hasShield = false;
  bool rapidFireActive = false;
  double _rapidFireTimer = 0;
  static const double _rapidFireDuration = 5.0;

  double get _shootCooldown =>
      rapidFireActive ? _baseCooldown / 3 : _baseCooldown;

  // Visuals
  Sprite? _sprite;
  final Paint _bodyPaint = Paint()..color = Colors.blue;
  final Paint _shieldPaint = Paint()
    ..color = Colors.cyanAccent.withOpacity(0.45)
    ..style = PaintingStyle.stroke
    ..strokeWidth = 3;

  Player({{required this.game}}) : super(size: Vector2(48, 48));

  @override
  Future<void> onLoad() async {{
    try {{
      _sprite = await game.loadSprite('imported/player.png');
    }} catch (_) {{
      // no sprite file – will render colored shape
    }}
    position = Vector2(game.size.x / 2 - 24, game.size.y - 80);
    add(RectangleHitbox());
  }}

  @override
  void render(Canvas canvas) {{
    if (_sprite != null) {{
      _sprite!.render(canvas, size: size);
    }} else {{
      // Triangle pointing upward
      final path = Path()
        ..moveTo(size.x / 2, 0)
        ..lineTo(size.x, size.y)
        ..lineTo(0, size.y)
        ..close();
      canvas.drawPath(path, _bodyPaint);
    }}
    if (hasShield) {{
      canvas.drawOval(
        Rect.fromCenter(
            center: Offset(size.x / 2, size.y / 2),
            width: size.x + 10,
            height: size.y + 10),
        _shieldPaint,
      );
    }}
    super.render(canvas);
  }}

  void handleKeys(Set<LogicalKeyboardKey> keys) {{
    _keyDir.setZero();
    if (keys.contains(LogicalKeyboardKey.arrowLeft) ||
        keys.contains(LogicalKeyboardKey.keyA)) _keyDir.x -= 1;
    if (keys.contains(LogicalKeyboardKey.arrowRight) ||
        keys.contains(LogicalKeyboardKey.keyD)) _keyDir.x += 1;
    if (keys.contains(LogicalKeyboardKey.arrowUp) ||
        keys.contains(LogicalKeyboardKey.keyW)) _keyDir.y -= 1;
    if (keys.contains(LogicalKeyboardKey.arrowDown) ||
        keys.contains(LogicalKeyboardKey.keyS)) _keyDir.y += 1;
  }}

  void shoot() {{
    if (_shootTimer <= 0) {{
      game.bulletPool.fire(
        position: Vector2(position.x + size.x / 2 - 3, position.y),
        direction: Vector2(0, -1),
      );
      _shootTimer = _shootCooldown;
    }}
  }}

  void applyRapidFire() {{
    rapidFireActive = true;
    _rapidFireTimer = _rapidFireDuration;
  }}

  void applyShield() => hasShield = true;

  void reset() {{
    position = Vector2(game.size.x / 2 - 24, game.size.y - 80);
    hasShield = false;
    rapidFireActive = false;
    _rapidFireTimer = 0;
    _shootTimer = 0;
    _keyDir.setZero();
  }}

  @override
  void update(double dt) {{
    super.update(dt);
    if (_shootTimer > 0) _shootTimer -= dt;
    if (rapidFireActive) {{
      _rapidFireTimer -= dt;
      if (_rapidFireTimer <= 0) rapidFireActive = false;
    }}
    final jd = game.joystick.relativeDelta;
    if (_keyDir.length2 > 0) {{
      position.addScaled(_keyDir.normalized(), _speed * dt);
    }} else if (jd.length2 > 0) {{
      position.addScaled(jd, _speed * dt);
    }}
    position.x = position.x.clamp(0, game.size.x - size.x);
    position.y = position.y.clamp(0, game.size.y - size.y);
  }}

  @override
  void onCollisionStart(
      Set<Vector2> intersectionPoints, PositionComponent other) {{
    if (other is Enemy) {{
      if (hasShield) {{
        hasShield = false;
        other.removeFromParent();
        return;
      }}
      game.triggerGameOver();
    }}
  }}
}}
"""


# ---------------------------------------------------------------------------
# lib/game/enemy.dart
# ---------------------------------------------------------------------------

def _enemy_dart(name: str) -> str:
    return f"""\
import 'package:flame/collisions.dart';
import 'package:flame/components.dart';
import 'package:flutter/material.dart';
import 'game.dart';

/// Enemy ship.  HP and speed scale with the current wave number.
/// Falls back to a red rectangle when no sprite is found.
class Enemy extends PositionComponent with CollisionCallbacks {{
  final {name}Game game;
  final int wave;

  late int hp;
  late int maxHp;
  late double _speed;

  Sprite? _sprite;

  Enemy({{
    required this.game,
    required Vector2 position,
    required this.wave,
  }}) : super(size: Vector2(48, 48), position: position);

  @override
  Future<void> onLoad() async {{
    maxHp = 1 + wave;
    hp = maxHp;
    _speed = (80 + wave * 12).toDouble();
    try {{
      _sprite = await game.loadSprite('imported/enemy.png');
    }} catch (_) {{
      // fallback: drawn in render()
    }}
    add(RectangleHitbox());
  }}

  @override
  void render(Canvas canvas) {{
    if (_sprite != null) {{
      _sprite!.render(canvas, size: size);
    }} else {{
      final progress = maxHp > 0 ? hp / maxHp : 1.0;
      final color = Color.lerp(Colors.orange, Colors.red, 1 - progress)!;
      canvas.drawRect(size.toRect(), Paint()..color = color);
    }}
    // Health bar (shown when HP > 1)
    if (maxHp > 1) {{
      final barW = size.x;
      final barH = 4.0;
      final ratio = hp / maxHp;
      canvas.drawRect(
        Rect.fromLTWH(0, -6, barW, barH),
        Paint()..color = Colors.grey.shade800,
      );
      canvas.drawRect(
        Rect.fromLTWH(0, -6, barW * ratio, barH),
        Paint()..color = Colors.greenAccent,
      );
    }}
    super.render(canvas);
  }}

  void takeDamage(int amount) {{
    hp -= amount;
    if (hp <= 0) {{
      game.onEnemyKilled(position + size / 2);
      removeFromParent();
    }}
  }}

  @override
  void update(double dt) {{
    super.update(dt);
    position.y += _speed * dt;
    if (position.y > game.size.y + size.y) removeFromParent();
  }}
}}
"""


# ---------------------------------------------------------------------------
# lib/game/bullet.dart
# ---------------------------------------------------------------------------

def _bullet_dart(name: str) -> str:
    return f"""\
import 'package:flame/collisions.dart';
import 'package:flame/components.dart';
import 'package:flutter/material.dart';
import 'enemy.dart';
import 'game.dart';

/// Bullet.  Falls back to a yellow rectangle when no sprite is found.
class Bullet extends PositionComponent with CollisionCallbacks {{
  final {name}Game game;
  final Vector2 direction;

  static const double _speed = 420;
  bool active = false;

  Sprite? _sprite;
  final Paint _paint = Paint()..color = Colors.yellowAccent;

  Bullet({{required this.game}})
      : direction = Vector2(0, -1),
        super(size: Vector2(6, 14));

  @override
  Future<void> onLoad() async {{
    try {{
      _sprite = await game.loadSprite('imported/bullet.png');
    }} catch (_) {{
      // fallback colored rect
    }}
    add(RectangleHitbox());
  }}

  @override
  void render(Canvas canvas) {{
    if (_sprite != null) {{
      _sprite!.render(canvas, size: size);
    }} else {{
      canvas.drawRect(size.toRect(), _paint);
    }}
    super.render(canvas);
  }}

  @override
  void update(double dt) {{
    if (!active) return;
    super.update(dt);
    position.addScaled(direction, _speed * dt);
    if (position.y < -size.y) deactivate();
  }}

  void activate(Vector2 pos, Vector2 dir) {{
    position.setFrom(pos);
    direction.setFrom(dir.normalized());
    active = true;
  }}

  void deactivate() {{
    active = false;
    position.setValues(-2000, -2000);
  }}

  @override
  void onCollisionStart(
      Set<Vector2> intersectionPoints, PositionComponent other) {{
    if (other is Enemy) {{
      other.takeDamage(1);
      deactivate();
    }}
  }}
}}
"""


# ---------------------------------------------------------------------------
# lib/game/bullet_pool.dart  (unchanged logic, updated import)
# ---------------------------------------------------------------------------

def _bullet_pool_dart(name: str) -> str:
    return f"""\
import 'package:flame/components.dart';
import 'bullet.dart';
import 'game.dart';

/// Object pool for bullets – avoids per-shot allocations.
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

  void fire({{required Vector2 position, required Vector2 direction}}) {{
    for (final b in _pool) {{
      if (!b.active) {{
        b.activate(position, direction);
        return;
      }}
    }}
    // Pool exhausted – silently skip
  }}
}}
"""


# ---------------------------------------------------------------------------
# lib/game/powerup.dart
# ---------------------------------------------------------------------------

def _powerup_dart(name: str) -> str:
    return f"""\
import 'package:flame/collisions.dart';
import 'package:flame/components.dart';
import 'package:flutter/material.dart';
import 'game.dart';
import 'player.dart';

enum PowerupType {{ rapidFire, shield }}

/// Falling powerup pickup.  Drawn as a coloured circle with an icon.
class Powerup extends PositionComponent with CollisionCallbacks {{
  final {name}Game game;
  final PowerupType type;

  static const double _fallSpeed = 70;

  Powerup({{
    required this.game,
    required Vector2 position,
    required this.type,
  }}) : super(size: Vector2(28, 28), position: position);

  Color get _color =>
      type == PowerupType.rapidFire ? Colors.orange : Colors.cyanAccent;

  @override
  Future<void> onLoad() async {{
    add(CircleHitbox());
  }}

  @override
  void render(Canvas canvas) {{
    canvas.drawCircle(
      Offset(size.x / 2, size.y / 2),
      size.x / 2,
      Paint()..color = _color.withOpacity(0.88),
    );
    // Inner symbol
    final tp = TextPaint(
      style: TextStyle(
        fontSize: 14,
        color: Colors.black.withOpacity(0.85),
        fontWeight: FontWeight.bold,
      ),
    );
    tp.render(
      canvas,
      type == PowerupType.rapidFire ? '⚡' : '🛡',
      Vector2(size.x / 2 - 7, size.y / 2 - 9),
    );
    super.render(canvas);
  }}

  @override
  void update(double dt) {{
    super.update(dt);
    position.y += _fallSpeed * dt;
    if (position.y > game.size.y + size.y) removeFromParent();
  }}

  @override
  void onCollisionStart(
      Set<Vector2> intersectionPoints, PositionComponent other) {{
    if (other is Player) {{
      if (type == PowerupType.rapidFire) {{
        other.applyRapidFire();
      }} else {{
        other.applyShield();
      }}
      removeFromParent();
    }}
  }}
}}
"""


# ---------------------------------------------------------------------------
# lib/game/explosion.dart
# ---------------------------------------------------------------------------

def _explosion_dart() -> str:
    return """\
import 'package:flame/components.dart';
import 'package:flutter/material.dart';

/// Expanding + fading circle played at the position an enemy was destroyed.
class ExplosionComponent extends PositionComponent {
  static const double _maxRadius = 38;
  static const double _duration = 0.35;

  double _elapsed = 0;

  ExplosionComponent({required Vector2 position})
      : super(position: position);

  @override
  void render(Canvas canvas) {
    final progress = (_elapsed / _duration).clamp(0.0, 1.0);
    final radius = _maxRadius * progress;
    final opacity = (1 - progress) * 0.85;
    canvas.drawCircle(
      Offset.zero,
      radius,
      Paint()..color = Colors.orange.withOpacity(opacity),
    );
    canvas.drawCircle(
      Offset.zero,
      radius * 0.55,
      Paint()..color = Colors.yellow.withOpacity(opacity * 0.7),
    );
  }

  @override
  void update(double dt) {
    super.update(dt);
    _elapsed += dt;
    if (_elapsed >= _duration) removeFromParent();
  }
}
"""


# ---------------------------------------------------------------------------
# lib/game/hud.dart
# ---------------------------------------------------------------------------

def _hud_dart(name: str) -> str:
    return f"""\
import 'package:flame/components.dart';
import 'package:flutter/material.dart';
import 'game.dart';

class Hud extends TextComponent with HasGameRef<{name}Game> {{
  Hud({{required {name}Game game}})
      : super(
          text: 'Score: 0  Wave: 1',
          textRenderer: TextPaint(
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
              shadows: [
                Shadow(
                    color: Colors.black,
                    offset: Offset(1, 1),
                    blurRadius: 2),
              ],
            ),
          ),
          position: Vector2(8, 8),
        );

  @override
  void update(double dt) {{
    super.update(dt);
    text = 'Score: ${{gameRef.score}}  Wave: ${{gameRef.wave}}';
  }}
}}
"""


# ---------------------------------------------------------------------------
# lib/game/mobile_controls.dart  (unchanged)
# ---------------------------------------------------------------------------

def _mobile_controls_dart(name: str) -> str:
    return f"""\
import 'package:flame/components.dart';
import 'package:flame/input.dart';
import 'package:flutter/material.dart';
import 'game.dart';

class MobileControls extends Component {{
  final {name}Game game;
  late final JoystickComponent joystick;

  MobileControls({{required this.game}});

  @override
  Future<void> onLoad() async {{
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


# ---------------------------------------------------------------------------
# lib/game/game_over_overlay.dart
# ---------------------------------------------------------------------------

def _game_over_overlay_dart(name: str) -> str:
    return f"""\
import 'package:flutter/material.dart';
import 'game.dart';

class GameOverOverlay extends StatelessWidget {{
  final {name}Game game;

  const GameOverOverlay({{required this.game, super.key}});

  @override
  Widget build(BuildContext context) {{
    final highScore = game.saveManager.highScore;
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 36, vertical: 28),
          margin: const EdgeInsets.symmetric(horizontal: 28),
          decoration: BoxDecoration(
            color: const Color(0xFF1a1a2e),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.redAccent, width: 2),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'GAME OVER',
                style: TextStyle(
                  color: Colors.redAccent,
                  fontSize: 38,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 3,
                ),
              ),
              const SizedBox(height: 14),
              Text(
                'Score: ${{game.score}}',
                style: const TextStyle(color: Colors.white, fontSize: 24),
              ),
              const SizedBox(height: 4),
              Text(
                'Best: $highScore',
                style: const TextStyle(color: Colors.amber, fontSize: 20),
              ),
              Text(
                'Wave reached: ${{game.wave}}',
                style: const TextStyle(
                    color: Colors.white54, fontSize: 15),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 22, vertical: 12),
                      textStyle: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    onPressed: game.restart,
                    child: const Text('▶  Play Again'),
                  ),
                  const SizedBox(width: 14),
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white70,
                      side: const BorderSide(color: Colors.white30),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 22, vertical: 12),
                      textStyle: const TextStyle(fontSize: 16),
                    ),
                    onPressed: () {{
                      game.overlays.remove('GameOver');
                      game.onReturnToMenu?.call();
                    }},
                    child: const Text('Menu'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }}
}}
"""


# ---------------------------------------------------------------------------
# lib/game/save_manager.dart
# ---------------------------------------------------------------------------

def _save_manager_dart() -> str:
    return """\
import 'package:shared_preferences/shared_preferences.dart';

/// Persists high score between sessions.
class SaveManager {
  int highScore = 0;

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    highScore = prefs.getInt('high_score') ?? 0;
  }

  Future<void> save({required int score}) async {
    final prefs = await SharedPreferences.getInstance();
    if (score > highScore) {
      highScore = score;
      await prefs.setInt('high_score', score);
    }
  }

  Future<void> reset() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('high_score');
    highScore = 0;
  }
}
"""

