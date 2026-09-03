# Style Bible — ستايل "الجرايد" (arabic-newsprint)

المرجع البصري: فيديوهات Vox الاستقصائية وتطبيقها العربي في قناة "تريكات". العناصر الثابتة للهوية:

1. **الورق:** خلفية جرائد قديمة مصفرّة (cream/sepia)، أعمدة طباعة صغيرة غير مقروءة، بقع قهوة خفيفة، حبيبات تصوير ضوئي.
2. **الصور:** أرشيفية أبيض وأسود بنقاط هاف تون، مقصوصة بحواف بيضاء (scissor-cut) وظل ورقي ناعم. شريط أسود على العيون للمجهولين.
3. **النص:** عناوين عربية ثقيلة (Cairo Black) على بارات تظليل ممزّقة: أصفر للحقائق، أحمر لـ"خبر عاجل"/الصدمة، أبيض للكابشن، أسود للتأكيد.
4. **الأختام:** حمراء، إطار مزدوج، مائلة، متآكلة: "سري للغاية"، "تم كشفه"، "دراسة"، "مهم".
5. **القلم الأحمر:** دوائر حول الدليل، أسهم من العنوان للصورة، تسطير تحت الرقم.
6. **الإكسسوارات:** تيب شفاف على زوايا الصور، دبابيس حمراء، طيارة ورق، مشبك ورق.
7. **الحركة:** كل شيء يدخل كأنه يُلصق على الطاولة: pop للقصاصات، slam للعناوين، ضربة للأختام، رسم تدريجي للقلم. الكاميرا تدفع ببطء (push-in) على الإطار كله. حدث جديد كل ~ثانية.

## كتابة وصف اللوحة `plate` (إنجليزي)
- ابدأ بالمشهد كقصاصات ورقية مصفوفة، ثم الإكسسوارات، ثم أين تترك فراغاً للنص.
- قل صراحة ما يجب أن يكون أبيض/أسود وما يكون ملوناً.
- لا تصف نصاً أو أرقاماً أبداً (السكربت يضيف `NO TEXT` تلقائياً، لكن لا تناقضه).
- أمثلة جيدة:
  - `"a scattered pile of old newspaper clippings and a stapled research paper with charts, a paper magnifying glass, red push pins, on aged cream newsprint"`
  - `"a big bold flat red paper background with a torn-paper hole revealing a black-and-white photo of a parent and toddler talking, halftone dots, paper airplane doodle"`
  - `"an aged cream newsprint page with a wide torn yellow paper strip across the upper third, a pinned blank paper note, faint coffee stain"`

## كتابة وصف القصاصة `subject`
شيء واحد فقط، من زاوية واضحة، بدون خلفية: `"toddler holding a tablet, side view"`, `"old rotary telephone"`, `"stack of coins"`,
`"doctor in a white coat, waist up, facing camera"`. أضف `effects: ["bw"]` للصور "الأرشيفية" و`["censor_eyes"]` لإخفاء الهوية.

## الثيمات الأخرى (كل ثيم = لوحة ألوان + خط + نوع ورق إجرائي + برومبت لوحات)
- `modern-editorial`: ورق أبيض نظيف، أسود/أحمر/أصفر، Vox المعاصر — علم، صحة، تربية.
- `dark-investigative`: ورق أسود، نص أبيض، أحمر — جريمة، أسرار، ملفات.
- `blueprint`: ورق مخططات أزرق مشبّك، أبيض/أصفر — تقنية و"كيف يعمل".
- `retro-magazine`: مجلات الخمسينات، خردل/تركواز/أحمر، خط Changa — نوستالجيا.
- `clean-flat`: فلات حديث بألوان محدودة — شروحات هادئة.

## الألوان (paperfx.PALETTE)
paper `#ECE2CC` · ink `#181614` · red `#C41E20` · yellow `#F7C92C` · white `#FAF7F0` · black `#0C0C0C`
