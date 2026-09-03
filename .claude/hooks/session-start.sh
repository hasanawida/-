#!/bin/bash
# vox-ar — تجهيز البيئة: ffmpeg، اعتماديات بايثون، نموذج العمق، صوت الراوي العربي.
# آمن للتكرار: كل خطوة تتخطى نفسها إذا كانت جاهزة.
set -euo pipefail

# على جهاز المستخدم المحلي لا نلمس النظام — الهوك للبيئة السحابية فقط.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

SKILL="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/skills/vox-ar"
VOXAR_HOME="$HOME/.voxar"
PIPER_NAME="vits-piper-ar_JO-kareem-medium"
PIPER_URL="https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/${PIPER_NAME}.tar.bz2"
MIDAS_URL="https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx"

mkdir -p "$VOXAR_HOME/models" "$VOXAR_HOME/voices"

# 1) ffmpeg + ffprobe (يستخدمهما المونتاج والتجميع)
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[vox-ar] تثبيت ffmpeg …"
  apt-get update -qq >/dev/null 2>&1 || true
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg >/dev/null 2>&1 \
    || echo "[vox-ar] تحذير: فشل تثبيت ffmpeg — الرندر لن يعمل بدونه" >&2
fi

# 2) اعتماديات بايثون (rembg ثقيل واختياري — يُتجاوَز بهدوء عند الفشل)
if [ -f "$SKILL/requirements.txt" ]; then
  echo "[vox-ar] تثبيت اعتماديات بايثون …"
  pip install -q --disable-pip-version-check -r "$SKILL/requirements.txt" 2>/dev/null \
    || pip install -q --disable-pip-version-check pillow numpy arabic-reshaper python-bidi edge-tts google-genai onnxruntime 2>/dev/null \
    || echo "[vox-ar] تحذير: بعض حزم بايثون لم تُثبَّت" >&2
fi
# محرك الصوت المحلي (بلا مفتاح ولا إنترنت وقت الرندر)
python3 -c "import sherpa_onnx, soundfile" 2>/dev/null \
  || pip install -q --disable-pip-version-check sherpa-onnx soundfile 2>/dev/null \
  || echo "[vox-ar] تحذير: sherpa-onnx غير مثبت — محرك piper لن يعمل" >&2

# 3) نموذج العمق MiDaS (لحركة الـ parallax) — 66MB مرة واحدة
if [ ! -f "$VOXAR_HOME/models/midas_small.onnx" ]; then
  echo "[vox-ar] تنزيل نموذج العمق MiDaS …"
  curl -fsSL --retry 3 -o "$VOXAR_HOME/models/midas_small.onnx.part" "$MIDAS_URL" \
    && mv "$VOXAR_HOME/models/midas_small.onnx.part" "$VOXAR_HOME/models/midas_small.onnx" \
    || { rm -f "$VOXAR_HOME/models/midas_small.onnx.part"; echo "[vox-ar] تحذير: تعذّر تنزيل نموذج العمق" >&2; }
fi

# 4) صوت الراوي العربي (Piper ar_JO) — 67MB مرة واحدة
if [ ! -d "$VOXAR_HOME/voices/$PIPER_NAME" ]; then
  echo "[vox-ar] تنزيل صوت الراوي العربي …"
  tmp=$(mktemp -d)
  if curl -fsSL --retry 3 -o "$tmp/voice.tar.bz2" "$PIPER_URL" \
     && tar xjf "$tmp/voice.tar.bz2" -C "$VOXAR_HOME/voices"; then
    :
  else
    echo "[vox-ar] تحذير: تعذّر تنزيل صوت piper — استخدم edge أو elevenlabs" >&2
  fi
  rm -rf "$tmp"
fi

# 5) تقرير المفاتيح — لا تُخزَّن في المستودع أبداً، مصدرها متغيرات البيئة
if [ -n "${GEMINI_API_KEY:-}${GOOGLE_API_KEY:-}" ]; then
  echo "[vox-ar] ✓ GEMINI_API_KEY موجود — اللوحات الذكية والصور متاحة"
else
  echo "[vox-ar] ○ GEMINI_API_KEY غير موجود — اللوحات الإجرائية فقط (مجاني)"
fi
if [ -n "${ELEVENLABS_API_KEY:-}" ]; then
  echo "[vox-ar] ✓ ELEVENLABS_API_KEY موجود — راوٍ بتوقيت كلمات حقيقي"
else
  echo "[vox-ar] ○ ELEVENLABS_API_KEY غير موجود — الراوي المحلي piper_ar"
fi

echo "[vox-ar] البيئة جاهزة."
