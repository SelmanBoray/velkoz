# Architecture decisions

*Back to the [README](README.md) · [Türkçe README](README.tr.md)*

This file records why Gözcü is built the way it is. Each decision gives the **choice**, the
**reason**, and the **fallback** if it fails. Dated notes were added as measurements came in,
so later sections sometimes revise earlier ones. Experiment notes linked from here are in
Turkish; the numbers and code paths in them are what matter.

The project was designed on 2 July 2026; the dates below are when each decision was made or
revised.

**Planned vs built.** A few items below were design intentions that have not been
implemented. They are marked *(planned, not built)*.

## 1. Embedding model: `jinaai/jina-clip-v2`, Turkish embedded directly

- **Choice:** no query translation; the Turkish query is embedded as is. The model pairs an
  XLM-RoBERTa text tower (89 languages) with an EVA02-L image tower at 512×512 input, which
  helps with small cars and people in wide car-park shots. Vectors are kept at the full **1024**
  dimensions; storage is not a constraint at this scale.
- **VRAM:** about 2 GB in fp16, so it runs next to YOLO on a 6 GB card.
- **CPU fallback:** the code falls back to fp32 PyTorch on CPU. Query encoding then takes about
  13 s instead of 286 ms on GPU (measured, [PROGRESS.md](PROGRESS.md), 5 July 2026). The
  published ONNX int8 weights would give the same vector space on CPU *(planned, not built;
  `onnxruntime` is in `requirements.txt` but not imported)*.
- **Fallback plan:** if Turkish recall had been weak: translate the query and switch to
  `google/siglip2-so400m-patch14-384` (1152-d). The decision was to be made by measurement on
  the evaluation set (risk 3), not by feel. It was not needed.

## 2. Frame sampling

> **Revised 3 July 2026.** The first design deduplicated frames with pHash. On real CCTV
> (VIRAT campus footage) it was structurally blind to small distant subjects: a global 64-bit
> hash gives Hamming distance 0 for a person moving three pixels, and 44 frames collapsed into
> one. The mechanism was replaced. Diagnosis:
> [`experiments/2026-07-03_gercek_cctv_testi/`](experiments/2026-07-03_gercek_cctv_testi/deney_notu.md)

1. Decode with PyAV, take candidate frames at **2 fps**.
2. **Downscale and normalise:** 320×180 greyscale, 5×5 Gaussian blur, **mean normalisation**,
   so automatic gain changes or a passing cloud do not count as "everything changed".
3. **OSD mask:** pixels that change in more than 50% of recent candidates (a burnt-in DVR
   clock) are excluded from every count.
4. **Motion gate:** normalised absolute difference to the previous candidate **> 10**, then a
   **connected-component filter** on the change mask (≥ 5 px; rain and grain are not blobs, a
   person is). The candidate is kept if the remaining ratio is **> 0.0005**.
5. **Cumulative-change dedup (instead of pHash):** the masked change ratio relative to the last
   *kept* frame must exceed **0.001**. A distant person walking accumulates difference across
   frames and crosses the threshold; zero-mean noise does not accumulate. pHash is kept as
   metadata only.
6. **Global-event guard:** if the raw change against the reference exceeds 25% (a lighting or
   exposure jump), one frame is kept and the reference is reset; the stream is not flooded.
7. An **anchor frame every 60 s** is kept even without motion, for scene coverage.
8. **Rate cap:** at most **600** frames per camera-hour (anchors exempt), so a pathological
   camera (rain, failing sensor) degrades gracefully instead of exploding the index.
9. Kept frames are embedded in batches (16 on GPU, 4 on CPU) and a **480 px JPEG (q=80)**
   thumbnail is written.

**Validation on VIRAT/UCF:** car park 3 → 59 kept frames, campus 1 → 31; frames with walking
people are now in the index.

**Index arithmetic:** 2 fps is 7,200 candidates per hour. A car-park camera realistically keeps
**about 300–500 frames per hour, 8–12k per day**. A pilot of one week × 4 cameras is roughly
**250–350k vectors, 1–1.4 GB** before any quantisation. These are estimates, not measurements.

## 3. Vector store: Qdrant, local mode

Collection `frames`: **1024** dimensions, **cosine** distance, default HNSW settings
(m=16, ef_construct=100, enough up to a few million vectors). Scalar int8 quantisation with
`always_ram` would cut RAM about 4× *(planned, not built)*.

| Payload field | Type | Note |
|---|---|---|
| `source` | keyword | `frame` or `crop` |
| `video_id` | keyword | |
| `video_path` | keyword | absolute path; the viewer opens the video from here |
| `camera_id` | keyword | payload index requested (ignored in local mode, used by a Qdrant server) |
| `ts` | float (epoch UTC) | payload index requested; range filter |
| `offset_s` | float | seconds from the start of the video; the viewer's `start_time` |
| `frame_idx` | int | |
| `motion_score` | float | |
| `phash` | keyword | |
| `thumb_path` | keyword | |
| `yolo_class`, `yolo_conf` | keyword / float | crops only; class names are stored **in Turkish** (`araba`, `insan`) |
| `track_ids`, `plates` | | reserved for later; empty |

## 4. Turkish query pipeline

- **Rule-based parser.** Regex plus `dateparser` (Turkish) pulls out time expressions
  ("dün gece" = last night, "bu sabah 8'den sonra" = after 8 this morning) and turns them into
  a `ts` range filter. Only the remaining visual phrase ("beyaz Transit") is embedded. **Time
  words are never embedded; this is the single biggest quality lever.** If the time range
  returns nothing, the search falls back to the whole archive and says so.
- **Timestamps** are derived from file modification time minus video duration
  (`sampler.video_start_ts`). See risk 2.
- **LLM parser:** a full local-LLM parser (Qwen3-4B) was planned and then **deferred**: the rules
  work, and a 4B LLM plus the 3B VLM plus CLIP do not fit in 8 GB together. A narrow hybrid was
  built instead (6 July 2026): only when the rules find **no object** in the query (an
  out-of-vocabulary word such as "forklift"), the already-loaded `qwen2.5vl:3b` is asked, text
  only, for `{object, colour}` in English. It can only add; it never overrides a rule result,
  and any error falls back to the rules (`query.augment_intent`).
- **Privacy:** queries contain no images but can contain personal data (a plate, a name), so
  no cloud translation API is used.

## 4b. Not-found gate (object inventory, 4 July 2026)

Evaluation finding: the system had no reliable "not found" signal. CLIP cosine scores are not
calibrated across queries, and an object absent from the corpus (a red bicycle) still returned
plausible but wrong results: the lowest positive score (0.282) was below the highest negative
(0.36). The fix is **not** a score threshold but the **YOLO inventory**: if the query asks for a
detectable class (`query.extract_object_intent`, with Turkish synonyms and ASCII folding so it
survives suffixes) and that class was never detected in the corpus
(`store.available_object_classes`), the search returns empty without asking CLIP.

- **Production path only** (`source=None`); ablation runs skip the gate so raw retrieval stays
  measurable.
- **No calibration**: it is an inventory check, not a threshold, and adapts as the corpus grows.
- **Measured effect at the time:** positive metrics unchanged (no false gates), negative catch
  rate 0.25 (`neg_bisiklet` returned empty). It covers only "no detectable class". Attributes and
  weather (rain, snow) and undetectable objects (dog) were left to the Phase 2 VLM.
- Detail: [`experiments/2026-07-04_bulunamadi_kapisi/`](experiments/2026-07-04_bulunamadi_kapisi/deney_notu.md)

## 5. Module layout (flat package)

| Module | Responsibility |
|---|---|
| `config.py` | pydantic-settings: paths, model ids, every threshold; sets the offline lock |
| `sampler.py` | decoding, 2 fps sampling, motion gate, cumulative-change dedup → stream of `FrameRecord` |
| `detector.py` | YOLO11m person/vehicle detection, static suppression, person-first cap, cropping |
| `embedder.py` | jina-clip-v2 wrapper, batched image/text encoding, CUDA/CPU selection |
| `thumbs.py` | frame and crop thumbnails |
| `store.py` | Qdrant schema, frame and crop upserts, filtered search, class inventory |
| `query.py` | Turkish parsing: time phrase, intent, VQA targets, suffix-aware root matching |
| `search.py` | query embedding, Qdrant call, dedup, intent rerank, VLM fusion, streaming job, event clustering |
| `verifier.py` | VLM client (Ollama): atomic yes/no questions, availability check, warm-up |
| `recrop.py` | re-crops candidates from the original video at full resolution; draws boxes |
| `viewer.py` | Streamlit: query box → result grid with live badges → play the video from that second |
| `cli.py` | typer: `index`, `search`, `stats`, `doctor`, `ui` |

## 5b. Phase 1.5: YOLO crop embeddings (built 3 July 2026)

Brought forward once risk 1 was measured and confirmed. On every kept frame YOLO11m runs at
`imgsz=1280` (for small subjects, input resolution matters more than model size) and detects
people and vehicles. Crops (20% context margin, padded to square, taken from the original
resolution) are embedded with the same jina-clip-v2 and written to the **same** collection with
`source: "crop"`, pointing back to their frame.

- Low confidence thresholds (person 0.15, vehicle 0.25), with `yolo_conf` stored in the payload:
  the bar can be raised at search time, but a detection that was never indexed cannot be recovered.
- **Static suppression:** same class with IoU > 0.85 against the previous kept frame → skip. A
  parked car gets a vector only when it first appears.
- **Person-first cap (24 per frame):** sorting by confidence alone let parked cars crowd out
  people, and people are the rarest and most valuable class in CCTV search.
- No score offset: object queries naturally pick crops, scene queries pick frames.
- Validation: "uzakta tek başına yürüyen insan" (a person walking alone in the distance) → all of
  the top 3 are the correct person crop (before: lost to a close-up in the wrong video).
  [`experiments/2026-07-03_faz15_yolo_crop/`](experiments/2026-07-03_faz15_yolo_crop/deney_notu.md)
- **Known limit (4 July 2026, found while growing the corpus):** "no offset, it self-corrects"
  breaks when a scene query contains an **object word**. In "araçlarla dolu açık otopark" (an
  open car park full of vehicles) the flood of vehicle crops pushed the right scene frame to
  rank 8 (Phase 1.5 margin −0.333 on that query). Fixed by intent-conditioned ranking, §7.
  [`experiments/2026-07-04_korpus_buyutme/`](experiments/2026-07-04_korpus_buyutme/deney_notu.md)

## 6. The three biggest risks

1. **Whole-frame embeddings dilute small subjects.** A man in a red coat is about 40 px in a wide
   1080p shot. If recall disappointed, crop embeddings were to be pulled forward as Phase 1.5.
   **→ 3 July 2026: confirmed and fixed the same day.** Ranking within a video was right, but a
   0.02–0.07 dilution across videos buried the frame with the small subject. Phase 1.5 (§5b)
   fixed it. Remaining limit: people under about 10 px are below YOLO's detection floor (VIRAT
   campus segment); tiled inference (SAHI) is the option if needed.
2. **Timestamps lie.** DVR file names and modification times are unreliable; if the base time is
   wrong, every "last night" answer is wrong. Planned check: OCR the burnt-in on-screen clock and
   cross-check *(planned, not built)*.
3. **No evaluation set, no decisions.** Every model and threshold decision (including a switch to
   SigLIP2) must be measured against a fixed set of Turkish queries with known answers. Embeddings
   and thumbnails are personal data under KVKK too, so retention and deletion need a policy from
   day one.
   **→ 4 July 2026: closed.** A 22-query tiered set (`eval/queries.yaml`, frozen) with the runner
   `eval/run_eval.py`. First measurement: scorable R@5 = 1.0, golden R@1 = 1.0, **Phase 1.5 margin
   +0.333**. **Open finding: negative discrimination collapsed (lowest positive 0.282 < highest
   negative 0.36). No reliable "not found" signal, which is the reason for the Phase 2 verifier.**
   Detail: [`experiments/2026-07-04_eval/`](experiments/2026-07-04_eval/rapor.md)

### 6b. Evaluation methodology (4 July 2026)

| Query type (`gt_type`) | Metric | Why |
|---|---|---|
| `class` (bus, motorcycle) | video-level Recall@k | derived from exact class counts, `|relevant| ≤ 2–3` |
| `scene` (night, covered car park) | video-level Recall@k | scene-specific, checkable automatically |
| `golden` (driver on the phone, walking person) | Recall@1 / MRR on one frame | a ubiquitous class is trivial at video level; the frame was checked by eye |
| `advisory` (black SUV, blue pickup) | top-1 inspection only | colour ground truth cannot be checked automatically, so it is kept out of recall |
| `zaman` / time (last night, last 3 hours) | parse and fallback | boundary behaviour of time parsing |
| `negatif` / negative (red bicycle, snow) | discrimination (score distribution) | no absolute threshold; CLIP cosine is not calibrated across queries |

Rules: the set is **frozen before looking at results** (pre-registration); every aggregate is
printed with a **Wilson 95% CI** (n ≈ 12, so an indicator, not a benchmark); changes are compared
**paired (McNemar)** on the same set, not as independent proportions.

### 6c. Phase 2 end-to-end score and the hard-negative axis (21 July 2026)

`eval/faz2_eval.py` runs the full CLIP + VLM pipeline against the expectations in
`queries_faz2.yaml`. It is the objective score that iteration is steered by. Two
**independent** axes:

- **Axis 1, outcome:** `not_found` / `has_results`, matched against `expect`.
- **Axis 2, discrimination (`forbid`):** if a forbidden YOLO class **leaks** into the results, the
  query fails. This is independent of outcome; for `expect: any` it is the only verdict.

**Why a separate axis:** a found / not-found pair cannot tell whether the results are of the
*right class*. "kırmızı kıyafetli adam" (man in red clothing) returning five results, three of
them red *cars*, would still pass as `has_results`. That was exactly the bug of the session.

**`forbid: vehicles` is symbolic** and resolves to `gozcu.query.VEHICLE_CLASSES`. The stored
`yolo_class` values are **Turkish** (araba/kamyon/otobüs); an English list typed by hand would
never match and the test would silently pass. The symbolic value closes that trap structurally.

**Honesty about vacuous passes:** `forbid` is necessary but not sufficient; if no forbidden
candidate shows up at all, it passes trivially. The evaluator flags this with ⚠ by comparing
what leaked into the result with what the VLM filtered out. First run
([`experiments/2026-07-21_hard_negatif_eval/`](experiments/2026-07-21_hard_negatif_eval/OZET.md)):
`hn_kirmizi_kiyafet` is **non-vacuous**: CLIP proposed 6 red cars, the VLM removed all 6, none
leaked. `hn_siyah_kiyafet` is vacuous (the person query did not pull black cars) and stays as a
canary. **Score 11/12** (the earlier 9/10 baseline unchanged; entries without `forbid` skip axis 2).

**Thresholds were deliberately not calibrated:** the verifier's `confidence` is binary {0.0, 1.0},
so `vlm_drop_below` anywhere in (0, 1) has the same effect, and `vlm_beta` adds a constant to
colour survivors (no effect on order). Calibration would need a continuous confidence, which is a
feature, not a calibration task.

### 6d. Pooling ground truth while the corpus grows (4 August 2026)

When the corpus went from 13 to 17 videos, the C1 query set showed **R@5 0.917 → 0.833 and
MRR 0.917 → 0.785**. Inspection showed the regression was **not real**: the whole top 5 for
`gold_yuruyen_insan` were *correct* walking-person crops from the new videos, scoring higher than
the old top 1 (0.409 vs 0.384). The fault was in the ground truth, not the model: the
`relevant_videos` lists did not know about the new videos. In IR terms, **incomplete relevance
judgments**.

**Protocol (also in the header of `eval/queries_c2.yaml`):**
1. The old query set **stays frozen** as a valid record for its own corpus.
2. The new corpus version gets a **separate file** (`queries.yaml` → `queries_c2.yaml`).
3. Extensions are decided by **the content of the video, not by search results**: per-video class
   inventory plus crop and frame thumbnails checked by eye.
4. Weakly supported extensions are **rejected and the reason is written down** (four rejections on
   4 August: G339 not a full car park, G339 truck crop blurry, G330 basketball is not "walking",
   G505 not "between cars"). Recording rejections matters as much as acceptances: it shows the
   selection did not work in the metric's favour.
5. `golden_frame` fields are **never touched**.
6. Both versions are reported **side by side**; C2 alone does not count as evidence of progress.

With C2 ground truth: **R@1 0.833 · R@5 0.833 · MRR 0.847**; `beh_uzakta_yuruyen` went from rank
4 back to 1.

**Limitation this exposed: the golden-frame metric depends on corpus size.** `gold_yuruyen_insan`
stayed at rank 6 even after pooling, because `gold_*` assumes a single correct frame
(`VIRAT_otopark/180`) and the corpus now has five better legitimate matches. That is not a bug but
a broken design assumption of the metric. Moving to graded relevance is an **open item**. It was
deliberately not "fixed" by editing ground truth.

### 6e. Turkish root matching: suffix validation (4 August 2026)

To survive Turkish inflection, the parser matched **root prefixes** (`tok.startswith(root)`):
`kar` (snow) → `karda`, `karlı`, `kardan`. Right idea, wrong implementation: the same rule also
caught unrelated words that merely **start with** the root.

**Concrete effect:** for "karanlıkta ilerleyen araçlar" (vehicles moving in the dark) the object
target came out as `snow`, the verifier was asked *"is there SNOW in this image?"*, all **9
correct** CLIP candidates were rejected, and the query returned "not found". The evaluation had
reported it as a `false_gate` for two rounds. In CCTV use, "karayolunda ilerleyen araçlar"
(vehicles on the highway) would hit the same trap, a much more likely query.

**Fix:** after a root matches, the remainder must be a **valid Turkish suffix chain**
(`_EK_DIZISI`: plural · possessive · case · derivational, in order). `_kok_eslesir()` is used at
every match site: colour roots, class roots, scene roots, generic vehicle roots, the TR→EN
dictionary and the `needs_vlm` trigger (9 call sites).

```
karda    → kar + "da"     ✓ case suffix        → snow
karlı    → kar + "lı"     ✓ derivational       → snow
karanlık → kar + "anlık"  ✗ not a suffix       → no match
karayolu → kar + "ayolu"  ✗ not a suffix       → no match
```

**Known limit:** root plus a single vowel (`kara` = `kar` + dative `a`) is grammatically valid and
cannot be told apart. A full fix needs morphological analysis (e.g. Zemberek); this check removes
the common collisions. The limit is documented, not hidden.

**Measured (same corpus, same query set, one variable):** R@5 0.833 → **0.917** ·
R@10 0.917 → **1.000** · MRR 0.847 → **0.889** · Phase 1.5 margin +0.167 → **+0.250** · false
gates **zero**. Phase 2 (11/12) and the discrimination axis (2/2) unchanged; no negative broke.
Detail: [`experiments/2026-08-04_kok_eslesme_fix/OZET.md`](experiments/2026-08-04_kok_eslesme_fix/OZET.md).

## 7. Intent-conditioned ranking (4 July 2026)

The corpus expansion found it: when a scene query contains an object word ("araçlarla dolu açık
otopark"), that object's crops flood the results and bury the right scene frame. This is the
limit of "no offset, it self-corrects".

**The intent signal is case morphology, not word position** (`query.scene_or_object_intent`).
Turkish word order is free, but suffixes encode role: a noun with -DA/-DAn/-lA/-In is an adjunct,
and the head is the last **nominative** content noun. "araçlar**LA** … otopark" → head is otopark
(car park) → scene. "otopark**TA** … insan" (a person in the car park) → head is insan (person) →
object. Scene intent requires the head to be a scene word, not merely contain one (the "otopark
bariyeri", car-park barrier, trap). Classifier accuracy is reported separately (12/12 on dev).

**Mechanism: z-normalised soft frame boost, only for scene intent** (`search._intent_rerank`):
over the overfetched pool, `_rank = z(cos) + λ·[source == frame]`, with `λ = 1.0`
(`scene_boost_lambda`). Object intent is neutral, so the Phase 1.5 gain is kept. Not a hard
filter (risk of a recall cliff): a strong crop cosine can still win and legitimate cross-video
relevance is not crushed.

- **λ calibration:** from the score gap, not from the metric; gains are monotonic across the
  robustness band (λ/2, λ, 1.5λ); chosen on dev, verified on the locked set.
- **Measured effect:** the dev crop-flood cases improve (truck car park frame rank 10 → 4, garage
  6 → 3; 3 improvements, 0 regressions). The locked v1 set has **zero regressions** (R@5 = 1.0
  unchanged); object and no-object controls do not regress.
- **Limit:** the other half of the problem, a static lot yielding a single frame, is not the
  boost's job. It was handled by re-cutting those clips longer
  ([`experiments/2026-07-04_lot_zenginlestirme/`](experiments/2026-07-04_lot_zenginlestirme/deney_notu.md)).
  Detail: [`experiments/2026-07-04_olgu_b_frame_boost/`](experiments/2026-07-04_olgu_b_frame_boost/deney_notu.md)

## 8. Phase 2: VLM verifier (retrieve then verify, 4–5 July 2026)

Gaps CLIP could not close in evaluation: negation overlap (dog, rain, snow: weather, attributes
and undetectable objects the gate cannot handle) and colour (black SUV, blue pickup). Solution:
CLIP's top-N candidates are checked by a small VLM **at full resolution**.

- **Model: `qwen2.5vl:3b`** (Ollama, 3.2 GB Q4_K_M), **non-thinking**. On an 8 GB card it fits on
  the GPU next to CLIP (~2 GB): Ollama logs `offloaded 37/37 layers to GPU` (measured, no CPU
  offload). `keep_alive: 30m`. **Why not `qwen3-vl:2b`:** it is a thinking model; on ambiguous
  crops it loops until the context fills and returns empty JSON (33% failures, deterministic), and
  none of `think:false`, `/no_think` or a `num_predict` cap fixed it in that Ollama build.
  Diagnosis: [`experiments/2026-07-05_vlm_latency/`](experiments/2026-07-05_vlm_latency/deney_notu.md).
- **Contract: yes/no questions, not JSON.** Small VLMs **rubber-stamp** a multi-attribute,
  rejection-biased JSON schema: shown a red car, the model answered "blue car? yes, confidence
  1.0", ignoring the colour. The same model answers plain yes/no colour questions **perfectly**
  (red 9/9, blue 0/9). So the query is reduced to (object, colour) targets
  (`query.extract_vqa_targets`) and the verifier asks **two separate atomic questions**: "Is there
  a {obj}?" and "Is the {obj} {colour}?". `num_predict: 4` makes runaway generation structurally
  impossible.
- **The VLM's Turkish is not trusted:** targets are translated to English with a deterministic
  dictionary (mavi → blue, köpek → dog). A hard concept (dog) takes priority over a class name
  (person), because it is what CLIP missed. No extra VRAM, local.
- **Full resolution:** a crop thumbnail can be 36 px with no usable colour, so the candidate is
  re-cropped from the original video by its box (`recrop.py`, 384 px).
- **Conditional trigger:** only colour or hard-concept queries (`query.needs_vlm`) and only when
  Ollama is up. Object and scene queries already have high recall and do not pay the VLM cost.
- **For people, colour means clothing:** "kırmızı kıyafetli adam" is not "a red man". For person
  objects (`verifier._PERSON_OBJECTS`) the question is "Is this man **wearing** red clothing?"; for
  vehicles "Is the car red in color?". Otherwise everyone gets "no" and the person in red never
  surfaces.
- **Verdict:** `{object_present, color_match, confidence}`; `confidence` is 1.0 (present) or 0.0
  (absent), the distinction lives in the booleans. A VLM error yields `None` (leave the candidate alone).
- **Fusion is a filter.** A candidate that fails is removed from the main grid (it stays visible in
  a "rejected by VLM" expander); if all fail, the answer is "not found". A candidate is removed if
  the **object is absent** (`confidence < vlm_drop_below`) **or the colour does not match**
  (`color_match is False` on a colour query; colour is reliable per the 9/9 vs 0/9 measurement).
  So "man in red clothing" on a corpus with nobody in red shows no red *cars*: it says not found,
  and the red cars are in the expander. Survivors are reranked by `z(cos) + β·conf`.
  **`vlm_top_n = default_top_k`**, so every displayed candidate is verified (no unverified tail).
  An earlier "colour is unreliable, rerank only" design existed only because of the qwen3-vl JSON
  rubber-stamping; with the new model and contract colour became a hard filter.
- **Which image to verify on, chosen by measurement (5 July):** on small or blurry crops the VLM
  showed a yes-bias ("dog" on a person, "man" on a car), and multi-object scenes (a dog outside the
  person's box) cannot be judged from a tight crop. So the image depends on the question:
  - **Colour / attribute → tight crop** (subject fills the frame, colour is clear, fast). Full
    frames were tried but, downscaled to 768 px, distant cars vanished and real matches were
    rejected (black SUV 7 → 2, checked by eye), so tight crops stayed.
  - **Hard concept (dog, rain) → full frame without a box** (`recrop.vlm_frame_for_hit`, long side
    `vlm_frame_max_side = 768`): the VLM sees the whole scene and can say "there is no dog".
    Measured: "köpek gezdiren adam" (man walking a dog) had 1 false positive on tight crops and
    returns **not found** (0) on full frames.
- **Measured (5 July, deterministic):** discrimination is clean: "red car" present + colour 9/9,
  "blue car" colour 0/9, "dog" present 0/9. End to end, "köpek gezdiren insan" → target `dog`;
  of CLIP's 5 candidates **4 false positives were removed**, the 1 with a dog stayed.
- **Reliability:** non-thinking plus `num_predict: 4` gives **100% valid answers**. Latency for an
  atomic yes/no is a few seconds per image when warm; a colour query costs 2 calls per card, so a
  page of 12 takes tens of seconds, hidden by per-item streaming (§8b). `vlm_timeout_s = 30` is a
  safety net only.
- **VRAM co-residency and graceful failure (5 July):** on 8 GB, CLIP (~2 GB) plus qwen2.5vl
  (2.9 GB) plus background GPU apps occasionally ran out of memory and crashed Ollama. Moving CLIP
  to CPU was tried (the text tower takes ~13 s per call on CPU, which kills interactive search) and
  rejected. Instead of preventing the crash, the system **recovers from it**: (1) a self-healing
  availability check with a short TTL and reset on error (no more "false once, false forever");
  (2) separate UX for a single failed verification (a card badge) and a VLM that is down entirely
  (a global "VLM off, CLIP only" banner, `SearchOutcome.vlm_unavailable`); (3) a warm-up on start in
  a background thread, so the first query is not cold; (4) Ollama runs supervised (the desktop app
  restarts the server).

### 8b. Progressive rendering in the viewer (5 July 2026)

VLM latency was about 4–6 s per image (the bottleneck is image prefill, not tokens; lowering
`num_predict` or image size did not help), about 30 s for the top 8. Interactive search must not
block on it.

- `search()` was split: `search(use_vlm=False)` returns CLIP results immediately, and the public
  `refine_vlm(outcome)` runs the VLM phase. `search(use_vlm=True)` does both (the CLI stays
  synchronous).
- **Per-item streaming:** CLIP cards appear at once with a ⏳ badge; each candidate is verified in
  turn and its card's badge is filled live (⏳ → ✅ colour / ✅ present / 🚫). When all are done the
  grid is reordered and the rejected candidates move to the expander, so CLIP's raw recall stays
  visible. `search.py` provides `verify_top_n` (with callback), `_fuse_verdicts` and `stream_verify`.
- **Caching:** `@st.cache_data` for CLIP results and `session_state`, keyed by query, for VLM
  results, so clicking Play or a rerun does not re-run the VLM. Queries are submitted through
  `st.form`, not on every keystroke.
- **Stalls:** a slow VLM call can pause visible progress briefly; the timeout closes hangs, the
  card shows "could not verify" and the stream continues.
- The prompt was tightened ("every part of the description must be visible"), which fixed
  partial-match false accepts on negation (dog / rain → not found) without hurting attributes.
- **No parallel VLM calls** (one Ollama model; extra KV slots risk running out of memory).
  Sequential plus streaming.
- **Decoupled streaming (5 July, freeze fixed):** a synchronous `stream_verify` blocked the main
  thread for ~40 s and froze the browser. Now a **worker thread** fills in verdicts (no `st.*`
  calls, so no ScriptRunContext needed; verdicts live in a module-level `StreamJob` behind a
  `Lock`, not in `session_state`), and the viewer polls the job with
  **`st.fragment(run_every="0.5s")`** and draws the grid. When the job is done, `st.rerun` drops to
  the cached branch and polling stops. The main thread never blocks (checked in a browser: the
  page stays responsive during verification).
- **Card image = full frame with the box drawn** (`viewer._card_image`, `recrop.draw_bbox`): the
  matched subject is outlined in red, giving context instead of a tiny crop.
- **YOLO presence skip:** on a colour query, if the candidate crop's YOLO class already matches the
  target (araba = car), the presence question is skipped. About half as many VLM calls.

## 9. Time grounding: "when was it seen" (6 July 2026)

Turn point hits into events: when, and for how long, a query's matches were visible.

- **No identity tracking, so no "entered / left".** Tracking was not built (`track_ids` is
  reserved but empty), and IoU tracking between sparse CLIP + VLM hits breaks (it needs dense
  detection). The honest alternative is a **"seen between"** interval.
- **Clustering (`search.cluster_events`):** verified results are grouped by `video_id` and sorted
  by `ts`; a gap above `event_gap_s` (50 s) starts a new **event**. Each event has first and last
  sighting, frame count and a representative (highest score).
- **Presentation only**: it does not touch retrieval or verification, so it cannot move the
  evaluation baseline.
- **UI (`viewer.render_timeline`):** per event "İlk 21:26:07 · Son 21:28:18 (~131s, 9 kare)"
  (first / last seen, ~131 s, 9 frames); a single-hit event shows "seen at 21:33:36" (no fake
  interval). The UI warns: "no identity tracking; grouped by time proximity". Measured: red car,
  9 results → 1 event (~131 s); walking person → 2 events (VIRAT ~18 s plus one MEVA moment).
- **Deferred (v1.5):** split an event when the box centre "teleports" more than 50% of the frame
  between hits. Not tracking, just blocking physically impossible merges. To be added if the
  evaluation shows conflation.
