# Presets — القوالب الجاهزة (الطريقة الأسهل)

بدل تحديد كل طبقة يدوياً، اللقطة تحمل `preset` وحقولاً قصيرة و`presets.py` يوسّعها لطبقات كاملة بمواقع وتوقيتات مناسبة للصيغة (16:9 أو 9:16):

| preset | الاستخدام | الحقول |
|---|---|---|
| `hero_right` / `hero_left` | قصاصة كبيرة + عنوان وعنوان فرعي على الجهة الأخرى | `cutout`, `effects`, `headline`, `sub`, `stamp`, `mark`, `tape`, `pin` |
| `hero_center` | قصاصة في المنتصف، عنوان فوق، فرعي تحت | نفسها |
| `title` | عنوان كبير في المنتصف (خطّاف/انتقال) | `headline`, `headline_bar`, `sub`, `stamp`, `mark` |
| `quote` | اقتباس على بار أبيض | نفسها |
| `number` | رقم ضخم + شرح بجانبه | `headline` (الرقم), `sub`, `stamp`, `mark` |
| `split` | قصاصتان متقابلتان | `cutout`, `cutout2`, `effects2`, `headline`, `sub` |
| `list` | حتى 4 بنود تدخل تباعاً | `headline`, `items[]`, `cutout` (اختياري), `stamp` |
| `checklist` | بنود مع ✓/✗ | `headline`, `items: [["نص", true/false], …]`, `cutout` |
| `stats` | رسم أعمدة متحرك | `headline`, `items: [["ليبل", رقم], …]`, `stamp` |
| `timeline` | خط زمني بدبابيس | `headline`, `items: ["1950", "1997", …]` |
| `versus` | مقارنة خيارين | `cutout`, `cutout2`, `headline`, `left`, `right` |
| `callouts` | تسميات بخطوط توجيه على صورة | `cutout`, `callouts: [{"text","x","y","tx","ty"}, …]`, `headline` |
| `note` | ورقة لاصقة + دبوس | `cutout`, `headline`, `note` |

إضافات على أي قالب: `value` (+`prefix`/`suffix`) = عدّاد رقمي بدل العنوان، `bubble` (+`bubble_x/y`) = فقاعة كلام، `badge` = شارة دائرية.

حقول مشتركة: `bg` (`cream` `red` `black` `yellow` `blue`)، `camera`، `headline_bar` (`yellow` `red` `white` `black`)،
`headline_size`، `sub_size`، `cutout_w`، `cutout_rot`، `mark` (`circle` `arrow` `underline` `none`).
أي `layers` إضافية تُلحق بعد طبقات القالب.

# Layers — مرجع طبقات اللقطة (`shots[].layers[]`)

كل الإحداثيات نسبية للإطار: `x`,`y` مركز الطبقة (0..1)، `w` عرض نسبة من عرض الإطار، `size` نسبة من ارتفاع الإطار.
`at` زمن الدخول بالثواني من بداية اللقطة. `in` نوع الدخول. `until` (اختياري) زمن الخروج، `out`: `fade|shrink|slide_l|slide_r|slide_up|slide_down`.
`idle`: `bob` (افتراضي للقصاصات) | `sway` (افتراضي للعناوين) | `float` | `none`. `idle_amp` قوة الخمول (1.0).

| type | الحقول الخاصة | الدخول الافتراضي | ملاحظات |
|---|---|---|---|
| `cutout` | `subject` (إنجليزي، شيء واحد معزول)، `effects`: `bw`,`censor_eyes`,`torn`,`old`، `extra`، `w`، `rot`، `border`، `shadow`، `halftone` | `pop` | يُولَّد على خلفية بيضاء ثم تُفصل. أو `"image": "path.png"` لصورة المستخدم (`remove_bg: false` لإبقائها). |
| `image` | `image` (مسار)، `w`، `rot`، `effects: ["bw"]` | `pop` | صورة جاهزة كقصاصة (لوغو، صورة حقيقية). |
| `headline` | `text` (عربي)، `bar`: `yellow|red|white|black|paper`، `fill`، `size` (0.045–0.09)، `max_w`، `rot`، `font`، `torn` | `slam` | العنوان على بار تظليل ممزّق الحواف — توقيع الستايل. يلتف على أسطر تلقائياً. |
| `stamp` | `text`، `color`، `size` (0.04–0.06)، `rot` (-15..15)، `font` | `stamp` | ختم مطاطي أحمر مزدوج الإطار مع تآكل. أمثلة: سري للغاية، دراسة، مهم، تم كشفه، خبر عاجل. |
| `circle` | `w`،`h`، `color`، `in_dur` (0.4–0.7) | `draw` | دائرة قلم تُرسم تدريجياً حول عنصر. |
| `arrow` | `x0,y0,x1,y1`، `color` | `draw` | سهم مرسوم باليد من نقطة لنقطة. |
| `underline` | `w`، `color` | `draw` | تسطير أحمر تحت كلمة. |
| `tape` | `w`، `h`، `rot` | `fade` | شريط تيب شبه شفاف. |
| `pin` | `size` | `pop` | دبوس أحمر. |
| `censor` | `w`، `h`، `rot` | `pop` | شريط أسود (لتغطية عيون في صورة المستخدم). |
| `callout` | `text`، `tx`,`ty` (نقطة الهدف)، `size`، `bar`، `color` | `draw` | ليبل + خط توجيه يُرسم تدريجياً + نقطة. |
| `counter` | `value`، `prefix`، `suffix`، `decimals`، `size`، `bar` | `draw` | رقم يعدّ من 0 للقيمة خلال `in_dur` (1.6 ث). |
| `check` / `cross` | `size` | `draw` | علامة صح خضراء / خطأ حمراء تُرسم. |
| `bars` | `items: [[label, value]]`، `w`، `h`، `size`، `ink`، `label_w` | `draw` | أعمدة أفقية تنمو بالتسلسل. |
| `timeline` | `items: [labels]`، `w`، `size`، `ink` | `draw` | خط + دبابيس + ليبلات تظهر تباعاً. |
| `bubble` | `text`، `size`، `max_w`، `tail` (`bl`/`br`) | `pop` | فقاعة كلام. |
| `sticky` | `text`، `size` | `pop` | ورقة لاصقة صفراء بخط Changa. |
| `vs` / `badge` | `size` / `text`,`color` | `pop` | شارة VS / شارة دائرية بنص قصير. |
| `bigquote` | `size` | `fade` | علامتا اقتباس ضخمتان شبه شفافتين. |

**العمق `z`** (0 بعيد … 1 قريب، اختياري لكل طبقة): يحدد مقدار حركة الطبقة مع الكاميرا. الافتراضي: قصاصات 0.72، عناوين/أختام 0.9.

## أنواع الدخول `in`
`pop` (كِبَر مع ارتداد) · `slam` (يهبط من كبير لصغير مع اهتزاز — للعناوين) · `stamp` (ضربة ختم) ·
`fade` · `slide_l` / `slide_r` / `slide_up` / `slide_down` · `draw` (للقلم). `in_dur` لتغيير مدة الدخول.

## حقول اللقطة `shot`
`id`، `dur` (3.5–5)، `camera`: `push_in|pull_out|pan_l|pan_r|pan_up|pan_down|static`، `camera_strength` (1.0)،
`plate` (وصف اللوحة، إنجليزي، بدون نص) أو `plate_image` (صورة المستخدم) أو لا شيء (خلفية ورق إجرائية)،
`bg` (لون/نوع الورق الإجرائي: `cream` `white` `graph` `red` `black` `yellow` `blue`)، `parallax` (1.0)، `fx` (`["dust","sweep"]`)،
`transition` (`tear`|`slide`|`flip`|`wipe`|`cut`)، `sfx_hint` (+`sfx_gain` 0.5، `sfx_at` 0.3، `sfx_max` 6)،
`motion`: `code` (افتراضي) | `veo` (مدفوع، مع `veo_motion` و`veo_duration`).

## حقول البيت `beat`
`id`، `narration` (عربي)، `feel` (إنجليزي قصير للمزاج)، `shots[]`، واختيارياً `audio_path` لتسجيل جاهز.

## حقول المشروع (الجذر)
`project`، `topic`، `aspect` (`9:16`|`16:9`|`1:1`|`4:5`)، `fps` (30)، `theme` (`arabic-newsprint`|`modern-editorial`|`dark-investigative`|`blueprint`|`retro-magazine`)،
`provider` (`gemini`|`pollinations`|`hf`|`placeholder`)، `plates` (`procedural`|`ai`)، `parallax`، `fx`،
`tts` {`persona` أو `engine`,`voice`,`speed`,`style`}، `music` {`path`: ملف|`auto`|`jamendo`, `mood`, `gain_db`}،
`captions` {`enabled`,`style`: `highlight|plain`,`bar`,`fill`,`size`,`position`,`max_words`,`font`}،
`sfx` {`pop`,`slam`,`stamp`,`draw`,`fade`: مسارات ملفات صوت}، `sfx_gain`، `watermark`، `grain` (22)، `beat_tail` (0.35).

## مثال لقطة نموذجية (خطّاف)
```json
{
  "id": "a", "dur": 4.5, "camera": "push_in",
  "plate": "a toddler seen from behind facing a glowing tablet in a dim room, torn newspaper scraps, tape corners",
  "layers": [
    {"type": "cutout", "subject": "toddler holding a tablet, side view", "effects": ["bw","torn"], "x": 0.5, "y": 0.55, "w": 0.7, "rot": -3, "at": 0.1},
    {"type": "headline", "text": "خبر عاجل", "bar": "red", "fill": "white", "size": 0.07, "x": 0.5, "y": 0.13, "rot": -2, "at": 0.5},
    {"type": "headline", "text": "سنتين وبعده ما بيحكي؟", "bar": "yellow", "size": 0.052, "x": 0.5, "y": 0.70, "rot": 2, "at": 1.6},
    {"type": "circle", "x": 0.5, "y": 0.5, "w": 0.45, "h": 0.28, "at": 2.3, "in_dur": 0.6}
  ]
}
```
