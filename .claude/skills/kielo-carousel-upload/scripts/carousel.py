#!/usr/bin/env python3
"""Publish a story book from archives/ as a Finnish KieloTV image carousel, directly in prod (GCS + PlanetScale
Postgres), producing the same rows/objects the admin UI + media processor make (e.g. "Kesäpäivä laiturilla").

Credentials: the DB connection string is read in-process from GCP Secret Manager (secret DATABASE_URL,
project kielo-backend-prod) via gcloud. It is never printed or stored.

Commands
  status                         archives/ stories and whether each is already a carousel in cms_fi
  upload STORY_DIR [--music MP3] [--thumb N] [--cefr A1|A2] [--yes]
                                 slides = STORY_DIR/images/page_1..N.png (text-free), captions = data/story.json
                                 pages[].text_fi (one cue per slide, 5s, slide 0 = title), music defaults to
                                 STORY_DIR/audio/background_music.mp3. Dry-run unless --yes.
  rollback RECORD.json [--yes]   delete everything one upload created (DB rows + GCS objects). Dry-run unless --yes.
"""
import argparse, base64, glob, hashlib, json, os, re, subprocess, sys, unicodedata, uuid

PROJECT = "kielo-backend-prod"
SECRET = "DATABASE_URL"
SCHEMA = "cms_fi"
OUT_BUCKET = "kielo-media-processor-kielo-backend-prod"
UPLOAD_BUCKET = "kielo-media-uploads-kielo-backend-prod"
PUBLIC = f"https://storage.googleapis.com/{OUT_BUCKET}"
BRAND_ID = "d20a9961-6764-40e7-829e-291953274d93"      # brand on every existing fi carousel
UPLOADER = "2fe4f64b-cd56-48ea-b9ec-82f08f2de7e7"      # uploader_user_id on every existing fi carousel asset
CACHE = "public, max-age=31536000"
SECONDS = 5
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
STATE = os.path.expanduser("~/.cache/kielo-carousel-upload")


def connect(readonly=True):
    import certifi, psycopg2
    url = subprocess.run(
        ["gcloud", "secrets", "versions", "access", "latest", f"--secret={SECRET}", f"--project={PROJECT}"],
        capture_output=True, text=True, check=True).stdout.strip()
    conn = psycopg2.connect(url, connect_timeout=15, sslrootcert=certifi.where())  # verify-full, public CA
    conn.set_session(readonly=readonly, autocommit=False)
    return conn


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def slugify(s):
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def existing_titles(cur):
    cur.execute(f"select title from {SCHEMA}.content_versions where data->>'format_type'='image-carousel' and is_latest")
    return {r[0] for r in cur.fetchall()}


def cmd_status(a):
    have = existing_titles(connect().cursor())
    for d in sorted(glob.glob(os.path.join(REPO, "archives", "*", "data", "story.json"))):
        s = json.load(open(d)); sd = os.path.dirname(os.path.dirname(d))
        music = "music" if os.path.exists(os.path.join(sd, "audio", "background_music.mp3")) else "-"
        print(f"{'UPLOADED' if s['title_fi'] in have else 'new     '}  {len(s['pages'])}p  {music:<5}  "
              f"{os.path.relpath(sd, REPO)}  | {s['title_fi']}")


def prep_image(src, work, mid):
    import thumbhash
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    d = os.path.join(work, mid); os.makedirs(d, exist_ok=True)
    main = im if w <= 768 else im.resize((768, round(h * 768 / w)), Image.LANCZOS)
    main.save(os.path.join(d, "main.webp"), "WEBP", quality=75)
    prev = im.resize((300, round(h * 300 / w)), Image.LANCZOS)
    prev.save(os.path.join(d, "preview.webp"), "WEBP", quality=75)
    subprocess.run(["cp", src, os.path.join(d, "original.png")], check=True)
    size = os.path.getsize(src)
    variants = {
        "main": {"path": "main.webp", "size": os.path.getsize(os.path.join(d, "main.webp")), "codec": "webp",
                 "width": main.width, "height": main.height, "mime_type": "image/webp"},
        "preview": {"path": "preview.webp", "size": os.path.getsize(os.path.join(d, "preview.webp")), "codec": "webp",
                    "width": prev.width, "height": prev.height, "mime_type": "image/webp"},
        "original": {"path": "original.png", "size": size, "mime_type": "image/png"},
    }
    t = Image.open(src).convert("RGBA"); t.thumbnail((100, 100))  # same thumbhash the media processor stores
    th = base64.b64encode(bytes(thumbhash.rgba_to_thumb_hash(t.width, t.height, list(t.tobytes())))).decode()
    meta = {"thumbhash": th, "original_width": w, "original_height": h}
    return d, dict(mime="image/png", size=size, variants=variants, metadata=meta, media_type="Image",
                   rel="KieloTVCarouselImage", profile="kielotv-carousel", files={
                       "original.png": "image/png", "main.webp": "image/webp", "preview.webp": "image/webp"})


def prep_audio(src, work, mid):
    d = os.path.join(work, mid); os.makedirs(d, exist_ok=True)
    subprocess.run(["cp", src, os.path.join(d, "original.mp3")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-c:a", "libmp3lame", "-b:a", "192k",
                    os.path.join(d, "main.mp3")], check=True)
    dur = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                         capture_output=True, text=True, check=True).stdout)
    size = os.path.getsize(src)
    variants = {"main": {"path": "main.mp3", "size": os.path.getsize(os.path.join(d, "main.mp3")), "codec": "mp3",
                         "bitrate": "192k", "duration": round(dur(os.path.join(d, "main.mp3")), 3), "mime_type": "audio/mpeg"},
                "original": {"path": "original.mp3", "size": size, "mime_type": "audio/mpeg"}}
    meta = {"original_codec": "mp3", "original_format": "mp3", "original_duration": round(dur(src), 6)}
    return d, dict(mime="audio/mpeg", size=size, variants=variants, metadata=meta, media_type="Audio",
                   rel="KieloTVAudio", profile="kielotv-audio", files={"original.mp3": "audio/mpeg", "main.mp3": "audio/mpeg"})


def cmd_upload(a):
    story_dir = os.path.abspath(a.story_dir)
    music = a.music or os.path.join(story_dir, "audio", "background_music.mp3")
    if not os.path.exists(music):
        sys.exit(f"no music at {music}: generate it with gen_music.py or pass --music")
    story = json.load(open(os.path.join(story_dir, "data", "story.json")))
    pages = sorted(story["pages"], key=lambda p: p["page_number"])
    imgs = [os.path.join(story_dir, "images", f"page_{p['page_number']}.png") for p in pages]
    missing = [p for p in imgs if not os.path.exists(p)]
    if missing:
        sys.exit(f"missing images: {missing}")
    if not 1 <= a.thumb <= len(imgs):
        sys.exit(f"--thumb must be 1..{len(imgs)}")
    title, desc = story["title_fi"], story["title_en"]

    conn = connect(readonly=not a.yes); cur = conn.cursor()
    if title in existing_titles(cur):
        sys.exit(f"an image carousel titled {title!r} already exists in {SCHEMA}")
    hashes = [sha256(p) for p in imgs] + [sha256(music)]
    cur.execute("select hash_value, media_id from public.media_hashes where hash_type='sha256' and hash_value = any(%s)", (hashes,))
    dup = cur.fetchall()

    eid, vid = str(uuid.uuid4()), str(uuid.uuid4())
    work = os.path.join(STATE, "work", eid[:8])
    assets = []
    for p, h in zip(imgs, hashes):
        mid = str(uuid.uuid4()); d, info = prep_image(p, work, mid)
        assets.append(dict(mid=mid, dir=d, src=p, sha=h, **info))
    amid = str(uuid.uuid4()); d, info = prep_audio(music, work, amid)
    audio = dict(mid=amid, dir=d, src=music, sha=hashes[-1], **info)
    prefix = lambda m: f"kielotv/{eid}/{m}"
    url = lambda m, f: f"{PUBLIC}/{prefix(m)}/{f}"

    images = [url(x["mid"], "main.webp") for x in assets]
    data = {"locale": "fi", "audio_url": url(amid, "main.mp3"), "cefr_level": a.cefr, "format_type": "image-carousel",
            "thumbnail_url": images[a.thumb - 1], "carousel_images": images, "duration_seconds": 0,
            "cefr_level_source": "captions-v1", "transcription_status": "pending"}
    cues = [{"end_time": (i + 1) * SECONDS, "start_time": i * SECONDS, "slide_index": i, "text_primary": p["text_fi"].strip()}
            for i, p in enumerate(pages)]
    slug = f"{eid[:8]}-{slugify(title)}"

    print(f"title {title!r}  description {desc!r}  cefr {a.cefr}  thumbnail page_{a.thumb}  slug {slug}")
    for i, (x, c) in enumerate(zip(assets, cues)):
        print(f"  slide {i}: {os.path.basename(x['src'])}  main {x['variants']['main']['size']}B  | {c['text_primary']}")
    print(f"  audio: {os.path.relpath(music, REPO) if music.startswith(REPO) else music}  {audio['variants']['main']['duration']}s")
    if dup:
        print(f"note: {len(dup)} file(s) already in media_hashes (same bytes uploaded before): {[m for _, m in dup]}")
    if not a.yes:
        print("\ndry-run only; re-run with --yes to upload + insert")
        return

    os.makedirs(os.path.join(STATE, "rollback"), exist_ok=True)
    rec = os.path.join(STATE, "rollback", f"{eid[:8]}-{slugify(title)}.json")
    json.dump({"title": title, "entry_id": eid, "version_id": vid, "media_ids": [x["mid"] for x in assets] + [amid],
               "gcs_prefix": f"gs://{OUT_BUCKET}/kielotv/{eid}/"}, open(rec, "w"), indent=1, ensure_ascii=False)
    for x in assets + [audio]:
        for f, ct in x["files"].items():
            subprocess.run(["gcloud", "storage", "cp", "-q", os.path.join(x["dir"], f), f"gs://{OUT_BUCKET}/{prefix(x['mid'])}/{f}",
                            f"--content-type={ct}", f"--cache-control={CACHE}"], check=True, capture_output=True)
    print("GCS upload done")

    from psycopg2.extras import Json
    cur.execute(f"""insert into {SCHEMA}.content_entries (id, content_type, content_source, category, external_id, metadata, slug,
        title, description, status, published_at, brand_id) values (%s,'video','kielotv_videos','',%s,'{{}}',%s,%s,%s,'published',now(),%s)""",
                (eid, eid, slug, title, desc, BRAND_ID))
    cur.execute(f"""insert into {SCHEMA}.content_versions (id, content_entry_id, version_number, title, description, data, status,
        is_latest, source_locale, translation_status, enrichment_status, processing_status)
        values (%s,%s,1,%s,%s,%s,'published',true,'fi','{{}}','pending','pending')""", (vid, eid, title, desc, Json(data)))
    for x in assets + [audio]:
        cur.execute("""insert into media.media_assets (media_id, uploader_user_id, processing_status, original_storage_path, content_type,
            size_bytes, variants, related_entity_type, related_entity_id, original_filename, original_storage_bucket, original_mime_type,
            original_file_size_bytes, media_type, storage_bucket, storage_path_prefix, metadata, file_hash_sha256, results_published_at, profile)
            values (%s,%s,'Completed',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)""",
                    (x["mid"], UPLOADER, f"temp-uploads/{x['mid']}/{os.path.basename(x['src'])}", x["mime"], x["size"], Json(x["variants"]),
                     x["rel"], eid, os.path.basename(x["src"]), UPLOAD_BUCKET, x["mime"], x["size"], x["media_type"], OUT_BUCKET,
                     prefix(x["mid"]), Json(x["metadata"]), x["sha"], x["profile"]))
        cur.execute("insert into media.media_attachments (media_id, owner_type, owner_id, role) values (%s,%s,%s,'primary')",
                    (x["mid"], x["rel"], eid))
        cur.execute("insert into public.media_hashes (hash_type, hash_value, media_id) values ('sha256',%s,%s)", (x["sha"], x["mid"]))
    cur.execute(f"""insert into {SCHEMA}.kielotv_captions (video_id, content_version_id, locale, source_locale, cues)
        values (%s,%s,'fi','fi',%s)""", (eid, vid, Json(cues)))
    cur.execute(f"select k.cues, v.data from {SCHEMA}.kielotv_captions k join {SCHEMA}.content_versions v on v.id=k.content_version_id where v.id=%s", (vid,))
    got_cues, got_data = cur.fetchone()
    if got_cues != cues or got_data != data:
        conn.rollback(); sys.exit(f"verification failed; DB rolled back (GCS objects remain: rollback {rec})")
    conn.commit()
    print(f"DB committed. verified equal: True\nentry {eid}\nrollback record: {rec}")
    bad = 0
    for u in images + [data["audio_url"]]:
        code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", u], capture_output=True, text=True).stdout
        bad += code != "200"
        print(f"  {code} {u}")
    print("all public URLs OK" if not bad else f"{bad} URL(s) not reachable")


def cmd_rollback(a):
    rec = json.load(open(a.record))
    eid, mids = rec["entry_id"], rec["media_ids"]
    conn = connect(readonly=not a.yes); cur = conn.cursor()
    cur.execute(f"select title from {SCHEMA}.content_entries where id=%s", (eid,))
    row = cur.fetchone()
    print(f"rollback {rec['title']!r} entry {eid} (in DB: {bool(row)}), {len(mids)} media, GCS {rec['gcs_prefix']}")
    if not a.yes:
        print("dry-run only; re-run with --yes to delete"); return
    cur.execute(f"delete from {SCHEMA}.kielotv_captions where video_id=%s", (eid,))
    cur.execute(f"delete from {SCHEMA}.content_entries where id=%s", (eid,))  # cascades content_versions
    cur.execute("delete from public.media_hashes where media_id = any(%s::uuid[])", (mids,))
    cur.execute("delete from media.media_assets where media_id = any(%s::uuid[]) and related_entity_id=%s", (mids, eid))  # cascades attachments
    conn.commit()
    subprocess.run(["gcloud", "storage", "rm", "-r", "-q", rec["gcs_prefix"]], check=False)
    print("rolled back")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    u = sub.add_parser("upload"); u.add_argument("story_dir"); u.add_argument("--music")
    u.add_argument("--thumb", type=int, default=1, help="page number used as thumbnail (default 1 = cover)")
    u.add_argument("--cefr", default="A1", choices=["A1", "A2", "B1", "B2", "C1", "C2"])
    u.add_argument("--yes", action="store_true"); u.set_defaults(fn=cmd_upload)
    r = sub.add_parser("rollback"); r.add_argument("record"); r.add_argument("--yes", action="store_true")
    r.set_defaults(fn=cmd_rollback)
    a = p.parse_args(); a.fn(a)


if __name__ == "__main__":
    main()
