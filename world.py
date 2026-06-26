# world.py — the map: ground tiles + interactable objects.
# v0.1 keeps the world simple (no collision) so the focus stays on the
# people. Objects are what villagers walk to: food, home, fun spots.

import random
import math
import heapq
import pygame
import settings as S


class Obj:
    """An interactable thing on the map (food bush, hut, shrine)."""
    def __init__(self, kind, tx, ty):
        self.kind = kind          # "food" | "home" | "fun"
        self.tx, self.ty = tx, ty
        self.center = (tx * S.TILE + S.TILE / 2, ty * S.TILE + S.TILE / 2)
        self.owner = None         # for homes: which villager lives here
        self.amount = 0           # remaining gathers (trees/rocks)
        self.state = None         # plot state: untilled/tilled/seeded/ripe
        self.growth = 0.0         # crop growth timer
        self.regrow = 0.0         # node regrow timer
        self.height = 0           # height in z-levels (trees)


class World:
    def __init__(self, seed=7):
        self.rng = random.Random(seed)
        # tile grid: 0 grass, 1 grass-variant, 2 water, 3 tree
        self.tiles = [[0 for _ in range(S.GRID_W)] for _ in range(S.GRID_H)]
        self.objects = []
        self.stock = {k: 0 for k in S.STOCK_KINDS}  # settlement stockpile
        self.stock["wood"] = 30  # starting materials (replaced by point-buy at 1.0)
        self.stock["stone"] = 20
        self.berries = []        # perishable: list of {count, age} batches
        self.sel_recipe = 0      # which workbench recipe is selected
        # built structures: build[y][x] = {"kind","mat"} or None (walls block)
        self.build = [[None for _ in range(S.GRID_W)] for _ in range(S.GRID_H)]
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

        # bare earth and a rocky outcrop — future shovel/pick targets (v0.6)
        for y in range(2, 4):
            for x in range(18, 22):
                self.tiles[y][x] = 4              # dirt patch
        for y in range(2, 6):
            for x in range(31, 35):
                self.tiles[y][x] = 5              # stone outcrop
        for (x, y) in [(32, 3), (33, 4), (31, 2), (34, 5)]:
            self.tiles[y][x] = 6                  # ore veins in the stone

        # fun spot: a shrine beside the pond
        self.objects.append(Obj("fun", 24, 18))

        # water: drinking spots at the pond's edge
        self.objects.append(Obj("water", 25, 18))
        self.objects.append(Obj("water", 32, 18))

        # food: berry bushes scattered around (harvested for berries)
        for (tx, ty) in [(6, 5), (15, 20), (29, 6), (10, 13), (20, 9)]:
            bush = Obj("food", tx, ty)
            bush.amount = S.BUSH_AMOUNT
            self.objects.append(bush)

        # homes: three huts in different corners
        self.homes = [Obj("home", 4, 3), Obj("home", 30, 21), Obj("home", 4, 21)]
        self.objects.extend(self.homes)

        # gatherable + workable objects (v0.3) — trees span several z-levels
        tree_pos = [(12, 4), (8, 9), (20, 4), (14, 15), (4, 9), (18, 13),
                    (22, 7), (10, 3), (30, 4), (16, 17), (26, 5), (6, 13)]
        self.trees = [Obj("tree", *p) for p in tree_pos]
        self.rocks = [Obj("rock", *p) for p in [(28, 10), (31, 13), (26, 8)]]
        for o in self.trees + self.rocks:
            o.amount = S.NODE_AMOUNT
        for t in self.trees:
            t.height = self.rng.choice([3, 4, 5])   # 3..5 levels tall
        self.plots = []
        for py in (7, 8):
            for px in (6, 7, 8):
                plot = Obj("plot", px, py)
                plot.state = "untilled"
                self.plots.append(plot)
        self.bench = Obj("bench", 16, 11)
        workables = self.trees + self.rocks + self.plots + [self.bench]
        self.objects.extend(workables)
        for o in workables:                       # clear ground under them
            self.tiles[o.ty][o.tx] = 0

        # decorative trees, avoiding water and objects
        blocked = {(o.tx, o.ty) for o in self.objects}
        for _ in range(46):
            x = self.rng.randrange(S.GRID_W)
            y = self.rng.randrange(S.GRID_H)
            if self.tiles[y][x] not in (0, 1) or (x, y) in blocked:
                continue                          # only place decor on plain grass
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

    # -- movement / pathfinding ----------------------------------------
    def tile_of(self, pt):
        tx = max(0, min(S.GRID_W - 1, int(pt[0] // S.TILE)))
        ty = max(0, min(S.GRID_H - 1, int(pt[1] // S.TILE)))
        return (tx, ty)

    def walkable(self, tx, ty):
        if not (0 <= tx < S.GRID_W and 0 <= ty < S.GRID_H):
            return False
        if self.tiles[ty][tx] == 2:                    # water blocks
            return False
        b = self.build[ty][tx]
        return not (b and b["kind"] == "wall")         # walls block; doors/floors don't

    def _neighbors(self, tx, ty):
        for nx, ny in ((tx + 1, ty), (tx - 1, ty), (tx, ty + 1), (tx, ty - 1)):
            if self.walkable(nx, ny):
                yield nx, ny

    def find_path(self, start, goal):
        """A* over the tile grid. Returns a list of waypoint points (ending on
        the exact goal point), or [] if there's no route."""
        sx, sy = self.tile_of(start)
        gx, gy = self.tile_of(goal)
        if not self.walkable(gx, gy):                  # retarget to nearest open neighbor
            best, bd = None, 1e9
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = gx + dx, gy + dy
                    if self.walkable(nx, ny):
                        d = (nx - sx) ** 2 + (ny - sy) ** 2
                        if d < bd:
                            bd, best = d, (nx, ny)
            if best is None:
                return []
            gx, gy = best
        if (sx, sy) == (gx, gy):
            return [goal]
        openh = [(0, (sx, sy))]
        came, gscore = {}, {(sx, sy): 0}
        while openh:
            _, cur = heapq.heappop(openh)
            if cur == (gx, gy):
                break
            for nx, ny in self._neighbors(*cur):
                ng = gscore[cur] + 1
                if (nx, ny) not in gscore or ng < gscore[(nx, ny)]:
                    gscore[(nx, ny)] = ng
                    f = ng + abs(nx - gx) + abs(ny - gy)
                    heapq.heappush(openh, (f, (nx, ny)))
                    came[(nx, ny)] = cur
        if (gx, gy) not in came:
            return []                                  # unreachable
        path, cur = [], (gx, gy)
        while cur != (sx, sy):
            path.append(cur)
            cur = came[cur]
        path.reverse()
        pts = [(tx * S.TILE + S.TILE / 2, ty * S.TILE + S.TILE / 2) for tx, ty in path]
        if pts:
            pts[-1] = goal                             # finish on the exact point
        return pts

    # -- simulation ----------------------------------------------------
    def update(self, gdt):
        for o in self.objects:
            if o.kind in ("tree", "rock", "food") and o.amount <= 0 and o.regrow > 0:
                o.regrow -= gdt
                if o.regrow <= 0:
                    o.amount = S.BUSH_AMOUNT if o.kind == "food" else S.NODE_AMOUNT
            elif o.kind == "plot" and o.state == "seeded":
                o.growth += gdt
                if o.growth >= S.CROP_GROW:
                    o.state = "ripe"
        # berries age and rot away
        for b in self.berries:
            b["age"] += gdt
        self.berries = [b for b in self.berries if b["age"] < S.BERRY_SPOIL]

    # -- work outcomes (called by a villager finishing a task) ---------
    def gather(self, obj, kind):
        if obj is None or obj.amount <= 0:
            return ("nothing left", S.C_DIM)
        obj.amount -= 1
        if obj.amount <= 0:
            obj.regrow = S.NODE_REGROW
        amt = S.YIELD_WOOD if kind == "wood" else S.YIELD_STONE
        self.stock[kind] += amt
        return (f"+{amt} {kind}", S.C_GOLD)

    def tend_plot(self, obj):
        if obj.state == "untilled":
            obj.state = "tilled"
            return ("tilled", S.C_GOOD)
        if obj.state == "tilled":
            obj.state = "seeded"
            obj.growth = 0.0
            return ("planted", S.C_GOOD)
        if obj.state == "seeded":
            return ("still growing", S.C_DIM)
        if obj.state == "ripe":
            obj.state = "tilled"
            obj.growth = 0.0
            self.stock["grain"] += S.YIELD_GRAIN
            return (f"+{S.YIELD_GRAIN} grain", S.C_GOLD)
        return (None, None)

    def craft(self):
        name, ins, outs = S.RECIPES[self.sel_recipe]
        if all(self.stock[k] >= v for k, v in ins.items()):
            for k, v in ins.items():
                self.stock[k] -= v
            for k, v in outs.items():
                self.stock[k] += v
            return (", ".join(f"+{v} {k}" for k, v in outs.items()), S.C_GOLD)
        return (f"need {name} mats", S.C_BAD)

    # -- berry store (perishable foraged food) -------------------------
    def add_berries(self, n):
        self.berries.append({"count": n, "age": 0.0})

    def berry_count(self):
        return sum(b["count"] for b in self.berries)

    def take_berry(self):
        for b in self.berries:
            if b["count"] > 0:
                b["count"] -= 1
                break
        self.berries = [b for b in self.berries if b["count"] > 0]

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
                elif t == 4:
                    col = S.C_DIRT
                elif t == 5:
                    col = S.C_STONEG
                elif t == 6:
                    col = S.C_ORE
                else:
                    col = S.C_GRASS
                pygame.draw.rect(surf, col, (rx, ry, S.TILE, S.TILE))
                if t == 3:  # tree: trunk + canopy
                    pygame.draw.rect(surf, S.C_TRUNK,
                                     (rx + S.TILE // 2 - 2, ry + S.TILE - 9, 4, 9))
                    pygame.draw.circle(surf, S.C_TREE,
                                       (rx + S.TILE // 2, ry + S.TILE // 2 - 2),
                                       S.TILE // 2 - 1)
                elif t == 6:  # ore flecks
                    pygame.draw.circle(surf, (214, 184, 126),
                                       (rx + S.TILE // 2, ry + S.TILE // 2), 3)

        for o in self.objects:
            cx, cy = o.center[0], o.center[1] + S.TOPBAR
            if o.kind == "tree":
                continue          # trees are drawn per z-level in draw_trees()
            if o.kind == "food":
                if o.amount > 0:
                    pygame.draw.circle(surf, S.C_BUSH, (int(cx), int(cy)), 9)
                    pygame.draw.circle(surf, (200, 90, 130), (int(cx), int(cy)), 4)
                else:
                    pygame.draw.circle(surf, (70, 92, 72), (int(cx), int(cy)), 6)
            elif o.kind == "home":
                pygame.draw.rect(surf, S.C_HUT, (cx - 12, cy - 8, 24, 16))
                pygame.draw.polygon(surf, S.C_HUT_ROOF,
                                    [(cx - 14, cy - 8), (cx + 14, cy - 8), (cx, cy - 20)])
            elif o.kind == "fun":
                pygame.draw.polygon(surf, S.C_SHRINE,
                                    [(cx, cy - 14), (cx - 11, cy + 8), (cx + 11, cy + 8)])
                pygame.draw.circle(surf, (255, 255, 235), (int(cx), int(cy - 2)), 3)
            elif o.kind == "rock":
                if o.amount > 0:
                    pygame.draw.circle(surf, S.C_ROCK, (int(cx), int(cy)), 10)
                    pygame.draw.circle(surf, (92, 94, 102), (int(cx), int(cy)), 10, 1)
                else:
                    pygame.draw.circle(surf, (100, 102, 110), (int(cx), int(cy)), 5)
            elif o.kind == "plot":
                r = pygame.Rect(o.tx * S.TILE + 3, o.ty * S.TILE + S.TOPBAR + 3,
                                S.TILE - 6, S.TILE - 6)
                pygame.draw.rect(surf, S.C_PLOT if o.state == "untilled" else S.C_PLOT_T, r)
                if o.state == "seeded":
                    pygame.draw.circle(surf, S.C_SPROUT, r.center, 3)
                elif o.state == "ripe":
                    pygame.draw.rect(surf, S.C_CROP,
                                     (r.centerx - 6, r.y + 2, 12, r.height - 4))
            elif o.kind == "bench":
                pygame.draw.rect(surf, S.C_BENCH, (cx - 12, cy - 6, 24, 12))
                pygame.draw.rect(surf, (90, 72, 44), (cx - 12, cy - 6, 24, 12), 1)
            elif o.kind == "water":
                pygame.draw.circle(surf, (70, 120, 170), (int(cx), int(cy)), 8)
                pygame.draw.circle(surf, (150, 200, 230), (int(cx), int(cy)), 4)

    def draw_build(self, surf):
        """Draw placed walls, doors, and floors."""
        for by in range(S.GRID_H):
            for bx in range(S.GRID_W):
                b = self.build[by][bx]
                if not b:
                    continue
                rx, ry = bx * S.TILE, by * S.TILE + S.TOPBAR
                if b["kind"] == "floor":
                    col = (110, 92, 64) if b["mat"] == "wood" else (120, 120, 128)
                    pygame.draw.rect(surf, col, (rx + 1, ry + 1, S.TILE - 2, S.TILE - 2))
                elif b["kind"] == "wall":
                    col = (140, 100, 56) if b["mat"] == "wood" else (122, 124, 132)
                    edge = (60, 44, 28) if b["mat"] == "wood" else (72, 74, 82)
                    pygame.draw.rect(surf, col, (rx, ry, S.TILE, S.TILE))
                    pygame.draw.rect(surf, edge, (rx, ry, S.TILE, S.TILE), 2)
                elif b["kind"] == "door":
                    pygame.draw.rect(surf, (96, 72, 44), (rx + 4, ry, S.TILE - 8, S.TILE))
                    pygame.draw.rect(surf, (150, 116, 70), (rx + 4, ry, S.TILE - 8, S.TILE), 2)

    def draw_trees(self, surf, view_z):
        """Draw each tree's slice for the level being viewed (trunk -> crown)."""
        for t in self.trees:
            cx, cy = int(t.center[0]), int(t.center[1] + S.TOPBAR)
            self._tree_segment(surf, cx, cy, view_z, t.height, t.amount > 0)

    def _tree_segment(self, surf, cx, cy, z, h, alive):
        if not alive:                                  # chopped — only a stump
            if z == 0:
                pygame.draw.rect(surf, S.C_TRUNK, (cx - 4, cy + 2, 8, 6))
            return
        if z >= h:
            return                                     # above the treetop: open sky
        top = h - 1
        if z == top:                                   # leafy crown
            pygame.draw.circle(surf, S.C_LEAF, (cx, cy), 13)
            pygame.draw.circle(surf, S.C_LEAF2, (cx - 4, cy - 3), 6)
        elif z == top - 1:                             # branches + leaves
            pygame.draw.rect(surf, S.C_TRUNK, (cx - 2, cy - 4, 4, 14))
            for dx in (-11, 11):
                pygame.draw.line(surf, S.C_TRUNK, (cx, cy + 2), (cx + dx, cy - 6), 2)
                pygame.draw.circle(surf, S.C_LEAF, (cx + dx, cy - 6), 5)
        else:                                          # trunk
            pygame.draw.rect(surf, S.C_TRUNK, (cx - 3, cy - 6, 6, 18))
