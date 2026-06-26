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
GRID_W = PLAY_W // TILE     # 35
GRID_H = PLAY_H // TILE     # 25

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

# --- Needs -------------------------------------------------------------
NEEDS = ["hunger", "energy", "social", "fun"]
NEED_LABEL = {"hunger": "Food", "energy": "Energy",
              "social": "Social", "fun": "Fun"}

# per game-second decay (need drains toward 0)
DECAY = {"hunger": 2.2, "energy": 1.6, "social": 2.0, "fun": 1.8}
# per game-second restore while performing the matching action
RESTORE = {"hunger": 40, "energy": 34, "social": 30, "fun": 34}

SATED = 92        # a need this high counts as satisfied -> stop the action
ACT_URGE = 45     # only chase a need once its "urge" (100-value) passes this

# --- Movement / interaction -------------------------------------------
SPEED = 95.0          # villager move speed, px / game-second
ARRIVE = 14.0         # distance that counts as "reached the target"
TALK_RADIUS = 42.0    # close enough to socialize
REL_RATE = 7.0        # relationship change per game-second of socializing
ACTION_TIMEOUT = 16.0 # give up on an action after this many game-seconds

# --- Time --------------------------------------------------------------
GAME_MIN_PER_SEC = 12     # in-game minutes per real second at speed x1
SPEEDS = [1, 2, 4]        # selectable game speeds

# --- Player requests ---------------------------------------------------
REQUEST_THRESHOLD = 35    # willingness must clear this for a villager to comply

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
