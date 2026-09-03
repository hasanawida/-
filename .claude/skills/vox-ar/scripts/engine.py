#!/usr/bin/env python3
"""engine.py — يبدّل مشروع vox-ar بين محركات التوليد بأمان.

    python3 scripts/engine.py out/<project> --images gemini --tts eleven --voice <voice_id>
    python3 scripts/engine.py out/<project> --images procedural --tts edge

--images  procedural (مجاني، بلا API) | gemini (لوحات ذكية) | pollinations | placeholder
--tts     edge | gemini | eleven | piper (محلي، بلا مفتاح ولا إنترنت)
--voice   voice id لـ ElevenLabs، أو اسم صوت edge/gemini

عند تغيير الـ TTS يُمسح كاش الصوت (narration_cached) كي يُعاد التوليد بالمحرك الجديد.
"""
import argparse, json, os, sys

PERSONA = {"edge": "documentary_male", "gemini": "gemini_narrator",
           "eleven": "eleven", "piper": "piper_ar"}

ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("--images", choices=["procedural", "gemini", "pollinations", "placeholder"])
ap.add_argument("--tts", choices=["edge", "gemini", "eleven", "piper"])
ap.add_argument("--voice")
a = ap.parse_args()

path = os.path.join(a.project, "beats.json")
doc = json.load(open(path, encoding="utf-8"))

if a.images:
    if a.images == "procedural":
        doc["plates"] = "procedural"
        doc["provider"] = doc.get("provider", "placeholder")
    elif a.images == "gemini":
        missing = [f"{b['id']}{s['id']}" for b in doc["beats"] for s in b["shots"] if not s.get("plate")]
        if missing:
            sys.exit(f"لقطات بلا وصف plate: {', '.join(missing)}")
        doc["plates"] = "ai"; doc["provider"] = "gemini"
        if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
            print("تنبيه: GEMINI_API_KEY غير مضبوط — الرندر سيفشل عند مرحلة الصور.", file=sys.stderr)
    else:
        doc["plates"] = "ai"; doc["provider"] = a.images
    print(f"الصور → {a.images} (plates={doc['plates']}, provider={doc['provider']})")

if a.tts:
    tts = {"persona": PERSONA[a.tts]}
    if a.voice:
        tts["voice"] = a.voice
    doc["tts"] = tts
    cleared = 0
    for b in doc["beats"]:
        if b.pop("narration_cached", None) is not None:
            b.pop("word_timings", None); b.pop("audio_duration", None); b.pop("audio_path", None)
            cleared += 1
    print(f"الصوت → {a.tts} (persona={tts['persona']}) — مُسح كاش {cleared} تعليق")
    if a.tts == "eleven":
        if not os.environ.get("ELEVENLABS_API_KEY"):
            print("تنبيه: ELEVENLABS_API_KEY غير مضبوط.", file=sys.stderr)
        if not (a.voice or os.environ.get("ELEVEN_VOICE_ID")):
            print("تنبيه: لم يُحدَّد voice id (--voice أو ELEVEN_VOICE_ID).", file=sys.stderr)
    if a.tts == "gemini":
        print("تنبيه: Gemini TTS لا يعطي توقيت كلمات — الكابشن سيوزَّع بالتساوي.", file=sys.stderr)

json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("تم →", path)
