#!/usr/bin/env python3
"""
sfx_freesound.py — contextual sound effects from Freesound (free API key, CC-licensed sounds).

  Get a key at https://freesound.org/apiv2/apply (free) and set FREESOUND_API_KEY.
  In beats.json a shot can say  "sfx_hint": "police siren"  (English, 1–3 words) — assemble.py fetches a short
  matching sound, ducks it under the narration with fades, and logs attribution to audio/sfx_credits.txt.
  Sounds are cached in ~/.voxar/sfx/ so the same hint is downloaded once.

  fetch(query, max_dur=6) -> local mp3 path or None
"""
import json
import os
import sys
import urllib.parse
import urllib.request

CACHE = os.path.join(os.path.expanduser("~"), ".voxar", "sfx")


def fetch(query, max_dur=6.0, credits_path=None, prefer_cc0=True):
    os.makedirs(CACHE, exist_ok=True)
    slug = "".join(c if c.isalnum() else "_" for c in query.lower())[:40]
    for f in os.listdir(CACHE):
        if f.startswith(slug + "__"):
            return os.path.join(CACHE, f)
    key = os.environ.get("FREESOUND_API_KEY")
    if not key:
        print(f"  [freesound] FREESOUND_API_KEY not set — skipping '{query}'", file=sys.stderr)
        return None
    flt = f"duration:[0.3 TO {max_dur}]"
    if prefer_cc0:
        flt += ' license:"Creative Commons 0"'
    params = {"query": query, "filter": flt, "fields": "id,name,username,license,previews,duration,avg_rating",
              "sort": "rating_desc", "page_size": 8, "token": key}
    url = "https://freesound.org/apiv2/search/text/?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.load(r)
        res = data.get("results", [])
        if not res and prefer_cc0:
            return fetch(query, max_dur, credits_path, prefer_cc0=False)
        if not res:
            return None
        s = res[0]
        prev = s["previews"].get("preview-hq-mp3") or s["previews"].get("preview-lq-mp3")
        dest = os.path.join(CACHE, f"{slug}__{s['id']}.mp3")
        urllib.request.urlretrieve(prev, dest)
        line = f"SFX \"{s['name']}\" by {s['username']} — Freesound #{s['id']} — {s['license']}\n"
        if credits_path:
            with open(credits_path, "a", encoding="utf-8") as f:
                f.write(line)
        print(f"  [freesound] {query} → {s['name']} ({s['duration']:.1f}s)")
        return dest
    except Exception as e:
        print(f"  [freesound] {query}: {str(e)[:80]}", file=sys.stderr)
        return None


if __name__ == "__main__":
    print(fetch(" ".join(sys.argv[1:]) or "police siren"))
