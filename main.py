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
    return [
        Character("Eldra", "Wood Elf",  (120, 200, 130), ["Cheerful", "Loner"],     h[0], 130, 110, player_rel=28),
        Character("Brakka", "Hill Dwarf", (210, 150, 90), ["Glutton", "Hardy"],     h[1], 820, 560, player_rel=8),
        Character("Pip",   "Halfling",  (180, 140, 220), ["Gregarious", "Lazy"],    h[2], 140, 560, player_rel=44),
    ]


def request_target(world, villagers, selected, mx, my):
    """Map a right-click to a (need, action) the selected villager could do."""
    for v in villagers:                      # another villager -> socialize
        if v is not selected and v.hit(mx, my):
            return "social", {"type": "talk", "partner": v, "t": 0.0}
    lx, ly = mx, my - S.TOPBAR               # nearest world object -> use it
    best, bd = None, 1e9
    for o in world.objects:
        d = ((o.center[0] - lx) ** 2 + (o.center[1] - ly) ** 2) ** 0.5
        if d < bd:
            best, bd = o, d
    if best is None or bd > 30:
        return None
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
    work = {"tree": "chop", "rock": "mine", "plot": "farm", "bench": "craft"}.get(best.kind)
    if work:
        return None, {"type": work, "target": best.center, "obj": best, "t": 0.0, "work": 0.0}
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
    selected = None

    game_seconds = S.DAY_SECONDS * 0.30   # open on Day 1, mid-morning
    speed_idx = 0
    paused = False

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
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                if mx < S.PLAY_W:
                    selected = next((v for v in villagers if v.hit(mx, my)), None)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                mx, my = e.pos
                if selected is not None and mx < S.PLAY_W:
                    req = request_target(world, villagers, selected, mx, my)
                    if req:
                        selected.consider_request(*req)

        # --- update ---
        game_seconds += gdt
        world.update(gdt)
        for v in villagers:
            v.update(gdt, world, villagers)

        # --- calendar / day-night ---
        cal = S.calendar(game_seconds)

        # --- draw ---
        screen.fill(S.C_GRASS)
        world.draw(screen)
        for v in villagers:
            v.draw(screen, font, v is selected)
        # night falls as daylight fades — depth and timing vary by season
        darkness = int((1.0 - cal["intensity"]) * S.NIGHT_ALPHA)
        if darkness > 0:
            tint = pygame.Surface((S.PLAY_W, S.PLAY_H), pygame.SRCALPHA)
            tint.fill((10, 14, 40, darkness))
            screen.blit(tint, (0, S.TOPBAR))
        from ui import draw_topbar, draw_panel
        draw_topbar(screen, font, cal, speed, paused)
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
