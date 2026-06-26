# world.py — the map: ground tiles + interactable objects.
# v0.1 keeps the world simple (no collision) so the focus stays on the
# people. Objects are what villagers walk to: food, home, fun spots.

import random
import math
import pygame
import settings as S


class Obj:
    """An interactable thing on the map (food bush, hut, shrine)."""
    def __init__(self, kind, tx, ty):
        self.kind = kind          # "food" | "home" | "fun"
        self.tx, self.ty = tx, ty
        self.center = (tx * S.TILE + S.TILE / 2, ty * S.TILE + S.TILE / 2)
        self.owner = None         # for homes: which villager lives here


class World:
    def __init__(self, seed=7):
        self.rng = random.Random(seed)
        # tile grid: 0 grass, 1 grass-variant, 2 water, 3 tree
        self.tiles = [[0 for _ in range(S.GRID_W)] for _ in range(S.GRID_H)]
        self.objects = []
        self._build()

    # -- generation ----------------------------------------------------
    def _build(self):
        # speckle two shades of grass for texture
        for y in range(S.GRID_H):
            for x in range(S.GRID_W):
                self.tiles[y][x] = 1 if self.rng.random() < 0.18 else 0

        # a pond in the lower-right-ish area
        for y in range(16, 21):
            for x in range(26, 32):
                if 0 <= y < S.GRID_H and 0 <= x < S.GRID_W:
                    self.tiles[y][x] = 2

        # fun spot: a shrine beside the pond
        self.objects.append(Obj("fun", 24, 18))

        # food: berry bushes scattered around
        for (tx, ty) in [(6, 5), (15, 20), (29, 6), (10, 13), (20, 9)]:
            self.objects.append(Obj("food", tx, ty))

        # homes: three huts in different corners
        self.homes = [Obj("home", 4, 3), Obj("home", 30, 21), Obj("home", 4, 21)]
        self.objects.extend(self.homes)

        # decorative trees, avoiding water and objects
        blocked = {(o.tx, o.ty) for o in self.objects}
        for _ in range(46):
            x = self.rng.randrange(S.GRID_W)
            y = self.rng.randrange(S.GRID_H)
            if self.tiles[y][x] == 2 or (x, y) in blocked:
                continue
            self.tiles[y][x] = 3

    # -- queries -------------------------------------------------------
    def nearest(self, pos, kind):
        best, bd = None, 1e9
        for o in self.objects:
            if o.kind != kind:
                continue
            d = math.hypot(o.center[0] - pos[0], o.center[1] - pos[1])
            if d < bd:
                best, bd = o, d
        return best

    # -- drawing -------------------------------------------------------
    def draw(self, surf):
        for y in range(S.GRID_H):
            for x in range(S.GRID_W):
                t = self.tiles[y][x]
                rx, ry = x * S.TILE, y * S.TILE + S.TOPBAR
                if t == 2:
                    col = S.C_WATER
                elif t == 1:
                    col = S.C_GRASS2
                else:
                    col = S.C_GRASS
                pygame.draw.rect(surf, col, (rx, ry, S.TILE, S.TILE))
                if t == 3:  # tree: trunk + canopy
                    pygame.draw.rect(surf, S.C_TRUNK,
                                     (rx + S.TILE // 2 - 2, ry + S.TILE - 9, 4, 9))
                    pygame.draw.circle(surf, S.C_TREE,
                                       (rx + S.TILE // 2, ry + S.TILE // 2 - 2),
                                       S.TILE // 2 - 1)

        for o in self.objects:
            cx, cy = o.center[0], o.center[1] + S.TOPBAR
            if o.kind == "food":
                pygame.draw.circle(surf, S.C_BUSH, (int(cx), int(cy)), 9)
                pygame.draw.circle(surf, (200, 90, 130), (int(cx), int(cy)), 4)
            elif o.kind == "home":
                pygame.draw.rect(surf, S.C_HUT, (cx - 12, cy - 8, 24, 16))
                pygame.draw.polygon(surf, S.C_HUT_ROOF,
                                    [(cx - 14, cy - 8), (cx + 14, cy - 8), (cx, cy - 20)])
            elif o.kind == "fun":
                pygame.draw.polygon(surf, S.C_SHRINE,
                                    [(cx, cy - 14), (cx - 11, cy + 8), (cx + 11, cy + 8)])
                pygame.draw.circle(surf, (255, 255, 235), (int(cx), int(cy - 2)), 3)
