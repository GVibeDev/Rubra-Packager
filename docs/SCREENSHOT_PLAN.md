# Public Screenshot Plan

The repository should eventually show only a small number of strong screenshots.

Target: **one banner + three real R5c7 application captures**.

All demonstration subjects should be original and should not imitate recognizable third-party characters or brands.

---

## Screenshot 1 — Image Generation

### Purpose
Show that Sprite Studio includes a real local image-generation workflow while remaining visibly a production tool rather than a single prompt box.

### Subject
**Original pixel/chibi explorer**

Suggested concept:

- small dungeon courier / mechanical scout;
- readable silhouette;
- compact backpack or lantern as one identity anchor;
- 4–6 dominant colors;
- neutral background;
- no resemblance to a known franchise.

### Capture
Show:

- Image Generation workspace;
- relevant generation controls;
- the generated output clearly visible;
- no tokens or credentials;
- no personal filesystem paths;
- a clean project/profile name suitable for public screenshots.

---

## Screenshot 2 — Clean-up

### Purpose
Show the part of the suite that most clearly distinguishes a production pipeline from a raw AI frontend.

### Subject
**Original normal-proportion toon character**

Suggested concept:

- retro-tech scavenger / alchemist courier;
- strong silhouette;
- simple outfit with two or three identity-critical details;
- one prop such as a lantern, satchel or short staff;
- neutral/chroma-friendly background.

This should also be the **single subject used for the demonstration video**, because normal proportions make temporal identity drift and cleanup work easy to understand.

### Capture
Use a real generated frame with a defect that is worth repairing rather than a deliberately destroyed image.

Show:

- checkerboard / transparency or mask result;
- selected frame;
- Clean-up controls;
- a visible before/after quality improvement if possible;
- enough of the UI to communicate that the frame belongs to a sequence.

---

## Screenshot 3 — Character Set / Layer Manager

### Purpose
Show scalability: Sprite Studio is intended for repeated production across animations and directions, not only one isolated sprite.

### Subject
**Original HD / illustrated guardian** or the toon subject after enough directions/animations have been produced.

Suggested standalone HD concept:

- retro-futurist guardian / occult artificer;
- cloth + metal + one clearly readable accessory;
- original insignia;
- restrained detail density so the model has a realistic chance of preserving identity.

### Capture
Prefer Character Set / Layer Manager with:

- subject visible;
- multiple animation/direction slots populated;
- clear direction matrix;
- layer information if it improves readability;
- no test junk or private local paths.

If the Character Set screenshot becomes too visually dense, use **Guided Workflows** as the fallback third screenshot.

---

## Why not Prompt Builder as one of the main three?

Prompt Builder is functionally important, but a public screenshot of forms/text fields communicates less quickly than Generation, Clean-up and Character Set.

It should appear in tutorial material or a secondary documentation image later.

---

## Capture checklist

Before every public screenshot or video clip:

- use an original subject;
- hide/remove personal paths and usernames;
- never show Hugging Face tokens, API keys or credentials;
- use neutral project/profile names;
- close unrelated applications and notifications;
- use a consistent application window size where practical;
- avoid Windows taskbar/desktop clutter unless it is intentionally part of a tutorial;
- capture the actual R5c7 workflow, not a mockup;
- prefer a real useful output over a spectacular but unrepeatable output;
- keep the raw capture so future crops can be produced without rerunning generation.

---

## Tutorial capture

While producing the screenshot material, record the generation session if possible.

Useful future tutorial fragments include:

- creating a prompt profile;
- loading/creating a reference;
- changing a generation setting and comparing results;
- extracting frames;
- rejecting bad frames;
- cleaning a mask edge;
- aligning a sequence;
- assigning an animation/direction in Character Set;
- exporting the final spritesheet.

The tutorial should show that iteration is normal rather than pretending the first generation is always the final asset.
