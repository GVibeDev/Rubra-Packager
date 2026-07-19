# RP-R4 differentiation audit

## Compared snapshots

- Original supplied archive: `HTML2EXE(1).zip`
- Original archive SHA-256: `96b96374cb09f5d5273ec1a98e898b59d099f5e28c673cb844d4781f0921f09c`
- Candidate repository: Rubra Packager RP-R4
- Audit date: 19 July 2026

## Repository shape

| Measure | Original supplied source | Rubra Packager RP-R4 |
|---|---:|---:|
| Non-environment files compared | 11 | 51 |
| Source/document bytes compared | 1,835,528 | 144,920 |
| Python lines | 2,613 in one main file | 1,891 across modules and tests |
| UI lines | 5,084 across original HTML/CSS/JS/API files | 648 across a new HTML/CSS/JS interface |

## Deliberate removals

RP-R4 does not contain:

- the original `.git` history;
- the original `.venv`;
- `builder.py`;
- `builder_ui/`;
- `api.js`;
- the original logo or screenshot assets;
- Python-to-EXE conversion;
- project template creation;
- the original dashboard/color-panel workflow;
- invasive Next.js route/config rewriting.

## New identity and architecture

RP-R4 introduces:

- a `src/rubra_packager/` package;
- a new project registry under the Rubra Packager application-data directory;
- legacy metadata migration without reusing the previous runtime;
- a new profile schema and FULL/LITE staging engine;
- a new preflight implementation;
- separate Windows and Android build modules;
- persistent PyWebView storage for packaged Windows applications;
- a new navy-and-gold interface;
- new documentation, tests, security policy and provenance record.

## Exact-file comparison

Number of byte-identical files between the original non-environment tree and RP-R4: **0**.

No byte-identical files were found.

## Nearest whole-file line similarity

These figures use a whole-file line SequenceMatcher. They are a practical accidental-copy check, not a legal test.

| Original file | Nearest RP-R4 source file | Similarity |
|---|---|---:|
| `builder.py` | `src/rubra_packager/preflight.py` | 1.5% |
| `builder_ui/index.html` | `src/rubra_packager/config.py` | 3.9% |
| `builder_ui/script.js` | `tests/test_security.py` | 1.1% |
| `builder_ui/style.css` | `src/rubra_packager/config.py` | 1.6% |
| `builder_ui/api.js` | `tests/test_icons.py` | 5.1% |
| `README.md` | `src/rubra_packager/config.py` | 8.2% |

No original source/UI file has a high-similarity counterpart in RP-R4.

## Publication conclusion

RP-R4 is structured as a separate implementation rather than a renamed fork. The historical inspiration remains acknowledged in `NOTICE.md` and `PROVENANCE.md`.

This audit is evidence of technical differentiation, not a substitute for legal advice or permission where required.
