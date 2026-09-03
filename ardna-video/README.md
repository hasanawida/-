# فيديو «أرضنا» — منشور لجنة المزارعين في الطيبة

فيديو وثائقي عمودي (9:16) مدته 3 دقائق بستايل vox-ar (كولاج الجرايد)، مبني على منشور
«أرضنا» عن مصادرة أراضي الطيبة: من 80 ألف دونم عام 1948 إلى 18,774 دونماً اليوم،
ومشروعا مكب النفايات (2,099 دونماً) وشارعي 444/553 (1,900 دونم) اللذان يهددان الباقي.

- `final_720p.mp4` — الفيديو النهائي (720×1280، ~24MB)
- `beats.json` — سيناريو الفيديو الكامل (21 بيت، 24 لقطة) لإعادة الرندر عبر vox-ar
- `contact_sheet.png` — لوحة معاينة اللقطات

لإعادة الرندر بدقة 1080×1920: شغّل أداة vox-ar على `beats.json`
(`python run.py out/ardna`) مع صوت الراوي piper `ar_JO-kareem-medium`.

## التبديل إلى Gemini / ElevenLabs

`engine.py` يبدّل المشروع بين المحركات (انسخه إلى `vox-ar/scripts/`):

```bash
export GEMINI_API_KEY=...        # مجاني: https://aistudio.google.com/apikey
export ELEVENLABS_API_KEY=...    # مجاني 10k حرف/شهر

# لوحات ذكية بجميني + راوٍ ElevenLabs بتوقيت كلمات حقيقي
python3 scripts/engine.py out/ardna --images gemini --tts eleven --voice <voice_id>
python3 run.py out/ardna --gate     # بوابة الشكل
python3 run.py out/ardna            # الرندر النهائي
```

كل لقطة في `beats.json` تحمل حقل `plate` (وصف إنجليزي بلا نص) جاهزاً للتوليد بجميني.
للرجوع للوضع المجاني: `--images procedural --tts piper`.
