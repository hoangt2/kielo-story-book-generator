# Checks every picture of a finished story against the story itself, and redraws the ones that do not fit.
#
# The pages are drawn one by one from their own image_description, so a picture can be fine on its own
# and still wrong for the story: a choir rehearsal with only two people in it, the same hall drawn as a
# different room, someone walking beside a friend they have not met yet, white "ghost" skin, outdoor shoes
# inside a Finnish home (Tung's review of the 2026-11-14 stories). A Gemini vision model looks at each page
# with the whole story in front of it. A page with a problem that breaks the story gets a rewritten
# image_description and is redrawn, then checked again, at most MAX_ROUNDS times.
#
# Usage:
#   python story_checker.py output_sv               # check and redraw what does not fit
#   python story_checker.py output_sv --report-only # only report, draw nothing
#
# Writes data/picture_check.json in the story folder: every round's verdict per page.

import argparse
import io
import json
import os
import time

from dotenv import load_dotenv

load_dotenv()

CHECK_MODELS = ["gemini-2.5-pro", "gemini-2.5-flash"]  # pro reads the story more carefully; flash if pro fails
MAX_ROUNDS = 2          # redraws per page; more rarely helps and each one costs an image generation
MIN_INTERVAL = 0        # no spacing: the key is past the old free-tier limit (Tung, 2026-11-14); a 429 still waits and retries
_last_call = 0.0

# Two steps, so the model answers plain questions and the code decides what is worth a redraw.
# 1. plan_story: one text-only call reads the whole story and writes, per page, what its picture must show
#    (place, who must and must not be there, a group or not, a home or not, the one key action). Saved to
#    data/picture_plan.json, so a re-check uses the same plan.
# 2. check_page: per picture, factual questions (who is visible, how many other people, is it that kind of
#    place, is the key action clearly missing...). An open "find the problems" question made the model
#    nitpick pages Tung called very good (loose hair, closed mouths, snow on the ground).
GROUP_MIN_OTHERS = 3    # a group scene needs at least this many people besides the main characters

PLAN_PROMPT = """Read this illustrated story for adult language learners. For EVERY page (page 1 is the cover), say
what its picture must show so that it does not contradict the story. Use the text of all pages: who has met whom
by this page, where it happens, what happens on this page.

Answer with JSON only, one object per page, in page order:
[{"page": 1,
  "place": "<short kind of place, e.g. 'a parish hall rehearsal room', 'a snowy street', 'a home kitchen'>",
  "is_home": <true when the place is inside someone's home>,
  "must_show": ["<main character names that must be visible>"],
  "must_not_show": ["<main character names that cannot be at this place at this moment: the text has the hero travelling or arriving alone, or they meet only later somewhere else. Someone who is already in the same room, just not mentioned on this page, is NOT listed>"],
  "group_expected": <true when the text is about a group activity with more people than the main characters: a choir, a class, a party, colleagues>,
  "key_action": "<the one concrete, visible thing this page's text says happens (e.g. 'the pies go into the oven', 'people hold lit candles'), short; empty when the page only describes a feeling, a look or a mood>"}]
"""

LOOK_PROMPT = """Look at this picture from an illustrated story. The main characters are:
{characters}

Answer these questions about the picture, with JSON only:
{{"visible_main_characters": ["<names of the main characters you can see, judged by their look>"],
 "other_people": <how many other people you can see, a number>,
 "is_place": "<yes | no | unclear>: is this picture set in: {place}?",
 "key_action_shown": "<yes | partly | no>: does the picture show: {action}",
 "skin_uncoloured": <true if people's skin is left white or uncoloured like the paper>,
 "footwear": [{{"person": "<name or 'other'>", "feet": "<not visible | socks | slippers | outdoor shoes>"}}],
 "duplicated_main_character": "<name of a main character drawn more than once in the picture, or empty>",
 "panels_or_text": <true only if there are comic panel borders dividing the picture, speech bubbles, or readable words or letters drawn in it (not blank papers or signs)>,
 "note": "<one short sentence on anything else that clearly contradicts the story, or empty>"}}
"""

FIX_PROMPT = """This page's picture contradicts the story. Problems:
{problems}

Its current image_description: {desc}

Write a new image_description that fixes every problem. Start it with "{shot}:" (the camera shot) and drop the old shot:
the old camera angle cropped out what the story needs. Repeat every visible main character's full look from their description. Name the place as: {place}.
When someone must not be visible, say so ("<Name> is NOT in this picture"). For a group scene, add "about ten other
adults of mixed ages, clearly different people from the main characters". In a home, people wear socks or slippers.
End with: "Full-bleed picture that fills the whole frame edge to edge, no white border, no frame."
Answer with JSON only: {{"image_description": "..."}}
"""


def _story_context(story, lang_key):
    lines = [f"Title: {story.get(lang_key.replace('text', 'title'), '')} / {story.get('title_en', '')}", "Characters:"]
    for c in story.get("characters", []):
        lines.append(f"- {c.get('name')}: {c.get('description')}")
    lines.append("Pages (page 1 is the cover):")
    for i, p in enumerate(story.get("pages", []), 1):
        lines.append(f"- Page {i}: {p.get(lang_key, '')} | {p.get('text_en', '')}")
    return "\n".join(lines)


def _client():
    from google import genai
    from google.genai import types
    return genai.Client(api_key=os.getenv("GOOGLE_API_KEY"), http_options=types.HttpOptions(timeout=180000))


def _ask(contents, models=tuple(CHECK_MODELS)):
    """One JSON answer from the first model that gives one; None when all fail."""
    global _last_call
    from google.genai import types
    client = _client()
    for model in models:
        for _attempt in range(2):
            wait = MIN_INTERVAL - (time.time() - _last_call)
            if wait > 0:
                time.sleep(wait)
            _last_call = time.time()
            try:
                r = client.models.generate_content(model=model, contents=contents,
                                                   config=types.GenerateContentConfig(response_mime_type="application/json"))
                return json.loads(r.text)
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    time.sleep(20)
    return None


def plan_story(story, lang_key, plan_path):
    if os.path.exists(plan_path):
        with open(plan_path, encoding="utf-8") as f:
            return {int(p["page"]): p for p in json.load(f)}
    data = _ask([PLAN_PROMPT + "\n\nTHE STORY:\n" + _story_context(story, lang_key)]) or []
    if isinstance(data, dict):
        data = data.get("pages", [])
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return {int(p["page"]): p for p in data if "page" in p}


def check_page(story, page_number, image_path, plan):
    """Returns {"verdict": ok | major | error, "problems": [...], "answers": {...}}."""
    from google.genai import types
    from PIL import Image
    if not os.getenv("GOOGLE_API_KEY"):
        return {"verdict": "error", "problems": ["GOOGLE_API_KEY is not set"]}
    want = plan.get(page_number, {})
    buf = io.BytesIO()
    Image.open(image_path).convert("RGB").resize((540, 960)).save(buf, format="JPEG", quality=85)
    chars = "\n".join(f"- {c.get('name')}: {c.get('description')}" for c in story.get("characters", []))
    q = LOOK_PROMPT.format(characters=chars, place=want.get("place") or "the place of the story",
                           action=want.get("key_action") or "-")
    a = _ask([q, types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")])
    if not isinstance(a, dict):
        return {"verdict": "error", "problems": ["the picture check got no answer"]}
    seen = {str(n).strip().lower() for n in a.get("visible_main_characters", []) or []}
    problems, notes, wide = [], [], False   # problems are worth a redraw; notes are only reported
    # The cover teases the whole story, so "not here yet" does not apply to it. "must_show" is not checked:
    # close-ups and over-the-shoulder shots crop people out on purpose (cinematography.py).
    for name in (want.get("must_not_show", []) or []) if page_number > 1 else []:
        if name.lower() in seen:
            problems.append(f"{name} is in the picture, but the story does not have them here yet (or has the hero alone)")
    try:
        others = int(a.get("other_people") or 0)
    except (TypeError, ValueError):
        others = 0
    if want.get("group_expected") and others < GROUP_MIN_OTHERS:
        problems.append(f"the text is about a group, but only {others} other people are in the picture")
        wide = True
    if str(a.get("is_place", "")).lower().startswith("no"):
        problems.append(f"the picture is not set in {want.get('place')}")
        wide = True
    # "Is the action shown" was the least reliable answer (2026-11-14: it called a man hanging up his coat
    # "not taking off his coat", and the redraw made the page worse), so it is reported, not redrawn.
    if want.get("key_action") and str(a.get("key_action_shown", "")).lower().startswith("no"):
        notes.append(f"may not show: {want.get('key_action')}")
    if a.get("skin_uncoloured") is True:
        problems.append("skin is left white")
    shod = [f.get("person", "someone") for f in a.get("footwear", []) or []
            if isinstance(f, dict) and "shoe" in str(f.get("feet", "")).lower()]
    if want.get("is_home") and shod:
        problems.append(f"outdoor shoes inside a home ({', '.join(shod)})")
    if str(a.get("duplicated_main_character") or "").strip():
        problems.append(f"{a['duplicated_main_character']} is drawn twice")
    if a.get("panels_or_text") is True:
        problems.append("comic panels or written words in the picture")
    return {"verdict": "major" if problems else ("note" if notes else "ok"),
            "problems": problems, "notes": notes, "wide": wide, "answers": a}


def has_paper_border(image_path, band=0.02, paper=245, share=0.9):
    """True when a side of the picture is a band of plain paper white: the inset-in-a-frame look.
    Stricter than story_generator.looks_inset, so snow and white walls inside the scene do not count."""
    from PIL import Image
    im = Image.open(image_path).convert("RGB")
    w, h = im.size
    bw, bh = max(2, int(w * band)), max(2, int(h * band))
    white_sides = 0
    for box in ((0, 0, w, bh), (0, h - bh, w, h), (0, 0, bw, h), (w - bw, 0, w, h)):
        px = list(im.crop(box).getdata())
        if sum(1 for p in px if min(p) >= paper) / len(px) > share:
            white_sides += 1
    # A framed inset is white on two or more sides; one white side is usually snow or a white wall.
    return white_sides >= 2


def trim_border(image_path, paper=245):
    """Crops a white paper border away and scales the picture back to fill the canvas. No new drawing needed."""
    from PIL import Image, ImageOps
    im = Image.open(image_path).convert("RGB")
    mask = im.point(lambda v: 255 if v < paper else 0).convert("L")
    box = mask.getbbox()
    if not box:
        return False
    inner = im.crop(box)
    # crop a little further in, past the thin frame line many inset pictures have
    m = int(min(inner.size) * 0.015)
    inner = inner.crop((m, m, inner.width - m, inner.height - m))
    ImageOps.fit(inner, im.size, method=Image.LANCZOS).save(image_path)
    return True


def fix_description(story, page_number, problems, plan, wide=False):
    want = plan.get(page_number, {})
    desc = story["pages"][page_number - 1].get("image_description", "")
    chars = "\n".join(f"- {c.get('name')}: {c.get('description')}" for c in story.get("characters", []))
    data = _ask([FIX_PROMPT.format(problems="\n".join(f"- {p}" for p in problems), desc=desc,
                                   shot="ESTABLISHING WIDE SHOT" if wide else "MEDIUM SHOT",
                                   place=want.get("place") or "the same place as on the other pages")
                 + "\n\nMain characters:\n" + chars])
    return (data or {}).get("image_description", "") if isinstance(data, dict) else ""


def check_story(output_dir, aspect_ratio="9:16", redraw=True, pages=None, log=print):
    """Checks every page (or `pages`), redraws the major ones, rebuilds the PDF. Returns pages still wrong."""
    import story_generator as sg
    from languages import normalize_language, text_key

    story_path = os.path.join(output_dir, "data", "story.json")
    with open(story_path, encoding="utf-8") as f:
        story = json.load(f)
    lang_key = text_key(normalize_language(story.get("language")))
    if not any(lang_key in p for p in story.get("pages", [])):  # older stories: pick whichever text key is there
        lang_key = next((k for k in story["pages"][0] if k.startswith("text_") and k != "text_en"), lang_key)

    plan = plan_story(story, lang_key, os.path.join(output_dir, "data", "picture_plan.json"))
    report = {}
    still_wrong = []
    numbers = pages or list(range(1, len(story.get("pages", [])) + 1))
    import shutil
    from image_composer import create_story_card
    keep = os.path.join(output_dir, "data", "picture_versions")
    os.makedirs(keep, exist_ok=True)

    def card_path(n):
        return os.path.join(output_dir, "cards", f"story_card_{n}.png")

    def recompose(n, image_path):
        page = story["pages"][n - 1]
        create_story_card(image_path, page.get(lang_key), page.get("text_en"), card_path(n), aspect_ratio=aspect_ratio)

    for n in numbers:
        image_path = os.path.join(output_dir, "images", f"page_{n}.png")
        if not os.path.exists(image_path):
            continue
        rounds, versions = [], []   # versions: (problem count, round, saved image, saved card, description)
        for round_no in range(MAX_ROUNDS + 1):
            if redraw and has_paper_border(image_path) and trim_border(image_path):
                log(f"  page {n}: trimmed a white border")
                recompose(n, image_path)
            result = check_page(story, n, image_path, plan)
            rounds.append(result)
            if redraw:  # keep every version, so a redraw can never leave the page worse than it was
                img_copy = os.path.join(keep, f"page_{n}_v{round_no}.png")
                card_copy = os.path.join(keep, f"story_card_{n}_v{round_no}.png")
                shutil.copy(image_path, img_copy)
                if os.path.exists(card_path(n)):
                    shutil.copy(card_path(n), card_copy)
                score = len(result["problems"]) if result["verdict"] != "error" else 99
                versions.append((score, round_no, img_copy, card_copy, story["pages"][n - 1].get("image_description", "")))
            note = f" (note: {'; '.join(result.get('notes', []))})" if result.get("notes") else ""
            if result["verdict"] != "major":
                log(f"  page {n}: {result['verdict']}" + (f" ({'; '.join(result['problems'])})" if result["verdict"] == "error" else "") + note)
                if result["verdict"] == "error":
                    still_wrong.append({"page": n, "problems": result["problems"]})
                break
            log(f"  page {n}: major: {'; '.join(result['problems'])}{note}")
            new_desc = fix_description(story, n, result["problems"], plan, wide=result.get("wide")) \
                if redraw and round_no < MAX_ROUNDS else ""
            if not new_desc:
                break
            story["pages"][n - 1]["image_description"] = new_desc
            log(f"  page {n}: redrawing (round {round_no + 1} of {MAX_ROUNDS})")
            ok, _ = sg.regenerate_page_image(n, output_dir=output_dir, aspect_ratio=aspect_ratio)
            if not ok:
                break
        if versions:
            best = min(versions, key=lambda v: (v[0], v[1]))   # fewest problems; on a tie, the earlier version
            shutil.copy(best[2], image_path)
            if os.path.exists(best[3]):
                shutil.copy(best[3], card_path(n))
            story["pages"][n - 1]["image_description"] = best[4]
            if len(versions) > 1:
                log(f"  page {n}: kept version {best[1]} of {len(versions) - 1} redraws ({best[0]} problem(s) left)")
            if best[0]:
                still_wrong.append({"page": n, "problems": rounds[best[1]]["problems"]})
        elif rounds and rounds[-1]["verdict"] == "major":
            still_wrong.append({"page": n, "problems": rounds[-1]["problems"]})
        report[str(n)] = rounds

    with open(story_path, "w", encoding="utf-8") as f:
        json.dump(story, f, indent=2, ensure_ascii=False)
    with open(os.path.join(output_dir, "data", "picture_check.json"), "w", encoding="utf-8") as f:
        json.dump({"checked": time.strftime("%Y-%m-%dT%H:%M:%S"), "pages": report, "still_wrong": still_wrong},
                  f, indent=2, ensure_ascii=False)
    if redraw:
        from pdf_generator import compile_to_pdf
        compile_to_pdf(os.path.join(output_dir, "cards"), os.path.join(output_dir, "story.pdf"))
    if still_wrong:
        log(f"Picture check: {len(still_wrong)} page(s) still need a human look: "
            + ", ".join(str(w["page"]) for w in still_wrong))
    else:
        log("Picture check: every page fits the story.")
    return still_wrong


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check every picture of a story against the story and redraw the ones that do not fit")
    parser.add_argument("output_dir", help="The story folder (output_fi, output_sv, or an archive folder)")
    parser.add_argument("--report-only", action="store_true", help="Only report; draw nothing")
    parser.add_argument("--pages", help="Only these pages, e.g. 2,5,9")
    parser.add_argument("--aspect-ratio", default="9:16")
    a = parser.parse_args()
    only = [int(x) for x in a.pages.split(",")] if a.pages else None
    check_story(a.output_dir, aspect_ratio=a.aspect_ratio, redraw=not a.report_only, pages=only)
