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
    "eat": "harvesting berries",
    "snack": "eating",
    "drink": "drinking",
    "handdrink": "drinking by hand",
    "fetch": "fetching water",
    "sleep": "sleeping",
    "play": "at the shrine",
    "talk": "chatting",
    "wander": "wandering",
    "goto": "walking",
    "minework": "mining",
    "chop": "chopping wood",
    "mine": "mining stone",
    "farm": "working the field",
    "craft": "crafting",
    "smelt": "smelting",
    "minetile": "mining",
    "dig": "digging",
}


class Character:
    _next_id = 0

    def __init__(self, name, race, color, traits, home, x, y, player_rel=20.0,
                 gender="?", controlled=False):
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
        self.gender = gender      # "M" / "F" / "?"
        self.controlled = controlled  # True = the player drives this one directly
        self.inventory = {}       # carried items (groundwork for tools/goods)
        self.z = 0                # which level the character is on (0 = surface)
        self.path = []            # current A* waypoint list (px, py, z)
        self.path_goal = None     # (tile, z) the cached path heads to

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

    def goto(self, x, y, z=0):
        """Send this character to a point on level z (direct player movement)."""
        self.action = {"type": "goto", "target": (float(x), float(y)),
                       "tz": z, "t": 0.0}

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
        if not self.controlled and not self.action:   # the player drives their own char
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
            if world.berry_count() > 0:
                self.action = {"type": "snack", "need": "hunger", "t": 0.0}
            else:
                obj = world.nearest(self.pos, "food")
                self.action = {"type": "eat", "need": "hunger",
                               "target": obj.center, "obj": obj, "t": 0.0}
        elif need == "thirst":
            if world.stock["water"] > 0:
                self.action = {"type": "drink", "need": "thirst", "t": 0.0}
            elif world.stock["bucket"] > 0:
                obj = world.nearest(self.pos, "water")
                self.action = {"type": "fetch", "need": "thirst",
                               "target": obj.center, "t": 0.0}
            else:                          # no bucket — drink by hand at the pond
                obj = world.nearest(self.pos, "water")
                self.action = {"type": "handdrink", "need": "thirst",
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
        if a["t"] > a.get("timeout", S.ACTION_TIMEOUT):   # avoid getting stuck forever
            self.action = None
            return

        self.label = ACTION_LABEL[a["type"]]

        if a["type"] in ("wander", "goto"):
            tz = a.get("tz", self.z)
            self._step_toward(a["target"], gdt, world, tz)
            if self._at(a["target"]) and self.z == tz:
                self.action = None
            return

        if a["type"] == "minework":        # descend & excavate an underground cell
            self._step_toward(a["stand"], gdt, world, a["z"])
            if self._at(a["stand"]) and self.z == a["z"]:
                a["work"] += gdt
                if a["work"] >= S.WORK_TIME:
                    mat = world.under[a["z"]][a["ty"]][a["tx"]]
                    tool = "pickaxe" if mat == "stone" else "shovel"
                    res = world.use_tool(tool)
                    if res is None:
                        self.say(f"need a {tool}", S.C_BAD)
                    else:
                        msg, col = world.dig(a["z"], a["tx"], a["ty"])
                        self.say(msg, col)
                        if res == "broke":
                            self.say(f"{tool} broke!", S.C_BAD)
                    self.action = None
            return

        if a["type"] == "talk":
            p = a["partner"]
            self.label = "chatting with " + p.name
            self._step_toward(p.pos, gdt, world)
            if self._near(p.pos, S.TALK_RADIUS):
                self._socialize(p, gdt)
            if self.needs["social"] >= S.SATED:
                self.action = None
            return

        if a["type"] in S.WORK_TYPES:
            self._step_toward(a["target"], gdt, world)
            if self._at(a["target"]):
                a["work"] += gdt
                if a["work"] >= S.WORK_TIME:
                    self._finish_work(a, world)
                    self.action = None
            return

        if a["type"] == "snack":           # eat from the berry store, in place
            self._eat_from_store(world)
            self.action = None
            return

        if a["type"] == "drink":           # drink from the water store, in place
            self._drink_from_store(world)
            self.action = None
            return

        if a["type"] == "eat":             # walk to a bush, harvest, then eat
            self._step_toward(a["target"], gdt, world)
            if self._at(a["target"]):
                obj = a.get("obj")
                if obj is not None and obj.amount > 0:
                    obj.amount -= 1
                    if obj.amount <= 0:
                        obj.regrow = S.NODE_REGROW
                    world.add_berries(S.BERRIES_PER_HARVEST)
                    self.say(f"+{S.BERRIES_PER_HARVEST} berries", S.C_GOLD)
                elif obj is not None:
                    self.say("bush is bare", S.C_DIM)
                self._eat_from_store(world)
                self.action = None
            return

        if a["type"] == "fetch":           # carry water back — needs a bucket
            self._step_toward(a["target"], gdt, world)
            if self._at(a["target"]):
                if world.stock["bucket"] > 0:
                    world.stock["water"] += S.BUCKET_WATER
                    self._drink_from_store(world)
                else:
                    self.say("need a bucket", S.C_BAD)
                self.action = None
            return

        if a["type"] == "handdrink":       # cup water by hand — slow, no storage
            self._step_toward(a["target"], gdt, world)
            if self._at(a["target"]):
                self.needs["thirst"] = min(100.0, self.needs["thirst"] + S.HAND_DRINK * gdt)
                if self.needs["thirst"] >= S.SATED:
                    self.action = None
            return

        # sleep / play: walk to a fixed spot, then restore the need over time
        self._step_toward(a["target"], gdt, world)
        if self._at(a["target"]):
            n = a["need"]
            self.needs[n] = min(100.0, self.needs[n] + S.RESTORE[n] * gdt)
            if self.needs[n] >= S.SATED:
                self.action = None

    def _eat_from_store(self, world):
        eaten = 0
        while self.needs["hunger"] < S.SATED and world.berry_count() > 0:
            world.take_berry()
            self.needs["hunger"] = min(100.0, self.needs["hunger"] + S.BERRY_FILL)
            eaten += 1
        if eaten:
            self.say(f"ate {eaten}", S.C_GOOD)

    def _drink_from_store(self, world):
        drank = 0
        while self.needs["thirst"] < S.SATED and world.stock["water"] > 0:
            world.stock["water"] -= 1
            self.needs["thirst"] = min(100.0, self.needs["thirst"] + S.WATER_FILL)
            drank += 1
        if drank:
            self.say(f"drank {drank}", S.C_GOOD)

    def _finish_work(self, a, world):
        t = a["type"]
        obj = a.get("obj")
        if t == "chop":
            msg, col = world.gather(obj, "wood")
        elif t == "mine":
            msg, col = world.gather(obj, "stone")
        elif t == "farm":
            msg, col = world.tend_plot(obj)
        elif t == "craft":
            msg, col = world.craft()
        elif t == "smelt":
            msg, col = world.smelt()
        elif t == "minetile":
            if world.tiles[a["ty"]][a["tx"]] not in (5, 6):
                msg, col = ("nothing to mine", S.C_DIM)
            else:
                res = world.use_tool("pickaxe")
                if res is None:
                    msg, col = ("need a pickaxe", S.C_BAD)
                else:
                    msg, col = world.mine_tile(a["tx"], a["ty"])
                    if res == "broke":
                        self.say("pickaxe broke!", S.C_BAD)
        elif t == "dig":
            if world.tiles[a["ty"]][a["tx"]] != 4:
                msg, col = ("nothing to dig", S.C_DIM)
            else:
                res = world.use_tool("shovel")
                if res is None:
                    msg, col = ("need a shovel", S.C_BAD)
                else:
                    msg, col = world.dig_tile(a["tx"], a["ty"])
                    if res == "broke":
                        self.say("shovel broke!", S.C_BAD)
        else:
            msg, col = None, None
        if msg:
            self.say(msg, col)

    def _socialize(self, p, gdt):
        # both villagers benefit; the relationship warms over time
        g = S.RESTORE["social"] * gdt
        self.needs["social"] = min(100.0, self.needs["social"] + g * self._social_gain())
        p.needs["social"] = min(100.0, p.needs["social"] + g * p._social_gain())
        d = S.REL_RATE * gdt
        self.rel[p.id] = _clamp(self.rel.get(p.id, 0) + d * self._rel_gain())
        p.rel[self.id] = _clamp(p.rel.get(self.id, 0) + d * p._rel_gain())

    # -- movement / geometry ------------------------------------------
    def _step_toward(self, target, gdt, world, target_z=None):
        """Move toward a target along a 3D A* path; z changes at stair tiles."""
        if target_z is None:
            target_z = self.z
        goal = (world.tile_of(target), target_z)
        if self.path_goal != goal or not self.path:
            self.path = world.find_path3((self.x, self.y, self.z),
                                         (target[0], target[1], target_z))
            self.path_goal = goal
        if not self.path:
            return                                     # no route — wait it out
        wx, wy, wz = self.path[0]
        self._move_to((wx, wy), gdt)
        if math.hypot(wx - self.x, wy - self.y) <= S.ARRIVE:
            self.z = wz                                # cross onto this waypoint's level
            self.path.pop(0)

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
    def draw(self, surf, font, selected, cam):
        cx, cy = int(self.x - cam[0]), int(self.y - cam[1] + S.TOPBAR)
        if self.controlled:
            pygame.draw.circle(surf, S.C_GOLD, (cx, cy), self.radius + 6, 2)
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

    def hit(self, wx, wy):
        return math.hypot(wx - self.x, wy - self.y) <= self.radius + 4


def _clamp(v):
    return max(-100.0, min(100.0, v))
