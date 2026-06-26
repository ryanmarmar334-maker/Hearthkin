# Hearthkin — Road to v1.0

The goal for **1.0**: start a new game by **creating your player character**, spend
**point-buy** on starting supplies and companion NPCs (with family relations), then
drop into a living world where you **build, craft, farm, hunt, survive the seasons,
and raise a family that ages across the years**.

That's a RimWorld/Dwarf-Fortress-class simulation. We get there the way we've gotten
everywhere so far: **small, tested, committed increments**. Each milestone below is
itself several build sessions.

---

## Where we are (v0.5)
Autonomous villagers with needs/moods/traits/relationships · a persuasion-based
request system · gathering/farming/crafting · perishable berries + bucket water ·
a seasonal calendar with day-length by season · positive z-levels with multi-level trees.

---

## Cross-cutting foundations (must land early)
These aren't flashy, but almost everything else depends on them. Building them first
prevents painful rewrites later.

1. **Item & inventory framework** — one catalog of items (food, wood, stone, ore,
   ingots, tools, finished goods) with stacks, per-character carry, and a unified
   stockpile. *Unblocks:* point-buy, tools, crafting chains, hauling.
2. **Terrain & materials** — real tile materials (grass, dirt, stone, water, ore
   veins) so tools have targets. *Unblocks:* digging, mining, smelting metal.
3. **Pathfinding + collision (A\*)** — replace direct movement with grid pathfinding
   on a walkability map. *Unblocks:* walls/doors/buildings and animal navigation.
   **This is the linchpin — nothing with walls works without it.**
4. **Player-controlled character + control refactor** — you directly control one
   character; NPCs stay autonomous + requestable. *Touches input everywhere — do early.*
5. **Serializable state (design-for-save early)** — keep world/characters easy to
   serialize from the start, even though save/load ships at 1.0.
6. **Scrolling camera + bigger map** — the single fixed screen will feel cramped once
   we have buildings and animals; introduce a camera around the building milestone.

---

## Milestones

### v0.6 — "You, and Things"
*Foundations 1, 2, 4 + gender.*
- A **player character** you directly control (movement + selection refactor).
- **Item & inventory** system; migrate the current stockpile into it.
- **Terrain materials** (grass/dirt/stone/water/ore) under the tile grid.
- Every character gets a **gender** (male/female) — groundwork for mating.

### v0.7 — "Walls & Ways"
*Foundation 3 + building + camera.*
- **A\* pathfinding** on a walkability grid.
- **Build/designation mode**: place **wood/stone walls, doors, floors** — one tile
  each (RimWorld/DF style). Construction consumes materials and takes work.
- Doors gate passage; walls define **enclosed rooms** (indoor detection — needed for
  temperature later).
- **Scrolling camera** + a larger map.

### v0.8 — "Tools, Smelting & Crafting"
*Durability + stations + production chains.*
- **Tools with durability** (X uses), material tiers **wood < stone < metal**. Tools
  **gate actions**: axe→chop, pickaxe→mine stone/ore, shovel→dig dirt, hoe→till plots.
- **Smelter**: ore + fuel → **ingots**.
- **Crafting tables**: **woodworking** (wood goods/tools), **blacksmithing** (metal
  tools/goods from ingots), **cooking** (raw → meals).
- **Finished goods**: beds, chests, shrines, fishing poles, boats, etc.
- Per-station **crafting/recipe UI**.

### v0.9 — "Seasons Bite & Skills"
*Temperature survival + seasonal farming + skills.*
- **Temperature model**: ambient temp from season + day/night. A **warmth/comfort**
  state — **summer heat** (seek shade, water, or indoors) and **winter cold** (seek
  indoors, build a **fireplace** that burns wood to warm a room).
- **Seasonal farming**: each crop grows only in its season(s); winter halts growth;
  a real planting calendar.
- **Skill system**: skills (farming, woodcutting, mining, smithing, cooking, combat…)
  **improve with use**; higher skill → faster work, better yield/quality.

### v0.10 — "Beasts & Bloodlines"
*Animals + mating + combat.*
- **Roaming animals** (deer, rabbits, fowl; later sheep/cattle) with simple AI.
- **Hunting** with bow/sword → **meat, hide**; butchering.
- **Domestication/taming** → pens; products **meat, wool (shear), milk**.
- **Mating system for all living things**: gender on every creature; **female +
  male → pregnancy** (gestation measured in our day/month/season time system) →
  offspring that **ages through life stages** (baby → child → adult → elder).
- **Combat & health**: HP, **melee (sword)** and **ranged (bow + arrows)**, hit/damage;
  predators may threaten the settlement.

### v1.0 — "New Game & Dynasty"
*The front-end, the payoff, and the polish.*
- **Character creation**: build your PC (name, gender, traits, starting skills).
- **Point-buy**: spend points on **starting supplies** (food, materials, tools,
  finished goods) **and** on **companion NPCs**.
- **Companion NPCs with relations**: **spouse, sibling, child, parent, stranger** —
  relations seed bonds (spouse enables mating; family shapes the like-you score).
- **Save / load**.
- **Death, corpses, graves/burial**; **family tree** view; **inheritance & succession**
  — the CK2 dynasty payoff, now that people age and reproduce.
- **Onboarding/tutorial**, **balance pass**, bug-fix, UI polish.

---

## Also worth adding along the way
- **Hauling & stockpile zones** (designate where items go).
- **Sleep tied to night** + beds improving rest quality.
- **Mood/thoughts** expansion: buffs/debuffs from comfort, food quality, family,
  weather, a tidy home.
- **Fishing** (poles) and **boats** for crossing water.
- **Day/night** affecting visibility and animal behavior.
- **Multi-level buildings** using the z-level system (likely post-1.0).
- **Negative z-levels** (digging down, mining, cellars) — explicitly deferred.
- **Sound/music** (polish).

---

## Risks & sequencing notes
- **Pathfinding before building** — walls are meaningless without A\*. Do v0.7's
  pathfinding first within that milestone.
- **Do the control-model change early** (v0.6) — direct player control touches input
  across the whole game.
- **Refactor the stockpile into the item system early** (v0.6) so crafting/point-buy
  don't get built twice.
- **Design for save/load from v0.6** even though it ships at v1.0 — keep state plain.
- **Each milestone is multi-session.** We keep the rhythm: build → headless test →
  push → playtest → iterate.

## Open design questions (decide as we reach them)
- Direct control: **click-to-move** vs **WASD**?
- Map: keep a **handcrafted** map or go **procedural + scrolling**?
- Combat: **real-time** or **pausable/real-time-with-pause**?
- Do multi-level buildings (z-levels) make it into 1.0, or wait?
