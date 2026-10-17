# Picks where the caption goes on a full-bleed 9:16 story card.
#
# The caption goes low on the card by default. When that would land on a main character,
# it moves to the upper end of the safe area instead. A Gemini vision model says where the
# characters (faces first) are; the caption takes the band that covers less of them.
# Any failure (no key, no network, bad answer) falls back to "bottom". Answers are cached
# per picture in .text_zone_cache.json, so tuning the layout does not repeat the requests.

import hashlib
import io
import json
import os
import time

from dotenv import load_dotenv

load_dotenv()

from image_composer import SAFE_BOTTOM_FRAC, SAFE_TOP_FRAC  # the safe area the text stays inside

VISION_MODEL = "gemini-2.5-flash"
BAND = 0.27            # tallest text block, as a share of the card height (matches image_composer)
FACE_WEIGHT = 3.0      # covering a face is what moves the text up
BODY_WEIGHT = 0.15     # legs and torsos under the text barely count
OBJECT_WEIGHT = 0.1
MIN_INTERVAL = 6.5      # seconds between requests: a free-tier key allows about 10 a minute
last_error = ""
_last_call = 0.0
last_zone = "bottom"      # the latest answer, for logs
last_check_ok = False   # True when the latest choose_zone() really got an answer from the model
CLEAR_ENOUGH = 0.01    # bottom is kept unless it covers more than this (weighted share of the card)
_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".text_zone_cache.json")

_PROMPT = (
    "This is an illustration for a children's language-learning story card. "
    "Find every character in the scene (and only the single most important prop, if any). "
    "Return JSON only, in this exact shape: "
    '{"subjects": [{"label": "face" | "body" | "object", "box": [ymin, xmin, ymax, xmax]}]} '
    "with all box coordinates as integers from 0 to 1000 (fractions of the image height and "
    "width). Give one 'face' box per visible character face, one 'body' box per character body, "
    "and at most one 'object' box for the single most important prop."
)


def _cache_get(digest):
    try:
        with open(_CACHE_FILE, encoding="utf-8") as f:
            hit = json.load(f).get(digest)
        return None if hit is None else [(label, tuple(box)) for label, box in hit]
    except Exception:
        return None


def _cache_put(digest, subjects):
    try:
        try:
            with open(_CACHE_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data[digest] = [[label, list(box)] for label, box in subjects]
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def find_subjects(pil_image):
    """Returns [(label, (y0, x0, y1, x1))] with coordinates as 0-1 fractions, or None on failure."""
    global _last_call, last_error
    last_error = ""
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        last_error = "GOOGLE_API_KEY is not set"
        return None
    try:
        from google import genai
        from google.genai import types

        buf = io.BytesIO()
        pil_image.convert("RGB").resize((512, 910)).save(buf, format="JPEG", quality=85)
        digest = hashlib.sha1(buf.getvalue()).hexdigest()
        cached = _cache_get(digest)
        if cached is not None:
            return cached
        # A hung request must not stall card making: give up after 60 s (falls back to "bottom")
        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=60000))
        data = None
        error = None
        for attempt in range(3):  # retries: a slow, dropped or rate-limited request should not decide the layout
            wait = MIN_INTERVAL - (time.time() - _last_call)
            if wait > 0:
                time.sleep(wait)
            _last_call = time.time()
            try:
                response = client.models.generate_content(
                    model=VISION_MODEL,
                    contents=[_PROMPT, types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        thinking_config=types.ThinkingConfig(thinking_budget=0),  # a plain lookup, no reasoning needed
                    ),
                )
                data = json.loads(response.text)
                break
            except Exception as e:
                error = e
                last_error = f"{type(e).__name__}: {str(e)[:160]}"
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    time.sleep(20)  # over the per-minute limit: wait it out
        if data is None:
            raise error
        subjects = []
        items = data.get("subjects", []) if isinstance(data, dict) else data
        for s in items or []:
            try:  # one malformed item must not throw away the rest of the answer
                y0, x0, y1, x1 = [max(0.0, min(1.0, float(v) / 1000.0)) for v in s["box"]]
                if y1 > y0 and x1 > x0:
                    subjects.append((str(s.get("label", "object")), (y0, x0, y1, x1)))
            except Exception:
                continue
        _cache_put(digest, subjects)
        return subjects
    except Exception as e:
        last_error = last_error or f"{type(e).__name__}: {str(e)[:160]}"
        print(f"Text zone check skipped: {e}")
        return None


def _covered(subjects, band_top, band_bottom):
    """Weighted share of the card area that subjects cover inside one horizontal band."""
    total = 0.0
    for label, (y0, x0, y1, x1) in subjects:
        top, bottom = max(y0, band_top), min(y1, band_bottom)
        if bottom > top:
            weight = FACE_WEIGHT if label == "face" else BODY_WEIGHT if label == "body" else OBJECT_WEIGHT
            total += (bottom - top) * (x1 - x0) * weight
    return total


def choose_zone(pil_image):
    """Returns "top" or "bottom": where the caption should go on this picture."""
    global last_check_ok, last_zone
    subjects = find_subjects(pil_image)
    last_check_ok = subjects is not None
    if not subjects:
        last_zone = "bottom"
        return "bottom"
    bottom_cover = _covered(subjects, SAFE_BOTTOM_FRAC - BAND, SAFE_BOTTOM_FRAC)
    top_cover = _covered(subjects, SAFE_TOP_FRAC, SAFE_TOP_FRAC + BAND)
    zone = "bottom"
    if bottom_cover > CLEAR_ENOUGH and top_cover < bottom_cover * 0.6:
        zone = "top"
    last_zone = zone
    print(f"Text zone: {zone} (covered: top {top_cover:.3f}, bottom {bottom_cover:.3f})")
    return zone
