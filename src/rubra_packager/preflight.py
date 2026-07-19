from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

from .models import BuildProfile, Finding, PreflightReport
from .staging import should_skip

TEXT_EXTENSIONS = {
    ".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".json", ".xml", ".svg", ".txt", ".md", ".csv"
}
REFERENCE_SCAN_EXCLUDED_ROOTS = {".git", "docs", "node_modules", "tests"}
EXTERNAL_PREFIXES = ("http://", "https://", "//")
LOCAL_SCHEME_PREFIXES = ("data:", "blob:", "mailto:", "tel:", "javascript:", "about:")

HTML_ATTRIBUTE_PATTERN = re.compile(
    r"\b(?:src|href|poster|data)\s*=\s*[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)
HTML_SRCSET_PATTERN = re.compile(r"\bsrcset\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
CSS_URL_PATTERN = re.compile(r"url\(\s*[\"']?([^\"')]+)[\"']?\s*\)", re.IGNORECASE)
CSS_IMPORT_PATTERN = re.compile(
    r"@import\s+(?:url\(\s*)?[\"']([^\"']+)[\"']\s*\)?",
    re.IGNORECASE,
)
JS_STATIC_IMPORT_PATTERN = re.compile(
    r"(?m)^\s*import\s+(?:[^\"'\n;]+?\s+from\s+)?[\"']([^\"']+)[\"']"
)
JS_EXPORT_FROM_PATTERN = re.compile(
    r"(?m)^\s*export\s+[^\"'\n;]+?\s+from\s+[\"']([^\"']+)[\"']"
)
JS_DYNAMIC_IMPORT_PATTERN = re.compile(
    r"\bimport\s*\(\s*[\"']([^\"']+)[\"']\s*\)"
)
JS_IMPORT_META_URL_PATTERN = re.compile(
    r"\bnew\s+URL\s*\(\s*[\"']([^\"']+)[\"']\s*,\s*import\.meta\.url\s*\)"
)


def _files(source: Path) -> list[Path]:
    return [path for path in sorted(source.rglob("*")) if path.is_file()]


def _strip_query_fragment(raw: str) -> str:
    value = raw.strip()
    for separator in ("#", "?"):
        value = value.split(separator, 1)[0]
    return unquote(value.strip())


def _is_dynamic_reference(raw: str) -> bool:
    return any(token in raw for token in ("${", "{{", "}}", "<%", "%>"))


def _is_external(raw: str) -> bool:
    lowered = raw.casefold()
    return lowered.startswith(EXTERNAL_PREFIXES)


def _is_ignored_scheme(raw: str) -> bool:
    lowered = raw.casefold()
    return lowered.startswith(LOCAL_SCHEME_PREFIXES) or raw.startswith("#")


def _is_local_js_specifier(raw: str) -> bool:
    # Browsers treat any non-dot, non-root module specifier as a bare package or
    # import-map key. It is not a file path relative to the current module.
    return raw.startswith(("./", "../", "/"))


def _scan_references(relative: str, text: str) -> list[tuple[str, str]]:
    path = Path(relative)
    if path.parts and path.parts[0].casefold() in REFERENCE_SCAN_EXCLUDED_ROOTS:
        return []

    suffix = path.suffix.casefold()
    found: list[tuple[str, str]] = []

    if suffix in {".html", ".htm"}:
        for match in HTML_ATTRIBUTE_PATTERN.finditer(text):
            found.append((match.group(1), "document"))
        for match in HTML_SRCSET_PATTERN.finditer(text):
            for candidate in match.group(1).split(","):
                raw = candidate.strip().split(None, 1)[0] if candidate.strip() else ""
                if raw:
                    found.append((raw, "document"))
        return found

    if suffix == ".css":
        for pattern in (CSS_URL_PATTERN, CSS_IMPORT_PATTERN):
            for match in pattern.finditer(text):
                found.append((match.group(1), "document"))
        return found

    if suffix in {".js", ".mjs", ".cjs"}:
        for pattern in (
            JS_STATIC_IMPORT_PATTERN,
            JS_EXPORT_FROM_PATTERN,
            JS_DYNAMIC_IMPORT_PATTERN,
            JS_IMPORT_META_URL_PATTERN,
        ):
            for match in pattern.finditer(text):
                raw = match.group(1)
                if _is_local_js_specifier(raw):
                    found.append((raw, "module"))
        return found

    # JSON, XML, SVG, TXT, Markdown and CSV are still checked for UTF-8, but
    # generic prose or data strings are not interpreted as executable paths.
    return []


def _candidate_path(base_file: Path, source: Path, raw: str) -> Path | None:
    raw = _strip_query_fragment(raw)
    if not raw or _is_dynamic_reference(raw) or _is_ignored_scheme(raw) or _is_external(raw):
        return None
    if raw.startswith("/"):
        return (source / raw.lstrip("/")).resolve()
    return (base_file.parent / raw).resolve()


def _existing_candidate(candidate: Path) -> Path | None:
    if candidate.is_file():
        return candidate

    if not candidate.suffix:
        for extension in (".js", ".mjs", ".cjs", ".json", ".css", ".html"):
            extended = candidate.with_suffix(extension)
            if extended.is_file():
                return extended
        if candidate.is_dir():
            for filename in ("index.js", "index.mjs", "index.cjs", "index.json", "index.html"):
                indexed = candidate / filename
                if indexed.is_file():
                    return indexed
    return None


def _manifest_paths(data: object) -> list[str]:
    paths: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key.casefold() in {"path", "src", "file", "asset"} and isinstance(value, str):
                paths.append(value)
            else:
                paths.extend(_manifest_paths(value))
    elif isinstance(data, list):
        for value in data:
            paths.extend(_manifest_paths(value))
    return paths


def _append_unique(findings: list[Finding], seen: set[tuple[str, str, str, str | None]], finding: Finding) -> None:
    key = (finding.severity, finding.code, finding.message, finding.path)
    if key not in seen:
        seen.add(key)
        findings.append(finding)


def run_preflight(source: Path, profile: BuildProfile, variant_id: str | None = None) -> PreflightReport:
    source = source.resolve()
    variant = profile.variant(variant_id)
    all_files = _files(source)
    included: list[str] = []
    excluded: list[str] = []
    findings: list[Finding] = []
    seen_findings: set[tuple[str, str, str, str | None]] = set()
    case_map: dict[str, list[str]] = defaultdict(list)

    for path in all_files:
        relative = path.relative_to(source).as_posix()
        case_map[relative.casefold()].append(relative)
        if should_skip(relative, variant):
            excluded.append(relative)
        else:
            included.append(relative)

    included_set = set(included)
    excluded_set = set(excluded)

    for required in profile.required_paths:
        if required not in included_set:
            _append_unique(
                findings,
                seen_findings,
                Finding("error", "REQUIRED_PATH_MISSING", f"Required path is missing: {required}", required),
            )

    for values in case_map.values():
        if len(values) > 1:
            _append_unique(
                findings,
                seen_findings,
                Finding("error", "CASE_COLLISION", f"Case-insensitive filename collision: {', '.join(values)}"),
            )

    for relative in included:
        path = source / relative
        if len(str(path)) > 230:
            _append_unique(
                findings,
                seen_findings,
                Finding("warning", "LONG_PATH", "Path may exceed conservative Windows tooling limits", relative),
            )
        if path.stat().st_size > 50 * 1024 * 1024:
            _append_unique(
                findings,
                seen_findings,
                Finding("warning", "LARGE_FILE", f"Single asset is {path.stat().st_size / 1048576:.1f} MB", relative),
            )
        if path.suffix.casefold() not in TEXT_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            _append_unique(
                findings,
                seen_findings,
                Finding("error", "INVALID_UTF8", "Text file is not valid UTF-8", relative),
            )
            continue

        for raw, _kind in _scan_references(relative, text):
            if _is_external(raw):
                _append_unique(
                    findings,
                    seen_findings,
                    Finding("warning", "EXTERNAL_RESOURCE", f"External resource may break offline use: {raw}", relative),
                )
                continue

            candidate = _candidate_path(path, source, raw)
            if candidate is None:
                continue
            try:
                candidate.relative_to(source)
            except ValueError:
                _append_unique(
                    findings,
                    seen_findings,
                    Finding("error", "REFERENCE_ESCAPE", f"Reference leaves project root: {raw}", relative),
                )
                continue

            existing = _existing_candidate(candidate)
            if existing is None:
                _append_unique(
                    findings,
                    seen_findings,
                    Finding("error", "REFERENCE_MISSING", f"Referenced file not found: {raw}", relative),
                )
                continue

            existing_relative = existing.relative_to(source).as_posix()
            if existing_relative in excluded_set:
                _append_unique(
                    findings,
                    seen_findings,
                    Finding("error", "REFERENCE_EXCLUDED", f"Variant excludes referenced file: {raw}", relative),
                )

    manifest = next((source / name for name in profile.manifest_candidates if (source / name).is_file()), None)
    if manifest is None and profile.manifest_candidates:
        _append_unique(
            findings,
            seen_findings,
            Finding("warning", "MANIFEST_NOT_FOUND", "No optional asset manifest was found"),
        )
    elif manifest is not None:
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            for raw in _manifest_paths(data):
                if _is_external(raw):
                    continue
                candidate = (source / _strip_query_fragment(raw)).resolve()
                try:
                    rel = candidate.relative_to(source).as_posix()
                except ValueError:
                    _append_unique(
                        findings,
                        seen_findings,
                        Finding("error", "MANIFEST_ESCAPE", f"Manifest path leaves project root: {raw}", manifest.name),
                    )
                    continue
                if not candidate.exists():
                    _append_unique(
                        findings,
                        seen_findings,
                        Finding("error", "MANIFEST_ASSET_MISSING", f"Manifest asset missing: {raw}", rel),
                    )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _append_unique(
                findings,
                seen_findings,
                Finding("error", "MANIFEST_INVALID", f"Asset manifest is not valid UTF-8 JSON: {exc}", manifest.name),
            )

    return PreflightReport(
        profile_id=profile.profile_id,
        variant_id=variant.variant_id,
        source_path=str(source),
        scanned_files=len(all_files),
        included_files=len(included),
        excluded_files=len(excluded),
        included_bytes=sum((source / relative).stat().st_size for relative in included),
        findings=findings,
        included_paths=included,
        excluded_paths=excluded,
    )
