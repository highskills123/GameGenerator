"""
level_generation.py – Procedural level / map generation utilities.

Fully deterministic (seed-based), no external dependencies beyond stdlib.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Room:
    id: int
    x: int
    y: int
    width: int
    height: int
    room_type: str = "normal"  # "normal" | "start" | "end" | "boss" | "treasure"

    @property
    def center(self) -> Tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2

    def overlaps(self, other: "Room", padding: int = 1) -> bool:
        return (
            self.x - padding < other.x + other.width
            and self.x + self.width + padding > other.x
            and self.y - padding < other.y + other.height
            and self.y + self.height + padding > other.y
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "room_type": self.room_type,
            "center": list(self.center),
        }


@dataclass
class Corridor:
    from_room: int
    to_room: int
    path: List[Tuple[int, int]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "from_room": self.from_room,
            "to_room": self.to_room,
            "path": [list(p) for p in self.path],
        }


@dataclass
class Level:
    width: int
    height: int
    rooms: List[Room] = field(default_factory=list)
    corridors: List[Corridor] = field(default_factory=list)
    tile_map: List[List[str]] = field(default_factory=list)
    seed: int = 0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "width": self.width,
            "height": self.height,
            "metadata": self.metadata,
            "rooms": [r.to_dict() for r in self.rooms],
            "corridors": [c.to_dict() for c in self.corridors],
            "tile_map": self.tile_map,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_ascii(self) -> str:
        """Render the tile map as an ASCII string."""
        return "\n".join("".join(row) for row in self.tile_map)


# ---------------------------------------------------------------------------
# Tile symbols
# ---------------------------------------------------------------------------
TILE_WALL = "#"
TILE_FLOOR = "."
TILE_CORRIDOR = ","
TILE_START = "S"
TILE_END = "E"
TILE_BOSS = "B"
TILE_TREASURE = "T"
TILE_EMPTY = " "

ROOM_TYPE_TILES = {
    "start": TILE_START,
    "end": TILE_END,
    "boss": TILE_BOSS,
    "treasure": TILE_TREASURE,
    "normal": TILE_FLOOR,
}


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class ProceduralLevelGenerator:
    """
    Generates 2-D dungeon-style levels deterministically from a seed.

    Parameters
    ----------
    width, height : int
        Dimensions of the tile grid.
    num_rooms : int
        Target number of rooms to place.  Actual count may be lower if
        placement fails due to overlaps.
    min_room_size, max_room_size : int
        Room dimension bounds (applied to both width and height independently).
    max_placement_attempts : int
        How many times to try placing each room before giving up.
    """

    def __init__(
        self,
        width: int = 60,
        height: int = 40,
        num_rooms: int = 12,
        min_room_size: int = 4,
        max_room_size: int = 10,
        max_placement_attempts: int = 50,
    ) -> None:
        if width < 10 or height < 10:
            raise ValueError("Map must be at least 10×10 tiles.")
        if min_room_size < 2:
            raise ValueError("min_room_size must be ≥ 2.")
        if max_room_size > min(width, height) - 2:
            raise ValueError("max_room_size is too large for the map dimensions.")
        if min_room_size > max_room_size:
            raise ValueError("min_room_size must be ≤ max_room_size.")

        self.width = width
        self.height = height
        self.num_rooms = num_rooms
        self.min_room_size = min_room_size
        self.max_room_size = max_room_size
        self.max_placement_attempts = max_placement_attempts

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def generate(self, seed: Optional[int] = None) -> Level:
        """
        Generate a full level and return a :class:`Level` object.

        Parameters
        ----------
        seed : int, optional
            RNG seed.  Passing the same seed always produces the same level.
        """
        if seed is None:
            seed = random.randint(0, 2**31 - 1)

        rng = random.Random(seed)
        tile_map = self._blank_map()
        rooms = self._place_rooms(rng, tile_map)
        corridors = self._connect_rooms(rng, rooms, tile_map)
        self._assign_special_rooms(rng, rooms)
        self._paint_rooms(rooms, tile_map)
        self._paint_corridors(corridors, tile_map)

        level = Level(
            width=self.width,
            height=self.height,
            rooms=rooms,
            corridors=corridors,
            tile_map=tile_map,
            seed=seed,
            metadata={
                "room_count": len(rooms),
                "corridor_count": len(corridors),
                "generator": "ProceduralLevelGenerator",
            },
        )
        return level

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _blank_map(self) -> List[List[str]]:
        return [[TILE_WALL] * self.width for _ in range(self.height)]

    def _place_rooms(self, rng: random.Random, tile_map: List[List[str]]) -> List[Room]:
        rooms: List[Room] = []
        for i in range(self.num_rooms):
            for _ in range(self.max_placement_attempts):
                w = rng.randint(self.min_room_size, self.max_room_size)
                h = rng.randint(self.min_room_size, self.max_room_size)
                x = rng.randint(1, self.width - w - 1)
                y = rng.randint(1, self.height - h - 1)
                candidate = Room(id=i, x=x, y=y, width=w, height=h)
                if not any(candidate.overlaps(r) for r in rooms):
                    rooms.append(candidate)
                    break
        return rooms

    def _connect_rooms(
        self, rng: random.Random, rooms: List[Room], tile_map: List[List[str]]
    ) -> List[Corridor]:
        """Connect rooms using a minimum spanning tree via Prim's algorithm."""
        if len(rooms) < 2:
            return []
        corridors: List[Corridor] = []
        connected = {rooms[0].id}
        remaining = {r.id for r in rooms[1:]}
        room_by_id = {r.id: r for r in rooms}

        while remaining:
            best: Optional[Tuple[int, int, int]] = None  # (dist, from_id, to_id)
            for from_id in connected:
                for to_id in remaining:
                    a, b = room_by_id[from_id].center, room_by_id[to_id].center
                    dist = abs(a[0] - b[0]) + abs(a[1] - b[1])
                    if best is None or dist < best[0]:
                        best = (dist, from_id, to_id)

            assert best is not None
            _, from_id, to_id = best
            path = self._l_corridor(
                room_by_id[from_id].center, room_by_id[to_id].center, rng
            )
            corridors.append(Corridor(from_room=from_id, to_room=to_id, path=path))
            connected.add(to_id)
            remaining.discard(to_id)

        return corridors

    def _l_corridor(
        self,
        a: Tuple[int, int],
        b: Tuple[int, int],
        rng: random.Random,
    ) -> List[Tuple[int, int]]:
        """Return cells for an L-shaped (or straight) corridor between a and b."""
        path: List[Tuple[int, int]] = []
        x, y = a
        # Randomly choose horizontal-first or vertical-first
        if rng.random() < 0.5:
            while x != b[0]:
                x += 1 if b[0] > x else -1
                path.append((x, y))
            while y != b[1]:
                y += 1 if b[1] > y else -1
                path.append((x, y))
        else:
            while y != b[1]:
                y += 1 if b[1] > y else -1
                path.append((x, y))
            while x != b[0]:
                x += 1 if b[0] > x else -1
                path.append((x, y))
        return path

    def _assign_special_rooms(self, rng: random.Random, rooms: List[Room]) -> None:
        if not rooms:
            return
        rooms[0].room_type = "start"
        rooms[-1].room_type = "end"
        if len(rooms) >= 4:
            boss_idx = rng.randint(len(rooms) // 2, len(rooms) - 2)
            rooms[boss_idx].room_type = "boss"
        for room in rooms[1:-1]:
            if room.room_type == "normal" and rng.random() < 0.2:
                room.room_type = "treasure"

    def _paint_rooms(self, rooms: List[Room], tile_map: List[List[str]]) -> None:
        for room in rooms:
            center_tile = ROOM_TYPE_TILES.get(room.room_type, TILE_FLOOR)
            cx, cy = room.center
            for y in range(room.y, room.y + room.height):
                for x in range(room.x, room.x + room.width):
                    tile_map[y][x] = TILE_FLOOR
            # Mark the center with the special tile
            tile_map[cy][cx] = center_tile

    def _paint_corridors(
        self, corridors: List[Corridor], tile_map: List[List[str]]
    ) -> None:
        for corridor in corridors:
            for x, y in corridor.path:
                if 0 <= y < self.height and 0 <= x < self.width:
                    if tile_map[y][x] == TILE_WALL:
                        tile_map[y][x] = TILE_CORRIDOR
