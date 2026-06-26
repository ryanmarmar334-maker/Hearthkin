# settings.py — global config & constants for Hearthkin
# v0.1: the "people" layer — autonomous villagers with needs, moods,
# traits, and relationships. World & dynasty layers come later.

# --- Window / layout ---------------------------------------------------
TOPBAR = 24                 # status bar across the top
PANEL_W = 300               # right-hand inspection panel
PLAY_W = 980                # play area width
PLAY_H = 700                # play area height
WIDTH = PLAY_W + PANEL_W    # 1280
HEIGHT = PLAY_H + TOPBAR    # 724
FPS = 60

TILE = 28
GRID_W = 70                 # map is larger than the viewport — the camera scrolls
GRID_H = 50
WORLD_W = GRID_W * TILE     # full map size in pixels
WORLD_H = GRID_H * TILE
PAN_SPEED = 480             # camera pan speed (px/sec) with the arrow keys

# --- Colors ------------------------------------------------------------
C_GRASS   = (74, 110, 64)
C_GRASS2  = (82, 120, 70)
C_WATER   = (54, 96, 140)
C_TREE    = (38, 74, 44)
C_TRUNK   = (92, 64, 40)
C_BUSH    = (140, 60, 92)     # berry bush (food)
C_HUT     = (120, 92, 60)     # home
C_HUT_ROOF= (92, 60, 44)
C_SHRINE  = (150, 140, 190)   # fun spot
C_PANEL   = (28, 30, 38)
C_PANEL2  = (40, 43, 54)
C_TOPBAR  = (20, 22, 28)
C_TEXT    = (228, 230, 236)
C_DIM     = (150, 154, 164)
C_SELECT  = (250, 220, 120)
C_BAR_BG  = (60, 63, 74)
C_GOOD    = (96, 190, 110)
C_WARN    = (220, 190, 90)
C_BAD     = (210, 90, 90)
C_GOLD    = (240, 210, 130)

# terrain materials — tile codes 4 dirt, 5 stone, 6 ore (v0.6 groundwork)
C_DIRT    = (120, 92, 60)
C_STONEG  = (122, 122, 130)
C_ORE     = (140, 122, 98)

# --- Needs -------------------------------------------------------------
NEEDS = ["hunger", "thirst", "energy", "social", "fun"]
NEED_LABEL = {"hunger": "Food", "thirst": "Water", "energy": "Energy",
              "social": "Social", "fun": "Fun"}

# per game-second decay (need drains toward 0) — thirst builds faster than hunger
DECAY = {"hunger": 2.2, "thirst": 2.6, "energy": 1.6, "social": 2.0, "fun": 1.8}
# per game-second restore while performing the matching action
RESTORE = {"hunger": 40, "thirst": 45, "energy": 34, "social": 30, "fun": 34}

SATED = 92        # a need this high counts as satisfied -> stop the action
ACT_URGE = 45     # only chase a need once its "urge" (100-value) passes this

# --- Movement / interaction -------------------------------------------
SPEED = 95.0          # villager move speed, px / game-second
ARRIVE = 14.0         # distance that counts as "reached the target"
TALK_RADIUS = 42.0    # close enough to socialize
REL_RATE = 7.0        # relationship change per game-second of socializing
ACTION_TIMEOUT = 16.0 # give up on an action after this many game-seconds

# --- Time --------------------------------------------------------------
SPEEDS = [1, 2, 4, 8]     # selectable game speeds

# --- Calendar & day/night (v0.4) --------------------------------------
# One day = 20 real minutes at speed x1 (10 day / 10 night at the equinox).
DAY_SECONDS = 1200.0
DAYS_PER_WEEK = 7
WEEKS_PER_MONTH = 4
DAYS_PER_MONTH = DAYS_PER_WEEK * WEEKS_PER_MONTH     # 28
MONTHS_PER_YEAR = 4
DAYS_PER_YEAR = DAYS_PER_MONTH * MONTHS_PER_YEAR     # 112
SEASONS = ["Spring", "Summer", "Autumn", "Winter"]   # one season per month
# fraction of each day that is daylight, by season (winter short, summer long)
DAYLIGHT = {"Spring": 0.50, "Summer": 0.70, "Autumn": 0.50, "Winter": 0.30}
TWILIGHT = 0.05           # dawn/dusk ramp length (fraction of a day)
NIGHT_ALPHA = 140         # darkness of the deep-night overlay

# --- Player requests ---------------------------------------------------
REQUEST_THRESHOLD = 35    # willingness must clear this for a villager to comply

# --- Resources, gathering, farming, crafting (v0.3) -------------------
STOCK_KINDS = ["wood", "stone", "ore", "ingot", "grain", "food", "bucket", "water"]
WORK_TYPES = {"chop", "mine", "farm", "craft", "smelt", "minetile", "dig"}

WORK_TIME = 2.4           # game-seconds of effort per work action
YIELD_WOOD = 2            # wood per chop
YIELD_STONE = 2           # stone per mine
YIELD_ORE = 2             # ore per ore-tile mine
YIELD_GRAIN = 3           # grain per harvest
NODE_AMOUNT = 3           # chops/mines before a tree/rock is spent
NODE_REGROW = 45.0        # game-seconds for a spent node to come back
CROP_GROW = 30.0          # game-seconds for a planted crop to ripen
BUSH_AMOUNT = 4           # harvests a berry bush gives before it's bare

# berries: foraged food that fills hunger and spoils
BERRIES_PER_HARVEST = 5   # berries gained per bush harvest
BERRY_FILL = 18           # hunger restored per berry eaten
BERRY_SPOIL = 60.0        # game-seconds before a batch of berries rots

# water: must craft a bucket to collect it; it fills thirst
BUCKET_WATER = 8          # water units collected per trip (needs a bucket)
WATER_FILL = 25           # thirst restored per water unit drunk
HAND_DRINK = 16.0         # thirst/game-second when drinking by hand (slow, no storage)

# build palette (v0.7): (name, kind, material, cost). walls block movement;
# doors and floors do not. Press B to toggle build mode, TAB to cycle.
BUILDABLES = [
    ("Wood Wall",  "wall",  "wood",  {"wood": 2}),
    ("Stone Wall", "wall",  "stone", {"stone": 2}),
    ("Door",       "door",  "wood",  {"wood": 1}),
    ("Wood Floor", "floor", "wood",  {"wood": 1}),
]

# --- Tools (v0.8) — durability scales worst->best: wood < stone < metal ----
TOOL_KINDS = ["axe", "pickaxe", "shovel", "hoe"]
TOOL_MATS = ["wood", "stone", "metal"]
TOOL_USES = {"wood": 15, "stone": 35, "metal": 80}   # uses before it breaks
ACTION_TOOL = {"minetile": "pickaxe", "dig": "shovel"}  # gated actions -> tool

# workbench recipes; press C in-game to pick which one to craft.
# a {"tool": (kind, mat)} output crafts a durable tool instead of a stockpile item.
RECIPES = [
    ("meal",   {"grain": 3}, {"food": 2}),
    ("bucket", {"wood": 2}, {"bucket": 1}),
]
_TOOL_COST = {
    "wood":  {"wood": 3},
    "stone": {"wood": 2, "stone": 2},
    "metal": {"wood": 1, "ingot": 2},
}
for _m in TOOL_MATS:
    for _k in TOOL_KINDS:
        RECIPES.append((f"{_m} {_k}", dict(_TOOL_COST[_m]), {"tool": (_k, _m)}))

# --- Z-levels (v0.5) — vertical layers, 0 = ground -------------------
ZLEVELS = 6               # z0 (ground) .. z5
FEET_PER_Z = 6            # each level is roughly six feet of height
C_LEAF  = (74, 140, 80)        # tree foliage
C_LEAF2 = (104, 176, 104)
C_HAZE  = (175, 198, 224)      # sky haze when looking down from a height

# resource / station colors
C_TREE_R  = (46, 92, 52)       # resource-tree canopy
C_ROCK    = (132, 134, 142)
C_PLOT    = (104, 74, 48)      # untilled soil
C_PLOT_T  = (84, 58, 40)       # tilled soil
C_SPROUT  = (120, 180, 90)
C_CROP    = (212, 192, 92)
C_BENCH   = (150, 120, 70)

# --- Traits ------------------------------------------------------------
# Each trait tweaks decay rates, social/relationship gains, or mood.
TRAIT_EFFECTS = {
    "Cheerful":   {"mood": +12},
    "Gloomy":     {"mood": -12},
    "Glutton":    {"decay_hunger": 1.7},
    "Hardy":      {"decay_energy": 0.7, "decay_hunger": 0.85},
    "Lazy":       {"decay_energy": 1.3},
    "Loner":      {"decay_social": 0.5, "social_gain": 0.6, "rel_gain": 0.6},
    "Gregarious": {"decay_social": 1.5, "social_gain": 1.3, "rel_gain": 1.3},
}

# --- Mood labels (by 0-100 value) -------------------------------------
def mood_label(v):
    if v >= 80:  return "Joyful"
    if v >= 62:  return "Happy"
    if v >= 42:  return "Content"
    if v >= 25:  return "Glum"
    return "Miserable"

# --- Relationship labels (by -100..100 score) -------------------------
def rel_label(v):
    if v >= 70:  return "Close"
    if v >= 30:  return "Friend"
    if v >= 8:   return "Warm"
    if v > -8:   return "Stranger"
    if v > -30:  return "Cool"
    return "Rival"


# --- Calendar / day-night helpers -------------------------------------
def _daylight(frac, dl):
    """Daylight intensity 0..1 across a day; daytime centered on noon (frac 0.5)."""
    dawn = 0.5 - dl / 2.0
    dusk = 0.5 + dl / 2.0
    tw = TWILIGHT
    if frac < dawn - tw or frac >= dusk + tw:
        return 0.0
    if dawn + tw <= frac < dusk - tw:
        return 1.0
    if frac < dawn + tw:
        return max(0.0, (frac - (dawn - tw)) / (2 * tw))
    return max(0.0, 1.0 - (frac - (dusk - tw)) / (2 * tw))


def calendar(game_seconds):
    """Convert elapsed game-seconds into a calendar + day/night reading."""
    total_days = game_seconds / DAY_SECONDS
    di = int(total_days)
    frac = total_days - di                       # progress through the day
    doy = di % DAYS_PER_YEAR                      # day of year (0-based)
    month_i = doy // DAYS_PER_MONTH              # 0..3 -> season index
    dom = doy % DAYS_PER_MONTH                    # day of month (0-based)
    intensity = _daylight(frac, DAYLIGHT[SEASONS[month_i]])
    return {
        "year": di // DAYS_PER_YEAR + 1,
        "season": SEASONS[month_i],
        "week": dom // DAYS_PER_WEEK + 1,
        "dow": dom % DAYS_PER_WEEK + 1,
        "day_num": di + 1,
        "hh": int(frac * 24) % 24,
        "mm": int(frac * 24 * 60) % 60,
        "intensity": intensity,
        "is_day": intensity > 0.5,
    }
