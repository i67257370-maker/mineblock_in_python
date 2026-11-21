import random

import pygame

TILE = 16
COLS = 4
ROWS = 4

T_GRASS_TOP = 0
T_GRASS_SIDE = 1
T_DIRT = 2
T_STONE = 3
T_WOOD_SIDE = 4
T_WOOD_TOP = 5
T_LEAVES = 6
T_PLANK = 7
T_BRICK = 8


def _clamp255(v):
    return int(max(0, min(255, v)))


def fill_noise(surf, x0, y0, base, spread, rng):
    for y in range(TILE):
        for x in range(TILE):
            k = rng.uniform(1.0 - spread, 1.0 + spread)
            surf.set_at((x0 + x, y0 + y), tuple(_clamp255(v * k) for v in base))


def tile_origin(tile):
    return (tile % COLS) * TILE, (tile // COLS) * TILE


def build_atlas_surface(seed=7):
    rng = random.Random(seed)
    surf = pygame.Surface((COLS * TILE, ROWS * TILE))

    x0, y0 = tile_origin(T_GRASS_TOP)
    fill_noise(surf, x0, y0, (100, 164, 62), 0.14, rng)

    x0, y0 = tile_origin(T_GRASS_SIDE)
    fill_noise(surf, x0, y0, (136, 99, 68), 0.16, rng)
    for x in range(TILE):
        depth = rng.randint(3, 5)
        for y in range(depth):
            k = rng.uniform(0.85, 1.1)
            surf.set_at((x0 + x, y0 + y),
                        tuple(_clamp255(v * k) for v in (100, 164, 62)))

    x0, y0 = tile_origin(T_DIRT)
    fill_noise(surf, x0, y0, (136, 99, 68), 0.16, rng)

    x0, y0 = tile_origin(T_STONE)
    fill_noise(surf, x0, y0, (128, 128, 130), 0.12, rng)
    for _ in range(24):
        px, py = rng.randrange(TILE), rng.randrange(TILE)
        surf.set_at((x0 + px, y0 + py), (104, 104, 106))

    x0, y0 = tile_origin(T_WOOD_SIDE)
    for y in range(TILE):
        for x in range(TILE):
            stripe = 0.78 if x % 4 == 0 else 1.0
            k = stripe * rng.uniform(0.92, 1.06)
            surf.set_at((x0 + x, y0 + y),
                        tuple(_clamp255(v * k) for v in (146, 104, 56)))

    x0, y0 = tile_origin(T_WOOD_TOP)
    for y in range(TILE):
        for x in range(TILE):
            d = int(max(abs(x - 7.5), abs(y - 7.5)))
            base = (168, 126, 72) if d % 3 else (130, 92, 48)
            k = rng.uniform(0.95, 1.05)
            surf.set_at((x0 + x, y0 + y),
                        tuple(_clamp255(v * k) for v in base))

    x0, y0 = tile_origin(T_LEAVES)
    fill_noise(surf, x0, y0, (52, 118, 40), 0.35, rng)

    x0, y0 = tile_origin(T_PLANK)
    for y in range(TILE):
        band = y // 4
        for x in range(TILE):
            k = 0.78 if y % 4 == 3 else 1.0
            if x == (band * 5 + 3) % TILE:
                k *= 0.8
            k *= rng.uniform(0.95, 1.05)
            surf.set_at((x0 + x, y0 + y),
                        tuple(_clamp255(v * k) for v in (190, 148, 96)))

    x0, y0 = tile_origin(T_BRICK)
    for y in range(TILE):
        row = y // 4
        for x in range(TILE):
            if y % 4 == 0 or (x + row * 4) % 8 == 0:
                c = (188, 184, 178)
            else:
                k = rng.uniform(0.85, 1.1)
                c = tuple(_clamp255(v * k) for v in (152, 66, 56))
            surf.set_at((x0 + x, y0 + y), c)

    return surf


def tile_uv(tile):
    col = tile % COLS
    row = tile // COLS
    u0 = col / COLS
    u1 = (col + 1) / COLS
    v1 = 1.0 - row / ROWS
    v0 = 1.0 - (row + 1) / ROWS
    return u0, v0, u1, v1
