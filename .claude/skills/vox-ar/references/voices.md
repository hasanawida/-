# Voices — الأصوات العربية

## الأسهل: شخصيات جاهزة `tts.persona`
| persona | المحرك | الصوت | الاستخدام |
|---|---|---|---|
| `documentary_male` | edge | ar-EG-ShakirNeural | وثائقي جاد (افتراضي) |
| `documentary_female` | edge | ar-EG-SalmaNeural | وثائقي دافئ |
| `levant_male` / `levant_female` | edge | ar-JO-Taim / ar-JO-Sana | لهجة شامية قريبة |
| `gulf_male` | edge | ar-SA-HamedNeural | فصيح خليجي |
| `energetic` | edge | Shakir ×1.12 | ريلز سريعة |
| `calm_teacher` | edge | ar-LB-RamiNeural ×0.96 | شرح هادئ |
| `gemini_narrator` / `gemini_warm` / `gemini_energetic` | gemini | Charon / Kore / Puck | تعبير أعلى مع أسلوب مكتوب بالعربي |



## edge-tts (مجاني، بدون مفتاح، يعطي توقيت الكلمات → كابشن متزامن)
| voice | اللهجة | ملاحظة |
|---|---|---|
| `ar-EG-ShakirNeural` | مصري (ذكر) | افتراضي — واضح ووثائقي |
| `ar-EG-SalmaNeural` | مصري (أنثى) | دافئ |
| `ar-SA-HamedNeural` | سعودي (ذكر) | فصيح رسمي |
| `ar-SA-ZariyahNeural` | سعودي (أنثى) | |
| `ar-JO-TaimNeural` | أردني (ذكر) | الأقرب للهجة الشامية |
| `ar-JO-SanaNeural` | أردني (أنثى) | |
| `ar-LB-RamiNeural` / `ar-LB-LaylaNeural` | لبناني | |
| `ar-SY-LaithNeural` / `ar-SY-AmanyNeural` | سوري | |
| `ar-AE-HamdanNeural` / `ar-AE-FatimaNeural` | إماراتي | |

`speed` 1.0–1.1 للريلز. ملاحظة: الأصوات فصيحة النطق؛ العامية المكتوبة تُقرأ بشكل مقبول إذا كتبت الكلمات كما تُلفظ.

## Gemini TTS (`tts.engine: "gemini"`، طبقة مجانية، بدون توقيتات)
أصوات: `Charon` (عميق وثائقي)، `Kore`، `Puck`، `Fenrir`، `Aoede`، `Zephyr`.
`tts.style` مثل: `"اقرأ بصوت راوٍ وثائقي جاد، بإيقاع سريع وحماس خفيف"`. يفهم العربية جيداً.

## صوت المستخدم نفسه
سجّل التعليق لكل بيت وضع `"audio_path": "audio/my_1.wav"` في البيت — يتخطى التوليد ويستخدم تسجيلك،
والكابشن يُقسَّم بالتساوي على الكلمات (أو أضف `word_timings` يدوياً).
