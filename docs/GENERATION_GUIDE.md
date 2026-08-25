# Generation Guide

Local generative models are not deterministic animation engines. They are probabilistic systems that can produce excellent material and still fail on individual details, frames or instructions.

Sprite Studio is designed around that fact.

This guide describes the production habits that have proven most useful with the current local pipeline.

---

## 1. Start from the cleanest source you can

A weak source is not neutral. It gives the model weak information.

Before animation or image-to-image work, inspect:

- silhouette clarity;
- anatomy / object structure;
- face and hands if they matter to identity;
- small accessories that must remain consistent;
- contrast between subject and background;
- existing compression or scaling damage;
- whether the source already contains duplicated, melted or ambiguous details.

Generative motion tends to magnify uncertainty already present in the source.

---

## 2. Avoid contradictory instructions

Structured options and free prompt text should describe the same intended result.

Examples of dangerous contradictions:

- structured camera = fixed, prompt = orbit around the subject;
- motion = subtle, prompt = explosive full-body movement;
- background = neutral/green, prompt = cinematic city environment;
- identity preservation = strict, prompt = transform the character into another creature;
- fixed 3/4 view, prompt = rotate continuously through all directions.

The model may follow one instruction, partially blend both, or fail in a less obvious way.

Prompt Builder helps organize the instruction set. It cannot force a model to obey mutually incompatible goals.

---

## 3. Use modular prompts

Prefer a prompt that clearly separates:

- subject identity;
- action;
- direction / camera;
- motion strength;
- background;
- output purpose;
- technical constraints;
- negative constraints.

This makes it easier to identify which part of the instruction needs to change.

A large unstructured paragraph may look expressive to a human while giving the model several overlapping priorities.

---

## 4. More is not automatically better

Do not assume that increasing all of these together improves quality:

- resolution;
- number of frames;
- number of steps;
- duration;
- guidance / prompt strength;
- precision / memory consumption.

Higher values increase compute and memory pressure and may simply give the model more opportunities to drift.

Establish a stable baseline first. Increase one expensive dimension only when you know why you need it.

---

## 5. Keep backgrounds simple when the final target is a sprite

A simple background helps both the model and the cleanup stage.

Complex scenery can:

- contaminate subject edges;
- introduce moving background detail;
- create colors that are difficult to separate from the subject;
- increase temporal instability;
- make chroma or mask cleanup less reliable.

If the final target is a transparent game asset, visual spectacle in the background is usually wasted information.

---

## 6. Expect identity drift

Identity drift can affect:

- facial structure;
- hands;
- weapons;
- small accessories;
- logos / symbols;
- fabric patterns;
- jewelry;
- exact costume geometry;
- fine texture detail.

The more small mandatory details a subject contains, the more points the model has to preserve over time.

For production tests, start with a strong silhouette and a limited number of identity-critical details.

---

## 7. Treat generation as a test loop

When a run is promising:

1. record it;
2. rate it;
3. preserve the seed where useful;
4. change one parameter;
5. compare the new run against the baseline;
6. promote the better configuration into a Generation Profile or Production Preset.

The Calibration Lab exists to make this process explicit.

The purpose of a preset is not to declare a universal best configuration. It is to preserve a configuration that worked for a specific model, hardware profile and type of material.

---

## 8. A bad frame does not necessarily mean a failed generation

Before regenerating, ask:

- Is the overall motion useful?
- Are enough frames usable?
- Are the defects local rather than structural?
- Can edge contamination be cleaned?
- Can positional drift be aligned?
- Can a broken frame be omitted without damaging timing?

Sprite Studio includes Extraction, frame selection, Clean-up and Alignment specifically because model output is rarely uniformly perfect.

Regeneration is expensive. Salvage can be faster.

---

## 9. Typical failure modes

| Symptom | Likely contributors | First things to try |
| --- | --- | --- |
| Character changes appearance over time | source ambiguity, too much detail, weak identity instruction, excessive motion | simplify source, strengthen identity constraint, reduce motion, shorten test |
| Hands / accessories deform | small-detail instability, difficult pose | simplify test action, improve source, accept/select better frames, repair where practical |
| Background invades the subject edge | complex background, poor chroma separation, similar colors | use a simpler background, improve source separation, clean manually |
| Camera moves despite fixed-camera intent | conflicting prompt text or model drift | remove cinematic/camera language, use explicit fixed-camera constraints |
| Output becomes noisy at higher settings | compute/memory pressure, excessive resolution/frames/steps | return to known baseline and increase one variable at a time |
| Motion is too weak | prompt/action mismatch, conservative motion setting | increase motion deliberately; avoid adding unrelated prompt complexity |
| Motion destroys identity | action too aggressive for the source/model | lower motion, reduce duration, simplify action, strengthen reference |
| Good motion but inconsistent frame placement | temporal/positional drift | use Alignment rather than regenerating immediately |
| Good frame with contaminated alpha | background/mask problem | use Clean-up tools and propagation |

---

## 10. Krea 2 review step

Krea-generated output must be reviewed before it is promoted into the WAN reference pipeline.

This is both a practical and policy-oriented checkpoint:

- inspect whether the image actually matches the intended reference;
- reject obvious artifacts before motion generation;
- verify that the intended use and output comply with the current Krea license and Acceptable Use Policy.

See `KREA_SAFETY_AND_USE.txt` in the repository root.

---

## 11. Original and lawful material

Use material that you have the right to use.

A generative pipeline does not remove copyright, trademark, publicity or other rights that may apply to source material or outputs. Demonstration material in the public Sprite Studio documentation intentionally uses original subjects rather than recognizable third-party characters.

---

## 12. Experimental uses

The pipeline may also be useful for:

- animated props;
- spell / VFX frames;
- environment elements;
- animated textures;
- UI animation material;
- other frame-based 2D assets.

Not all of these have been formally validated by the project. Treat them as experimental workflows rather than guaranteed features.
