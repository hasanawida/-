#!/usr/bin/env python3
"""
music_jamendo.py — OPTIONAL free real music via the Jamendo API (Creative-Commons tracks).

Get a free client_id at https://devportal.jamendo.com/ and set JAMENDO_CLIENT_ID.
beats.json:  "music": {"path": "jamendo", "mood": "investigative"}   (or "query": "cinematic piano")
The chosen track's title/artist/license are written to audio/music_credits.txt — put them in your
video description (CC-BY requires attribution).
"""
import json
import os
import sys
import urllib.parse
import urllib.request

MOOD_TAGS = {
    "investigative": "cinematic+documentary+suspense", "tense": "dark+suspense+cinematic",
    "hopeful": "inspiring+uplifting+piano", "upbeat": "upbeat+happy+pop", "epic": "epic+orchestral+cinematic",
    "calm": "ambient+calm+piano", "tech": "electronic+minimal+corporate", "kids": "children+happy+ukulele",
}


def fetch(mood="investigative", out_dir=".", query=None, client_id=None):
    cid = client_id or os.environ.get("JAMENDO_CLIENT_ID")
    if not cid:
        print("  [jamendo] JAMENDO_CLIENT_ID not set", file=sys.stderr)
        return None
    params = {"client_id": cid, "format": "json", "limit": 8, "audiodownload_allowed": "true",
              "include": "licenses", "order": "popularity_month", "audioformat": "mp32"}
    if query:
        params["search"] = query
    else:
        params["fuzzytags"] = MOOD_TAGS.get(mood, mood)
    url = "https://api.jamendo.com/v3.0/tracks/?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.load(r)
        tracks = [t for t in data.get("results", []) if t.get("audiodownload") and 90 <= int(t.get("duration", 0)) <= 400]
        if not tracks:
            return None
        tr = tracks[0]
        os.makedirs(out_dir, exist_ok=True)
        dest = os.path.join(out_dir, f"jamendo_{tr['id']}.mp3")
        if not os.path.exists(dest):
            urllib.request.urlretrieve(tr["audiodownload"], dest)
        with open(os.path.join(out_dir, "music_credits.txt"), "a", encoding="utf-8") as f:
            f.write(f"Music: \"{tr['name']}\" by {tr['artist_name']} — Jamendo, license {tr.get('license_ccurl', 'CC')} — {tr.get('shareurl', '')}\n")
        print(f"  [jamendo] {tr['name']} — {tr['artist_name']}")
        return dest
    except Exception as e:
        print(f"  [jamendo] failed: {str(e)[:80]}", file=sys.stderr)
        return None


if __name__ == "__main__":
    print(fetch(sys.argv[1] if len(sys.argv) > 1 else "investigative", "/tmp"))
