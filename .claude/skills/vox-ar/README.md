# vox-ar — مولّد فيديوهات Vox العربية (ستايل الجرايد)

سكيل لوكيل برمجي (Claude Code / Cowork / Codex) يحوّل موضوعاً واحداً إلى ريل أو فيديو وثائقي عربي كامل
بستايل القصاصات الصحفية: لوحات كولاج، صور أرشيفية أبيض وأسود، عناوين عربية على تظليل أصفر/أحمر، أختام،
دوائر وأسهم بالقلم، تعليق صوتي عربي، كابشن متزامن، موسيقى — **بأدوات مجانية**.

مبني على فكرة [vox-ai-motion-graphics-generator](https://github.com/Anil-matcha/vox-ai-motion-graphics-generator)
مع 4 فروق جوهرية:

| | الأصلي | vox-ar |
|---|---|---|
| النص | يُولَّد داخل الصورة (إنجليزي) | يُركَّب بالكود فوق الصورة — عربي سليم وحاد 100% |
| التحريك | Veo على اللوحة كاملة (مدفوع) | مونتاج عناصر بالكود (pop/slam/stamp/draw) + Veo اختياري |
| المزوّد | MuAPI (مدفوع) | Gemini API (طبقة مجانية) + edge-tts + ffmpeg |
| الستايل | ريترو أمريكي | جريدة استقصائية عربية (تريكات/Vox) |

## التثبيت
```bash
pip install pillow arabic-reshaper python-bidi edge-tts google-genai "rembg[cpu]"
# + ffmpeg على المسار (Windows: choco install ffmpeg / winget install ffmpeg)
set GEMINI_API_KEY=...        # مجاني من https://aistudio.google.com/apikey
```

## التشغيل (أمر واحد)
```bash
python run.py examples/ai-history --gate                     # صور + معاينة اللقطات (بوابة الشكل)
python run.py out/ai-history --provider gemini --tts edge     # الفيلم كامل → out/ai-history/final.mp4
python run.py examples/screen-time --provider placeholder     # تجربة بدون أي مفتاح
```
**بدون تثبيت:** افتح `vox-ar.ipynb` في Google Colab (ارفع الـ zip إلى Drive، ضع `GEMINI_API_KEY` في 🔑 الأسرار، Run all).
**Windows:** `run_ai_history.bat` / `run_screen_time.bat`.

## ما الجديد في v4
- **ساحر القصة** (`references/story-wizard.md`): فئة → 10 أفكار → إعدادات → حقائق → سكربت → مشاهد، مثل برومبت تريكات لكن مدمج.
- **سكربت مضغوط** (`beats_from_script.py`): تكتب القصة والقوالب بصيغة نصية قصيرة بدل JSON.
- **جسر Google Flow** (`flow_export.py` / `flow_import.py`): بدون أي مفتاح API — صدّر البرومبتات، ولّد في Flow (Nano Banana / Veo)، استورد.
- **انتقالات ورقية** بالكود (تمزيق، انزلاق، طيّ، مسح) مع ووش — "الفصل الأهم" في فيديو تريكات.
- **مؤثرات سياقية** من Freesound (`sfx_hint`) مع توثيق الاعتماد.
- **المراقب** (`qa.py`): فحوصات تداخل/كابشن/إيقاع/حقائق + مراجعة بصرية Gemini، يشتغل تلقائياً في `run.py`.
- **ElevenLabs** كمحرك راوٍ (مجاني 10k حرف/شهر) مع توقيت كلمات.

## ما الجديد في v3
- **كل صورة تتحرك بأجزائها**: عمق MiDaS محلي → parallax 2.5D على اللوحات والعناصر. غبار وضوء حيّ.
- **15 قالباً** و**10 علامات حديثة** (callout، عدّاد، ✓/✗، أعمدة، خط زمني، VS، فقاعة، ورقة لاصقة، شارة).
- **5 ثيمات** كاملة (جرايد، افتتاحية حديثة، داكن استقصائي، مخططات، ريترو).
- **8 مزاجات موسيقى** مولّدة + Jamendo (موسيقى CC حقيقية) + **10 شخصيات راوٍ**.
- مزوّدات مجانية إضافية: Pollinations (بدون مفتاح) و Hugging Face (توكن مجاني) — تجريبية.
- دليل إخراج فني `references/art-direction.md`: كيف تختار الشكل والموسيقى والراوي حسب الموضوع.

## لماذا مجاني وسريع
اللوحات صفحات جرايد عربية مرسومة بالكود (بدون API)، القصاصات فقط عبر Gemini المجاني (أو صور أرشيفية حقيقية)،
الصوت edge-tts، المؤثرات والموسيقى مولّدة بالكود، والرندر متوازٍ. فيلم 3 دقائق: ~25 صورة و~5 دقائق رندر.

## سير العمل الكامل
انظر `SKILL.md` (بوابتا موافقة: القصة ثم الشكل) و`references/` (كتابة البيتات، الطبقات، الستايل، الأصوات).

## الهيكل
```
run.py  vox-ar.ipynb  run_*.bat
scripts/  provider.py styles.py artext.py paperfx.py newsprint.py presets.py marks.py depth.py transitions.py
          sfx_gen.py sfx_freesound.py music_jamendo.py beats_from_script.py flow_export.py flow_import.py qa.py
          keyframes.py preview_frame.py audio.py veo_clips.py animate.py assemble.py
references/  story-wizard.md art-direction.md beat-writing.md layers.md style-bible.md voices.md
examples/  ai-history (16:9, 3 min) · screen-time (9:16 reel) · zodiac (script.txt → dark-investigative)
examples/screen-time/beats.json
assets/fonts/  Cairo · Noto Kufi Arabic · Tajawal · Changa (OFL)
```
