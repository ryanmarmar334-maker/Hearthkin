# main.py — Hearthkin entry point.
# A fantasy life-sim: autonomous villagers with needs, moods, traits,
# and relationships. v0.1 focuses on "the people"; the survival, world,
# and dynasty layers come in later versions.
#
# Run:   py main.py            (Windows)  /  python3 main.py
# Test:  py main.py --selftest (headless simulation, no window)

import sys
import pygame
import settings as S
from world import World
from character import Character


def make_villagers(world):
    h = world.homes
    you = Character("You", "Human", (236, 226, 138), ["Cheerful"], h[0], 480, 360,
                    player_rel=100, gender="M", controlled=True)
    return [
        you,
        Character("Eldra", "Wood Elf",  (120, 200, 130), ["Cheerful", "Loner"],     h[0], 130, 110, player_rel=28, gender="F"),
        Character("Brakka", "Hill Dwarf", (210, 150, 90), ["Glutton", "Hardy"],     h[1], 760, 600, player_rel=8, gender="M"),
        Character("Pip",   "Halfling",  (180, 140, 220), ["Gregarious", "Lazy"],    h[2], 140, 560, player_rel=44, gender="F"),
    ]


def place_build(world, villagers, bx, by, z, sel):
    if not (0 <= bx < S.GRID_W and 0 <= by < S.GRID_H):
        return
    name, kind, mat, cost = S.BUILDABLES[sel]
    if kind in ("wall", "door", "floor"):              # surface structures (z0)
        if z != 0 or world.tiles[by][bx] == 2 or world.build[by][bx] is not None:
            return
        for v in villagers:                            # don't wall a villager into a tile
            if int(v.x) // S.TILE == bx and int(v.y) // S.TILE == by:
                return
        if all(world.stock[k] >= v for k, v in cost.items()):
            for k, v in cost.items():
                world.stock[k] -= v
            world.build[by][bx] = {"kind": kind, "mat": mat}
            world.recompute_rooms()
            for v in villagers:
                v.path = []
    elif kind == "dig":
        if z < 0:
            world.dig(z, bx, by)
    elif kind.startswith("stairs") or kind.startswith("ramp"):
        if z <= 0:
            world.place_struct(z, bx, by, kind)


def remove_build(world, villagers, bx, by, z):
    if not (0 <= bx < S.GRID_W and 0 <= by < S.GRID_H):
        return
    if z == 0 and world.build[by][bx]:
        world.build[by][bx] = None
        world.recompute_rooms()
        for v in villagers:
            v.path = []
    elif world.zstruct.get(z) and world.zstruct[z][by][bx]:
        world.zstruct[z][by][bx] = None


def assign_mine(world, z, tx, ty):
    """Build a mining action: stand on an open neighbour and excavate the cell."""
    for nx, ny in ((tx + 1, ty), (tx - 1, ty), (tx, ty + 1), (tx, ty - 1)):
        if world.walk3(z, nx, ny):
            stand = (nx * S.TILE + S.TILE / 2, ny * S.TILE + S.TILE / 2)
            return {"type": "minework", "tx": tx, "ty": ty, "z": z,
                    "stand": stand, "t": 0.0, "work": 0.0, "timeout": 40.0}
    return None


def request_target(world, villagers, selected, wx, wy):
    """Map a right-click (world coords) to a (need, action) for the villager."""
    for v in villagers:                      # another villager -> socialize
        if v is not selected and v.hit(wx, wy):
            return "social", {"type": "talk", "partner": v, "t": 0.0}
    lx, ly = wx, wy                          # nearest world object -> use it
    best, bd = None, 1e9
    for o in world.objects:
        d = ((o.center[0] - lx) ** 2 + (o.center[1] - ly) ** 2) ** 0.5
        if d < bd:
            best, bd = o, d
    if best is not None and bd <= 30:
        if best.kind == "food":
            return "hunger", {"type": "eat", "need": "hunger",
                              "target": best.center, "obj": best, "t": 0.0}
        if best.kind == "water":
            kind = "fetch" if world.stock["bucket"] > 0 else "handdrink"
            return "thirst", {"type": kind, "need": "thirst", "target": best.center, "t": 0.0}
        if best.kind == "home":
            return "energy", {"type": "sleep", "need": "energy", "target": best.center, "t": 0.0}
        if best.kind == "fun":
            return "fun", {"type": "play", "need": "fun", "target": best.center, "t": 0.0}
        # work tasks — no personal need is met, so willingness leans on how much
        # they like you (need is None => zero "wanted it anyway" urge)
        work = {"tree": "chop", "rock": "mine", "plot": "farm",
                "bench": "craft", "smelter": "smelt"}.get(best.kind)
        if work:
            return None, {"type": work, "target": best.center, "obj": best,
                          "t": 0.0, "work": 0.0}
    # no object nearby — a mineable (stone/ore) or diggable (dirt) tile?
    tx, ty = int(lx // S.TILE), int(ly // S.TILE)
    if 0 <= tx < S.GRID_W and 0 <= ty < S.GRID_H:
        tile = world.tiles[ty][tx]
        center = (tx * S.TILE + S.TILE / 2, ty * S.TILE + S.TILE / 2)
        if tile in (5, 6):
            return None, {"type": "minetile", "target": center,
                          "tx": tx, "ty": ty, "t": 0.0, "work": 0.0}
        if tile == 4:
            return None, {"type": "dig", "target": center,
                          "tx": tx, "ty": ty, "t": 0.0, "work": 0.0}
    return None


def run(selftest=False):
    if selftest:
        import os
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
    pygame.display.set_caption("Hearthkin — v0.1")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)
    big = pygame.font.Font(None, 28)

    world = World()
    villagers = make_villagers(world)
    player = villagers[0]            # the character you control directly
    selected = player

    game_seconds = S.DAY_SECONDS * 0.30   # open on Day 1, mid-morning
    speed_idx = 0
    paused = False
    view_z = 0                            # which z-level we're looking at
    build_mode = False                    # placing walls/doors/floors
    build_sel = 0                         # index into S.BUILDABLES
    cam_x = max(0, min(S.WORLD_W - S.PLAY_W, player.x - S.PLAY_W / 2))
    cam_y = max(0, min(S.WORLD_H - S.PLAY_H, player.y - S.PLAY_H / 2))

    frames = 0
    running = True
    while running:
        dt = clock.tick(S.FPS) / 1000.0
        speed = S.SPEEDS[speed_idx]
        gdt = 0.0 if paused else dt * speed

        # --- events ---
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif e.key == pygame.K_SPACE:
                    paused = not paused
                elif e.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    speed_idx = min(len(S.SPEEDS) - 1, speed_idx + 1)
                elif e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_idx = max(0, speed_idx - 1)
                elif e.key == pygame.K_c:
                    world.sel_recipe = (world.sel_recipe + 1) % len(S.RECIPES)
                elif e.key == pygame.K_PAGEUP:
                    view_z = min(S.ZLEVELS - 1, view_z + 1)
                elif e.key == pygame.K_PAGEDOWN:
                    view_z = max(S.ZMIN, view_z - 1)
                elif e.key == pygame.K_b:
                    build_mode = not build_mode
                elif e.key == pygame.K_TAB and build_mode:
                    build_sel = (build_sel + 1) % len(S.BUILDABLES)
            elif e.type == pygame.MOUSEWHEEL:
                view_z = max(S.ZMIN, min(S.ZLEVELS - 1, view_z + e.y))
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                if mx < S.PLAY_W:
                    wx, wy = mx + int(cam_x), (my - S.TOPBAR) + int(cam_y)
                    if build_mode and view_z <= 0:
                        place_build(world, villagers, wx // S.TILE, wy // S.TILE, view_z, build_sel)
                    elif not build_mode and view_z == 0:
                        hit = next((v for v in villagers if v.hit(wx, wy)), None)
                        if hit is not None:
                            selected = hit             # click a villager to inspect
                        else:
                            player.goto(wx, wy)        # click ground to move you
                    elif not build_mode and view_z < 0:
                        player.goto(wx, wy, view_z)    # walk you down/around underground
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                mx, my = e.pos
                if mx < S.PLAY_W:
                    wx, wy = mx + int(cam_x), (my - S.TOPBAR) + int(cam_y)
                    if build_mode and view_z <= 0:
                        remove_build(world, villagers, wx // S.TILE, wy // S.TILE, view_z)
                    elif not build_mode and view_z == 0 and selected is not None:
                        req = request_target(world, villagers, selected, wx, wy)
                        if req:
                            if selected.controlled:
                                selected.action = req[1]   # you obey your own commands
                            else:
                                selected.consider_request(*req)
                    elif not build_mode and view_z < 0 and selected is not None:
                        bx, by = wx // S.TILE, wy // S.TILE
                        if (0 <= bx < S.GRID_W and 0 <= by < S.GRID_H
                                and world.under[view_z][by][bx] is not None):
                            act = assign_mine(world, view_z, bx, by)
                            if act:
                                if selected.controlled:
                                    selected.action = act
                                else:
                                    selected.consider_request(None, act)

        # --- camera (arrow keys pan, clamped to the map) ---
        keys = pygame.key.get_pressed()
        pan = S.PAN_SPEED * dt
        if keys[pygame.K_LEFT]:  cam_x -= pan
        if keys[pygame.K_RIGHT]: cam_x += pan
        if keys[pygame.K_UP]:    cam_y -= pan
        if keys[pygame.K_DOWN]:  cam_y += pan
        cam_x = max(0, min(S.WORLD_W - S.PLAY_W, cam_x))
        cam_y = max(0, min(S.WORLD_H - S.PLAY_H, cam_y))
        cam = (int(cam_x), int(cam_y))

        # --- update ---
        game_seconds += gdt
        world.update(gdt)
        for v in villagers:
            v.update(gdt, world, villagers)

        # --- calendar / day-night ---
        cal = S.calendar(game_seconds)

        # --- draw ---
        if view_z < 0:
            screen.fill((18, 16, 20))                 # underground darkness
            world.draw_underground(screen, cam, view_z)
            world.draw_struct(screen, cam, view_z)
            for v in villagers:                       # only those on this level
                if v.z == view_z:
                    v.draw(screen, font, v is selected, cam)
        else:
            screen.fill(S.C_GRASS)
            world.draw(screen, cam)
            world.draw_build(screen, cam)
            world.draw_struct(screen, cam, 0)         # surface stairwells
            if view_z == 0:
                for v in villagers:
                    if v.z == 0:
                        v.draw(screen, font, v is selected, cam)
            # looking down from a height: haze the ground & villagers below us
            if view_z > 0:
                haze = pygame.Surface((S.PLAY_W, S.PLAY_H), pygame.SRCALPHA)
                haze.fill((*S.C_HAZE, min(190, view_z * 38)))
                screen.blit(haze, (0, S.TOPBAR))
            world.draw_trees(screen, view_z, cam)     # tree slice at this level, on top
            # night falls as daylight fades — depth and timing vary by season
            darkness = int((1.0 - cal["intensity"]) * S.NIGHT_ALPHA)
            if darkness > 0:
                tint = pygame.Surface((S.PLAY_W, S.PLAY_H), pygame.SRCALPHA)
                tint.fill((10, 14, 40, darkness))
                screen.blit(tint, (0, S.TOPBAR))
        # build mode: ghost tile under the cursor + a control banner
        if build_mode and view_z <= 0:
            mx, my = pygame.mouse.get_pos()
            if mx < S.PLAY_W and my > S.TOPBAR:
                wx, wy = mx + int(cam_x), (my - S.TOPBAR) + int(cam_y)
                bx, by = wx // S.TILE, wy // S.TILE
                ghost = pygame.Surface((S.TILE, S.TILE), pygame.SRCALPHA)
                ghost.fill((250, 240, 150, 90))
                screen.blit(ghost, (bx * S.TILE - int(cam_x),
                                    by * S.TILE + S.TOPBAR - int(cam_y)))
            name, kind, mat, cost = S.BUILDABLES[build_sel]
            costs = ", ".join(f"{v} {k}" for k, v in cost.items())
            pygame.draw.rect(screen, S.C_TOPBAR, (0, S.HEIGHT - 24, S.PLAY_W, 24))
            banner = font.render(
                f"BUILD: {name} ({costs})   ·   TAB cycle · L-click place · R-click remove · B exit",
                True, S.C_GOLD)
            screen.blit(banner, (10, S.HEIGHT - 22))

        from ui import draw_topbar, draw_panel
        draw_topbar(screen, font, cal, speed, view_z, paused)
        draw_panel(screen, font, big, selected, villagers, world)
        pygame.display.flip()

        if selftest:
            frames += 1
            if frames >= 600:        # ~simulate then bail out
                running = False

    pygame.quit()
    if selftest:
        print("SELFTEST OK — simulated", frames, "frames")
        for v in villagers:
            print(f"  {v.name}: mood {int(v.mood)} "
                  f"needs={ {k:int(x) for k,x in v.needs.items()} } rel={v.rel}")


if __name__ == "__main__":
    run(selftest="--selftest" in sys.argv)
