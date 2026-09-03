#!/usr/bin/env python3
"""Builds beats.json for 'قصة الذكاء الاصطناعي' — a 3-minute 16:9 Vox-style documentary."""
import json, os

def H(text, x, y, at, bar="yellow", size=0.075, rot=-2, fill=None, max_w=0.5, **k):
    d = {"type": "headline", "text": text, "bar": bar, "size": size, "x": x, "y": y, "rot": rot, "at": at, "max_w": max_w}
    if fill: d["fill"] = fill
    d.update(k); return d

def C(subject, x, y, w, at, effects=("bw",), rot=-3, **k):
    d = {"type": "cutout", "subject": subject, "effects": list(effects), "x": x, "y": y, "w": w, "rot": rot, "at": at}
    d.update(k); return d

def S(text, x, y, at, size=0.06, rot=-12, **k):
    d = {"type": "stamp", "text": text, "x": x, "y": y, "size": size, "rot": rot, "at": at}; d.update(k); return d

def CIRC(x, y, w, h, at, **k):
    d = {"type": "circle", "x": x, "y": y, "w": w, "h": h, "at": at, "in_dur": 0.6}; d.update(k); return d

def ARR(x0, y0, x1, y1, at):
    return {"type": "arrow", "x0": x0, "y0": y0, "x1": x1, "y1": y1, "at": at}

def TAPE(x, y, at, w=0.12, rot=-7):
    return {"type": "tape", "x": x, "y": y, "w": w, "rot": rot, "at": at}

def PIN(x, y, at):
    return {"type": "pin", "x": x, "y": y, "at": at}

def UL(x, y, w, at):
    return {"type": "underline", "x": x, "y": y, "w": w, "at": at}

def shot(i, dur, plate, layers, camera="push_in", **k):
    d = {"id": i, "dur": dur, "camera": camera, "plate": plate, "layers": layers}; d.update(k); return d

NP = "on aged cream newsprint with dense illegible Arabic newspaper columns, halftone dots, tape corners, red push pins"

beats = [
 # ---------------------------------------------------------------- 1 HOOK
 dict(id=1, feel="urgent, investigative, dramatic",
  narration="في سنة 1950، واحد من أذكى الناس بالعالم سأل سؤال بسيط: هل الآلة بتقدر تفكّر؟ بعد 75 سنة، الجواب صار بجيبتك.",
  shots=[
   shot("a", 5.0, f"a cut-out black-and-white archival photo of a huge 1950s room-sized computer with vacuum tubes and reels, a paper question mark, {NP}",
        [C("vintage 1950s room-sized mainframe computer with tape reels, front view", 0.64, 0.5, 0.36, 0.1),
         H("خبر عاجل", 0.22, 0.16, 0.5, bar="red", fill="white", size=0.09),
         H("هل الآلة بتقدر تفكّر؟", 0.24, 0.40, 1.6, size=0.07, max_w=0.42),
         CIRC(0.64, 0.5, 0.3, 0.42, 3.2)], camera="push_in"),
   shot("b", 4.5, f"a cut-out photo of a modern smartphone in a hand glowing, surrounded by torn paper scraps and a big red arrow, {NP}",
        [C("smartphone held in a hand, screen glowing, close-up", 0.3, 0.52, 0.22, 0.1, effects=()),
         H("الجواب صار بجيبتك", 0.66, 0.38, 0.8, bar="red", fill="white", size=0.08, max_w=0.45),
         S("2025", 0.72, 0.62, 1.8, size=0.07, rot=8),
         ARR(0.55, 0.5, 0.4, 0.5, 2.4)], camera="pull_out")]),
 # ---------------------------------------------------------------- 2 TURING
 dict(id=2, feel="historical, mysterious",
  narration="اسمه آلان تورينغ. عالم رياضيات بريطاني فكّ شيفرة النازيين بالحرب. وبورقة من 1950 اقترح اختبار: إذا حكيت مع آلة وما عرفت إنها آلة، فهي بتفكّر.",
  shots=[
   shot("a", 5.5, f"a pinned black-and-white archival portrait card of a 1940s British mathematician in a suit, an old typewritten letter, a paper file folder marked with a red seal, {NP}",
        [C("1940s British mathematician in a tweed suit, portrait, chest up", 0.3, 0.5, 0.24, 0.1, effects=("bw", "old")),
         PIN(0.3, 0.2, 0.4),
         H("آلان تورينغ", 0.66, 0.3, 0.6, size=0.085),
         H("فكّ شيفرة النازيين", 0.66, 0.5, 2.2, bar="white", size=0.06, max_w=0.4),
         S("ملف سري", 0.7, 0.68, 3.4, size=0.06, rot=-10)], camera="push_in"),
   shot("b", 6.0, f"a torn typewritten scientific paper cut-out beside a paper speech bubble and a cut-out old telephone, {NP}",
        [C("typewritten 1950 scientific paper with a title block, slightly yellowed", 0.32, 0.5, 0.26, 0.1, effects=("old",), rot=3),
         S("1950", 0.42, 0.24, 0.6, size=0.06, rot=12),
         H("اختبار تورينغ", 0.68, 0.3, 1.0, bar="red", fill="white", size=0.08),
         H("إذا ما عرفت إنها آلة… فهي بتفكّر", 0.68, 0.55, 2.8, bar="yellow", size=0.055, max_w=0.42),
         UL(0.68, 0.62, 0.25, 4.6)], camera="pan_r")]),
 # ---------------------------------------------------------------- 3 DARTMOUTH 1956
 dict(id=3, feel="optimistic, 1950s energy",
  narration="سنة 1956، بجامعة دارتموث، اجتمع كم عالم بصيفية واحدة وقرروا يعطوا الحلم اسم: الذكاء الاصطناعي. وقالوا رح نحلّه بكم شهر.",
  shots=[
   shot("a", 5.5, f"a group black-and-white 1950s photo of scientists standing in front of a college building, cut out and taped, a paper calendar page, {NP}",
        [C("group of 1950s scientists in suits standing in front of a college building, wide shot", 0.6, 0.52, 0.42, 0.1, effects=("bw",), rot=-2),
         TAPE(0.45, 0.28, 0.4), TAPE(0.78, 0.3, 0.5, rot=9),
         H("1956 — دارتموث", 0.2, 0.2, 0.7, size=0.07),
         H("الذكاء الاصطناعي", 0.2, 0.5, 2.3, bar="red", fill="white", size=0.08, max_w=0.3)], camera="push_in"),
   shot("b", 4.5, f"a paper cut-out of a 1950s calendar page with a red pen, a coffee stain, a paper sun and a paper clock, {NP}",
        [C("vintage paper wall calendar showing summer months, front view", 0.34, 0.5, 0.24, 0.1, effects=("old",)),
         H("«رح نحلّه بكم شهر»", 0.68, 0.4, 0.6, bar="white", size=0.065, max_w=0.42),
         S("تفاؤل زايد", 0.7, 0.62, 2.0, size=0.06, rot=-8),
         CIRC(0.34, 0.5, 0.2, 0.4, 2.8)], camera="static")]),
 # ---------------------------------------------------------------- 4 ELIZA + first winter
 dict(id=4, feel="ironic, then cold and gloomy",
  narration="بالستينات ظهر أول شات بوت اسمه إليزا. الناس صدّقوا إنه بيفهمهم، وهو بس بيعيد كلامهم كأسئلة. وبعدها الوعود ما تحققت، فالتمويل انقطع. سمّوها: شتاء الذكاء الاصطناعي.",
  shots=[
   shot("a", 5.0, f"a cut-out 1960s teletype terminal printing a paper strip, a paper speech bubble, {NP}",
        [C("1960s teletype computer terminal with paper printout, three-quarter view", 0.62, 0.52, 0.34, 0.1, effects=("bw",)),
         H("إليزا — أول شات بوت", 0.24, 0.22, 0.6, size=0.07, max_w=0.4),
         H("بس بتعيد كلامك كسؤال", 0.24, 0.5, 2.3, bar="white", size=0.055, max_w=0.36),
         S("وهم", 0.7, 0.24, 3.6, size=0.07, rot=10)], camera="push_in"),
   shot("b", 5.5, f"a big torn dark grey-blue paper background with snowflake paper cut-outs, a cut-out empty wallet and a closed door, {NP}",
        [C("closed office door with a paper sign, front view", 0.3, 0.52, 0.2, 0.1, effects=("bw",)),
         H("شتاء الذكاء الاصطناعي", 0.66, 0.35, 0.6, bar="black", fill="white", size=0.08, max_w=0.45),
         H("التمويل انقطع", 0.66, 0.58, 2.2, bar="red", fill="white", size=0.06),
         S("1974", 0.28, 0.24, 3.4, size=0.06, rot=-12)], camera="pull_out", bg="cold slate grey-blue paper")]),
 # ---------------------------------------------------------------- 4b EXPERT SYSTEMS / 2nd winter
 dict(id=41, feel="corporate 1980s, then collapse",
  narration="بالثمانينات رجع الأمل بشكل تاني: الأنظمة الخبيرة. برامج فيها آلاف القواعد كتبها بشر بإيدهم: إذا صار هيك، اعمل هيك. الشركات صرفت مليارات. بس القواعد ما بتغطي الحياة الحقيقية، وانهار كل شي مرة تانية سنة 1987.",
  shots=[
   shot("a", 6.0, f"a cut-out photo of a 1980s office with beige computers and a man in a suit, a paper flowchart with many boxes, {NP}",
        [C("1980s beige desktop computer with a bulky monitor on an office desk, front view", 0.62, 0.52, 0.34, 0.1, effects=("bw",)),
         H("الثمانينات — الأنظمة الخبيرة", 0.22, 0.2, 0.6, size=0.06, max_w=0.36),
         H("إذا صار هيك… اعمل هيك", 0.22, 0.5, 2.6, bar="white", size=0.05, max_w=0.34),
         S("آلاف القواعد", 0.72, 0.22, 4.0, size=0.055, rot=10)], camera="push_in"),
   shot("b", 6.0, f"a torn stock-market chart cut-out falling sharply, a paper snowflake, a crumpled dollar bill cut-out, {NP}",
        [C("line chart on paper falling sharply downward, front view", 0.34, 0.5, 0.28, 0.1, effects=("old",), rot=-2),
         H("مليارات", 0.7, 0.3, 0.6, bar="red", fill="white", size=0.085),
         H("الشتاء التاني", 0.7, 0.55, 2.4, bar="black", fill="white", size=0.075),
         S("1987", 0.36, 0.24, 3.6, size=0.06, rot=-12),
         ARR(0.55, 0.62, 0.42, 0.66, 4.6)], camera="pull_out", bg="cold slate grey-blue paper")]),
 # ---------------------------------------------------------------- 5 DEEP BLUE 1997
 dict(id=5, feel="tense, sports-drama",
  narration="سنة 1997 صار شي هزّ العالم. كمبيوتر من IBM اسمه ديب بلو غلب بطل العالم بالشطرنج غاري كاسباروف. لأول مرة، آلة بتغلب أفضل عقل بشري بلعبته.",
  shots=[
   shot("a", 5.0, f"a black-and-white press photo of a chess grandmaster at a chessboard looking worried, a cut-out chess king piece, newspaper headline strips, {NP}",
        [C("chess grandmaster sitting at a chessboard with his head in his hand, side view", 0.34, 0.52, 0.3, 0.1, effects=("bw",)),
         H("1997", 0.7, 0.2, 0.5, bar="red", fill="white", size=0.09),
         H("ديب بلو ضد كاسباروف", 0.7, 0.45, 1.5, size=0.065, max_w=0.4),
         CIRC(0.34, 0.5, 0.26, 0.5, 3.4)], camera="push_in"),
   shot("b", 5.0, f"a cut-out photo of a tall black computer server cabinet next to a chess king lying on its side, confetti paper bits, {NP}",
        [C("tall black 1990s supercomputer cabinet, front view", 0.3, 0.5, 0.16, 0.1, effects=("bw",)),
         C("chess king piece lying on its side", 0.55, 0.62, 0.12, 0.8, effects=("bw",), rot=12),
         H("الآلة غلبت أفضل عقل بشري", 0.72, 0.35, 1.4, bar="yellow", size=0.06, max_w=0.36),
         S("كش ملك", 0.72, 0.62, 2.8, size=0.07, rot=-10)], camera="pan_l")]),
 # ---------------------------------------------------------------- 5b WATSON 2011
 dict(id=51, feel="TV-show excitement",
  narration="وسنة 2011 كمبيوتر تاني من IBM اسمه واتسون شارك ببرنامج مسابقات على التلفزيون، وغلب أقوى متسابقين بالتاريخ. المرة هاي مش أرقام وشطرنج، هاي لغة بشر، بنكات وألغاز.",
  shots=[
   shot("a", 5.5, f"a black-and-white photo cut-out of a TV quiz-show stage with two contestants at podiums and a big screen between them, paper spotlights, {NP}",
        [C("television quiz show stage with two contestants standing at podiums, wide shot", 0.6, 0.52, 0.42, 0.1, effects=("bw",), rot=0),
         H("2011 — واتسون", 0.22, 0.2, 0.6, size=0.07, max_w=0.34),
         H("على التلفزيون", 0.22, 0.5, 2.0, bar="white", size=0.055),
         CIRC(0.6, 0.45, 0.14, 0.3, 3.4)], camera="push_in"),
   shot("b", 5.0, f"a paper speech bubble cut-out with squiggly lines, a cut-out old TV set, a paper question mark and torn dictionary pages, {NP}",
        [C("vintage television set with antenna, front view", 0.32, 0.52, 0.22, 0.1, effects=("bw",)),
         H("مش أرقام… لغة بشر", 0.7, 0.35, 0.8, bar="yellow", size=0.065, max_w=0.42),
         H("نكات وألغاز", 0.7, 0.58, 2.4, bar="red", fill="white", size=0.065),
         S("فاز", 0.34, 0.24, 3.4, size=0.07, rot=12)], camera="static")]),
 # ---------------------------------------------------------------- 6 DATA + 2012
 dict(id=6, feel="building momentum, technical",
  narration="بس التحوّل الحقيقي ما كان بالشطرنج. كان بشيئين: إنترنت مليان صور وبيانات، وكروت رسومات الألعاب. سنة 2012 شبكة عصبية اسمها أليكس نت تعلّمت تشوف، وغلبت كل المنافسين بفرق كبير.",
  shots=[
   shot("a", 5.5, f"a collage of hundreds of tiny cut-out photographs scattered like a pile, a paper magnifying glass, a cut-out graphics card, {NP}",
        [C("pile of scattered small printed photographs, top view", 0.6, 0.5, 0.42, 0.1, effects=("bw",), rot=0),
         H("ملايين الصور", 0.22, 0.2, 0.6, size=0.07),
         C("computer graphics card with fans, front view", 0.22, 0.6, 0.2, 1.8, effects=(), rot=-6),
         H("+ كروت الألعاب", 0.22, 0.82, 2.6, bar="white", size=0.05, max_w=0.3)], camera="push_in"),
   shot("b", 5.0, f"a stapled research paper cut-out with a simple bar chart showing one very tall bar, a cut-out paper eye, {NP}",
        [C("stapled research paper with a bar chart where one bar is much taller", 0.32, 0.5, 0.26, 0.1, effects=("old",), rot=3),
         S("2012", 0.42, 0.22, 0.6, size=0.06, rot=12),
         H("الآلة تعلّمت تشوف", 0.7, 0.35, 1.2, bar="red", fill="white", size=0.075, max_w=0.42),
         H("أليكس نت", 0.7, 0.58, 2.6, size=0.06),
         ARR(0.6, 0.6, 0.45, 0.45, 3.4)], camera="static")]),
 # ---------------------------------------------------------------- 7 ALPHAGO 2016
 dict(id=7, feel="awe, cinematic",
  narration="سنة 2016 وصلنا للعبة كانوا يقولوا مستحيلة على الآلة: غو. احتمالاتها أكتر من ذرات الكون. ألفا غو غلب البطل لي سيدول أربعة لواحد. وبنقلة واحدة، النقلة 37، عملت حركة ما خطرت على بال أي إنسان.",
  shots=[
   shot("a", 5.5, f"a black-and-white press photo of a Go board with black and white stones, a cut-out hand placing a stone, {NP}",
        [C("Go board with black and white stones, overhead view", 0.62, 0.52, 0.34, 0.1, effects=("bw",), rot=-2),
         H("2016 — لعبة غو", 0.22, 0.2, 0.6, size=0.075),
         H("احتمالات أكتر من ذرات الكون", 0.22, 0.5, 2.2, bar="white", size=0.05, max_w=0.34),
         S("مستحيل؟", 0.7, 0.22, 3.6, size=0.065, rot=10)], camera="push_in"),
   shot("b", 5.5, f"a paper collage of a scoreboard-like torn strip, a black-and-white photo of a Go player looking stunned, a single paper stone with a red circle, {NP}",
        [C("professional Go player looking stunned with his hand over his mouth, chest up", 0.3, 0.52, 0.24, 0.1, effects=("bw",)),
         H("4 – 1", 0.68, 0.25, 0.6, bar="red", fill="white", size=0.1),
         H("النقلة 37", 0.68, 0.5, 2.4, size=0.075),
         CIRC(0.68, 0.5, 0.2, 0.22, 3.4),
         H("ما خطرت على بال إنسان", 0.68, 0.7, 4.0, bar="white", size=0.05, max_w=0.4)], camera="pull_out")]),
 # ---------------------------------------------------------------- 8 TRANSFORMERS 2017
 dict(id=8, feel="revealing the secret ingredient",
  narration="وسنة 2017 نشر فريق من غوغل ورقة بعنوان غريب: الانتباه هو كل اللي بتحتاجه. اسمها ترانسفورمر. هي الوصفة اللي كل الشات بوتات اليوم مبنية عليها.",
  shots=[
   shot("a", 5.0, f"a cut-out research paper with a diagram of stacked boxes and arrows, a red paper seal, torn edges, {NP}",
        [C("scientific paper with a diagram of stacked blocks connected by arrows, front view", 0.34, 0.5, 0.26, 0.1, effects=("old",), rot=-3),
         S("2017", 0.44, 0.22, 0.5, size=0.06, rot=12),
         H("«الانتباه هو كل اللي بتحتاجه»", 0.7, 0.35, 1.0, bar="yellow", size=0.055, max_w=0.42),
         H("ترانسفورمر", 0.7, 0.6, 2.8, bar="red", fill="white", size=0.08)], camera="push_in"),
   shot("b", 4.5, f"a paper recipe card cut-out, small paper icons of chat bubbles pinned around it with red strings, {NP}",
        [C("vintage handwritten recipe card, front view", 0.34, 0.5, 0.24, 0.1, effects=("old",)),
         PIN(0.34, 0.24, 0.4),
         H("الوصفة السرية", 0.7, 0.35, 0.8, size=0.075),
         H("كل الشات بوتات مبنية عليها", 0.7, 0.58, 2.2, bar="white", size=0.05, max_w=0.4),
         ARR(0.55, 0.5, 0.44, 0.5, 3.0)], camera="static")]),
 # ---------------------------------------------------------------- 9 CHATGPT 2022
 dict(id=9, feel="explosive, breaking-news",
  narration="ثلاثين نوفمبر 2022. شركة صغيرة اسمها أوبن إيه آي نزّلت موقع بسيط: شات جي بي تي. بخمسة أيام مليون مستخدم. بشهرين، مئة مليون. أسرع تطبيق بتاريخ البشرية.",
  shots=[
   shot("a", 5.0, f"a cut-out laptop screen showing a plain chat window, exploding paper confetti and torn newspaper headline strips, {NP}",
        [C("open laptop with a plain white chat interface on screen, front view", 0.6, 0.52, 0.4, 0.1, effects=()),
         H("خبر عاجل", 0.2, 0.16, 0.4, bar="red", fill="white", size=0.09),
         H("30 نوفمبر 2022", 0.2, 0.42, 1.2, size=0.065, max_w=0.32),
         H("شات جي بي تي", 0.2, 0.62, 2.4, bar="black", fill="white", size=0.07)], camera="push_in"),
   shot("b", 5.5, f"a huge paper counter made of torn number cards, a crowd photo cut-out of many people holding phones, a red rocket doodle, {NP}",
        [C("large crowd of people all looking at their phones, wide shot", 0.6, 0.55, 0.44, 0.1, effects=("bw",), rot=0),
         H("5 أيام = مليون", 0.22, 0.22, 0.5, size=0.065, max_w=0.34),
         H("شهرين = 100 مليون", 0.22, 0.45, 1.8, bar="red", fill="white", size=0.065, max_w=0.34),
         S("رقم قياسي", 0.75, 0.24, 3.2, size=0.065, rot=-10),
         UL(0.22, 0.52, 0.22, 3.8)], camera="pull_out")]),
 # ---------------------------------------------------------------- 9b IMAGES 2022
 dict(id=91, feel="colorful, creative, surprising",
  narration="وبنفس السنة الآلة صارت ترسم. بتكتب جملة، بتطلعلك لوحة. فنانين خافوا، ومصورين احتجّوا، ومسابقة فنية بولاية كولورادو فازت فيها صورة مرسومة بالذكاء الاصطناعي. والناس ما عرفت غير بعدين.",
  shots=[
   shot("a", 5.5, f"a cut-out ornate gold picture frame containing an abstract painting, paper paint splashes in bold colors, a cut-out typewriter, {NP}",
        [C("ornate golden picture frame with an abstract painting inside, front view", 0.6, 0.5, 0.34, 0.1, effects=(), rot=-2),
         H("الآلة صارت ترسم", 0.22, 0.22, 0.6, size=0.07, max_w=0.34),
         H("جملة → لوحة", 0.22, 0.5, 2.0, bar="white", size=0.06),
         S("2022", 0.74, 0.22, 3.2, size=0.06, rot=10)], camera="push_in"),
   shot("b", 5.5, f"a black-and-white photo cut-out of an art-fair ribbon and a trophy, a crowd of protesters with paper signs cut out, a red rosette, {NP}",
        [C("first-place blue ribbon rosette award, front view", 0.3, 0.5, 0.16, 0.1, effects=(), rot=-5),
         H("فازت بمسابقة فنية", 0.68, 0.32, 0.8, bar="red", fill="white", size=0.07, max_w=0.4),
         H("والناس ما عرفت غير بعدين", 0.68, 0.56, 2.6, bar="white", size=0.05, max_w=0.4),
         S("احتجاج", 0.3, 0.24, 3.8, size=0.06, rot=-12)], camera="pan_l")]),
 # ---------------------------------------------------------------- 10 WHAT IT REALLY IS
 dict(id=10, feel="calm explainer, honest",
  narration="بس خلينا نكون صريحين: الآلة ما بتفهم زيّنا. هي بتتوقع الكلمة الجاية بناءً على تريليونات الكلمات اللي قرأتها. وأحياناً بتتوقع غلط بثقة كاملة. سمّوها: هلوسة.",
  shots=[
   shot("a", 5.5, f"a paper collage of a torn dictionary page, cut-out word cards lined up with one blank card at the end and a red question mark, {NP}",
        [C("row of paper word cards with one blank card at the end, front view", 0.6, 0.5, 0.44, 0.1, effects=("old",), rot=0),
         H("كيف بتشتغل فعلاً؟", 0.22, 0.2, 0.5, size=0.07, max_w=0.34),
         H("بتتوقع الكلمة الجاية", 0.22, 0.5, 2.0, bar="white", size=0.055, max_w=0.32),
         CIRC(0.78, 0.5, 0.1, 0.24, 3.4)], camera="push_in"),
   shot("b", 5.0, f"a black-and-white photo cut-out of a confident man in a suit pointing, a torn paper sign, a red warning stamp, {NP}",
        [C("confident man in a suit pointing at the camera, chest up", 0.3, 0.52, 0.22, 0.1, effects=("bw", "censor_eyes")),
         H("غلط… بثقة كاملة", 0.68, 0.35, 0.8, bar="red", fill="white", size=0.075, max_w=0.42),
         S("هلوسة", 0.7, 0.6, 2.6, size=0.08, rot=-12),
         ARR(0.55, 0.62, 0.42, 0.5, 3.4)], camera="static")]),
 # ---------------------------------------------------------------- 11 TODAY
 dict(id=11, feel="present-day, fast montage",
  narration="واليوم؟ الذكاء الاصطناعي بيكتب، بيرسم، بيشخّص أمراض، بيقود سيارات، وبيتعلّم يشتغل لحاله كوكيل. ومع كل هاد، الأسئلة الكبيرة رجعت: مين بيتحكّم فيه؟ وشو بيصير بالشغل؟",
  shots=[
   shot("a", 5.5, f"a busy collage of cut-out photos: a robot arm, a stethoscope, a paintbrush, a car, a pen, arranged around a central paper brain cut-out, {NP}",
        [C("paper cut-out illustration of a human brain with circuit lines", 0.5, 0.5, 0.22, 0.1, effects=(), rot=0),
         H("بيكتب", 0.22, 0.25, 0.6, size=0.06), H("بيرسم", 0.78, 0.25, 1.1, size=0.06, rot=3),
         H("بيشخّص", 0.2, 0.62, 1.6, size=0.06, bar="white"), H("بيقود", 0.8, 0.62, 2.1, size=0.06, bar="white", rot=-3),
         S("وكيل", 0.5, 0.78, 3.0, size=0.06, rot=8)], camera="push_in"),
   shot("b", 5.5, f"a black-and-white photo cut-out of a boardroom of men in suits seen from behind, a red string web connecting paper cards, a big red question mark, {NP}",
        [C("boardroom of executives seen from behind facing a large window, wide shot", 0.6, 0.52, 0.42, 0.1, effects=("bw",), rot=0),
         H("مين بيتحكّم فيه؟", 0.22, 0.28, 0.6, bar="red", fill="white", size=0.07, max_w=0.34),
         H("وشو بيصير بالشغل؟", 0.22, 0.55, 2.4, size=0.06, max_w=0.34),
         S("سري للغاية", 0.76, 0.24, 3.6, size=0.06, rot=-12)], camera="pan_r")]),
 # ---------------------------------------------------------------- 12 CLOSE / CTA
 dict(id=12, feel="reflective, then call to action",
  narration="من سؤال تورينغ سنة 1950 لتطبيق بجيبة كل واحد فينا: 75 سنة من الأحلام والشتاء والانفجار. والقصة لسا ما خلصت. لو حابب تعرف كيف بتأثر هالأدوات على أطفالنا، تابع القناة.",
  shots=[
   shot("a", 6.0, f"a long paper timeline strip with pinned small black-and-white photos and paper flags along a red string, {NP}",
        [C("horizontal paper timeline with small pinned photographs and paper flags on a red string", 0.5, 0.5, 0.8, 0.1, effects=("old",), rot=0),
         H("1950", 0.15, 0.22, 0.5, size=0.06, bar="white"), H("1997", 0.4, 0.22, 1.3, size=0.06, bar="white"),
         H("2016", 0.62, 0.22, 2.0, size=0.06, bar="white"), H("2022", 0.85, 0.22, 2.7, size=0.06, bar="red", fill="white"),
         H("75 سنة", 0.5, 0.75, 3.6, size=0.08)], camera="pan_r"),
   shot("b", 5.5, f"a clean aged newsprint page with a wide torn red paper strip across the middle, a pinned blank note, a paper airplane doodle, {NP}",
        [H("القصة لسا ما خلصت", 0.5, 0.3, 0.3, size=0.08, bar="black", fill="white", max_w=0.5),
         H("تابع القناة", 0.5, 0.55, 1.6, bar="red", fill="white", size=0.1),
         CIRC(0.5, 0.55, 0.3, 0.3, 2.6),
         PIN(0.28, 0.4, 3.2)], camera="static")]),
]

doc = {
  "project": "ai-history",
  "topic": "قصة الذكاء الاصطناعي — فيلم وثائقي 3 دقائق",
  "language": "ar", "aspect": "16:9", "fps": 30, "theme": "arabic-newsprint",
  "provider": "placeholder", "plates": "procedural",
  "tts": {"engine": "placeholder", "persona": "documentary_male"},
  "music": {"path": "auto", "mood": "investigative", "gain_db": -18},
  "parallax": 1.0, "fx": ["dust", "sweep"],
  "captions": {"enabled": True, "style": "highlight", "bar": "white", "fill": "black", "size": 0.05, "position": 0.86, "max_words": 5},
  "watermark": "",
  "beats": beats,
}
for b in beats:
    for sh in b["shots"]:
        sh["dur"] = round(sh["dur"] * 1.13, 2)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "beats.json")
json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
words = sum(len(b["narration"].split()) for b in beats)
shots = sum(len(b["shots"]) for b in beats)
dur = sum(s["dur"] for b in beats for s in b["shots"])
print(f"{len(beats)} beats, {shots} shots, {words} words (~{words/2.7:.0f}s narration), planned {dur:.0f}s → {out}")
