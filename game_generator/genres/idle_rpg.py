"""
idle_rpg.py – Code generator for the idle RPG genre.

Produces a complete, multi-file Flutter/Flame project sub-tree for an
idle RPG / incremental game.  Components auto-battle on a timer;
the player taps to add bonus damage.
"""

from __future__ import annotations

from typing import Dict

from ..spec import GameSpec


def generate_files(spec: GameSpec) -> Dict[str, str]:
    """Return a dict of {relative_path: file_content} for the idle RPG."""
    title = spec.get("title", "Idle RPG")
    safe_name = _safe_class_name(title)

    files: Dict[str, str] = {}
    files["lib/game/game.dart"] = _game_dart(safe_name)
    files["lib/game/hero.dart"] = _hero_dart(safe_name)
    files["lib/game/enemy.dart"] = _enemy_dart(safe_name)
    files["lib/game/idle_manager.dart"] = _idle_manager_dart(safe_name)
    files["lib/game/hud.dart"] = _hud_dart(safe_name)
    files["lib/game/upgrade_overlay.dart"] = _upgrade_overlay_dart(safe_name)
    return files


def _safe_class_name(title: str) -> str:
    words = "".join(ch if ch.isalnum() or ch == " " else " " for ch in title).split()
    return "".join(w.capitalize() for w in words) if words else "MyGame"


def _game_dart(name: str) -> str:
    return f"""\
import 'package:flame/game.dart';
import 'package:flame/input.dart';
import 'package:flutter/material.dart';
import 'hero.dart';
import 'enemy.dart';
import 'idle_manager.dart';
import 'hud.dart';
import 'upgrade_overlay.dart';

class {name}Game extends FlameGame with TapCallbacks {{
  // Game state
  int gold = 0;
  int wave = 1;
  bool _gameOver = false;

  late final GameHero hero;
  late final GameEnemy enemy;
  late final IdleManager idleManager;

  @override
  Future<void> onLoad() async {{
    await super.onLoad();

    // Background
    final bgSprite = await loadSprite('imported/background.png');
    add(SpriteComponent(sprite: bgSprite, size: size));

    // Hero
    hero = GameHero(game: this);
    await hero.onLoad();
    add(hero);

    // Enemy
    enemy = GameEnemy(game: this, wave: wave);
    await enemy.onLoad();
    add(enemy);

    // Idle auto-battle manager
    idleManager = IdleManager(game: this);
    add(idleManager);

    // HUD
    add(Hud(game: this));

    overlays.addEntry(
      'Upgrade',
      (context, game) => UpgradeOverlay(game: game as {name}Game),
    );
  }}

  /// Called when the player taps the screen (bonus damage).
  @override
  void onTapDown(TapDownEvent event) {{
    if (_gameOver) return;
    hero.attack(enemy, bonus: hero.tapDamage);
    checkEnemyDead();
  }}

  void checkEnemyDead() {{
    if (enemy.hp <= 0) {{
      gold += wave * 10;
      wave++;
      _respawnEnemy();
      overlays.add('Upgrade');
    }}
  }}

  void _respawnEnemy() {{
    enemy.removeFromParent();
    enemy = GameEnemy(game: this, wave: wave);
    enemy.onLoad().then((_) => add(enemy));
  }}
}}
"""


def _hero_dart(name: str) -> str:
    return f"""\
import 'package:flame/components.dart';
import 'enemy.dart';
import 'game.dart';

class GameHero extends SpriteComponent {{
  final {name}Game game;

  int level = 1;
  int attackPower = 10;
  int tapDamage = 5;

  GameHero({{required this.game}}) : super(size: Vector2(64, 64));

  @override
  Future<void> onLoad() async {{
    sprite = await game.loadSprite('imported/hero.png');
    position = Vector2(game.size.x * 0.25 - 32, game.size.y * 0.5 - 32);
  }}

  void attack(GameEnemy target, {{int bonus = 0}}) {{
    target.takeDamage(attackPower + bonus);
  }}

  void levelUp() {{
    level++;
    attackPower = (attackPower * 1.5).round();
    tapDamage = (tapDamage * 1.3).round();
  }}
}}
"""


def _enemy_dart(name: str) -> str:
    return f"""\
import 'package:flame/components.dart';
import 'game.dart';

class GameEnemy extends SpriteComponent {{
  final {name}Game game;
  final int wave;

  late int maxHp;
  late int hp;

  GameEnemy({{required this.game, required this.wave}})
      : super(size: Vector2(64, 64));

  @override
  Future<void> onLoad() async {{
    sprite = await game.loadSprite('imported/enemy.png');
    position = Vector2(game.size.x * 0.65 - 32, game.size.y * 0.5 - 32);
    maxHp = 50 + wave * 20;
    hp = maxHp;
  }}

  void takeDamage(int amount) {{
    hp = (hp - amount).clamp(0, maxHp);
  }}
}}
"""


def _idle_manager_dart(name: str) -> str:
    return f"""\
import 'package:flame/components.dart';
import 'game.dart';

/// Automatically attacks the current enemy on a fixed interval.
class IdleManager extends Component {{
  final {name}Game game;

  static const double _attackInterval = 1.0;
  double _timer = 0;

  IdleManager({{required this.game}});

  @override
  void update(double dt) {{
    _timer += dt;
    if (_timer >= _attackInterval) {{
      _timer = 0;
      _autoAttack();
    }}
  }}

  void _autoAttack() {{
    game.hero.attack(game.enemy);
    game.checkEnemyDead();
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
          text: 'Gold: 0  Wave: 1',
          textRenderer: TextPaint(
            style: const TextStyle(
              color: Colors.amber,
              fontSize: 20,
            ),
          ),
        );

  @override
  void update(double dt) {{
    super.update(dt);
    text = 'Gold: ${{gameRef.gold}}  Wave: ${{gameRef.wave}}';
  }}
}}
"""


def _upgrade_overlay_dart(name: str) -> str:
    return f"""\
import 'package:flutter/material.dart';
import 'game.dart';

class UpgradeOverlay extends StatelessWidget {{
  final {name}Game game;

  const UpgradeOverlay({{required this.game, super.key}});

  @override
  Widget build(BuildContext context) {{
    return Center(
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: Colors.black87,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Wave ${{game.wave - 1}} Complete!',
              style: const TextStyle(
                color: Colors.amber,
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'Gold: ${{game.gold}}',
              style: const TextStyle(color: Colors.white, fontSize: 20),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {{
                game.hero.levelUp();
                game.overlays.remove('Upgrade');
              }},
              child: Text(
                'Level Up Hero (Lv.${{game.hero.level + 1}})',
              ),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => game.overlays.remove('Upgrade'),
              child: const Text(
                'Continue',
                style: TextStyle(color: Colors.white70),
              ),
            ),
          ],
        ),
      ),
    );
  }}
}}
"""
