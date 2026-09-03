# vox-ar — Agent Guide

This folder is an **agent skill**. Read `SKILL.md` first (Arabic) — it defines the workflow and the two
approval gates. Then `references/beat-writing.md`, `references/layers.md`, `references/style-bible.md`
before writing any `beats.json`. Work one project at a time under `out/<project>/`.

Stages (scripts/): keyframes.py → preview_frame.py → audio.py → [veo_clips.py] → animate.py → assemble.py

Hard rules: never put text inside generated images; run audio before animate; never run veo_clips.py
without telling the user it is paid and getting a yes; keep the 0.76–0.90 vertical band free for captions.
