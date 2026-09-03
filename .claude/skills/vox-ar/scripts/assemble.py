#!/usr/bin/env python3
"""
assemble.py — stitch shot clips → final.mp4 with narration, ducked music and optional SFX.

  music.path      background track (mp3/wav). Looped/trimmed to fit. Ducked under narration.
  music.gain_db   default -16
  sfx             optional map of entrance-animation → sound file, e.g.
                  {"pop": "assets/sfx/pop.wav", "slam": "assets/sfx/slam.wav", "stamp": "assets/sfx/stamp.wav",
                   "draw": "assets/sfx/marker.wav"}
  watermark       small text bottom-left (optional)

usage: python3 scripts/assemble.py out/<project> [--preview]
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artext   # noqa: E402
import presets  # noqa: E402
import transitions as trmod  # noqa: E402
import styles   # noqa: E402


def _mix_sfx_track(events, sfx_map, total, project_dir, gain):
    """Pre-mix every SFX hit into ONE wav (numpy) so ffmpeg gets a single input."""
    if not events or not sfx_map:
        return None
    import wave
    import numpy as np
    sr = 48000
    n = int((total + 1.0) * sr)
    track = np.zeros(n)
    cache = {}
    hits = 0
    for at, anim in events:
        hint = isinstance(anim, dict)
        p = anim["path"] if hint else sfx_map.get(anim)
        if not p:
            continue
        p = p if os.path.isabs(p) else os.path.join(project_dir, p)
        if not os.path.exists(p):
            continue
        if p not in cache:
            tmp = p + ".48k.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-ac", "1", "-ar", str(sr), tmp], check=True)
            with wave.open(tmp, "rb") as wf:
                cache[p] = np.frombuffer(wf.readframes(wf.getnframes()), dtype="<i2").astype(np.float64) / 32768
            os.remove(tmp)
        sig = cache[p]
        g = gain
        if hint:                                   # contextual sound: trim, fade in/out, own gain
            sig = sig[:int(anim["max"] * sr)].copy()
            fi, fo = int(sr * 0.08), int(sr * 0.6)
            if len(sig) > fi + fo:
                sig[:fi] *= np.linspace(0, 1, fi); sig[-fo:] *= np.linspace(1, 0, fo)
            g = anim["gain"]
        s0 = int(at * sr)
        s1 = min(n, s0 + len(sig))
        if s1 > s0:
            track[s0:s1] += sig[:s1 - s0] * g
            hits += 1
    if not hits:
        return None
    track = np.clip(track, -1, 1)
    out = os.path.join(project_dir, "audio", "sfx_track.wav")
    with wave.open(out, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes((track * 32767).astype("<i2").tobytes())
    print(f"sfx: {hits} hits → {os.path.basename(out)}")
    return out


def run(project_dir, preview=False):
    bpath = os.path.join(project_dir, "beats.json")
    with open(bpath, encoding="utf-8") as f:
        doc = json.load(f)
    presets.expand_doc(doc)
    suffix = "_preview" if preview else ""
    clips, narr, events = [], [], []
    t = 0.0
    W, H = styles.frame_size(doc.get("aspect", "9:16"))
    fps = int(doc.get("fps", 30))
    if preview:
        W, H, fps = W // 2, H // 2, 12
    tdir = os.path.join(project_dir, "clips", "transitions")
    os.makedirs(tdir, exist_ok=True)
    prev_clip = None
    for beat in doc["beats"]:
        beat_start = t
        if beat.get("audio_path"):
            narr.append((beat_start, os.path.join(project_dir, beat["audio_path"])))
        for shot in beat.get("shots", []):
            key = f"{beat['id']}{shot.get('id', '')}"
            cp = os.path.join(project_dir, "clips", f"shot_{key}{suffix}.mp4")
            if not os.path.exists(cp):
                raise SystemExit(f"missing clip {cp} — run animate.py first")
            td, kind = float(shot.get("transition_dur", 0) or 0), shot.get("transition_kind", "cut")
            if td > 0 and prev_clip and kind != "cut":
                tp = os.path.join(tdir, f"tr_{key}{suffix}.mp4")
                a = trmod.last_frame(prev_clip, os.path.join(tdir, f"a_{key}.png"))
                b = trmod.first_frame(cp, os.path.join(tdir, f"b_{key}.png"))
                trmod.render(a, b, kind, tp, fps=fps, W=W, H=H, dur=td)
                clips.append(tp)
                events.append((t, "transition"))
            clip_offset = t + td
            clips.append(cp)
            prev_clip = cp
            if shot.get("sfx_hint"):
                import sfx_freesound
                hp = sfx_freesound.fetch(shot["sfx_hint"], max_dur=float(shot.get("sfx_max", 6)),
                                         credits_path=os.path.join(project_dir, "audio", "sfx_credits.txt"))
                if hp:
                    events.append((clip_offset + float(shot.get("sfx_at", 0.3)), {"path": hp, "gain": float(shot.get("sfx_gain", 0.5)),
                                                                                  "max": float(shot.get("sfx_max", 6))}))
            for L in presets.layers_of(shot):
                events.append((clip_offset + float(L.get("at", 0)), L.get("in") or {"headline": "slam", "stamp": "stamp",
                                                                                    "circle": "draw", "arrow": "draw"}.get(L.get("type"), "pop")))
            t += float(shot.get("render_duration", shot.get("dur", 4)))
    total = t
    print(f"{len(clips)} clips, {total:.1f}s, {len(narr)} narration files")

    # ---- concat video
    lst = os.path.join(project_dir, "clips", "concat.txt")
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    video_only = os.path.join(project_dir, f"video_only{suffix}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", video_only], check=True)

    # ---- audio graph
    inputs = ["-i", video_only]
    fc, idx = [], 1
    narr_labels = []
    for start, path in narr:
        inputs += ["-i", path]
        fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(start * 1000)}|{int(start * 1000)}[n{idx}]")
        narr_labels.append(f"[n{idx}]"); idx += 1
    if narr_labels:
        fc.append("".join(narr_labels) + f"amix=inputs={len(narr_labels)}:normalize=0,apad=whole_dur={total + 0.5}[vo]")
    else:
        fc.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{total}[vo]")

    sfx_map = doc.get("sfx")
    music = doc.get("music") or {}
    if sfx_map is None or music.get("path") == "auto":       # free procedural sound design
        import sfx_gen
        total_len = sum(float(s.get("render_duration", s.get("dur", 4))) for b in doc["beats"] for s in b.get("shots", []))
        gen = sfx_gen.generate_all(os.path.join(project_dir, "audio", "sfx"),
                                   music_seconds=(total_len + 5) if music.get("path") == "auto" else None,
                                   mood=music.get("mood", "investigative"))
        if sfx_map is None:
            sfx_map = {k: v for k, v in gen.items() if k != "music"}
        if music.get("path") == "auto":
            music = dict(music, path=gen["music"])
    sfx_map = sfx_map or {}
    sfx_labels = []
    sfx_track = _mix_sfx_track(events, sfx_map, total, project_dir, float(doc.get("sfx_gain", 0.6)))
    if sfx_track:
        inputs += ["-i", sfx_track]
        fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo[sfx]")
        sfx_labels.append("[sfx]"); idx += 1

    mpath = music.get("path")
    if mpath == "jamendo" or (music.get("jamendo") and not (mpath and os.path.exists(os.path.join(project_dir, mpath)))):
        import music_jamendo
        got = music_jamendo.fetch(music.get("mood", "investigative"), os.path.join(project_dir, "audio"),
                                  query=music.get("query"))
        mpath = got or None
        if not got:
            print("  [music] jamendo unavailable → procedural underscore")
            import sfx_gen
            total_len = sum(float(s.get("render_duration", s.get("dur", 4))) for b in doc["beats"] for s in b.get("shots", []))
            mpath = sfx_gen.generate_all(os.path.join(project_dir, "audio", "sfx"), music_seconds=total_len + 5,
                                         mood=music.get("mood", "investigative"))["music"]
    if mpath:
        mpath = mpath if os.path.isabs(mpath) else os.path.join(project_dir, mpath)
    if mpath and os.path.exists(mpath):
        inputs += ["-stream_loop", "-1", "-i", mpath]
        gain = float(music.get("gain_db", -16))
        fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total},"
                  f"afade=t=in:d=1,afade=t=out:st={max(0, total - 2)}:d=2,volume={gain}dB[bgm]")
        fc.append("[vo]asplit=2[vo1][vo2]")
        fc.append("[bgm][vo1]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[bgmd]")
        mix = ["[vo2]", "[bgmd]"] + sfx_labels
        idx += 1
    else:
        mix = ["[vo]"] + sfx_labels
    if len(mix) > 1:
        fc.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first[aout]")
    else:
        fc.append(f"{mix[0]}acopy[aout]")

    # ---- watermark (optional)
    vf = None
    wm = doc.get("watermark")
    if wm:
        W, H = styles.frame_size(doc.get("aspect", "9:16"))
        if preview:
            W, H = W // 2, H // 2
        from PIL import Image
        fnt = artext.font(int(H * 0.018), "tajawal")
        png = artext.render_line(wm, fnt, fill=(255, 255, 255, 150))
        wm_path = os.path.join(project_dir, "clips", "watermark.png")
        png.save(wm_path)
        inputs += ["-i", wm_path]
        fc.append(f"[0:v][{idx}:v]overlay=x=24:y=H-h-24[vout]")
        vf = "[vout]"
        idx += 1

    final = os.path.join(project_dir, f"final{suffix}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", ";".join(fc),
           "-map", vf or "0:v", "-map", "[aout]", "-c:v", "copy" if not vf else "libx264",
           "-c:a", "aac", "-b:a", "192k", "-shortest", final]
    if vf:
        cmd[cmd.index("-c:v") + 1:cmd.index("-c:v") + 2] = ["libx264"]
        cmd += ["-crf", "18", "-pix_fmt", "yuv420p"]
    subprocess.run(cmd, check=True)
    print("final →", final)
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    run(os.path.abspath(a.project), preview=a.preview)
