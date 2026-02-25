"""
idle_rpg.py – Code generator for the idle RPG genre.

Produces a complete, multi-file Flutter/Flame project sub-tree for an
idle RPG / incremental game.  Components auto-battle on a timer;
the player taps to add bonus damage.

When the spec contains a ``design_doc_data`` key (a dict produced by
``game_generator.ai.design_assistant.generate_idle_rpg_design``), the
generator also writes:
  - ``assets/data/quests.json``
  - ``assets/data/characters.json``
  - ``assets/data/items.json``      (if items list is present)
  - ``assets/data/locations.json``  (if locations list is present)
and wires three Flutter UI screens into a bottom-navigation main.dart:
  - ``lib/screens/quest_log_screen.dart``
  - ``lib/screens/characters_screen.dart``
  - ``lib/screens/shop_screen.dart``
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ..spec import GameSpec


def generate_files(spec: GameSpec) -> Dict[str, str]:
    """Return a dict of {relative_path: file_content} for the idle RPG."""
    title = spec.get("title", "Idle RPG")
    safe_name = _safe_class_name(title)
    design_doc: Optional[Dict[str, Any]] = spec.get("design_doc_data")

    files: Dict[str, str] = {}

    # Core Flame game files
    files["lib/game/game.dart"] = _game_dart(safe_name)
    files["lib/game/hero.dart"] = _hero_dart(safe_name)
    files["lib/game/enemy.dart"] = _enemy_dart(safe_name)
    files["lib/game/idle_manager.dart"] = _idle_manager_dart(safe_name)
    files["lib/game/hud.dart"] = _hud_dart(safe_name)
    files["lib/game/upgrade_overlay.dart"] = _upgrade_overlay_dart(safe_name)

    # JSON data files (always generated; populated from design doc when available)
    files["assets/data/quests.json"] = _quests_json(design_doc)
    files["assets/data/characters.json"] = _characters_json(design_doc)
    if design_doc is None or design_doc.get("items"):
        files["assets/data/items.json"] = _items_json(design_doc)
    if design_doc is None or design_doc.get("locations"):
        files["assets/data/locations.json"] = _locations_json(design_doc)

    # Flutter UI screens
    files["lib/screens/quest_log_screen.dart"] = _quest_log_screen_dart(title)
    files["lib/screens/characters_screen.dart"] = _characters_screen_dart(title)
    files["lib/screens/shop_screen.dart"] = _shop_screen_dart(title)

    # Custom main.dart with bottom-navigation layout
    orientation = spec.get("orientation", "portrait")
    files["lib/main.dart"] = _main_dart_with_nav(safe_name, title, orientation)

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


# ---------------------------------------------------------------------------
# JSON data file generators
# ---------------------------------------------------------------------------

_DEFAULT_QUESTS: List[Dict[str, Any]] = [
    {
        "title": "First Steps",
        "summary": "Begin your adventure by defeating your first enemies.",
        "giver": "Village Elder",
        "level_range": [1, 3],
        "objectives": ["Defeat 5 enemies", "Collect 50 gold"],
        "rewards": ["50 gold", "10 XP"],
    },
    {
        "title": "The Iron Trial",
        "summary": "Prove your worth against stronger foes.",
        "giver": "Guild Master",
        "level_range": [4, 8],
        "objectives": ["Defeat 10 elite enemies", "Survive 5 waves"],
        "rewards": ["200 gold", "50 XP", "Iron Amulet"],
    },
]

_DEFAULT_CHARACTERS: List[Dict[str, Any]] = [
    {
        "name": "Aela",
        "role": "Hero",
        "backstory": "A determined warrior seeking redemption.",
        "motivations": ["Protect the innocent", "Grow stronger"],
    },
    {
        "name": "Elder Mira",
        "role": "NPC",
        "backstory": "The wise keeper of ancient knowledge.",
        "motivations": ["Guide young heroes", "Preserve history"],
    },
]

_DEFAULT_ITEMS: List[Dict[str, Any]] = [
    {
        "name": "Iron Sword",
        "type": "weapon",
        "rarity": "common",
        "description": "A reliable iron sword for beginners.",
        "stats": {"attack": 5},
    },
    {
        "name": "Leather Armor",
        "type": "armor",
        "rarity": "common",
        "description": "Basic protection against attacks.",
        "stats": {"defense": 3},
    },
]

_DEFAULT_LOCATIONS: List[Dict[str, Any]] = [
    {
        "name": "Starter Village",
        "type": "town",
        "description": "A peaceful village to begin your adventure.",
        "notable_features": ["Blacksmith", "Inn", "Quest Board"],
    },
    {
        "name": "Dark Forest",
        "type": "dungeon",
        "description": "A dangerous forest filled with lurking monsters.",
        "notable_features": ["Hidden Shrine", "Bandit Camp"],
    },
]


def _quests_json(design_doc: Optional[Dict[str, Any]]) -> str:
    quests = (design_doc.get("quests") or []) if design_doc else _DEFAULT_QUESTS
    if not quests:
        quests = _DEFAULT_QUESTS
    return json.dumps(quests, indent=2)


def _characters_json(design_doc: Optional[Dict[str, Any]]) -> str:
    characters = (design_doc.get("characters") or []) if design_doc else _DEFAULT_CHARACTERS
    if not characters:
        characters = _DEFAULT_CHARACTERS
    return json.dumps(characters, indent=2)


def _items_json(design_doc: Optional[Dict[str, Any]]) -> str:
    items = (design_doc.get("items") or []) if design_doc else _DEFAULT_ITEMS
    if not items:
        items = _DEFAULT_ITEMS
    return json.dumps(items, indent=2)


def _locations_json(design_doc: Optional[Dict[str, Any]]) -> str:
    locations = (design_doc.get("locations") or []) if design_doc else _DEFAULT_LOCATIONS
    if not locations:
        locations = _DEFAULT_LOCATIONS
    return json.dumps(locations, indent=2)


# ---------------------------------------------------------------------------
# Flutter UI screen generators
# ---------------------------------------------------------------------------


def _quest_log_screen_dart(title: str) -> str:
    return f"""\
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Displays the quest log loaded from assets/data/quests.json.
class QuestLogScreen extends StatefulWidget {{
  const QuestLogScreen({{super.key}});

  @override
  State<QuestLogScreen> createState() => _QuestLogScreenState();
}}

class _QuestLogScreenState extends State<QuestLogScreen> {{
  List<Map<String, dynamic>> _quests = [];
  bool _loading = true;

  @override
  void initState() {{
    super.initState();
    _loadQuests();
  }}

  Future<void> _loadQuests() async {{
    final str = await rootBundle.loadString('assets/data/quests.json');
    final list = jsonDecode(str) as List;
    setState(() {{
      _quests = list.cast<Map<String, dynamic>>();
      _loading = false;
    }});
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('Quest Log'),
        backgroundColor: Colors.black,
        foregroundColor: Colors.amber,
      ),
      backgroundColor: Colors.grey[900],
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Colors.amber))
          : _quests.isEmpty
              ? const Center(
                  child: Text('No quests found.',
                      style: TextStyle(color: Colors.white54)))
              : ListView.builder(
                  itemCount: _quests.length,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemBuilder: (context, index) {{
                    final q = _quests[index];
                    final lr = (q['level_range'] as List?)
                        ?.map((e) => e.toString())
                        .join('–');
                    return Card(
                      color: Colors.grey[800],
                      margin: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 6),
                      child: ListTile(
                        title: Text(
                          q['title'] as String? ?? '',
                          style: const TextStyle(
                              color: Colors.amber,
                              fontWeight: FontWeight.bold),
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              q['summary'] as String? ?? '',
                              style:
                                  const TextStyle(color: Colors.white70),
                            ),
                            if (q['giver'] != null)
                              Text('Giver: ${{q['giver']}}',
                                  style: const TextStyle(
                                      color: Colors.white38,
                                      fontSize: 12)),
                          ],
                        ),
                        trailing: lr != null
                            ? Text('Lv. $lr',
                                style: const TextStyle(
                                    color: Colors.white54))
                            : null,
                        isThreeLine: q['giver'] != null,
                      ),
                    );
                  }},
                ),
    );
  }}
}}
"""


def _characters_screen_dart(title: str) -> str:
    return f"""\
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Displays the character roster loaded from assets/data/characters.json.
class CharactersScreen extends StatefulWidget {{
  const CharactersScreen({{super.key}});

  @override
  State<CharactersScreen> createState() => _CharactersScreenState();
}}

class _CharactersScreenState extends State<CharactersScreen> {{
  List<Map<String, dynamic>> _characters = [];
  bool _loading = true;

  @override
  void initState() {{
    super.initState();
    _loadCharacters();
  }}

  Future<void> _loadCharacters() async {{
    final str = await rootBundle.loadString('assets/data/characters.json');
    final list = jsonDecode(str) as List;
    setState(() {{
      _characters = list.cast<Map<String, dynamic>>();
      _loading = false;
    }});
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('Characters'),
        backgroundColor: Colors.black,
        foregroundColor: Colors.amber,
      ),
      backgroundColor: Colors.grey[900],
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Colors.amber))
          : _characters.isEmpty
              ? const Center(
                  child: Text('No characters found.',
                      style: TextStyle(color: Colors.white54)))
              : ListView.builder(
                  itemCount: _characters.length,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemBuilder: (context, index) {{
                    final c = _characters[index];
                    final motivations =
                        (c['motivations'] as List?)?.join(', ') ?? '';
                    return Card(
                      color: Colors.grey[800],
                      margin: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 6),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: Colors.amber,
                          child: Text(
                            (c['name'] as String? ?? '?')[0],
                            style: const TextStyle(
                                color: Colors.black,
                                fontWeight: FontWeight.bold),
                          ),
                        ),
                        title: Text(
                          c['name'] as String? ?? '',
                          style: const TextStyle(
                              color: Colors.amber,
                              fontWeight: FontWeight.bold),
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Role: ${{c['role'] ?? ''}}',
                              style: const TextStyle(color: Colors.white70),
                            ),
                            if (c['backstory'] != null)
                              Text(
                                c['backstory'] as String,
                                style: const TextStyle(
                                    color: Colors.white54,
                                    fontSize: 12),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            if (motivations.isNotEmpty)
                              Text(
                                'Motivations: $motivations',
                                style: const TextStyle(
                                    color: Colors.white38,
                                    fontSize: 11),
                              ),
                          ],
                        ),
                        isThreeLine: true,
                      ),
                    );
                  }},
                ),
    );
  }}
}}
"""


def _shop_screen_dart(title: str) -> str:
    return f"""\
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Displays the item shop loaded from assets/data/items.json.
class ShopScreen extends StatefulWidget {{
  const ShopScreen({{super.key}});

  @override
  State<ShopScreen> createState() => _ShopScreenState();
}}

class _ShopScreenState extends State<ShopScreen> {{
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;

  @override
  void initState() {{
    super.initState();
    _loadItems();
  }}

  Future<void> _loadItems() async {{
    final str = await rootBundle.loadString('assets/data/items.json');
    final list = jsonDecode(str) as List;
    setState(() {{
      _items = list.cast<Map<String, dynamic>>();
      _loading = false;
    }});
  }}

  Color _rarityColor(String? rarity) {{
    switch (rarity?.toLowerCase()) {{
      case 'rare':
        return Colors.blue;
      case 'epic':
        return Colors.purple;
      case 'legendary':
        return Colors.orange;
      default:
        return Colors.white54;
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('Shop'),
        backgroundColor: Colors.black,
        foregroundColor: Colors.amber,
      ),
      backgroundColor: Colors.grey[900],
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Colors.amber))
          : _items.isEmpty
              ? const Center(
                  child: Text('No items available.',
                      style: TextStyle(color: Colors.white54)))
              : ListView.builder(
                  itemCount: _items.length,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemBuilder: (context, index) {{
                    final item = _items[index];
                    final rarity = item['rarity'] as String?;
                    final stats = item['stats'] as Map<String, dynamic>?;
                    final statsStr = stats?.entries
                            .map((e) => '${{e.key}}: ${{e.value}}')
                            .join(', ') ??
                        '';
                    return Card(
                      color: Colors.grey[800],
                      margin: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 6),
                      child: ListTile(
                        leading: Icon(
                          item['type'] == 'weapon'
                              ? Icons.security
                              : Icons.shield,
                          color: Colors.amber,
                        ),
                        title: Text(
                          item['name'] as String? ?? '',
                          style: const TextStyle(
                              color: Colors.amber,
                              fontWeight: FontWeight.bold),
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              item['description'] as String? ?? '',
                              style: const TextStyle(color: Colors.white70),
                            ),
                            if (statsStr.isNotEmpty)
                              Text('Stats: $statsStr',
                                  style: const TextStyle(
                                      color: Colors.white54,
                                      fontSize: 12)),
                          ],
                        ),
                        trailing: rarity != null
                            ? Text(
                                rarity,
                                style: TextStyle(
                                    color: _rarityColor(rarity),
                                    fontWeight: FontWeight.bold),
                              )
                            : null,
                        isThreeLine: statsStr.isNotEmpty,
                      ),
                    );
                  }},
                ),
    );
  }}
}}
"""


# ---------------------------------------------------------------------------
# main.dart with bottom-navigation layout
# ---------------------------------------------------------------------------


def _main_dart_with_nav(name: str, title: str, orientation: str) -> str:
    if orientation == "landscape":
        orient_values = (
            "DeviceOrientation.landscapeLeft,\n"
            "    DeviceOrientation.landscapeRight,"
        )
    else:
        orient_values = (
            "DeviceOrientation.portraitUp,\n"
            "    DeviceOrientation.portraitDown,"
        )
    return f"""\
import 'package:flame/game.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'game/game.dart';
import 'screens/quest_log_screen.dart';
import 'screens/characters_screen.dart';
import 'screens/shop_screen.dart';

void main() async {{
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([
    {orient_values}
  ]);
  runApp(const {name}App());
}}

class {name}App extends StatefulWidget {{
  const {name}App({{super.key}});

  @override
  State<{name}App> createState() => _{name}AppState();
}}

class _{name}AppState extends State<{name}App> {{
  int _selectedIndex = 0;

  late final List<Widget> _screens;

  @override
  void initState() {{
    super.initState();
    _screens = [
      GameWidget<{name}Game>(
        game: {name}Game(),
        loadingBuilder: (context) =>
            const Center(child: CircularProgressIndicator(color: Colors.amber)),
      ),
      const QuestLogScreen(),
      const CharactersScreen(),
      const ShopScreen(),
    ];
  }}

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{title}',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark(),
      home: Scaffold(
        backgroundColor: Colors.black,
        body: IndexedStack(
          index: _selectedIndex,
          children: _screens,
        ),
        bottomNavigationBar: BottomNavigationBar(
          backgroundColor: Colors.black,
          selectedItemColor: Colors.amber,
          unselectedItemColor: Colors.white38,
          currentIndex: _selectedIndex,
          onTap: (i) => setState(() => _selectedIndex = i),
          items: const [
            BottomNavigationBarItem(
                icon: Icon(Icons.videogame_asset), label: 'Battle'),
            BottomNavigationBarItem(
                icon: Icon(Icons.assignment), label: 'Quests'),
            BottomNavigationBarItem(
                icon: Icon(Icons.people), label: 'Heroes'),
            BottomNavigationBarItem(
                icon: Icon(Icons.store), label: 'Shop'),
          ],
        ),
      ),
    );
  }}
}}
"""
