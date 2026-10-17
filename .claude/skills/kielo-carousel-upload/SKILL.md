---
name: kielo-carousel-upload
description: Publish a generated story book from archives/ as a Finnish KieloTV image carousel directly in prod (GCS + Kielo DB in GCP, not the admin UI), with captions from the story's data/story.json and ElevenLabs-generated instrumental background music. Use when the user asks to upload/publish a story (or "the next story") to the carousel, add carousel captions, make background music for a story, or undo a carousel upload.
---

# Kielo carousel upload

Turns `archives/fi/<story>/` into a published `image-carousel` in `cms_fi`, identical in shape to the ones the admin UI made (reference: "Kesäpäivä laiturilla"). **Don't use the admin UI** (admin.kielo.app); everything goes directly to GCP.

- **Slides** = `images/page_1.png … page_N.png` (text-free). Never `cards/` (text burned in).
- **Captions** = `data/story.json` `pages[].text_fi`, one cue per slide, 5 s each, slide 0 = cover = `title_fi`, no `support_text`.
- **Title / description** = `title_fi` / `title_en`.
- **Music** = `audio/background_music.mp3` in the story folder, generated per story with ElevenLabs (instrumental, length = slides × 5 s).

Run everything from the repo root with `PY=~/.cache/kielo-carousel-upload/venv/bin/python` and `S=.claude/skills/kielo-carousel-upload/scripts`.

## Hard rules

- **Never print, echo, log or store credentials.** The DB URL is read in-process from Secret Manager (`DATABASE_URL`, project `kielo-backend-prod`); the ElevenLabs key is `ELEVENLABS_API_KEY` in this repo's `.env`. Don't cat `.env` (check key names with `grep -o '^[A-Z_]*=' .env`).
- **Prod writes need the user's approval of the dry-run.** Always run `upload` without `--yes` first and show the slide/caption table + music; then `--yes` after a clear go-ahead. Same for `rollback`.
- **Let the user hear the music before upload** (send `audio/background_music.mp3` with SendUserFile). Generating music costs ElevenLabs credits; regenerate only when asked (`--force`).
- Don't enable GCP APIs or change infra. Don't touch other carousels' rows.

## One-time setup

```bash
gcloud auth login   # user does this; account needs access to kielo-backend-prod (team.kielo.app@gmail.com)
python3 -m venv ~/.cache/kielo-carousel-upload/venv && ~/.cache/kielo-carousel-upload/venv/bin/pip install -q psycopg2-binary certifi pillow thumbhash
```
Needs `ffmpeg`/`ffprobe` (brew).

## Workflow

1. **Pick the story.** `$PY $S/carousel.py status` lists every `archives/fi/*` story as `UPLOADED` or `new` (matched by `title_fi`), with page count and whether music exists. "Next story" = the oldest `new` one. Show the user its title and page texts.
2. **Music.** `python3 $S/gen_music.py archives/fi/<story> --extra "<mood + instruments for this story>"`. The prompt already includes the story's English page text plus "slow, soft, even volume, no vocals"; `--extra` adds the setting/mood (e.g. "Cozy Finnish winter living room: soft acoustic guitar, warm felt piano, light glockenspiel, ~80 BPM."). Saves `audio/background_music.mp3` + `background_music.json`. Send the mp3 to the user. `--seconds N` overrides the length if they want a longer loop.
3. **Dry-run.** `$PY $S/carousel.py upload archives/fi/<story>` (options: `--thumb N` page used as thumbnail, default 1 = cover; `--cefr A1|A2`, default A1; `--music other.mp3`). It refuses if a carousel with that title already exists or an image is missing, and notes files whose bytes were uploaded before. Show the user the table.
4. **Upload** after approval: same command with `--yes`. It uploads to GCS, inserts all DB rows in one transaction, reads them back (`verified equal: True`), and checks every public URL returns 200. It writes a rollback record to `~/.cache/kielo-carousel-upload/rollback/<id8>-<slug>.json`.
5. **Report**: title, entry id, slides/captions, music length, URLs OK, rollback record path. Optionally confirm with `status` (now `UPLOADED`).

Undo (only when the user asks): `$PY $S/carousel.py rollback ~/.cache/kielo-carousel-upload/rollback/<file>.json` (dry-run), then `--yes`. Deletes the captions, entry (cascades version), media rows, hashes and the entry's GCS folder.

## What gets written (verified against existing carousels, 2026-10)

- GCS `gs://kielo-media-processor-kielo-backend-prod/kielotv/<entry_id>/<media_id>/`: images → `original.png`, `main.webp` (768 w, q75), `preview.webp` (300 w); audio → `original.mp3`, `main.mp3` (192k). `Cache-Control: public, max-age=31536000`; bucket is publicly readable.
- `cms_fi.content_entries`: `content_type='video'`, `content_source='kielotv_videos'`, `external_id=id`, `status='published'`, `brand_id=d20a9961-…`, slug `<id8>-<slugified title>`.
- `cms_fi.content_versions` v1 `published`, `source_locale='fi'`, `data = {locale, audio_url, cefr_level, format_type:'image-carousel', thumbnail_url, carousel_images[main.webp URLs], duration_seconds:0, cefr_level_source:'captions-v1', transcription_status:'pending'}`.
- `cms_fi.kielotv_captions`: `video_id=entry id`, `locale/source_locale='fi'`, `cues=[{start_time, end_time, slide_index, text_primary}]`.
- Per file: `media.media_assets` (`processing_status='Completed'`, `profile` `kielotv-carousel`/`kielotv-audio`, `related_entity_type` `KieloTVCarouselImage`/`KieloTVAudio`, variants, metadata incl. `thumbhash` identical to the media processor's), `media.media_attachments` (role `primary`, owner = entry), `public.media_hashes` (sha256).

## Log

- 2026-10-10 "Anni-mummon villasukka" (entry `db29e59d-817a-420a-82d9-e86736e6e330`), 6 slides, 30 s ElevenLabs music. First direct upload.
