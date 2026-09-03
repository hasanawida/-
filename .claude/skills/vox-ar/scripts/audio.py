#!/usr/bin/env python3
"""
audio.py — Arabic narration per beat.

  tts.engine = "edge"    (default) free Microsoft neural voices, word timings for caption sync
               "gemini"  Gemini TTS (free tier, expressive; no word timings)
               "elevenlabs"  ElevenLabs (free 10k chars/month, best Arabic voices, word timings) — ELEVENLABS_API_KEY + voice id
               "placeholder"  silence with fake timings (offline test)
  tts.voice   e.g. ar-EG-ShakirNeural / ar-SA-HamedNeural / ar-EG-SalmaNeural (edge)
              or  Charon / Kore / Puck … (gemini)
  tts.speed   1.0 = normal
  tts.style   (gemini only) a spoken-style hint, e.g. "بصوت وثائقي جاد وحماسي"
  tts.persona one word instead of engine/voice/speed/style: documentary_male · documentary_female ·
              levant_male · levant_female · gulf_male · energetic · calm_teacher · gemini_narrator ·
              gemini_warm · gemini_energetic

Writes audio/narr_<beat>.wav, and audio_duration / word_timings into beats.json.
Run BEFORE animate.py (shots stretch to fit the narration).

usage: python3 scripts/audio.py out/<project> [--force]
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provider import get_provider, get_tts, ProviderError  # noqa: E402


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


PERSONAS = {
    # name                engine    voice                   speed  gemini style hint
    "documentary_male":  ("edge",   "ar-EG-ShakirNeural",   1.0,  "راوٍ وثائقي جاد وهادئ"),
    "documentary_female":("edge",   "ar-EG-SalmaNeural",    1.0,  "راوية وثائقية دافئة وواثقة"),
    "levant_male":       ("edge",   "ar-JO-TaimNeural",     1.03, "راوٍ شامي قريب وودود"),
    "levant_female":     ("edge",   "ar-JO-SanaNeural",     1.03, "راوية شامية دافئة"),
    "gulf_male":         ("edge",   "ar-SA-HamedNeural",    1.0,  "راوٍ خليجي فصيح"),
    "energetic":         ("edge",   "ar-EG-ShakirNeural",   1.12, "راوٍ حماسي سريع لريلز"),
    "calm_teacher":      ("edge",   "ar-LB-RamiNeural",     0.96, "معلّم هادئ يشرح خطوة خطوة"),
    "gemini_narrator":   ("gemini", "Charon",               1.0,  "اقرأ بصوت راوٍ وثائقي عميق، إيقاع متوسط، مع تشويق خفيف"),
    "gemini_warm":       ("gemini", "Kore",                 1.0,  "اقرأ بصوت دافئ وقريب كأنك تنصح صديقاً"),
    "gemini_energetic":  ("gemini", "Puck",                 1.0,  "اقرأ بحماس وطاقة عالية، جمل قصيرة وسريعة"),
    "piper_ar":          ("piper",  "vits-piper-ar_JO-kareem-medium", 1.0, None),  # محلي، بلا مفتاح
    "eleven":            ("elevenlabs", None,               1.0,  None),   # voice id from tts.voice / ELEVEN_VOICE_ID
}


def run(project_dir, force=False):
    bpath = os.path.join(project_dir, "beats.json")
    with open(bpath, encoding="utf-8") as f:
        doc = json.load(f)
    adir = os.path.join(project_dir, "audio")
    os.makedirs(adir, exist_ok=True)
    cfg = dict(doc.get("tts", {}))
    if cfg.get("persona") in PERSONAS:                       # persona = engine + voice + speed + style in one word
        eng, voice, speed, style = PERSONAS[cfg["persona"]]
        for k, v in (("engine", eng), ("voice", voice), ("speed", speed), ("style", style)):
            cfg.setdefault(k, v)       # explicit tts.* keys still win over the persona
    try:
        base = get_provider(doc.get("provider"))
    except ProviderError:
        base = None
    engine = get_tts(cfg.get("engine", "edge"), base)
    if engine is None:
        raise ProviderError("tts.engine=gemini needs GEMINI_API_KEY")
    print(f"tts engine={engine.name} voice={cfg.get('voice')}")
    for beat in doc["beats"]:
        text = (beat.get("narration") or "").strip()
        if not text:
            continue
        dest = os.path.join(adir, f"narr_{beat['id']}.wav")
        user_audio = beat.get("audio_path") and not beat.get("narration_cached")
        if user_audio:                      # the user's own recording — never overwrite
            p = os.path.join(project_dir, beat["audio_path"])
            if os.path.exists(p):
                beat["audio_duration"] = round(probe(p), 3)
                beat.setdefault("word_timings", [])
                print(f"[{beat['id']}] user recording {beat['audio_path']} ({beat['audio_duration']}s)")
                continue
        if os.path.exists(dest) and beat.get("audio_duration") and not force and beat.get("narration_cached") == text:
            print(f"[{beat['id']}] reuse")
            continue
        print(f"[{beat['id']}] {text[:60]}…")
        words = engine.tts(text, cfg.get("voice"), dest, speed=float(cfg.get("speed", 1.0)), style=cfg.get("style"))
        beat["audio_path"] = os.path.relpath(dest, project_dir)
        beat["audio_duration"] = round(probe(dest), 3)
        beat["word_timings"] = [(round(s, 3), round(e, 3), w) for s, e, w in (words or [])]
        beat["narration_cached"] = text
        with open(bpath, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
    total = sum(float(b.get("audio_duration", 0) or 0) for b in doc["beats"])
    print(f"done — narration total {total:.1f}s → {bpath}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    run(os.path.abspath(a.project), force=a.force)
