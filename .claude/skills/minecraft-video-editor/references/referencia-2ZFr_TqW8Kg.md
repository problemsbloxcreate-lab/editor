# Reference edit analysis: "Enchi o MUNDO do MEU AMIGO de ÁGUA!" (ProbIems)

- Source: https://youtu.be/2ZFr_TqW8Kg (channel "ProbIems", uploaded 2026-09-30, ~720k views at download time)
- Analysis only. Nothing in Premiere was touched.
- Working files are all in `C:\Users\mathe\Skills\_research\mc-edit-ref\`:
  - `watch/download/video.mp4`: the video
  - `transcript.txt` / `transcript.json`: Whisper (Groq), 849 segments
  - `cuts_merged.txt`: 526 cut timestamps
  - `rms100ms.json`, `eburM.json`: loudness every 100 ms
  - `stem_vocals.wav` / `stem_music_sfx.wav`: demucs voice/music split
  - `stems_rms.npz`, `sfx_events.json`, `music_dropouts.json`, `music_changes.json`
  - `visual_events.json`: automatic blur, tint and flash detection at 10 fps
  - `sheets/`: 5 fps contact sheets for 0–3:00 (`w0_*`) and 4 fps sheets for the windows `w1`=5:00–5:48, `w2`=10:58–11:46, `w3`=15:55–16:37, `w4`=21:02–22:02
  - `ev/`: 10 fps strips around every detected event
  - `preset_names.txt`: the 192 BERSERKER preset names
- Confidence key: **[seen]** = verified frame by frame. **[measured]** = from ffmpeg or librosa numbers. **[hyp]** = a guess, mostly about audio, because the audio cannot be heard.

---

## 1. Overview

| Item | Value |
|---|---|
| Duration | 22:45 (1365 s) |
| Format | 1280×720, 60 fps, 16:9. Two players: Paulo ("Pró"), who narrates, and Cadu ("Kadukos"). A third player (PatoCarioca) appears in the late game. Brazilian Portuguese. |
| Camera material | About 60% third-person follow cam (replay/freecam behind or in front of the player, smooth), about 40% POV. Edit = alternating between these angles. |
| Cuts (scene detect gt(scene,0.25), merged at <0.15 s) | **526** [measured] |
| Median shot length | **1.93 s**; mean 2.59 s [measured] |
| Cuts per minute by minute | 41, 26, 27, 20, 28, 19, 19, 20, 19, 21, 23, 24, 20, 17, 20, 26, 14, 24, 22, 17, 20, **52**, 7 |
| Pacing by segment | 0–10 s hook: **54 cuts/min**. 10–60 s: 38/min. 1–3 min: 26/min. Body 3–21 min: **~21/min, flat**. Final minute (tsunami/meteor climax): 52/min. Outro: 7/min. |
| Integrated loudness | −22.6 LUFS [measured]. Per-minute median momentary loudness is flat (−22.3 to −23.0 LU). Music sits about **14 dB under the voice**: music+SFX stem median −40 dBFS RMS vs voice −26 dBFS. |
| Visible edit effects (verified) | About **4–5 per minute in the first 3 min**, about **2–4 per minute in the body**. The automatic detector flagged 143 candidate events (~6/min), but many are just cuts to blue water. |
| Captions / subtitles | **None.** |
| On-screen text added in the edit | Only in the first 6 s: the book promo card and the "Classificação indicativa L" badge. Every other text on screen is in-game: the mod HUD with the "INUNDAÇÃO x/1M" bar, the globe icon, "Nível do Mar", the "SORTE!" lucky-block text and the shop's "COMPRADO" signs. |

**Structure**

| Time | Section |
|---|---|
| 0:00–0:02.3 | Self-promo card for the book (the presenter's own) |
| 0:02.4–0:10.0 | Teaser hook: a montage of future footage, graded differently |
| 0:10 → | Story starts linearly: shipwreck → craft buckets → shop ("Loja de Água", an underwater dome) |
| Body | Loop: test item → inflate the % counter → return to shop → buy the next, stronger item (bucket, infinite bucket, water pistol, hair dryer, lucky block, trident, fire truck, giant faucet, tsunami summoner, water meteor) |
| End | Finale at 21:00+, outro "missão dada, missão cumprida… tchau" at 22:33 |

**Density shape**

- The hook is twice as dense as the body.
- From about 1:00 the body settles into a steady ~20 cuts/min.
- Density rises again only at the climax.
- Effects cluster around three moments: shop visits (teleport flash, purchase flash), number reveals (HUD zoom) and reactions (punch-in, color flash).

---

## 2. Timestamped event log

### 2.1 First ~3:10 (dense: 5 fps sheets + 10 fps strips)

| Time | Trigger (speech / action) | Effect (estimated parameters) | Probable SFX |
|---|---|---|---|
| 0:00.0–0:00.4 | VO "O livro do Paulo chegou" | Promo card: book cover left, title "MEU / NOVO / LIVRO" (white / magenta / cyan, heavy sans with neon glow) over a neon city. The title **fades and unblurs in about 0.3 s** (blur in). [seen] | Whoosh + music hit at 0.9 s (transient +10.6 dB) [hyp] |
| 0:00.8 | — | "LINK NA DESCRIÇÃO" pops in under the title. It has a light blur, then settles by 1.0 s. A "LANÇAMENTO" tag appears above the title at 1.0 s. [seen] | Pop [hyp] |
| 0:01.3–0:02.2 | — | Music drops out for 0.9 s right before the hook [measured] | — |
| 0:02.4–0:02.6 | Hook starts: "No vídeo de hoje, eu e o Cadu vamos inundar o mundo…" | **White overexposed blur flash** as a transition, about 0.25 s (Y jumps +104 above baseline, edges drop to 19%). [seen] | Whoosh / riser hit [hyp] |
| 0:02.6–0:06.2 | Premise sentence | **Teaser grade**: saturation about 45% of normal (SAT 13 vs 27–31 in the body), lifted blacks, soft bloom or glow. Badge top-left: **"indicativa" + green "L" box** (Brazilian age rating "Livre"). It is cut off at 6.2 s by sliding left. [seen] | Music on |
| 0:02.6–0:10.0 | Teaser montage of LATER footage: snow river, shop, giant faucet, flooded forest, snowy treetops | Hard cuts every **0.6–1.7 s** (9 cuts in 10 s). No zooms. All of it is future footage = a "takes futuros" teaser. [seen] | — |
| 0:10.0 | "Você tá maluco? Como é que a gente vai inundar…" | **Blur transition** (edges drop to 42%, about 0.1–0.2 s) into normal grade. The story starts at the beach. [seen] | Music drops out for 0.8 s at 10.6 s and 2.2 s at 11.5 s; there are stings at 13.7 / 15.2 / 17.3 s [measured] |
| 0:10–0:18 | Back-and-forth dialogue | Plain third-person follow shots of each speaker. A cut happens when the speaker changes (10.2 → 12.9 → 16.1 s). [seen] | — |
| 0:18.9–0:19.6 | "Mas a primeira coisa que a gente tem que fazer é conseguir um balde d'água" | **Zoom punch-in with motion blur and white bloom.** It runs in about 0.15 s to about **180–200%** on Paulo's character, then **holds** about 0.6 s and cuts away. There is no zoom back out. [seen] | Whoosh (+12 dB transient at 18.9 s) [hyp] |
| 0:19.7 | POV, the shipwreck | Hard cut [seen] | — |
| 0:24.6–0:27.8 | Searching for the chest | Pure POV mining footage, 3 cuts [seen] | — |
| 0:28.2 (0.1 s) | Right after "Balde não, **seu burro**" | **Single-frame insert (about 0.1 s)**: a close-up of Paulo holding a sand block, then a cut back to the wide shot. Comedic stab. [seen] | Punch / boing (+11.8 dB at 28.0 s) [hyp] |
| 0:32.8–0:35.8 | Opening the first chest, "Só lixo" | Chest GUI held on screen. No effect. Comedy comes from the line itself. [seen] | — |
| 0:39.9 | "Calma aí, Pró" | 0.1 s blur on a jump cut (whip-ish) [seen] | — |
| 0:42–0:44 | "E tá cheio da bufunfa" | Chest GUI full of iron and gold. Hard cuts only. [seen] | — |
| 0:54.8–0:56.7 | "É, pera aí. Vem um balde de água diferente aqui" | **Music drops out for 1.9 s** (suspense beat) [measured] | Silence / record-stop [hyp] |
| 0:59.6–1:00.3 | Teleport into the shop | Hard cut to the shop dome. 1:00.2 is red in-game cover, not an effect. [seen] | — |
| 1:00–1:28 | Shop tour, "50 blocos", bucket | Cuts between POV and third person every 1–3 s. No effects. [seen] | — |
| 1:27.6–1:31.2 | "Nossa, mas só isso aqui não aumentou nem 1%" | **HUD zoom.** The whole frame scales to about **200%** anchored top-left, so the "INUNDAÇÃO: 1/1M (0%)" bar fills the top of the frame. **Held about 3.5 s**, ended by a cut. No easing in: it is a hard scale on the cut. [seen] | Music drops out 1:29.7 (1.6 s) and 1:32.9 (1.2 s) = **joke / disappointment silence** [measured] |
| 1:41.7–1:42.0 | "9, 10, 11, 12" (counting) | **Zoom-out blur transition + white bloom**, about 0.3 s [seen] | Whoosh [hyp] |
| 1:57.9–1:59.1 | "Nossa, Cadu, não tá funcionando / Que porcaria é essa? / vai ser impossível" | **Red flash**: an instant full red or pink overlay with blur on the first 0.1 s, then a **linear fade over about 1.1 s**. The picture stays visible underneath. [seen] | Fail sound, transient at 1:58.5 [hyp: "fail" horn / sad trombone / bruh] |
| 2:06.8–2:07.2 | "E os itens na loja vão ajudar a gente a inundar o mundo inteiro" | **Green flash**: full green with blur, decays over about 0.4 s [seen] | Positive "ding" / whoosh [hyp] |
| 2:16.4 | "E foi" (50 blocks reached) | Hard cut (+9.8 dB transient) [measured] | Success ding / XP orb [hyp] |
| 2:19.0–2:19.3 | "Vamos lá pra loja" → shop | **Magenta/pink flash with blur**, about 0.3 s, as the teleport transition into the shop [seen] | Teleport whoosh [hyp] |
| 2:21.7–2:22.6 | "E agora a gente pode comprar o balde infinito" (purchase) | **Green flash plus an overlay of falling dollar bills** (money-rain PNG or green-screen clip, about 30 bills tumbling). Green fades in 0.3 s, bills keep falling about 0.9 s. In-game red "COMPRADO" sign right after. [seen] | Cash register "cha-ching" [hyp, very likely] |
| 2:25.7 | Leaving the shop | 0.1 s white or sky blink (teleport) [seen] | — |
| 2:50.6–2:50.8 | "Porque assim ela cai infinito. **Gênio**." | **White blur flash**, about 0.2 s, on the cut [seen] | Ding / "genius" sting (+9.6 dB at 2:50.7) [hyp] |
| 2:56.2 | Jump to another angle | Dark motion-blur whip, 0.1 s [seen] | Whoosh [hyp] |
| 3:03.7–3:03.9 | "A gente não vai conseguir inundar o mundo inteiro" / "Não, não, não…" | **Face punch-in** to about **250–300%** on Paulo's head (with bucket), held 0.2 s. Then a punch-in on Kadukos's head at 3:03.9, then a two-shot medium at about 150%. A rapid reaction ping-pong. [seen] | — |
| 3:08.9–3:09.7 | "E no final vai ser um **dilúvio**" | **Red/orange overlay (fire-like)**, about 0.8 s, with an edge flash on the first frame [seen] | **Biggest audio event of the video**: +39 dB over the music bed for 2.5 s = epic boom / thunder / choir hit [hyp] |
| 3:12.2 | "Bom, vai" | Music drops out 2.1 s [measured] | — |

### 2.2 Window 1: 5:00–5:48

| Time | Trigger | Effect | SFX |
|---|---|---|---|
| 5:02.9 | "Pronto / Que maneiro, caraca" | — | Transient +12.8 dB [hyp: success ding] |
| 5:08.0–5:08.4 | Teleport into the shop ("quanto será que custa o próximo item?") | **White flash** (full white, 0.1 s) decaying over 0.3 s into the shop [seen] | Whoosh [hyp] |
| 5:11–5:21 | "É um secador. / Hã? / Secador?" | No effect. The joke plays on dialogue cuts only. [seen] | — |
| 5:21.9–5:22.3 | Leaving the shop ("Mas se tá aqui é porque funciona") | **White flash**, 0.4 s fade [seen] | — |
| 5:27.0 | "Isso aqui é muito da hora" | — | Transient [hyp] |
| 5:41.7–5:42.0 | Kadukos arrives with the second water pistol ("eu tive uma ideia…") | **Green flash**, 0.3 s [seen] | — |
| 5:46.2–5:46.3 | "…a gente ainda tá com 0%" | **HUD zoom** on "INUNDAÇÃO 231/1M" (top-left, about 200%), very short, about 0.3 s [seen] | — |

### 2.3 Window 2: 10:58–11:46

| Time | Trigger | Effect |
|---|---|---|
| 11:05.6–11:06.7 | "Tá até meio bugado, a gente tá ganhando muito" | **HUD zoom** on "INUNDAÇÃO 6.587/1M", top-left anchored, about 200%, about 1.1 s [seen] |
| 11:07–11:33 | Hair-dryer melting snow mountains | Plain cuts between POV and third person every 1.5–3 s. No overlays. [seen] |
| 11:16.0–11:19.0 | "Uns 10, 25 mil / É, 1%" | **HUD zoom** again, held about 3 s, while the counter visibly ticks 9.752 → 9.979 [seen]. Music drops out 11:08.8 and 11:31.1 [measured]. |
| 11:22.4–11:22.8 | Teleport / scene change | **White flash** (full white 0.1 s, 0.4 s decay) [seen] |
| 11:54.7–11:55.5 | Buying the trident ("COMPRADO") | **Green flash + money-rain overlay**, identical to 2:21.7 [seen]. Probable SFX: cha-ching [hyp]. |

### 2.4 Window 3: 15:55–16:37

| Time | Trigger | Effect |
|---|---|---|
| 15:55–15:57 | Lucky block | In-game "SORTE! +4.324 blocos de inundação" text (not an edit) [seen] |
| 16:05.5–16:06.0 | Kadukos says the cut-off insult "Oi, seus filhos da p…" | **Punch-in** to about **250%** on Kadukos (head and torso), held 0.5 s, then a two-shot [seen]. Audio transient +18 dB at 16:05.5 = probable **censor bleep or comic sting** covering the word [hyp]. |
| 16:20.4–16:20.8 | Back to the shop ("o próximo item é um H2O?") | **White flash**, 0.4 s decay [seen] |

### 2.5 Window 4: 21:02–22:02 (climax)

| Time | Trigger | Effect |
|---|---|---|
| 21:07–21:13 | "Galera, corta tudo… a gente vai ser engolido pela tsunami" | Fast cutting (cuts every 0.3–0.8 s) between POV and wides; underwater shots. No overlay effects. [seen] |
| 21:25.0–21:26.0 | After "A tsunami é muito roubada!" | **1.1 s of full black + music drop (1.0 s)**: a beat or reset before "Galera, é o seguinte" [seen + measured] |
| 21:34–21:44 | "3, 2, 1, e…" | Countdown played straight, with hard cuts on "Clica, clica" [seen] |
| 22:05–22:16 | Meteor countdown and impact | Fast cuts (the 52-cuts/min minute) [measured] |

---

## 3. Patterns as rules

### 3.1 Trigger → effect rules (ranked by evidence)

1. **Teleport to or from the shop → white flash.**
   - Full white for 1–2 frames, decaying to clear in about 0.3–0.4 s, sometimes with a short blur-zoom.
   - Seen at 5:08, 5:21.9, 11:22.4, 16:20.4 (white) and 2:19.0 (magenta variant).
   - About 1 per shop round-trip, so roughly every 1–3 min.
2. **Purchase confirmed → green flash + money-rain overlay** (falling dollar bills, about 0.9 s), plus a probable cha-ching. Seen at 2:21.7 and 11:54.7. Every purchase.
3. **Counter or number spoken ("nem 1%", "0%", "6 mil", "25 mil") → HUD zoom.**
   - The whole frame scales to about 200%, anchored top-left, so the inundation bar fills the top.
   - It is a hard scale on the cut with no easing.
   - Held 0.3–3.5 s (long when the counter is ticking), ended by a cut.
   - Seen at 1:27.6, 5:46.2, 11:05.6, 11:16.
4. **Frustration or failure ("não tá funcionando", "impossível", "que porcaria") → red flash.** Red/pink overlay, first frame blurred, linear fade over about 1.1 s, with a fail sound [hyp]. Seen at 1:57.9.
5. **Hype or epic word ("dilúvio", the finale) → red-orange overlay** of about 0.8 s, plus the loudest SFX of the video (+39 dB, 2.5 s) [hyp boom / thunder]. Seen at 3:08.9.
6. **Good news, idea or new item → green flash**, 0.3–0.4 s, without money rain. Seen at 2:06.8 and 5:41.7.
7. **Insult, jab, "no no no", tense reply → face punch-in** to 200–300% on the speaker.
   - Hard cut-in with no animation, held 0.2–0.6 s.
   - Often ping-pongs between the two faces.
   - Seen at 0:18.9 (blur-zoom variant), 0:28.2 (a 1-frame stab on "seu burro"), 3:03.7 and 16:05.5.
8. **Big statement or "genius" moment → white blur flash** of about 0.2 s on the cut. Seen at 0:02.4 and 2:50.6.
9. **Joke or disappointment beat → music drops out** for 0.8–2.2 s. The joke lands in silence and the music returns on the next line.
   - 21 drop-outs in total. 5 of them fall in the first minute; after that, about 1 per minute.
   - Examples: 0:54.8 suspense, 1:29.7 "nem 1%", 3:12.2, 21:25 with a black screen.
10. **Reset before a new act → about 1 s of black + silence** (21:25). Used once.
11. **Hook = future footage** (takes futuros) for 7.5 s:
    - cuts every 0.6–1.7 s;
    - desaturated, soft-bloom grade (saturation about 45%);
    - narrator states the premise in one sentence;
    - the age-rating badge sits top-left;
    - entered and exited with a white flash and a blur transition.

### 3.2 Expectation breaks and comedic timing

- **Expectation breaks are cut, not decorated.**
  - Examples: "Só lixo" (0:35), "É um secador. / Hã? / Secador?" (5:11–5:16), "o mel deve estar bem" (18:45).
  - The edit just cuts to the reacting person's shot and lets the line play.
  - **No effect** on most jokes: the reaction shot is the joke.
- **Effects mark structure** (shop, purchase, numbers), not every joke.

### 3.3 Music

- Music sits low and steady: about −14 dB under the voice, with flat loudness the whole video.
- **Music changes** [hyp, from chroma/MFCC novelty]:
  - about 25 strong change points in 22.7 min, so **one track roughly every 50–60 s**;
  - the strongest fall at 3:52, 9:35, 12:02, 13:18, 18:52;
  - they tend to come at act boundaries (new item tested, return from the shop).
- The track mostly switches **on a cut together with a flash**, not with a crossfade [hyp].
- **Music drops out for jokes** (rule 9) and for the black-screen reset.

### 3.4 Frequency (per minute, verified)

| Segment | Visible edit effects/min | Detected SFX-like transients/min (music+SFX stem, ≥9 dB over the 10 s bed) |
|---|---|---|
| Hook, 0–1 min | ~6–8 | **7** |
| 1–3 min | ~4 | ~2 |
| Body, 3–21 min | **~2–4** | ~0.5–1 (detected; true SFX count is likely 2–4/min including quieter ones [hyp]) |
| Climax, 21 min | ~2 overlays, but 52 cuts | ~0 (in-game destruction audio dominates) |

### 3.5 Recurring inserts

| Insert | Where |
|---|---|
| Money-rain overlay (only extra-footage asset) | Each purchase |
| HUD zoom on the inundation counter | Every time a number is said |
| Book promo card | Only once, at 0:00 |
| Age-rating badge "L" | Only in the hook |

There are no meme clips, real-life footage, emoji, stickers or reaction PNGs.

---

## 4. Mapping to BERSERKER presets (exact names from `berserker_presets.json`)

| Reference effect | Closest preset(s) | Notes |
|---|---|---|
| White flash on teleport (shop in/out), 0.3–0.4 s | **Lava's White Flash A** (or **Lava's White Flash B**) | Put it on the cut. If the decay is too long, trim it to about 0.4 s. |
| White blur flash with zoom-in (0:02.4, 0:18.9, 2:50.6) | **Lava's Transition Zoom In A** + **Lava's White Flash A** | Or **Lava's Transition Zoom In B** |
| Zoom-out blur transition (1:41.7) | **Lava's Transition Zoom Out A** / **Lava's Transition Zoom Out B** | |
| Blur transition into the body (0:10) | **Lava's Blur In (Dissolve)** on the incoming clip | |
| Green flash (purchase, new item, good news) | **Lava's Green Flash A** (0.3–0.4 s) / **Lava's Green Flash B** | Plus a money-rain overlay clip on purchases (not a preset) |
| Red flash (fail/frustration, about 1.1 s fade) | **Lava's Red Flash A** / **Lava's Red Flash B** | Use the longer of the two for the 1 s fade |
| Red-orange "dilúvio" hit (0.8 s) | **Lava's Red Flash B** | No orange preset. Optionally add **Lava's Impact Shake Low** only if the SFX is an explosion; the reference itself does not shake. |
| Magenta teleport flash (2:19) | None | Closest: **Lava's White Flash A** with a pink tint, or just a white flash |
| HUD zoom on the counter (about 200%, top-left, hard, held) | No exact preset | Manual: Scale 200%, Anchor/Position on the HUD bar. Closest animated alternative: **Lava's Smooth Zoom to 150** (re-anchored), but the reference cuts in with **no animation**. |
| Face punch-in 200–300% (hard cut-in, hold, cut out) | No exact preset | Manual Scale 200–300% on a razor-cut segment. Animated alternative: **Lava's Smooth Zoom to 150** or **bela - zoom in**. The 0:18.9 variant = **Lava's Transition Zoom In A** landing on a held scale. |
| Dark motion-blur whip between angles (2:56.2) | **Lava's Pan To Left A** / **Lava's Pan To Right A** | |
| 1 s black reset (21:25) | **Lava's Black Flash A** | Or a 1 s black matte + music cut |
| Promo/title card text in (blur in) | **Lava's Blur In (Dissolve)** | |
| "LINK NA DESCRIÇÃO" pop | **Lava's Normal Pop In** or **Lava's Bouncy Pop In** | |
| Age-rating badge "L" in/out | **Lava's Normal Pop In** / **Lava's Simple Slide Out Left** | |
| Title glow (neon) | **Lava's Pink Glow**, **Lava's Blue Glow** | |
| Teaser grade (desaturated, bloom) | No preset | Lumetri Saturation about 45–50% + slight lift/glow. **Lava's Vignette Low** optional. |
| Not used by the reference | Lava's VHS / Lava's Extreme VHS / Lava's Screen VHS, Pixelates, Paper Effect, 3D flips/cubes, Outlines, Drop Shadows, Rounded Corners, Light Sweeps, 360 Movements, Angry Shakes, Handheld and Fullscreen shakes, Constant Zooms, Subtitles | Avoid, or use very sparingly |

---

## 5. Top 10 to copy / 5 to avoid

### Copy

1. **Cut every ~2 s** (median 1.93 s) by alternating third-person follow cam and POV. Cut when the speaker changes and when the action changes.
2. **Hook = 7–8 s of future footage** (takes futuros):
   - cuts every 0.6–1.7 s;
   - desaturated, bloomy grade;
   - narrator states the premise in one sentence;
   - white blur flash in, blur transition out to the normal grade.
3. **Hook density about 2× the body**: about 50 cuts/min for the first 10 s, about 38/min to 1:00, about 21/min after.
4. **White flash (Lava's White Flash A, about 0.35 s) on every teleport to or from the shop or base.**
5. **Purchase = Lava's Green Flash A + money-rain overlay + cha-ching**, every time something is bought.
6. **Any number or percentage spoken → hard 200% HUD zoom on the counter**, held while the number is on screen (0.3–3.5 s), ended by a cut.
7. **Fail or frustration → Lava's Red Flash (about 1 s fade) + fail SFX.** Good news or idea → Lava's Green Flash (0.3 s).
8. **Insult, "não não não" or comic jab → hard punch-in 200–300% on the speaker's face**, held 0.2–0.6 s. It can ping-pong between faces, and can be a 1–3 frame stab.
9. **Music about 14 dB under the voice. Cut the music for 1–2 s on a joke or disappointment line**, and change track about every 50–60 s at act boundaries (on a flash or cut).
10. **Pace the effects at 2–4 per minute in the body.** Tie them to structure (shop, purchase, number, reaction), not to every sentence.

### What the reference does NOT do (avoid overediting)

1. **No captions, subtitles or text overlays** after the first 6 s. The only text is in-game HUD text.
2. **No shakes, VHS, glitch, chromatic aberration, pixelate, fisheye/stretch or rotation/tilt.** Even explosions and tsunamis are left clean.
3. **No meme clips, real-life inserts, emoji, stickers or reaction PNGs.** The only extra asset is the money rain.
4. **No eased "zoom that breathes" on every line.** Zooms are rare, hard-cut and held; most jokes get no effect, just the reaction shot.
5. **No dense SFX bed**: detected SFX are sparse (about 1/min in the body). No B&W, freeze frames or speed ramps were seen in the sampled windows.

*SFX names are inferred from transients on the demucs music+SFX stem and from visual context, not heard. Treat them as hypotheses.*
