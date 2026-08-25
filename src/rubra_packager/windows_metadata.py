from __future__ import annotations

import re
from pathlib import Path


def _single_line(value: str, fallback: str = "") -> str:
    text = (value or fallback).replace("\r", " ").replace("\n", " ").strip()
    return " ".join(text.split())


def version_tuple(value: str) -> tuple[int, int, int, int]:
    """Convert a human/PEP-440-ish version into the four integers used by PE resources."""
    numbers = [int(item) for item in re.findall(r"\d+", value or "")]
    numbers = (numbers + [0, 0, 0, 0])[:4]
    return tuple(max(0, min(65535, item)) for item in numbers)  # type: ignore[return-value]


def write_version_file(
    path: Path,
    *,
    app_name: str,
    version: str,
    publisher: str = "",
    description: str = "",
    original_filename: str | None = None,
) -> Path:
    """Write a deterministic PyInstaller Windows version-resource description."""
    path.parent.mkdir(parents=True, exist_ok=True)
    product = _single_line(app_name, "Application")
    display_version = _single_line(version, "1.0.0")
    company = _single_line(publisher, "")
    file_description = _single_line(description, product)
    filename = _single_line(original_filename or f"{product}.exe", f"{product}.exe")
    numeric = version_tuple(display_version)

    strings = [
        ("CompanyName", company),
        ("FileDescription", file_description),
        ("FileVersion", display_version),
        ("InternalName", product),
        ("OriginalFilename", filename),
        ("ProductName", product),
        ("ProductVersion", display_version),
    ]
    string_rows = ",\n          ".join(
        f"StringStruct({key!r}, {value!r})" for key, value in strings
    )
    source = f"""VSVersionInfo(\n  ffi=FixedFileInfo(\n    filevers={numeric!r},\n    prodvers={numeric!r},\n    mask=0x3f,\n    flags=0x0,\n    OS=0x40004,\n    fileType=0x1,\n    subtype=0x0,\n    date=(0, 0)\n  ),\n  kids=[\n    StringFileInfo([\n      StringTable(\n        '040904B0',\n        [\n          {string_rows}\n        ]\n      )\n    ]),\n    VarFileInfo([VarStruct('Translation', [1033, 1200])])\n  ]\n)\n"""
    path.write_text(source, encoding="utf-8", newline="\n")
    return path
