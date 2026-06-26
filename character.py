# character.py — the heart of v0.1: an autonomous villager.
# Each villager drains needs, chooses what to do via a simple utility AI,
# moves toward a target, performs the action, and forms relationships.
#
# Designed so the future "request" system slots in cleanly: a request will
# just be a candidate action whose priority is weighted by how much the
# villager likes the asker (and whether they already wanted to do it).

import math
import pygame
import settings as S

ACTION_LABEL = {
    "eat": "eating berries",
    "sleep": "sleeping",
    "play": "at the shrine",
    "talk": "chatting",
    "wander": "wandering",
}


class Character:
    _next_id = 0

    def __init__(self, name, race, color, traits, home, x, y, player_rel=20.0):
        self.id = Character._next_id
        Character._next_id += 1
        self.name = name
        self.race = race
        self.color = color
        self.traits = list(traits)
        self.home = home
        self.x, self.y = float(x), float(y)
        self.radius = 11

        # needs start comfortably, slightly varied
        self.needs = {n: 70.0 for n in S.NEEDS}
        self.mood = 60.0
        self.action = None        # dict describing current activity
        self.label = "idle"
        self.rel = {}             # other_id -> -100..100
        self.player_rel = float(player_rel)  # how much they like YOU (the player)
        self.floats = []          # transient feedback: {text, color, t}

    @property
    def pos(self):
        return (self.x, self.y)

    # -- trait helpers -------------------------------------------------
    def _decay_mult(self, need):
        m = 1.0
        for t in self.traits:
            m *= S.TRAIT_EFFECTS.get(t, {}).get("decay_" + need, 1.0)
        return m

    def _social_gain(self):
        m = 1.0
        for t in self.traits:
            m *= S.TRAIT_EFFECTS.get(t, {}).get("social_gain", 1.0)
        return m

    def _rel_gain(self):
        m = 1.0
        for t in self.traits:
            m *= S.TRAIT_EFFECTS.get(t, {}).get("rel_gain", 1.0)
        return m

    def _mood_offset(self):
        return sum(S.TRAIT_EFFECTS.get(t, {}).get("mood", 0) for t in self.traits)

    # -- player requests ----------------------------------------------
    def say(self, text, color):
        self.floats.append({"text": text, "color": color, "t": 2.6})

    def consider_request(self, need, action):
        """Decide whether to honor a player request. Returns (accepted, reply).
        Willingness rises with how much they like you and whether they were
        going to do it anyway; falls when grumpy, tired, or lazy."""
        import random
        like = self.player_rel
        urge = 100.0 - self.needs.get(need, 100.0)   # did they want this anyway?
        mood = (self.mood - 50.0) * 0.3
        lazy = -15.0 if "Lazy" in self.traits else 0.0
        willingness = like + urge * 0.5 + mood + lazy + random.uniform(-10, 10)

        if willingness >= S.REQUEST_THRESHOLD:
            self.action = action
            self.player_rel = min(100.0, self.player_rel + 3.0)
            if urge > 55:
                reply = "Was headed there anyway."
            elif like > 40:
                reply = "For you? Of course."
            else:
                reply = "Alright, fine."
            self.say("Okay!", S.C_GOOD)
            return True, reply

        if like < 5:
            reply = "And why would I?"
        elif "Lazy" in self.traits or self.needs["energy"] < 35:
            reply = "Too tired right now."
        elif self.mood < 35:
            reply = "Not in the mood."
        else:
            reply = "Maybe later."
        self.say("No.", S.C_BAD)
        return False, reply

    # -- main update ---------------------------------------------------
    def update(self, gdt, world, others):
        """gdt = game-delta-time (real dt * speed); 0 when paused."""
        self._decay(gdt)
        if not self.action:
            self._choose(world, others)
        if self.action:
            self._perform(gdt, world, others)
        self._update_mood()
        for f in self.floats:
            f["t"] -= gdt
        self.floats = [f for f in self.floats if f["t"] > 0]

    def _decay(self, gdt):
        for n in S.NEEDS:
            self.needs[n] = max(0.0, self.needs[n] - S.DECAY[n] * self._decay_mult(n) * gdt)

    def _update_mood(self):
        base = sum(self.needs.values()) / len(self.needs)
        self.mood = max(0.0, min(100.0, base + self._mood_offset()))

    # -- decision ------------------------------------------------------
    def _choose(self, world, others):
        urges = {n: 100.0 - self.needs[n] for n in S.NEEDS}
        need = max(urges, key=urges.get)
        if urges[need] < S.ACT_URGE:
            self._set_wander(world)
            return

        if need == "hunger":
            obj = world.nearest(self.pos, "food")
            self.action = {"type": "eat", "need": "hunger",
                           "target": obj.center, "t": 0.0}
        elif need == "energy":
            self.action = {"type": "sleep", "need": "energy",
                           "target": self.home.center, "t": 0.0}
        elif need == "fun":
            obj = world.nearest(self.pos, "fun")
            self.action = {"type": "play", "need": "fun",
                           "target": obj.center, "t": 0.0}
        elif need == "social":
            partner = self._nearest_other(others)
            if partner:
                self.action = {"type": "talk", "need": "social",
                               "partner": partner, "t": 0.0}
            else:
                self._set_wander(world)

    def _set_wander(self, world):
        import random
        tx = max(20, min(S.PLAY_W - 20, self.x + random.uniform(-160, 160)))
        ty = max(20, min(S.PLAY_H - 20, self.y + random.uniform(-160, 160)))
        self.action = {"type": "wander", "target": (tx, ty), "t": 0.0}

    # -- carrying out an action ---------------------------------------
    def _perform(self, gdt, world, others):
        a = self.action
        a["t"] += gdt
        if a["t"] > S.ACTION_TIMEOUT:      # avoid getting stuck forever
            self.action = None
            return

        self.label = ACTION_LABEL[a["type"]]

        if a["type"] == "wander":
            self._move_to(a["target"], gdt)
            if self._at(a["target"]):
                self.action = None
            return

        if a["type"] == "talk":
            p = a["partner"]
            self.label = "chatting with " + p.name
            self._move_to(p.pos, gdt)
            if self._near(p.pos, S.TALK_RADIUS):
                self._socialize(p, gdt)
            if self.needs["social"] >= S.SATED:
                self.action = None
            return

        # eat / sleep / play: walk to a fixed spot, then restore the need
        self._move_to(a["target"], gdt)
        if self._at(a["target"]):
            n = a["need"]
            gain = S.RESTORE[n] * gdt
            if n == "social":
                gain *= self._social_gain()
            self.needs[n] = min(100.0, self.needs[n] + gain)
            if self.needs[n] >= S.SATED:
                self.action = None

    def _socialize(self, p, gdt):
        # both villagers benefit; the relationship warms over time
        g = S.RESTORE["social"] * gdt
        self.needs["social"] = min(100.0, self.needs["social"] + g * self._social_gain())
        p.needs["social"] = min(100.0, p.needs["social"] + g * p._social_gain())
        d = S.REL_RATE * gdt
        self.rel[p.id] = _clamp(self.rel.get(p.id, 0) + d * self._rel_gain())
        p.rel[self.id] = _clamp(p.rel.get(self.id, 0) + d * p._rel_gain())

    # -- movement / geometry ------------------------------------------
    def _move_to(self, target, gdt):
        dx, dy = target[0] - self.x, target[1] - self.y
        d = math.hypot(dx, dy)
        if d <= S.ARRIVE:
            return
        step = S.SPEED * gdt
        if step >= d:
            self.x, self.y = target
        else:
            self.x += dx / d * step
            self.y += dy / d * step

    def _at(self, target):
        return math.hypot(target[0] - self.x, target[1] - self.y) <= S.ARRIVE

    def _near(self, pos, r):
        return math.hypot(pos[0] - self.x, pos[1] - self.y) <= r

    def _nearest_other(self, others):
        best, bd = None, 1e9
        for o in others:
            if o is self:
                continue
            d = math.hypot(o.x - self.x, o.y - self.y)
            if d < bd:
                best, bd = o, d
        return best

    # -- drawing -------------------------------------------------------
    def draw(self, surf, font, selected):
        cx, cy = int(self.x), int(self.y + S.TOPBAR)
        if selected:
            pygame.draw.circle(surf, S.C_SELECT, (cx, cy), self.radius + 4, 2)
        pygame.draw.circle(surf, (12, 14, 18), (cx, cy), self.radius + 1)
        pygame.draw.circle(surf, self.color, (cx, cy), self.radius)
        label = font.render(self.name, True, S.C_TEXT)
        surf.blit(label, (cx - label.get_width() // 2, cy - self.radius - 16))
        for i, f in enumerate(self.floats[-2:]):
            rise = int((2.6 - f["t"]) * 6)
            txt = font.render(f["text"], True, f["color"])
            surf.blit(txt, (cx - txt.get_width() // 2,
                            cy - self.radius - 34 - i * 16 - rise))

    def hit(self, mx, my):
        return math.hypot(mx - self.x, my - (self.y + S.TOPBAR)) <= self.radius + 4


def _clamp(v):
    return max(-100.0, min(100.0, v))
