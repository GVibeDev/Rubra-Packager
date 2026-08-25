from pathlib import Path
import sys

root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
message = (root / "assets" / "message.txt").read_text(encoding="utf-8").strip()
print(message)
