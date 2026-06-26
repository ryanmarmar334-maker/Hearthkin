# ui.py — the top status bar and the right-hand inspection panel.

import pygame
import settings as S


def _bar_color(v):
    if v < 30:  return S.C_BAD
    if v < 60:  return S.C_WARN
    return S.C_GOOD


def draw_topbar(surf, font, cal, speed, paused):
    pygame.draw.rect(surf, S.C_TOPBAR, (0, 0, S.WIDTH, S.TOPBAR))
    phase = "Day" if cal["is_day"] else "Night"
    clock = (f"Year {cal['year']}  {cal['season']}  "
             f"Wk{cal['week']} Day{cal['dow']}  {cal['hh']:02d}:{cal['mm']:02d} {phase}")
    surf.blit(font.render(clock, True, S.C_GOLD), (10, 4))
    spd = "PAUSED" if paused else f"x{speed}"
    s = font.render(spd, True, S.C_SELECT if paused else S.C_TEXT)
    surf.blit(s, (440, 4))
    hint = "L-click select · R-click assign · C recipe · Space pause · +/- speed · Esc quit"
    h = font.render(hint, True, S.C_DIM)
    surf.blit(h, (S.WIDTH - h.get_width() - 10, 4))


def _need_bar(surf, font, x, y, w, label, value):
    surf.blit(font.render(label, True, S.C_DIM), (x, y))
    by = y + 16
    pygame.draw.rect(surf, S.C_BAR_BG, (x, by, w, 12), border_radius=3)
    fw = int(w * max(0, min(100, value)) / 100)
    if fw > 0:
        pygame.draw.rect(surf, _bar_color(value), (x, by, fw, 12), border_radius=3)
    surf.blit(font.render(f"{int(value)}", True, S.C_TEXT), (x + w + 6, y + 6))


def _draw_stockpile(surf, font, world):
    px = S.PLAY_W
    sy = S.TOPBAR + S.PLAY_H - 92
    pygame.draw.line(surf, S.C_BAR_BG, (px + 12, sy), (px + S.PANEL_W - 12, sy), 1)
    surf.blit(font.render("SETTLEMENT", True, S.C_DIM), (px + 16, sy + 4))
    l1 = "  ".join(f"{k}:{world.stock[k]}" for k in ("wood", "stone", "grain"))
    l2 = "  ".join(f"{k}:{world.stock[k]}" for k in ("food", "tools", "bucket"))
    l3 = f"water:{world.stock['water']}  berries:{world.berry_count()}"
    surf.blit(font.render(l1, True, S.C_GOLD), (px + 16, sy + 24))
    surf.blit(font.render(l2, True, S.C_GOLD), (px + 16, sy + 42))
    surf.blit(font.render(l3, True, S.C_GOLD), (px + 16, sy + 60))
    name, ins, _o = S.RECIPES[world.sel_recipe]
    cost = ", ".join(f"{v} {k}" for k, v in ins.items())
    surf.blit(font.render(f"Bench [C]: {name} ({cost})", True, S.C_DIM), (px + 16, sy + 78))


def draw_panel(surf, font, big, selected, villagers, world):
    px = S.PLAY_W
    pygame.draw.rect(surf, S.C_PANEL, (px, S.TOPBAR, S.PANEL_W, S.PLAY_H))
    _draw_stockpile(surf, font, world)
    x = px + 16
    y = S.TOPBAR + 16

    if selected is None:
        surf.blit(big.render("Hearthkin", True, S.C_GOLD), (x, y))
        surf.blit(font.render("v0.1 — the people", True, S.C_DIM), (x, y + 30))
        msg = ["", "Click a villager to inspect them.",
               "", "Select one, then right-click to",
               "assign work:",
               "  trees -> wood    rocks -> stone",
               "  field -> farming   bench -> craft",
               "or a bush/hut/shrine/villager to",
               "send them there.",
               "", "They may say no — it depends on",
               "how much they like you."]
        for i, line in enumerate(msg):
            surf.blit(font.render(line, True, S.C_TEXT), (x, y + 60 + i * 20))
        return

    c = selected
    # header
    pygame.draw.circle(surf, c.color, (x + 12, y + 10), 11)
    surf.blit(big.render(c.name, True, S.C_TEXT), (x + 32, y - 2))
    surf.blit(font.render(c.race, True, S.C_DIM), (x + 32, y + 22))
    y += 48

    surf.blit(font.render("Traits: " + ", ".join(c.traits), True, S.C_GOLD), (x, y))
    y += 24
    pr = c.player_rel
    pcol = S.C_GOOD if pr >= 8 else (S.C_BAD if pr <= -8 else S.C_DIM)
    surf.blit(font.render(f"Likes you: {S.rel_label(pr)} ({int(pr):+d})", True, pcol), (x, y))
    y += 26

    # mood
    pygame.draw.rect(surf, S.C_PANEL2, (x - 4, y - 4, S.PANEL_W - 24, 28), border_radius=4)
    surf.blit(font.render(f"Mood: {S.mood_label(c.mood)} ({int(c.mood)})",
                          True, _bar_color(c.mood)), (x, y))
    y += 34

    surf.blit(font.render(f"Now: {c.label}", True, S.C_TEXT), (x, y))
    y += 30

    surf.blit(font.render("NEEDS", True, S.C_DIM), (x, y))
    y += 20
    for n in S.NEEDS:
        _need_bar(surf, font, x, y, S.PANEL_W - 70, S.NEED_LABEL[n], c.needs[n])
        y += 36

    y += 6
    surf.blit(font.render("RELATIONSHIPS", True, S.C_DIM), (x, y))
    y += 22
    others = [o for o in villagers if o is not c]
    for o in others:
        score = c.rel.get(o.id, 0)
        col = S.C_GOOD if score >= 8 else (S.C_BAD if score <= -8 else S.C_DIM)
        line = f"{o.name}: {S.rel_label(score)} ({int(score):+d})"
        surf.blit(font.render(line, True, col), (x, y))
        y += 22
