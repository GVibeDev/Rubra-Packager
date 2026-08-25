# AI Runtime & Hardware

Sprite Studio has two distinct layers:

1. **Sprite Studio Core** — the desktop production application;
2. **optional local AI runtime** — separately installed/adopted WanGP, model checkpoints and supporting Python/PyTorch components.

The Core can be used without installing the AI runtime.

---

## Current R5c7 managed Windows profile

The validated managed runtime plan targets:

- Windows x64;
- Python 3.11.14 for the external WanGP environment;
- PyTorch 2.10.0;
- CUDA-capable NVIDIA execution for the managed local AI path;
- WanGP / Wan2GP as an external runtime;
- Wan 2.2 Animate 14B;
- Krea 2 Turbo.

CUDA Toolkit / `nvcc` is diagnostic and optional for the managed workflow. Actual GPU compatibility is checked through the installed PyTorch runtime and the GPU architectures it supports.

---

## Storage planning

The R5c7 runtime installation plan reserves approximately:

| Component | Installed / reserved size |
| --- | ---: |
| Miniconda + environment bootstrap | 1.5 GiB |
| WanGP + Python/PyTorch/dependencies | 20.0 GiB |
| Wan 2.2 Animate primary checkpoint | 16.7 GiB |
| Shared WanGP encoders / VAE / model assets reserve | 15.0 GiB |
| Krea 2 Turbo checkpoint | 13.5 GiB |
| Workspace / AI output reserve | 20.0 GiB |
| **Subtotal before safety margin** | **86.7 GiB** |

For a complete managed local setup, plan around **at least 100 GB of free disk space**.

This should be treated as a practical starting reserve, not a permanent maximum. Real projects, cached downloads, alternate checkpoints, intermediate video and frame sequences can require substantially more space.

---

## GPU expectations

Local image/video generation is a GPU workload.

The project intentionally does not publish a single arbitrary GPU model or VRAM threshold for every workflow because:

- different models have different memory footprints;
- quantized checkpoints change requirements;
- WanGP can offload model state between VRAM and system RAM;
- resolution changes memory consumption;
- frame count and duration change workload;
- some configurations can technically run but be too slow for useful production.

A modern compatible NVIDIA GPU is therefore strongly recommended for the current managed local AI path, but “supported” and “comfortable” are not the same thing.

Always use the Runtime Health Check to verify the actual GPU ↔ PyTorch architecture contract on the machine in front of you.

---

## System RAM expectations

System RAM matters because low-VRAM/offload strategies move part of the model workload out of GPU memory.

There is no universal RAM minimum published by Sprite Studio for every model/profile combination. More system RAM can make conservative offload strategies possible, but it does not make an underpowered GPU fast.

If a workflow approaches memory limits:

- lower resolution;
- reduce frame count / duration;
- use a more conservative WanGP memory profile;
- adjust reserved-RAM settings carefully;
- close unrelated memory-heavy applications;
- test a smaller run before committing to a long generation.

---

## Generation time

Do not assume local generation is instant.

Time varies with:

- GPU architecture and VRAM;
- system RAM and offload behavior;
- selected checkpoint / quantization;
- image or video resolution;
- frame count;
- generation steps;
- model-specific settings;
- current system load.

High-quality test material can require multiple calibration runs. In a real production session, the time spent finding a stable configuration may be more important than the time spent on the final run.

That is why Sprite Studio preserves profiles, presets and calibration results.

---

## Model-quality expectations

The local models integrated by the current release should not be marketed as equivalent to every frontier proprietary cloud image/video model.

Local downloadable models trade some combination of:

- speed;
- model size;
- hardware demand;
- ease of use;
- raw output quality;
- ecosystem maturity.

The current Sprite Studio workflow is designed around a narrower production target: **controlled 2D asset generation and refinement**, often with a simple/neutral background and a strong visual reference.

For that target, the integrated local models can be highly effective when configured well.

---

## WanGP / Wan2GP

WanGP is a separate external runtime. Sprite Studio does not incorporate it into the GPL-covered Core and does not sublicense it.

The current WanGP Community License contains its own conditions for use, redistribution, outputs and commercialized integrations/wrappers.

In particular, upstream terms should be reviewed again before:

- embedding WanGP in a paid product;
- selling access to WanGP functionality;
- providing paid API/SaaS/hosted access;
- white-labeling or redistributing WanGP commercially;
- materially changing how Sprite Studio and WanGP are packaged together.

A paid distribution of Sprite Studio should not assume that the GPL license of the Core overrides WanGP's separate terms.

Current upstream license:
https://github.com/deepbeepmeep/Wan2GP/blob/main/LICENSE.txt

Also see `THIRD_PARTY_NOTICES.txt`.

---

## Krea 2 Turbo

Krea 2 is optional and separately licensed.

Current upstream references:

- Community License: https://www.krea.ai/krea-2-licensing
- Acceptable Use Policy: https://www.krea.ai/krea-2-use-policy

At the time this document was prepared (August 2026), the Krea 2 Community License:

- permits commercial use only below its stated company-wide trailing-twelve-month revenue threshold;
- requires an Enterprise License when that threshold is reached;
- requires compliance with the Krea Acceptable Use Policy;
- recognizes content-filtering / review safeguards, including human review.

Sprite Studio therefore uses:

1. explicit Krea license/AUP acknowledgement for managed use;
2. a pre-generation compliance attestation;
3. manual review before a generated Krea image can be promoted into the WAN reference pipeline;
4. a minimal local review record without prompt text, tokens or user identity.

Always re-check the current upstream terms before commercial deployment or redistribution.

See `KREA_SAFETY_AND_USE.txt`.

---

## Privacy and credentials

The current local workflows are designed around local execution after required runtime/model downloads.

Never commit or publish:

- Hugging Face tokens;
- API keys;
- private model credentials;
- `.env` files;
- personal runtime paths where they reveal sensitive information;
- generated content that you do not have the right to redistribute.

Future online-provider integrations are planned around **user-owned credentials** rather than credentials embedded in Sprite Studio.

---

## Practical recommendation

Before a long production run:

1. run Runtime Health Check;
2. verify available storage;
3. test the intended resolution with a short/cheap run;
4. observe RAM/VRAM behavior;
5. save the configuration when it proves stable;
6. only then scale duration, frame count or resolution.

The fastest workflow is usually the one you do not have to rediscover twice.
