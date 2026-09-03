#!/usr/bin/env python3
"""
provider.py — pluggable media backends for vox-ar.

  gemini       Google Gemini API (GEMINI_API_KEY). Images: gemini-2.5-flash-image (free tier).
               TTS: gemini-2.5-flash-preview-tts (free tier). Veo: PAID — only used when a shot
               explicitly asks for "motion": "veo".
  edge         (audio only) Microsoft Edge neural voices via edge-tts — free, no key, Arabic voices,
               returns word timings (used for phrase-synced captions).
  pollinations Keyless free text-to-image (experimental; images only).
  hf           Hugging Face Inference API, free token (experimental; FLUX.1-schnell; images only).
  placeholder  Offline mock: procedural paper plates + labeled sticker shapes. Lets you run the
               whole pipeline end-to-end with zero API calls to check timing/layout.

Background removal: `rembg` if installed (free, local); else a white-background keyer.
"""
import io
import os
import struct
import sys
import time
import wave

from PIL import Image, ImageDraw, ImageFilter

import paperfx
import artext


class ProviderError(RuntimeError):
    pass


# ---------------------------------------------------------------- bg removal
def remove_background(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    if os.environ.get("VOXAR_NO_REMBG"):
        return _key_white(img)
    try:
        from rembg import remove, new_session  # type: ignore
        global _rembg_session
        if _rembg_session is None:
            _rembg_session = new_session(os.environ.get("VOXAR_REMBG_MODEL", "u2net"))
        out = remove(img, session=_rembg_session)
        return _tidy_alpha(out.convert("RGBA"))
    except Exception as e:  # rembg missing / model download failed → white keyer
        print(f"  [bg] rembg unavailable ({str(e)[:60]}), using white keyer", file=sys.stderr)
        return _key_white(img)


_rembg_session = None


def _tidy_alpha(img, cut=40):
    """Kill faint halo pixels and harden the sticker edge a little."""
    a = img.split()[3].point(lambda v: 0 if v < cut else min(255, int((v - cut) * 255 / (255 - cut) * 1.15)))
    img.putalpha(a)
    return img


def _key_white(img: Image.Image, thresh=235, soft=18) -> Image.Image:
    """Alpha = distance from pure white, then flood-fill from the border so white
    areas INSIDE the subject are kept."""
    from PIL import ImageOps, ImageChops
    rgb = img.convert("RGB")
    r, g, b = rgb.split()
    mn = ImageChops.darker(ImageChops.darker(r, g), b)
    # whiteness mask (255 = white)
    white = mn.point(lambda v: 255 if v >= thresh else 0)
    # flood-fill outside region from corners
    w, h = white.size
    outside = white.copy()
    seed_fill = Image.new("L", (w, h), 0)
    ImageDraw.floodfill(outside, (0, 0), 128)
    ImageDraw.floodfill(outside, (w - 1, 0), 128)
    ImageDraw.floodfill(outside, (0, h - 1), 128)
    ImageDraw.floodfill(outside, (w - 1, h - 1), 128)
    alpha = outside.point(lambda v: 0 if v == 128 else 255)
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
    out = img.copy()
    out.putalpha(alpha)
    return out


def trim(img: Image.Image, pad=4) -> Image.Image:
    bbox = img.split()[3].getbbox()
    if not bbox:
        return img
    l, t, r, b = bbox
    return img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))


# ---------------------------------------------------------------- base
class Provider:
    name = "base"

    def image(self, prompt: str, aspect: str = "9:16", size=None) -> Image.Image:
        raise NotImplementedError

    def tts(self, text: str, voice: str, out_path: str, speed: float = 1.0, style: str | None = None):
        """Write audio to out_path. Return list of (start_s, end_s, word) or []."""
        raise NotImplementedError

    def veo(self, prompt: str, image: Image.Image, out_path: str, aspect="9:16", duration=8):
        raise ProviderError(f"{self.name} has no video model")


# ---------------------------------------------------------------- placeholder
class PlaceholderProvider(Provider):
    name = "placeholder"

    def image(self, prompt, aspect="9:16", size=None):
        import styles
        w, h = size or styles.frame_size(aspect)
        is_cutout = "isolated" in prompt and "pure white background" in prompt
        if is_cutout:
            s = 640
            img = Image.new("RGBA", (s, s), (255, 255, 255, 255))
            d = ImageDraw.Draw(img)
            import random
            rnd = random.Random(hash(prompt) & 0xffff)
            col = rnd.choice([(60, 60, 60), (110, 100, 90), (40, 40, 40)])
            kind = rnd.choice(["person", "doc", "object"])
            if kind == "person":
                d.ellipse((220, 60, 420, 260), fill=col)
                d.rounded_rectangle((150, 270, 490, 600), 60, fill=col)
            elif kind == "doc":
                d.rectangle((120, 60, 520, 590), fill=(236, 226, 204))
                for y in range(120, 560, 26):
                    d.line((160, y, 480, y), fill=(90, 90, 90), width=4)
            else:
                d.polygon([(320, 60), (560, 320), (320, 580), (80, 320)], fill=col)
            label = prompt.split("isolated", 1)[1].split(",")[0].strip()[:28]
            fnt = artext.font(30, "tajawal")
            artext.draw_text(d, (s // 2, s - 40), label, fnt, (200, 30, 30), anchor="mm")
            return img
        bg = paperfx.paper_background(w, h, seed=hash(prompt) & 0xff)
        d = ImageDraw.Draw(bg)
        fnt = artext.font(int(min(w, h) * 0.035), "tajawal")
        artext.draw_text(d, (w // 2, int(h * 0.92)), "PLACEHOLDER PLATE", fnt, (150, 140, 120), anchor="mm")
        return bg

    def tts(self, text, voice, out_path, speed=1.0, style=None):
        # ~2.6 words/sec Arabic narration; write silence of that length (with a faint tick)
        n = max(1, len(text.split()))
        dur = max(1.2, n / (2.6 * speed))
        sr = 24000
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
            frames = bytearray()
            for i in range(int(sr * dur)):
                v = int(600 * ((i % 8000) < 40)) if i < sr * 0.05 else 0
                frames += struct.pack("<h", v)
            wf.writeframes(bytes(frames))
        # fake even word timings
        words = text.split()
        step = dur / len(words)
        return [(i * step, (i + 1) * step, wd) for i, wd in enumerate(words)]


# ---------------------------------------------------------------- gemini
class GeminiProvider(Provider):
    name = "gemini"
    IMAGE_MODEL = os.environ.get("VOXAR_IMAGE_MODEL", "gemini-2.5-flash-image")
    TTS_MODEL = os.environ.get("VOXAR_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    VEO_MODEL = os.environ.get("VOXAR_VEO_MODEL", "veo-3.1-fast-generate-preview")

    def __init__(self):
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ProviderError("GEMINI_API_KEY is not set (get one free at https://aistudio.google.com/apikey)")
        from google import genai
        self.genai = genai
        from google.genai import types
        self.types = types
        self.client = genai.Client(api_key=key)

    def _retry(self, fn, tries=4, wait=8):
        last = None
        for i in range(tries):
            try:
                return fn()
            except Exception as e:  # rate limits on the free tier are common
                last = e
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "503" in msg:
                    print(f"  [gemini] rate-limited, waiting {wait * (i + 1)}s …", file=sys.stderr)
                    time.sleep(wait * (i + 1))
                    continue
                raise
        raise ProviderError(f"gemini failed after retries: {last}")

    def image(self, prompt, aspect="9:16", size=None):
        t = self.types
        cfg = t.GenerateContentConfig(response_modalities=["IMAGE"],
                                      image_config=t.ImageConfig(aspect_ratio=aspect))

        def go():
            resp = self.client.models.generate_content(model=self.IMAGE_MODEL, contents=[prompt], config=cfg)
            for part in resp.candidates[0].content.parts:
                if getattr(part, "inline_data", None) and part.inline_data.data:
                    return Image.open(io.BytesIO(part.inline_data.data)).convert("RGBA")
            raise ProviderError("no image in response (safety block?)")
        return self._retry(go)

    def tts(self, text, voice, out_path, speed=1.0, style=None):
        t = self.types
        voice = voice or "Charon"
        prompt = f"{style}: {text}" if style else text
        cfg = t.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=t.SpeechConfig(voice_config=t.VoiceConfig(
                prebuilt_voice_config=t.PrebuiltVoiceConfig(voice_name=voice))))

        def go():
            resp = self.client.models.generate_content(model=self.TTS_MODEL, contents=prompt, config=cfg)
            return resp.candidates[0].content.parts[0].inline_data.data
        pcm = self._retry(go)
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000)
            wf.writeframes(pcm)
        if speed and abs(speed - 1.0) > 0.02:
            _atempo(out_path, speed)
        return []  # no word timings from Gemini TTS

    def veo(self, prompt, image, out_path, aspect="9:16", duration=8):
        t = self.types
        buf = io.BytesIO(); image.convert("RGB").save(buf, "PNG")
        op = self.client.models.generate_videos(
            model=self.VEO_MODEL, prompt=prompt,
            image=t.Image(image_bytes=buf.getvalue(), mime_type="image/png"),
            config=t.GenerateVideosConfig(aspect_ratio=aspect, duration_seconds=duration,
                                          number_of_videos=1))
        while not op.done:
            time.sleep(8)
            op = self.client.operations.get(op)
        vid = op.response.generated_videos[0]
        self.client.files.download(file=vid.video)
        vid.video.save(out_path)
        return out_path


# ---------------------------------------------------------------- edge-tts (audio only)
class EdgeTTS:
    name = "edge"

    def tts(self, text, voice, out_path, speed=1.0, style=None):
        import asyncio
        import edge_tts
        voice = voice or "ar-EG-ShakirNeural"
        rate = f"{int(round((speed - 1) * 100)):+d}%"
        words = []

        async def go():
            com = edge_tts.Communicate(text, voice, rate=rate)
            mp3 = out_path if out_path.endswith(".mp3") else out_path + ".mp3"
            with open(mp3, "wb") as f:
                async for chunk in com.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        s = chunk["offset"] / 1e7
                        words.append((s, s + chunk["duration"] / 1e7, chunk["text"]))
            if mp3 != out_path:
                import subprocess
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, out_path], check=True)
                os.remove(mp3)
        asyncio.run(go())
        return words


# ---------------------------------------------------------------- ElevenLabs (free tier: 10k chars/month)
class ElevenTTS:
    """ElevenLabs text-to-speech with word timestamps. Needs ELEVENLABS_API_KEY and a voice id
    (tts.voice, or ELEVEN_VOICE_ID). Model: eleven_multilingual_v2 (Arabic) or eleven_v3 if enabled."""
    name = "elevenlabs"
    MODEL = os.environ.get("VOXAR_ELEVEN_MODEL", "eleven_multilingual_v2")

    def tts(self, text, voice, out_path, speed=1.0, style=None):
        import base64, json as _json, subprocess, urllib.request
        key = os.environ.get("ELEVENLABS_API_KEY")
        voice = voice or os.environ.get("ELEVEN_VOICE_ID")
        if not key or not voice:
            raise ProviderError("elevenlabs needs ELEVENLABS_API_KEY and a voice id (tts.voice / ELEVEN_VOICE_ID)")
        body = _json.dumps({"text": text, "model_id": self.MODEL,
                            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "speed": speed}}).encode()
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps",
                                     data=body, headers={"xi-api-key": key, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = _json.load(r)
        mp3 = out_path + ".mp3"
        open(mp3, "wb").write(base64.b64decode(data["audio_base64"]))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, out_path], check=True)
        os.remove(mp3)
        # characters → word timings
        al = data.get("alignment") or {}
        chars, st, en = al.get("characters", []), al.get("character_start_times_seconds", []), al.get("character_end_times_seconds", [])
        words, cur, s0 = [], "", None
        for c, a, b in zip(chars, st, en):
            if c.isspace():
                if cur:
                    words.append((s0, b, cur)); cur, s0 = "", None
            else:
                if s0 is None:
                    s0 = a
                cur += c
        if cur:
            words.append((s0, en[-1] if en else 0, cur))
        return words


def _atempo(path, speed):
    import subprocess
    tmp = path + ".tmp.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-filter:a", f"atempo={speed}", tmp], check=True)
    os.replace(tmp, path)


# ---------------------------------------------------------------- pollinations (no key) — experimental
class PollinationsProvider(Provider):
    """Free, keyless text-to-image (flux) at image.pollinations.ai. Quality/availability vary; no TTS."""
    name = "pollinations"

    def image(self, prompt, aspect="9:16", size=None):
        import urllib.parse, urllib.request
        import styles
        w, h = size or styles.frame_size(aspect)
        w, h = (1024, int(1024 * h / w)) if w >= h else (int(1024 * w / h), 1024)
        url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt[:900]) +
               f"?width={w}&height={h}&nologo=true&model=flux&seed={abs(hash(prompt)) % 100000}")
        last = None
        for i in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "vox-ar/1.0"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    return Image.open(io.BytesIO(r.read())).convert("RGBA")
            except Exception as e:
                last = e; time.sleep(6 * (i + 1))
        raise ProviderError(f"pollinations failed: {last}")


# ---------------------------------------------------------------- hugging face inference (free token) — experimental
class HFProvider(Provider):
    """Hugging Face Inference API with a free token (HF_TOKEN): FLUX.1-schnell. Rate-limited on the free tier."""
    name = "hf"
    MODEL = os.environ.get("VOXAR_HF_MODEL", "black-forest-labs/FLUX.1-schnell")

    def __init__(self):
        self.token = os.environ.get("HF_TOKEN")
        if not self.token:
            raise ProviderError("HF_TOKEN not set (free at https://huggingface.co/settings/tokens)")

    def image(self, prompt, aspect="9:16", size=None):
        import json as _json, urllib.request
        import styles
        w, h = size or styles.frame_size(aspect)
        w, h = (1024, int(1024 * h / w) // 16 * 16) if w >= h else (int(1024 * w / h) // 16 * 16, 1024)
        body = _json.dumps({"inputs": prompt, "parameters": {"width": w, "height": h, "num_inference_steps": 4}}).encode()
        req = urllib.request.Request(f"https://api-inference.huggingface.co/models/{self.MODEL}", data=body,
                                     headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json",
                                              "x-wait-for-model": "true"})
        last = None
        for i in range(4):
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    return Image.open(io.BytesIO(r.read())).convert("RGBA")
            except Exception as e:
                last = e; time.sleep(10 * (i + 1))
        raise ProviderError(f"hf failed: {last}")


# ---------------------------------------------------------------- factory
def get_provider(name: str | None) -> Provider:
    name = (name or os.environ.get("VOXAR_PROVIDER") or "gemini").lower()
    if name == "placeholder":
        return PlaceholderProvider()
    if name == "gemini":
        return GeminiProvider()
    if name == "pollinations":
        return PollinationsProvider()
    if name == "hf":
        return HFProvider()
    raise ProviderError(f"unknown provider '{name}' (use gemini | pollinations | hf | placeholder)")


# ---------------------------------------------------------------- Piper (offline, no key, no network)
class PiperTTS:
    """Piper/VITS عبر sherpa-onnx — يعمل بالكامل بلا مفتاح وبلا إنترنت بعد تنزيل الصوت مرة.

    الصوت يُتوقَّع في VOXAR_PIPER_VOICE أو ~/.voxar/voices/<VOXAR_PIPER_NAME>/ ،
    الافتراضي vits-piper-ar_JO-kareem-medium (عربي، لهجة أردنية/شامية).
    sherpa-onnx لا يعطي توقيت كلمات، فيُقدَّر من أطوال الكلمات وعلامات الترقيم
    (الأرقام تُنطق أطول بكثير من الحروف) — يكفي لكابشن متزامن بشكل مقبول.
    """
    name = "piper"
    DEFAULT_VOICE = os.environ.get("VOXAR_PIPER_NAME", "vits-piper-ar_JO-kareem-medium")
    _tts = None

    def _voice_dir(self, voice=None):
        d = os.environ.get("VOXAR_PIPER_VOICE")
        if d and os.path.isdir(d):
            return d
        return os.path.join(os.path.expanduser("~"), ".voxar", "voices", voice or self.DEFAULT_VOICE)

    def _engine(self, voice=None):
        if PiperTTS._tts is not None:
            return PiperTTS._tts
        d = self._voice_dir(voice)
        if not os.path.isdir(d):
            raise ProviderError(f"صوت piper غير موجود في {d} — شغّل .claude/hooks/session-start.sh أو نزّله يدوياً")
        onnx = next((f for f in sorted(os.listdir(d)) if f.endswith(".onnx")), None)
        if not onnx:
            raise ProviderError(f"لا يوجد ملف .onnx داخل {d}")
        try:
            import sherpa_onnx
        except ImportError:
            raise ProviderError("sherpa-onnx غير مثبت (pip install sherpa-onnx soundfile)")
        cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=os.path.join(d, onnx), tokens=os.path.join(d, "tokens.txt"),
                data_dir=os.path.join(d, "espeak-ng-data")),
            num_threads=max(1, (os.cpu_count() or 2))))
        PiperTTS._tts = sherpa_onnx.OfflineTts(cfg)
        return PiperTTS._tts

    @staticmethod
    def _weight(w):
        core = w.strip("،,.؟?!:؛…\"'()")
        n = sum(3.4 if ch.isdigit() else (0.5 if ch in "%." else 1.0) for ch in core)
        n = max(n, 1.0) + 1.2                      # زمن ثابت لكل كلمة
        if w.rstrip()[-1:] in "،,.؟?!:؛…":
            n += 3.0                               # سكتة بعد علامة الترقيم
        return n

    def tts(self, text, voice, out_path, speed=1.0, style=None):
        import soundfile as sf
        eng = self._engine(voice)
        a = eng.generate(text, sid=0, speed=speed or 1.0)
        sf.write(out_path, a.samples, a.sample_rate)
        dur = len(a.samples) / float(a.sample_rate)
        words = text.split()
        if not words:
            return []
        ws = [self._weight(w) for w in words]
        lead, tail = 0.18, 0.30                    # صمت البداية/النهاية في مخرجات piper
        unit = max(dur - lead - tail, 0.5) / sum(ws)
        out, t = [], lead
        for w, wt in zip(words, ws):
            out.append((t, t + wt * unit, w))
            t += wt * unit
        return out


def get_tts(engine: str | None, fallback: Provider):
    engine = (engine or "edge").lower()
    if engine == "edge":
        return EdgeTTS()
    if engine in ("elevenlabs", "eleven"):
        return ElevenTTS()
    if engine == "piper":
        return PiperTTS()
    if engine == "placeholder":
        return PlaceholderProvider()
    return fallback  # gemini
