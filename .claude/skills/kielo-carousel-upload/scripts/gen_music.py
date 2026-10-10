#!/usr/bin/env python3
"""Generate instrumental background music for a story carousel with the ElevenLabs Music API.

  gen_music.py STORY_DIR [--extra "style hints"] [--seconds N] [--force]

Default length = pages x 5s (the carousel caption timeline). Writes STORY_DIR/audio/background_music.mp3 and
background_music.json (prompt, length, song id). The API key is ELEVENLABS_API_KEY from this repo's .env, never printed.
"""
import argparse, json, os, sys, urllib.error, urllib.request

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
SECONDS_PER_SLIDE = 5


def api_key():
    for line in open(os.path.join(REPO, ".env")):
        k, _, v = line.strip().partition("=")
        if k == "ELEVENLABS_API_KEY" and v.strip():
            return v.strip().strip('"').strip("'")
    sys.exit("ELEVENLABS_API_KEY not set in .env")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story_dir"); ap.add_argument("--extra", default="")
    ap.add_argument("--seconds", type=int, help="override length (default pages x 5s)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing background_music.mp3")
    a = ap.parse_args()
    out_dir = os.path.join(a.story_dir, "audio"); out = os.path.join(out_dir, "background_music.mp3")
    if os.path.exists(out) and not a.force:
        sys.exit(f"{out} exists (use --force to regenerate)")
    story = json.load(open(os.path.join(a.story_dir, "data", "story.json")))
    pages = story["pages"]
    length_ms = (a.seconds or len(pages) * SECONDS_PER_SLIDE) * 1000
    summary = " ".join(p["text_en"] for p in pages if p.get("type") != "cover")
    prompt = (f"Gentle instrumental background music for a calm children's picture-book story titled "
              f"\"{story['title_en']}\". Story: {summary} {a.extra} Slow tempo, warm and heartwarming, soft and even "
              f"volume so it sits quietly under reading, no vocals, no lyrics, no heavy drums, no sudden changes, "
              f"gentle ending.").replace("  ", " ")
    print(f"length {length_ms / 1000:.0f}s\nprompt: {prompt}")

    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/music?output_format=mp3_44100_128",
        data=json.dumps({"prompt": prompt, "music_length_ms": length_ms, "force_instrumental": True}).encode(),
        headers={"xi-api-key": api_key(), "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            audio, song_id = r.read(), r.headers.get("song-id")
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read()[:500]!r}")
    os.makedirs(out_dir, exist_ok=True)
    open(out, "wb").write(audio)
    json.dump({"prompt": prompt, "music_length_ms": length_ms, "force_instrumental": True, "song_id": song_id},
              open(os.path.join(out_dir, "background_music.json"), "w"), indent=1, ensure_ascii=False)
    print(f"saved {out} ({len(audio)} bytes)")


if __name__ == "__main__":
    main()
