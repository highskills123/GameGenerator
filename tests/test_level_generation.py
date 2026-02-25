"""Tests for ProceduralLevelGenerator – no network or GPU required."""

import pytest
from gamedesign_agent.level_generation import (
    ProceduralLevelGenerator,
    Level,
    Room,
    TILE_WALL,
    TILE_FLOOR,
    TILE_CORRIDOR,
    TILE_START,
    TILE_END,
)


class TestProceduralLevelGenerator:
    def test_returns_level_object(self):
        gen = ProceduralLevelGenerator(width=30, height=20, num_rooms=5)
        level = gen.generate(seed=1)
        assert isinstance(level, Level)

    def test_tile_map_dimensions(self):
        gen = ProceduralLevelGenerator(width=40, height=25, num_rooms=6)
        level = gen.generate(seed=2)
        assert len(level.tile_map) == 25
        assert all(len(row) == 40 for row in level.tile_map)

    def test_deterministic_with_same_seed(self):
        gen = ProceduralLevelGenerator(width=30, height=20, num_rooms=5)
        level_a = gen.generate(seed=42)
        level_b = gen.generate(seed=42)
        assert level_a.to_ascii() == level_b.to_ascii()
        assert level_a.seed == level_b.seed

    def test_different_seeds_produce_different_maps(self):
        gen = ProceduralLevelGenerator(width=30, height=20, num_rooms=5)
        level_a = gen.generate(seed=1)
        level_b = gen.generate(seed=9999)
        # With enough rooms they should differ (very high probability)
        assert level_a.to_ascii() != level_b.to_ascii()

    def test_rooms_within_bounds(self):
        gen = ProceduralLevelGenerator(width=30, height=20, num_rooms=5)
        level = gen.generate(seed=3)
        for room in level.rooms:
            assert room.x >= 1
            assert room.y >= 1
            assert room.x + room.width <= gen.width - 1
            assert room.y + room.height <= gen.height - 1

    def test_rooms_do_not_overlap(self):
        gen = ProceduralLevelGenerator(width=60, height=40, num_rooms=8)
        level = gen.generate(seed=7)
        rooms = level.rooms
        for i, r1 in enumerate(rooms):
            for j, r2 in enumerate(rooms):
                if i != j:
                    assert not r1.overlaps(r2), (
                        f"Room {r1.id} overlaps room {r2.id}"
                    )

    def test_start_and_end_rooms_assigned(self):
        gen = ProceduralLevelGenerator(width=40, height=30, num_rooms=6)
        level = gen.generate(seed=5)
        types = [r.room_type for r in level.rooms]
        assert "start" in types
        assert "end" in types

    def test_ascii_contains_floor_tiles(self):
        gen = ProceduralLevelGenerator(width=30, height=20, num_rooms=4)
        level = gen.generate(seed=6)
        ascii_map = level.to_ascii()
        assert TILE_FLOOR in ascii_map or TILE_CORRIDOR in ascii_map

    def test_to_dict_keys(self):
        gen = ProceduralLevelGenerator(width=30, height=20, num_rooms=4)
        level = gen.generate(seed=8)
        d = level.to_dict()
        assert "seed" in d
        assert "rooms" in d
        assert "corridors" in d
        assert "tile_map" in d
        assert "metadata" in d

    def test_to_json_valid(self):
        import json
        gen = ProceduralLevelGenerator(width=30, height=20, num_rooms=4)
        level = gen.generate(seed=9)
        data = json.loads(level.to_json())
        assert data["seed"] == level.seed

    def test_room_center_in_bounds(self):
        gen = ProceduralLevelGenerator(width=40, height=30, num_rooms=5)
        level = gen.generate(seed=10)
        for room in level.rooms:
            cx, cy = room.center
            assert 0 <= cx < gen.width
            assert 0 <= cy < gen.height

    def test_metadata_room_count(self):
        gen = ProceduralLevelGenerator(width=50, height=35, num_rooms=8)
        level = gen.generate(seed=11)
        assert level.metadata["room_count"] == len(level.rooms)

    def test_invalid_dimensions_raise(self):
        with pytest.raises(ValueError):
            ProceduralLevelGenerator(width=5, height=5)

    def test_invalid_room_size_raise(self):
        with pytest.raises(ValueError):
            ProceduralLevelGenerator(min_room_size=1)

    def test_min_greater_than_max_raises(self):
        with pytest.raises(ValueError):
            ProceduralLevelGenerator(min_room_size=8, max_room_size=4)

    def test_level_seed_stored(self):
        gen = ProceduralLevelGenerator(width=30, height=20, num_rooms=4)
        level = gen.generate(seed=12345)
        assert level.seed == 12345

    def test_no_seed_generates_valid_level(self):
        """Random seed (no explicit seed) still produces a valid level."""
        gen = ProceduralLevelGenerator(width=30, height=20, num_rooms=4)
        level = gen.generate()
        assert len(level.rooms) >= 1
        assert level.seed is not None
