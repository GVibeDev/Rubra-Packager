# Recommended Workflows

Sprite Studio is modular. The routes below are **recommendations, not restrictions**.

You can open the major workspaces directly, skip stages that are unnecessary, return to an earlier stage, or use the suite only for cleanup/alignment/export without using any generative model.

The safest production principle is simple:

> Enter the pipeline with the best material you already have, and use only the stages that add value.

---

## Choose where to start

| You already have… | Recommended starting point |
| --- | --- |
| only a concept | Prompt Builder |
| a reference image | Image / Generate workflow |
| an existing video | Extraction |
| a frame sequence | Clean-up or Alignment |
| a spritesheet | Sprite Sheet workspace |
| a partially built character | Character Set / Layer Manager |
| an existing generation you want to improve | Calibration Lab / relevant production stage |

---

## Workflow A — Full AI → Sprite

Best when you begin with a concept and want the entire local generative-production pipeline.

```text
Prompt Builder
    ↓
Image Generation
    ↓
Reference review / preparation
    ↓
Generate / Wan Animate
    ↓
Extraction
    ↓
Frame selection
    ↓
Clean-up
    ↓
Alignment
    ↓
Character Set / Layer Manager
    ↓
Export
```

### Practical loop

1. Build a clear prompt with Prompt Builder.
2. Generate or load a reference image.
3. Review the reference before spending time on motion generation.
4. Generate motion with conservative settings first.
5. Extract the sequence and reject obviously unusable frames.
6. Clean only the material worth preserving.
7. Align the accepted frames.
8. Organize the result by animation/direction if it belongs to a larger character set.
9. Export the frame sequence or spritesheet.
10. Save the generation configuration when it proves repeatable.

Do not begin by maximizing resolution, frame count and steps simultaneously. Establish a working baseline first.

---

## Workflow B — Existing image → Animated asset

Use this when the source image already exists or was created outside Sprite Studio.

```text
Reference image
    ↓
Optional reference preparation
    ↓
Generate / Wan Animate
    ↓
Extraction
    ↓
Frame selection
    ↓
Clean-up
    ↓
Alignment
    ↓
Export
```

### Before generation

Check that the source has:

- a readable silhouette;
- enough resolution for the intended output;
- no severe pre-existing anatomy or edge defects;
- a background that does not compete with the subject;
- the details that must remain recognizable during motion.

If the source already contains defects, motion generation can amplify them.

---

## Workflow C — Existing video → Sprite

This route does not require any local AI model.

```text
Open video
    ↓
Extraction
    ↓
Frame selection
    ↓
Clean-up
    ↓
Alignment
    ↓
Character Set / Layer Manager (optional)
    ↓
Export
```

A video does not have to be perfect to be useful. A sequence with several broken frames can still contain enough production-quality material to recover an animation.

The selection stage exists specifically so that bad frames do not automatically invalidate the entire clip.

---

## Workflow D — Existing spritesheet → Refine / Reuse / Variant

```text
Sprite Sheet workspace
    ↓
Decompose / normalize
    ↓
Clean-up and/or Alignment
    ↓
Build reference sheet (optional)
    ↓
Optional Image / Motion generation
    ↓
Character Set / Layer Manager
    ↓
Export
```

This workflow is useful when you want to:

- repair an old sheet;
- normalize inconsistent cells;
- extract a clean sequence;
- create a stronger reference for a model;
- produce a controlled variant while preserving the original material;
- reorganize an existing asset into the Character Set system.

---

## Workflow E — Frame sequence → Production-ready animation

```text
Frame sequence
    ↓
Clean-up
    ↓
Alignment
    ↓
Character Set / Layer Manager
    ↓
Export
```

This is the shortest route when another application or artist already supplied the animation frames.

---

## Calibration loop

The Calibration Lab is not a mandatory stage in every workflow. It becomes valuable when generation is unstable or expensive enough that repeating bad experiments wastes significant time.

A useful calibration cycle is:

```text
Working baseline
    ↓
Change one important variable
    ↓
Generate
    ↓
Compare result
    ↓
Keep / reject
    ↓
Promote useful configuration to profile or Production Preset
```

Changing several major parameters at once makes it difficult to understand what actually improved or damaged the result.

---

## Guided Workflows

The in-app Workflow workspace provides guided routes through the suite. It should be treated as navigation and production memory, not as a locked wizard.

Use it when it helps. Ignore it when you already know which workspace you need.

---

## When to stop using AI

Not every problem should be regenerated.

If the motion is good but a small number of frames contain edge contamination, alignment drift or isolated defects, the production tools may be faster and more predictable than another model run.

The goal is a usable asset, not maximum time spent inside the generator.
