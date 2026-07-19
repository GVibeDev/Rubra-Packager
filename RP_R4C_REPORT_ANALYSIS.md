# RP-R4c Analysis of Arena Rubra Preflight Report

- Profile: `arena-rubra/full`
- Files scanned/included: 707/707
- Bytes included: 166608193
- RP-R4b blocking findings: 32
- Warnings: 1

## Blocking findings by source

- `src/card_editor.js`: 10
- `src/events.js`: 2
- `src/map_skins.js`: 11
- `src/render.js`: 1
- `src/stats.js`: 2
- `src/storage.js`: 2
- `tests/f9o1_theme_audio_integration_smoke.js`: 2
- `tests/f9o1b_music_controls_smoke.js`: 1
- `tests/f9o2_camera_interaction_smoke.js`: 1

## Conclusion

All 32 findings are invalid as blocking errors:

- generic JavaScript expressions such as `Array.from(...)`, Blob/Data URL values and function arguments were parsed as file imports;
- runtime-composed map and token paths were resolved relative to the JavaScript module instead of their configured asset root;
- test fixtures were treated as runtime dependencies;
- six named map backgrounds, the audio track and `src/camera_interaction.js` are visibly present in `included_paths`;
- `tactical_blueprint.webp` is dynamic/optional and cannot be declared mandatory without a manifest.

RP-R4c therefore narrows blocking analysis to references with deterministic browser semantics. Dynamic required assets should be declared in the optional manifest.
