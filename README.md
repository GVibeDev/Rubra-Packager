<p align="center">
  <img src="docs/images/banner-readme.webp" alt="Unum Sunt Sprite Studio" width="100%">
</p>

# Unum Sunt Sprite Studio

**Local production workstation for turning generated images, videos, frame sequences and spritesheets into usable 2D game assets.**

**Current application baseline:** R5c7 · Windows x64  
**Core license:** GNU GPL-3.0-or-later  
**Release status:** validated public baseline  

Unum Sunt Sprite Studio is not a one-click “perfect sprite” generator. It is a production suite built around the opposite assumption: generative models drift, ignore instructions, create artifacts, deform details and often need selection, cleanup, alignment and calibration before their output becomes useful.

**Sprite Studio gives you control over that process.**

The suite can start from a generated image, an existing image, a video, a frame sequence or a complete spritesheet, and it can move those assets through generation, extraction, cleanup, alignment, organization and export. The built-in workflows are recommendations, not restrictions: every major workspace remains directly accessible.

> **More control, not more promises.**  
> The goal is not to hide generative complexity. The goal is to make it observable, reusable and recoverable.

---

## What you can do

- build structured prompts with reusable prompt profiles;
- generate still images through a local Krea 2 / WanGP workflow;
- animate reference material through WanGP / Wan Animate;
- import existing videos and extract candidate frames;
- select usable frames instead of discarding an entire imperfect generation;
- remove or refine backgrounds and masks with automatic and manual cleanup tools;
- propagate selected cleanup operations across compatible frames;
- align frames into consistent animation-ready sequences;
- import and decompose existing spritesheets;
- build new reference sheets from existing sprite material;
- organize subjects, animations, eight directions and logical layers;
- compare generation runs in the Calibration Lab;
- preserve successful configurations with profiles and Production Presets;
- export cleaned frame sequences and spritesheets.

### Flexible entry points

| Start with | Typical direction |
| --- | --- |
| A text concept | Prompt Builder → Image Generation → Motion → Extraction → Cleanup → Alignment → Export |
| An existing image | Reference → Motion → Extraction → Cleanup → Alignment → Export |
| An existing video | Extraction → Frame selection → Cleanup → Alignment → Export |
| A frame sequence | Cleanup / Alignment → Character Set → Export |
| An existing spritesheet | Decompose → Refine → Build reference → Optional generation → Export |
| A partially completed character set | Organize / complete directions → refine missing assets → Export |

See [Recommended Workflows](docs/WORKFLOWS.md) for concise step-by-step routes.

---

## Built for production, not only generation

A good generation is only the beginning of a usable asset pipeline.

Sprite Studio was designed to preserve the parts of a generation that work and give you tools for the parts that do not. A video with several bad frames is not automatically a failed video. A useful frame with a contaminated edge is not automatically a lost frame. A slightly unstable sequence can often be improved through selection, cleanup and alignment.

That is why the suite includes production systems around the generators rather than treating generation as the final output:

- **Prompt Builder** — modular prompt construction, technical constraints and identity-preservation guidance;
- **Calibration Lab** — compare runs, isolate parameter changes and preserve useful baselines;
- **Profiles and Production Presets** — keep configurations that actually worked on your hardware and material;
- **Extraction** — choose the useful temporal material instead of accepting every frame;
- **Clean-up** — automatic keying plus manual correction, selection tools, propagation and transaction history;
- **Alignment** — normalize frame placement before animation export;
- **Sprite Sheet tools** — decompose existing work or turn it back into reference material;
- **Character Set / Layer Manager** — organize production by subject, animation, direction and layer;
- **Guided Workflows** — optional routes through the suite without locking you into one way of working.

---

## Local AI: important expectations

Sprite Studio can manage local AI workflows, but local generative AI is **hardware-intensive, configuration-sensitive and probabilistic**.

You should expect:

- substantial disk usage for runtimes, checkpoints and working files;
- a compatible GPU and sufficient system memory for serious local generation;
- generation speed to vary significantly with model, resolution, frame count, precision and memory strategy;
- prompts and source quality to affect both quality and consistency;
- some outputs to contain artifacts, drift or unusable frames;
- calibration to be part of the workflow rather than a one-time setup step.

A complete managed local setup should be planned around **approximately 100 GB of free disk space**, with additional room recommended for projects, cached assets and generated media. The R5c7 runtime plan alone reserves roughly 86.7 GiB before safety margin and future workspace growth.

There is intentionally no single published “minimum VRAM” or “minimum RAM” number for every workflow. WanGP uses different memory/offload profiles, and workloads change substantially with the selected model and generation parameters. A configuration that technically runs can still be too slow for practical production.

For details, read [AI Runtime & Hardware](docs/AI_RUNTIME_AND_HARDWARE.md).

---

## About the included local model workflows

Sprite Studio currently targets local workflows around:

- **WanGP / Wan2GP** as a separately installed or adopted external runtime;
- **Wan 2.2 Animate** for reference-driven motion generation;
- **Krea 2 Turbo** for local image generation.

These components are not part of the GPL-covered Sprite Studio Core and remain subject to their own terms.

The project does **not** claim parity with the newest proprietary cloud image/video systems in speed, infrastructure or every aspect of output quality. That is not the design target. The current local models are valuable because they can be used in repeatable, reference-driven production workflows where local execution, control and iterative refinement matter.

For controlled 2D material — especially characters or objects on simple backgrounds — they can produce excellent results when configured well. Sprite Studio cannot sell or automate the skill required to configure a generative model; it can help you make successful configurations easier to understand, preserve, compare and reuse.

### Krea 2

Krea 2 is optional and separately licensed. Sprite Studio requires explicit policy acknowledgement before Krea generation and manual review before a newly generated Krea image can be promoted into the WAN reference pipeline.

Read:

- [KREA_SAFETY_AND_USE.txt](KREA_SAFETY_AND_USE.txt)
- [Krea 2 Community License](https://www.krea.ai/krea-2-licensing)
- [Krea Acceptable Use Policy](https://www.krea.ai/krea-2-use-policy)

At the time this documentation was prepared, Krea's Community License permits commercial use below its stated company-wide trailing-twelve-month revenue threshold and requires an Enterprise License when that threshold is reached. Always check the current upstream terms before commercial use or redistribution.

### WanGP

WanGP remains an external runtime and is not sublicensed by Sprite Studio. Its current Community License contains separate conditions for free use, outputs, redistribution and commercialized wrappers/integrations.

**If you intend to monetize a product or service that exposes or integrates WanGP functionality, review the current WanGP license and obtain upstream permission where required.**

Read [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt) and the current upstream WanGP license before changing the distribution or monetization model.

---

## Generation is a craft, not a button

The same model can behave very differently depending on source quality, prompt structure and generation settings.

Common causes of poor output include:

- contradictory prompt instructions;
- prompt text that conflicts with structured options such as camera or motion settings;
- low-quality, noisy or already-deformed source material;
- complex or ambiguous backgrounds;
- excessive detail that the model cannot preserve consistently over time;
- aggressive combinations of resolution, frame count and generation parameters;
- assuming that more steps or more frames always mean better quality.

The practical approach is iterative: stabilize the source, change one important variable at a time, compare runs, preserve working profiles and use the cleanup/alignment stages to recover imperfect but valuable material.

See [Generation Guide](docs/GENERATION_GUIDE.md).

---

## Designed with small game teams in mind

Sprite Studio was conceived for **retro, indie, roguelike/roguelite and sprite-heavy 2D production**, where a small team may need many characters, directions, variants and animation states without a large dedicated animation department.

A well-calibrated suite can reduce repetitive asset-preparation time so that more development time can be spent on gameplay, level design, balancing, writing, audio and polish.

The pipeline is intentionally broader than character sprites. Props, effects, animated textures and other frame-based 2D material are plausible experimental uses, although not every such workflow has been formally validated by the project yet.

---

## Visual tour

The public documentation is being updated with three R5c7 production captures:

1. **Image Generation** — a real local generation with its output visible;
2. **Clean-up** — a generated frame being repaired and prepared for production;
3. **Character Set / Layer Manager** — a multi-direction production set organized for export.

The screenshots will use original demonstration subjects rather than third-party characters or brands.

See [Screenshot Plan](docs/SCREENSHOT_PLAN.md).

---

## Recommended workflows

Sprite Studio includes guided workflows, but they are deliberately optional.

You can follow a full AI-to-sprite route, enter halfway through with an existing video, start from a spritesheet, use only cleanup/alignment, or move material back into generation as a new reference.

See [Recommended Workflows](docs/WORKFLOWS.md).

---

## Installation and source builds

The **Core application** can be used without installing any AI runtime. Local AI features are optional.

This repository is the public source tree. Packaged distributions may be provided separately from GitHub; the build tools required to reproduce the Windows artifacts remain in the repository.

Developers can run the source tree with the dependencies in `requirements.txt`.

Canonical Windows build commands:

```text
build_windows_standalone.bat
build_setup_windows.bat
```

Public release assembly helper:

```text
PREPARE_PUBLIC_RELEASE_R5C7.bat
```

R5c7 was validated with **322 automated tests**, compile checks and manual Windows validation covering installation, startup, branding, AI workflows, project/Character switching, maintenance/uninstall behavior and GPL/Krea compliance UI.

The `R5c7` Git tag identifies the validated application baseline. Documentation on `main` may continue to improve without changing the application version.

---

## Documentation

- [Recommended Workflows](docs/WORKFLOWS.md)
- [Generation Guide](docs/GENERATION_GUIDE.md)
- [AI Runtime & Hardware](docs/AI_RUNTIME_AND_HARDWARE.md)
- [Public Roadmap](docs/ROADMAP.md)
- [Screenshot Plan](docs/SCREENSHOT_PLAN.md)
- [Changelog](CHANGELOG.md)
- [Release Notes R5c7](RELEASE_NOTES_R5c7.md)
- [Third-party notices](THIRD_PARTY_NOTICES.txt)
- [Krea safety and use](KREA_SAFETY_AND_USE.txt)
- [Security Policy](SECURITY.md)

Detailed migration and milestone documents are preserved in the repository as development history.

---

## Roadmap

Future directions include Linux packaging, a 2D cutout rig editor, keyframe/interpolation support, weighted mesh deformation, stronger per-frame painting/editing tools, additional local model backends and optional online providers using user-owned API credentials.

These are development directions, not delivery promises or fixed dates.

See [Public Roadmap](docs/ROADMAP.md).

---

## License and third-party components

The project-owned Unum Sunt Sprite Studio Core is licensed under **GNU GPL-3.0-or-later**. See [LICENSE](LICENSE).

WanGP, Krea 2, Wan Animate, model weights, Python distributions, PyTorch and other third-party components remain under their own licenses and terms. See [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt).

Do not assume that the GPL license of the Core grants rights over separately licensed AI runtimes or model weights.

---

## Security

Please read [SECURITY.md](SECURITY.md).

Do not publish API keys, Hugging Face tokens, credentials, private model access data or sensitive vulnerability details in public issues.
