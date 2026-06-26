# Hearthkin

A fantasy life-sim that blends **Vintage Story** (survival & crafting),
**The Sims** (needs, moods, relationships), and **Crusader Kings II**
(characters, dynasty, generations).

You don't command villagers directly. They live their own lives — and the
long-term vision is that you *request* things of your kin, and whether they
listen depends on how much they like you (and whether they wanted to do it
anyway).

## Current version — v0.3

A living glade you steward across three layers:

### v0.1 — The People
Autonomous fantasy villagers in a small glade.

- **Needs** — Food, Energy, Social, Fun, each draining over time.
- **Utility AI** — villagers decide for themselves: eat at the berry
  bushes, sleep at home, relax at the shrine, or seek out company.
- **Traits** — Cheerful, Glutton, Loner, Gregarious, Hardy, Lazy… each
  bends behavior and mood.
- **Relationships** — villagers who spend time together grow closer
  (loners more slowly, the gregarious faster).
- **Mood** — emerges from how well a villager's needs are met, plus traits.
- A day/night clock and an inspection panel to watch any villager's inner life.

### v0.2 — The Request System
- **You don't command — you persuade.** Select a villager, right-click a target, and *ask*.
- Whether they comply depends on how much they like you, their mood, and whether
  they wanted to anyway. Loners and the grumpy refuse; help them and they warm to you.

### v0.3 — Survival & Crafting
- **Gathering** — assign villagers to chop trees (wood) and mine rocks (stone); spent nodes regrow.
- **Farming** — till plots, plant, wait for crops to ripen, harvest grain.
- **Crafting** — at the workbench, turn grain into meals and wood + stone into tools.
- Everything flows into a shared **settlement stockpile** — and it's all driven by the
  request system, so production depends on keeping your kin willing to work.

## Run it

You need Python 3 and pygame-ce (already a drop-in for pygame):

```
pip install -r requirements.txt
python main.py
```

On Windows you can also just double-click **`run.bat`**.

### Controls
- **Left-click** a villager to inspect them
- **Space** — pause / resume
- **+ / -** — change game speed (x1 / x2 / x4)
- **Esc** or **Q** — quit

## Roadmap
- **v0.4** — seasons & winter survival: crops that fail in the cold, food
  that must be stored, a stockpile that keeps your kin alive.
- **v0.5** — dynasty (CK2): aging, marriage, children, inherited traits, succession.
- **Claude-powered villagers** — real, in-character dialogue and reactions
  generated from each villager's traits, mood, and relationships.

## Tech
Python + [pygame-ce](https://pyga.me/). Modular by design:
`settings.py` (tuning), `world.py` (map), `character.py` (the villager AI),
`ui.py` (panels), `main.py` (loop). Run `python main.py --selftest` for a
headless simulation check.
