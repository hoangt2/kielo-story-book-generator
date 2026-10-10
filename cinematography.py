# Comic-style camera direction for page illustrations.
#
# Left to itself the story model writes every image_description as the same
# flat, straight-on mid shot, so a finished book reads like a row of identical
# portraits. This module hands the model an explicit shot plan — one framing per
# page, in a comic-book rhythm — and gives the image model the framing rules it
# needs to honour that plan.
import random

# Shot vocabulary, grouped by how close the camera is ("scale"). The "direction"
# text is what actually reaches the image model, so it describes camera
# position, height and distance in concrete terms rather than film jargon.
SHOTS = [
    # --- wide: the place, the situation, the scale of things -----------------
    {
        "name": "ESTABLISHING WIDE SHOT",
        "scale": "wide",
        "tags": [],
        "direction": "Camera far back and slightly above eye level, taking in the whole location. The characters are small in the frame; the setting is the subject.",
    },
    {
        "name": "HIGH ANGLE / BIRD'S-EYE VIEW",
        "scale": "wide",
        "tags": ["angle"],
        "direction": "Camera high above the scene looking down steeply, so we see the tops of heads, the ground pattern and the shapes people make in the space.",
    },
    {
        "name": "LONG SHOT FROM BEHIND",
        "scale": "wide",
        "tags": ["pov"],
        "direction": "Camera behind the characters at their own height, looking past their backs into the scene ahead. We see what they are facing, not their faces.",
    },
    {
        "name": "BACKLIT SILHOUETTE WIDE SHOT",
        "scale": "wide",
        "tags": ["angle"],
        "direction": "Camera facing a bright light source — a window, low sun, a lamp — so the characters read as dark simple shapes against the glow.",
    },
    {
        "name": "THROUGH-A-FRAME SHOT",
        "scale": "wide",
        "tags": ["angle"],
        "direction": "Camera outside the action shooting through something: a window, a doorway, a gap between trees, a bus window. The frame's dark edges take up the outer part of the picture.",
    },

    # --- medium: people doing things, relationships between them -------------
    {
        "name": "MEDIUM SHOT",
        "scale": "medium",
        "tags": [],
        "direction": "Camera at chest height, a few steps away, showing one or two characters from roughly the waist up with enough background to place them.",
    },
    {
        "name": "LOW ANGLE (WORM'S-EYE VIEW)",
        "scale": "medium",
        "tags": ["angle"],
        "direction": "Camera down near the ground tilted up, so the character towers above the viewer and the sky or ceiling fills the top of the frame.",
    },
    {
        "name": "OVER-THE-SHOULDER SHOT",
        "scale": "medium",
        "tags": ["pov"],
        "direction": "Camera just behind and beside one character's shoulder. That shoulder and the back of their head frame one side of the picture; what they are looking at is sharp in the middle.",
    },
    {
        "name": "PROFILE TWO-SHOT",
        "scale": "medium",
        "tags": [],
        "direction": "Camera to the side at eye level with two characters facing each other in profile, one on each side of the frame, the space between them at the centre.",
    },
    {
        "name": "TRACKING SIDE VIEW",
        "scale": "medium",
        "tags": [],
        "direction": "Camera alongside a character in motion, seen from the side, as if moving with them; the background streaks past behind and their stride crosses the frame.",
    },
    {
        "name": "DUTCH ANGLE",
        "scale": "medium",
        "tags": ["angle"],
        "direction": "Camera tilted so the horizon and all the verticals slant clearly off level, giving the moment a small jolt of unbalance.",
    },
    {
        "name": "REFLECTION SHOT",
        "scale": "medium",
        "tags": ["angle"],
        "direction": "We see the scene as a reflection — in a mirror, a puddle, a dark window, a metal kettle — with the reflecting surface's own edges and ripples visible.",
    },

    # --- close: faces, feeling, what the eyes land on ------------------------
    {
        "name": "CLOSE-UP",
        "scale": "close",
        "tags": [],
        "direction": "Camera close in on one character's face, filling much of the frame, the background soft and simple behind. The expression is the whole point of the picture.",
    },
    {
        "name": "FIRST-PERSON POV",
        "scale": "close",
        "tags": ["pov"],
        "direction": "The camera IS the character's eyes: we see only what they see. Their own hands or feet may enter the bottom edge of the frame, but their face never appears.",
    },
    {
        "name": "CLOSE-UP FROM BELOW",
        "scale": "close",
        "tags": ["angle"],
        "direction": "Camera close and just below chin height looking slightly up at the face, with the ceiling, treetops or sky behind.",
    },
    {
        "name": "TOP-DOWN OVER THE HANDS",
        "scale": "close",
        "tags": ["angle"],
        "direction": "Camera directly overhead pointing straight down at a table, floor or lap, so we see the surface flat-on and the hands working on it. No faces.",
    },

    # --- detail: the object the page is really about -------------------------
    {
        "name": "EXTREME CLOSE-UP DETAIL",
        "scale": "detail",
        "tags": [],
        "direction": "Camera extremely close on one small thing — a pair of hands, a mitten, a berry, a coin, a cat's paw — so it fills the frame. No full faces, no whole bodies.",
    },
    {
        "name": "FOREGROUND-OBJECT SHOT",
        "scale": "detail",
        "tags": [],
        "direction": "One object sits very large and close in the foreground, off to one side, while the characters are visible smaller and further back through the gap beside it.",
    },
]

COVER_SHOT = {
    "name": "HERO POSTER SHOT",
    "scale": "wide",
    "tags": [],
    "direction": (
        "A dynamic, eye-catching book-cover composition that immediately hints at the story's theme. "
        "Show the main character(s) MID-ACTION — running, reaching, laughing, riding, cooking, "
        "exploring — NOT standing still and facing the camera. "
        "Use a cinematic angle (slight low angle, dynamic diagonal, or dramatic perspective) "
        "and place the key story element (object, animal, vehicle, location) prominently in the scene. "
        "IMPORTANT: Whatever the title refers to (an object, animal, place, activity) MUST be clearly and prominently visible in the cover — "
        "it should be one of the first things the viewer notices. "
        "The setting should be vivid and fill the background, making the reader curious about what happens next. "
        "Keep the lower fifth of the image relatively clean for potential title overlay."
    ),
}

SCALES = ("wide", "medium", "close", "detail")

# Comics open by showing where we are, and close on something calm and readable
# rather than on a tilted angle or a cropped detail.
_OPENING_SHOT_NAMES = ("ESTABLISHING WIDE SHOT", "HIGH ANGLE / BIRD'S-EYE VIEW")
_CLOSING_SHOT_NAMES = (
    "ESTABLISHING WIDE SHOT",
    "MEDIUM SHOT",
    "PROFILE TWO-SHOT",
    "LONG SHOT FROM BEHIND",
)

# A comic page alternates distance rather than repeating one framing: place,
# then people, then a face, then the thing they are holding. This is the base
# rhythm; the starting point is rotated per story so books do not all match.
_SCALE_RHYTHM = [
    "wide", "medium", "close", "medium", "detail",
    "close", "wide", "medium", "close", "medium",
    "detail", "wide",
]


def _scale_sequence(page_count, rng):
    """Builds a scale-per-page rhythm: opens wide, never repeats back-to-back."""
    offset = rng.randrange(len(_SCALE_RHYTHM))
    seq = [_SCALE_RHYTHM[(offset + i) % len(_SCALE_RHYTHM)] for i in range(page_count)]

    seq[0] = "wide"  # open by showing where we are

    for i in range(1, len(seq)):
        if seq[i] == seq[i - 1]:
            seq[i] = rng.choice([s for s in SCALES if s != seq[i]])

    # End on something readable rather than a detail crop.
    if len(seq) > 1 and seq[-1] == "detail":
        seq[-1] = "wide" if seq[-2] != "wide" else "medium"

    return seq


def _shot_by_name(name):
    return next(s for s in SHOTS if s["name"] == name)


def _pick_named(names, exclude_name, rng):
    """Picks one of the named shots, avoiding `exclude_name` where possible."""
    options = [_shot_by_name(n) for n in names if n != exclude_name]
    return rng.choice(options or [_shot_by_name(n) for n in names])


def _pick_shot(scale, used_names, previous_name, rng):
    """Picks a shot of the given scale, preferring ones not used yet."""
    pool = [s for s in SHOTS if s["scale"] == scale]
    fresh = [s for s in pool if s["name"] not in used_names]
    candidates = fresh or [s for s in pool if s["name"] != previous_name] or pool
    return rng.choice(candidates)


def _ensure_tag(shots, tag, rng):
    """Guarantees at least one shot carrying `tag` somewhere in the middle."""
    if any(tag in s["tags"] for s in shots):
        return

    options = [s for s in SHOTS if tag in s["tags"]]
    if not options or len(shots) < 3:
        return

    # Swap into an interior page: the opening and closing framings are load-bearing.
    index = rng.randrange(1, len(shots) - 1)
    neighbours = {shots[index - 1]["name"], shots[index + 1]["name"]}
    allowed = [s for s in options if s["name"] not in neighbours] or options
    shots[index] = rng.choice(allowed)


def build_shot_plan(page_count, seed=None):
    """
    Returns a shot plan: one entry per page, page 1 being the cover.

    Each entry is {"page_number", "name", "direction"}. The plan opens with an
    establishing shot, alternates camera distance page to page, and (for stories
    long enough to afford it) always includes at least one point-of-view page
    and one unusual angle.
    """
    page_count = max(1, int(page_count))
    rng = random.Random(seed)

    scales = _scale_sequence(page_count, rng)

    shots = []
    used_names = set()
    for scale in scales:
        previous_name = shots[-1]["name"] if shots else COVER_SHOT["name"]
        shot = _pick_shot(scale, used_names, previous_name, rng)
        used_names.add(shot["name"])
        shots.append(shot)

    # Open on the place, so the reader knows where the story happens.
    shots[0] = _pick_named(_OPENING_SHOT_NAMES, None, rng)

    if page_count >= 6:
        _ensure_tag(shots, "pov", rng)
        _ensure_tag(shots, "angle", rng)

    # Land the ending on a calm, readable framing.
    if page_count >= 3:
        shots[-1] = _pick_named(_CLOSING_SHOT_NAMES, shots[-2]["name"], rng)

    # Final sweep: no page may repeat the framing of the page before it.
    for i in range(1, len(shots)):
        if shots[i]["name"] == shots[i - 1]["name"]:
            alternatives = [s for s in SHOTS
                            if s["scale"] == shots[i]["scale"] and s["name"] != shots[i]["name"]]
            if alternatives:
                shots[i] = rng.choice(alternatives)

    plan = [{"page_number": 1, "name": COVER_SHOT["name"], "direction": COVER_SHOT["direction"]}]
    for offset, shot in enumerate(shots):
        plan.append({
            "page_number": offset + 2,  # story pages start after the cover
            "name": shot["name"],
            "direction": shot["direction"],
        })
    return plan


CAMERA_RULES = """**MANDATORY CAMERA DIRECTION (SHOT PLAN):**
Each page below has an assigned camera framing. Think like a comic artist: the
words carry the story, the camera carries the mood.

Rules:
1. Every `image_description` MUST begin with its assigned shot name, followed by a colon.
2. After the shot name, describe the scene so that the assigned camera position, height and distance are unmistakable. Write it as what the picture shows, not as film jargon.
3. The camera changes; the story does not. The action in the picture must still match that page's text.
4. Still repeat the FULL visual description of every character visible in the frame, exactly as required above — a close-up needs the same hair, clothes and colours as a wide shot.
5. On a FIRST-PERSON POV page, the viewpoint character's face must NOT appear; describe what they see (their own hands may enter the bottom of the frame).
6. On pages framed with no faces (top-down, extreme close-up detail), describe the hands, objects and surroundings in rich detail instead.
7. Each page is ONE single illustration. Never describe a multi-panel comic page, panel borders, speech bubbles or captions.
"""


def format_shot_plan(plan):
    """Renders a shot plan as the prompt block that pins each page's framing."""
    lines = [CAMERA_RULES, "Shot assignments (use these exactly):"]
    for entry in plan:
        label = "Page 1 (cover)" if entry["page_number"] == 1 else f"Page {entry['page_number']}"
        lines.append(f"- {label} — **{entry['name']}**: {entry['direction']}")
    return "\n".join(lines)


# Composition notes for the image model itself. Kept separate from the style
# guide because it is about where the camera stands, not how lines are drawn.
#
# Deliberately never uses the word "panel": asked to compose "like a comic
# panel", the image model draws the panel too — a black outline with white
# margins around the artwork, which ruins a full-bleed card.
CAMERA_STYLE_GUIDE = """
Camera and composition: The camera direction at the start of the description is the single most important requirement — match the stated angle, camera height and distance exactly, and do not fall back on a flat, straight-on, eye-level view. Build real depth: a clear foreground, middle ground and background, subjects placed off-centre when the framing calls for it, and confident perspective with converging lines and foreshortening.

The drawing runs off all four edges of the image, full bleed, as if this were a crop out of a much larger picture — scenery, floor and sky continue past the edge on every side. It is ONE single illustration with no border, frame, white margin, rounded corner, speech bubble or caption.
"""


def _normalise(name):
    return "".join(ch for ch in name.upper() if ch.isalnum())


_SHOTS_BY_NAME = {_normalise(s["name"]): s for s in SHOTS + [COVER_SHOT]}


def camera_directive(image_description):
    """
    Re-states the camera direction for a page, in front of the image prompt.

    The story model writes `image_description` prefixed with its assigned shot
    name. Image models drift toward a default eye-level view when the angle is
    buried mid-paragraph, so we look the shot back up here and lead with its
    full camera notes.
    """
    if not image_description or ":" not in image_description:
        return ""

    prefix = image_description.split(":", 1)[0]
    if len(prefix) > 60:  # not a shot label, just a sentence with a colon in it
        return ""

    shot = _SHOTS_BY_NAME.get(_normalise(prefix))
    if not shot:
        return ""

    return (f"CAMERA DIRECTION — {shot['name']}. {shot['direction']} "
            "This camera position is the most important requirement of the image; "
            "do not replace it with a straight-on eye-level view.")


def camera_reminder(image_description):
    """
    A closing restatement of the camera position.

    Image models weight the start and the end of a prompt most heavily, so the
    angle is stated twice: once leading (camera_directive) and once trailing.
    """
    if not image_description or ":" not in image_description:
        return ""

    prefix = image_description.split(":", 1)[0]
    if len(prefix) > 60:
        return ""

    shot = _SHOTS_BY_NAME.get(_normalise(prefix))
    if not shot:
        return ""

    first_sentence = shot["direction"].split(". ")[0].rstrip(".")
    return f"\nREMEMBER: draw the entire picture from this camera position — {first_sentence}."

# The 9:16 story card darkens the bottom 35% of the image for the text overlay
# (see image_composer._create_fullbleed_card), so anything important down there
# is lost.
_FULLBLEED_FRAMING_NOTE = """
Framing for this canvas: text will be laid over the bottom third of this image. Keep faces, eyes and the main action inside the upper two thirds, and leave the bottom third as calm, simple background (ground, snow, water, floor, sky).
"""


def framing_note(aspect_ratio):
    """Returns canvas-specific framing advice, or "" when the canvas is clean."""
    if aspect_ratio == "9:16":
        return _FULLBLEED_FRAMING_NOTE
    return ""
