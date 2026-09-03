#!/usr/bin/env python3
"""
run.py — one command for the whole vox-ar pipeline (resumable; re-run after any failure).

  python run.py out/ai-history                # everything → out/ai-history/final.mp4
  python run.py out/ai-history --preview      # fast half-res check
  python run.py out/ai-history --gate         # stop after the preview frames (GATE 2)
  python run.py out/ai-history --provider gemini --tts edge --voice ar-EG-ShakirNeural
  python run.py examples/ai-history           # copies the example into out/ first
  python run.py out/zodiac --script examples/zodiac/script.txt   # compact script → beats.json → film
  python run.py out/x --no-qa                 # skip the supervisor (qa.py) reports

Stages: keyframes → preview_frame → audio → animate → assemble.
GEMINI_API_KEY is read from the environment (or Colab secrets) when provider=gemini.
"""
import argparse
import json
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--gate", action="store_true", help="stop after preview frames")
    ap.add_argument("--provider", default=None, help="gemini | placeholder")
    ap.add_argument("--plates", default=None, help="procedural | ai")
    ap.add_argument("--tts", default=None, help="edge | gemini | placeholder")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--skip-audio", action="store_true")
    ap.add_argument("--script", default=None, help="build beats.json from a compact script file first")
    ap.add_argument("--no-qa", action="store_true", help="skip the supervisor report at the end")
    a = ap.parse_args()

    proj = os.path.abspath(a.project)
    if a.script:
        import beats_from_script
        beats_from_script.build(a.script, proj)
    if os.path.normpath(proj).startswith(os.path.join(ROOT, "examples")):
        dest = os.path.join(ROOT, "out", os.path.basename(proj))
        if not os.path.exists(dest):
            shutil.copytree(proj, dest)
            print(f"copied example → {dest}")
        proj = dest
    bpath = os.path.join(proj, "beats.json")
    doc = json.load(open(bpath, encoding="utf-8"))
    if a.provider:
        doc["provider"] = a.provider
    if a.plates:
        doc["plates"] = a.plates
    if a.tts or a.voice:
        doc.setdefault("tts", {})
        if a.tts:
            doc["tts"]["engine"] = a.tts
        if a.voice:
            doc["tts"]["voice"] = a.voice
    if doc.get("provider") == "gemini" and not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        try:  # Colab secrets
            from google.colab import userdata  # type: ignore
            os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")
        except Exception:
            pass
    json.dump(doc, open(bpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"project={proj}\nprovider={doc.get('provider')} plates={doc.get('plates', 'procedural')} "
          f"tts={doc.get('tts', {}).get('engine')} aspect={doc.get('aspect')}")

    import keyframes, preview_frame, audio, animate, assemble, qa  # noqa: E401
    t0 = time.time()
    keyframes.run(proj)
    preview_frame.run(proj)
    print(f"[{time.time() - t0:.0f}s] images ready → {os.path.join(proj, 'preview', 'contact_sheet.png')}")
    if not a.no_qa:
        qa.run(proj, vision=False)
    if a.gate:
        return
    if not a.skip_audio:
        audio.run(proj)
    animate.run(proj, preview=a.preview, workers=a.workers)
    final = assemble.run(proj, preview=a.preview)
    print(f"[{time.time() - t0:.0f}s] DONE → {final}")
    if not a.no_qa:
        qa.run(proj, vision=True)


if __name__ == "__main__":
    main()
