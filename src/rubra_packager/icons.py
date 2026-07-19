from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

from .security import parse_hex_color

ANDROID_DENSITIES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}


def decode_data_uri(data_uri: str) -> Image.Image:
    if not data_uri.startswith("data:") or "," not in data_uri:
        raise ValueError("Icon must be supplied as a data URI")
    header, payload = data_uri.split(",", 1)
    if ";base64" not in header:
        raise ValueError("Icon data URI must use base64 encoding")
    binary = base64.b64decode(payload, validate=True)
    image = Image.open(io.BytesIO(binary))
    image.load()
    return image.convert("RGBA")


def fit_square(image: Image.Image, size: int, padding_ratio: float = 0.10) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    usable = max(1, round(size * (1 - 2 * padding_ratio)))
    copy = image.copy()
    copy.thumbnail((usable, usable), Image.Resampling.LANCZOS)
    x = (size - copy.width) // 2
    y = (size - copy.height) // 2
    canvas.alpha_composite(copy, (x, y))
    return canvas


def save_windows_ico(image: Image.Image, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fitted = fit_square(image, 256, 0.04)
    fitted.save(path, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return path


def write_android_icons(image: Image.Image, res_dir: Path, background: str = "#071426") -> list[str]:
    background = parse_hex_color(background)
    created: list[str] = []
    for density, size in ANDROID_DENSITIES.items():
        folder = res_dir / f"mipmap-{density}"
        folder.mkdir(parents=True, exist_ok=True)
        legacy = fit_square(image, size, 0.08)
        foreground = fit_square(image, round(size * 1.5), 0.18)
        for name, asset in (("ic_launcher.png", legacy), ("ic_launcher_round.png", legacy), ("ic_launcher_foreground.png", foreground)):
            target = folder / name
            asset.save(target, format="PNG", optimize=True)
            created.append(str(target))

    values = res_dir / "values"
    values.mkdir(parents=True, exist_ok=True)
    colors = values / "ic_launcher_background.xml"
    colors.write_text(
        f'<?xml version="1.0" encoding="utf-8"?>\n<resources><color name="ic_launcher_background">{background}</color></resources>\n',
        encoding="utf-8",
        newline="\n",
    )
    created.append(str(colors))

    for folder_name in ("mipmap-anydpi-v26", "mipmap-anydpi-v33"):
        folder = res_dir / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
            target = folder / name
            target.write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                '  <background android:drawable="@color/ic_launcher_background"/>\n'
                '  <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
                '</adaptive-icon>\n',
                encoding="utf-8",
                newline="\n",
            )
            created.append(str(target))
    return created
