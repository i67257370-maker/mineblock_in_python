import math
import random

from tex import T_BRICK, T_DIRT, T_GRASS_SIDE, T_GRASS_TOP, T_LEAVES, T_PLANK, \
    T_STONE, T_WOOD_SIDE, T_WOOD_TOP

AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
WOOD = 4
LEAVES = 5
PLANK = 6
BRICK = 7

BLOCK_NAMES = {
    GRASS: "Трава",
    DIRT: "Земля",
    STONE: "Камень",
    WOOD: "Дерево",
    LEAVES: "Листва",
    PLANK: "Доски",
    BRICK: "Кирпич",
}

BLOCK_TILES = {
    GRASS: (T_GRASS_TOP, T_GRASS_SIDE, T_DIRT),
    DIRT: (T_DIRT, T_DIRT, T_DIRT),
    STONE: (T_STONE, T_STONE, T_STONE),
    WOOD: (T_WOOD_TOP, T_WOOD_SIDE, T_WOOD_TOP),
    LEAVES: (T_LEAVES, T_LEAVES, T_LEAVES),
    PLANK: (T_PLANK, T_PLANK, T_PLANK),
    BRICK: (T_BRICK, T_BRICK, T_BRICK),
}

FACES = [
    ((0, 1, 0), 1.00, [(0, 1, 0, 0, 0), (0, 1, 1, 1, 0), (1, 1, 1, 1, 1), (1, 1, 0, 0, 1)]),
    ((0, -1, 0), 0.50, [(0, 0, 0, 0, 0), (1, 0, 0, 1, 0), (1, 0, 1, 1, 1), (0, 0, 1, 0, 1)]),
    ((1, 0, 0), 0.68, [(1, 0, 0, 0, 0), (1, 0, 1, 1, 0), (1, 1, 1, 1, 1), (1, 1, 0, 0, 1)]),
    ((-1, 0, 0), 0.68, [(0, 0, 1, 0, 0), (0, 0, 0, 1, 0), (0, 1, 0, 1, 1), (0, 1, 1, 0, 1)]),
    ((0, 0, 1), 0.85, [(0, 0, 1, 0, 0), (1, 0, 1, 1, 0), (1, 1, 1, 1, 1), (0, 1, 1, 0, 1)]),
    ((0, 0, -1), 0.85, [(1, 0, 0, 0, 0), (0, 0, 0, 1, 0), (0, 1, 0, 1, 1), (1, 1, 0, 0, 1)]),
]


def _hash2(x, z, seed):
    n = x * 374761393 + z * 668265263 + seed * 1274126177
    n &= 0xFFFFFFFFFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177
    n &= 0xFFFFFFFFFFFFFFFF
    return ((n ^ (n >> 16)) & 0x7FFFFFFF) / 0x7FFFFFFF


def _value_noise(x, z, seed, period):
    fx, fz = x / period, z / period
    x0, z0 = math.floor(fx), math.floor(fz)
    tx, tz = fx - x0, fz - z0
    tx = tx * tx * (3 - 2 * tx)
    tz = tz * tz * (3 - 2 * tz)
    h00 = _hash2(x0, z0, seed)
    h10 = _hash2(x0 + 1, z0, seed)
    h01 = _hash2(x0, z0 + 1, seed)
    h11 = _hash2(x0 + 1, z0 + 1, seed)
    return (h00 * (1 - tx) + h10 * tx) * (1 - tz) + (h01 * (1 - tx) + h11 * tx) * tz


class World:
    def __init__(self, seed=2011, size=64, height=48):
        self.seed = seed
        self.SIZE = size
        self.WORLD_HEIGHT = height
        self.blocks = {}
        self.dl = None
        self.dirty = True
        self._generate()

    def in_bounds(self, x, y, z):
        return 0 <= x < self.SIZE and 0 <= y < self.WORLD_HEIGHT and 0 <= z < self.SIZE

    def get(self, x, y, z):
        if not self.in_bounds(x, y, z):
            return AIR
        return self.blocks.get((x, y, z), AIR)

    def solid(self, x, y, z):
        return self.get(x, y, z) != AIR

    def set_block(self, x, y, z, b):
        if not self.in_bounds(x, y, z):
            return
        if b == AIR:
            self.blocks.pop((x, y, z), None)
        else:
            self.blocks[(x, y, z)] = b
        self.dirty = True

    def ground_height(self, x, z, start=None):
        ix, iz = int(math.floor(x)), int(math.floor(z))
        y = self.WORLD_HEIGHT - 1 if start is None else min(int(math.floor(start)), self.WORLD_HEIGHT - 1)
        while y >= 0 and not self.solid(ix, y, iz):
            y -= 1
        return y + 1

    def _column_height(self, x, z):
        h = 9.0
        h += 6.0 * _value_noise(x, z, self.seed, 24)
        h += 3.5 * _value_noise(x + 101, z - 77, self.seed + 1, 12)
        h += 1.5 * _value_noise(x - 43, z + 35, self.seed + 2, 6)
        return int(h)

    def _generate(self):
        rng = random.Random(self.seed + 12345)
        size = self.SIZE
        for x in range(size):
            for z in range(size):
                h = self._column_height(x, z)
                for y in range(0, h + 1):
                    if y == h:
                        b = GRASS
                    elif y >= h - 3:
                        b = DIRT
                    else:
                        b = STONE
                    if self.in_bounds(x, y, z):
                        self.blocks[(x, y, z)] = b

        trees = []
        for _ in range(140):
            if len(trees) >= 22:
                break
            x = rng.randint(3, size - 4)
            z = rng.randint(3, size - 4)
            if x * x + z * z < 49:
                continue
            if any((tx - x) ** 2 + (tz - z) ** 2 < 25 for tx, tz in trees):
                continue
            trees.append((x, z))
            self._place_tree(rng, x, z)

    def _place_tree(self, rng, x, z):
        h = self._column_height(x, z)
        trunk = 4 + rng.randint(0, 2)
        for y in range(1, trunk + 1):
            if self.in_bounds(x, h + y, z):
                self.blocks[(x, h + y, z)] = WOOD
        top = h + trunk
        for dy in (-1, 0, 1):
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    d = dx * dx + dz * dz + dy * dy * 1.6
                    if dy != 0 and abs(dx) == 2 and abs(dz) == 2:
                        continue
                    if d > 5.4:
                        continue
                    lx, ly, lz = x + dx, top + dy, z + dz
                    if self.in_bounds(lx, ly, lz) and (lx, ly, lz) not in self.blocks:
                        self.blocks[(lx, ly, lz)] = LEAVES


def raycast(w, ox, oy, oz, dx, dy, dz, reach=5.0, step=0.02):
    x, y, z = ox, oy, oz
    prev = None
    t = 0.0
    while t <= reach:
        cell = (int(math.floor(x)), int(math.floor(y)), int(math.floor(z)))
        if cell != prev:
            if w.solid(*cell):
                return cell, prev
            prev = cell
        x += dx * step
        y += dy * step
        z += dz * step
        t += step
    return None
