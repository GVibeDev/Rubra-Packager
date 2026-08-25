# Public Roadmap

This document describes intended development directions after the validated R5c7 Windows baseline.

It is **not a delivery contract**. Priorities may change as the application is tested in real production work.

---

## Current baseline — R5c7

R5c7 establishes the first distribution-ready Windows line with:

- standalone Windows Core;
- Inno Setup installer;
- managed/adopted external AI runtime architecture;
- Krea 2 image generation;
- Wan Animate motion generation;
- Prompt Builder;
- Calibration Lab;
- Production Presets;
- Guided Workflows;
- Sprite Sheet import/decomposition/reference building;
- frame Extraction;
- Clean-up tools;
- Alignment;
- Character Set / Layer Manager;
- export pipeline;
- validated update/repair/uninstall behavior;
- GPL/third-party release compliance.

---

## Documentation and onboarding

Near-term public work includes:

- concise workflow documentation;
- real R5c7 screenshots using original demonstration subjects;
- tutorial capture while real generation sessions are performed;
- clearer hardware/runtime expectations;
- separation between public-facing documentation and deep development history.

---

## Linux builds

Planned direction:

- Linux packaging;
- reproducible Core build path;
- runtime-path and dependency validation appropriate to Linux;
- parity checks for the non-AI production pipeline;
- local AI integration only where the external runtime contract can be validated cleanly.

Possible formats include AppImage and/or distribution packages; final packaging has not been frozen.

---

## 2D Cutout Rig Editor

Planned as the next major production subsystem.

First target:

- rigid 2D cutout layers;
- pivots / bones;
- hierarchy;
- transform editing;
- reusable rig data tied to Sprite Studio projects;
- export-friendly animation structure.

The goal is to complement generated animation with a deterministic manual animation path.

---

## Rig keyframes and interpolation

Following the basic cutout rig:

- timeline/keyframe editing;
- transform interpolation;
- reusable motion;
- controlled manual correction of generated assets;
- deterministic animation where generative motion is unnecessary or undesirable.

---

## Weighted mesh deformation

Longer-term direction:

- deformable 2D meshes;
- weighted influence from rig controls;
- finer correction of limbs, cloth and organic shapes;
- bridge between cutout animation and per-frame manual editing.

This is expected to require more research than rigid cutout animation.

---

## Painter / Adjuster expansion

Planned additions to frame editing include:

- bucket/flood fill;
- richer brush effects;
- stronger local color/alpha adjustment;
- text insertion;
- more general per-frame repair tools.

The long-term aim is to make generated frames increasingly repairable without requiring an external raster editor for every small defect.

---

## Additional local model backends

Sprite Studio should not be permanently coupled to one local generation stack.

Planned direction:

- additional local image models;
- additional local motion/video models;
- provider abstraction where practical;
- explicit per-provider capability and licensing notes;
- profiles that remain understandable rather than becoming an opaque “automatic” layer.

A model will not be integrated solely because it is newer. Production usefulness, licensing, reproducibility and hardware behavior matter as well.

---

## User-owned online API integrations

Future optional direction:

- connect online providers using credentials owned by the user;
- authenticate from the application;
- submit generation jobs without embedding project-owned service credentials;
- keep secrets out of project files and source control;
- clearly separate local and cloud privacy/cost expectations.

Provider support will depend on API terms, authentication requirements and licensing.

---

## Product philosophy

Future features should preserve the core design principles established by R5c7:

1. **control over hidden automation**;
2. **reusable production state** rather than disposable generations;
3. **non-destructive workflows** where practical;
4. **multiple entry points** into the pipeline;
5. **manual recovery paths** for imperfect AI output;
6. **clear separation of Core and third-party runtimes**;
7. **honest hardware and model expectations**;
8. **time saved on repetitive asset preparation should return to the game itself.**
