#!/usr/bin/env python3
"""Build Omamu theme assets and package a muOS-compatible .muxthm archive."""

from __future__ import annotations

import configparser
import struct
import zlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
RESOLUTION = ROOT / "640x480"
WALLPAPER = RESOLUTION / "image" / "wall" / "default.png"
PREVIEW = RESOLUTION / "preview.png"
OUTPUT = ROOT / "dist" / "Omamu.muxthm"
WIDTH, HEIGHT = 640, 480


def png_chunk(kind: bytes, data: bytes) -> bytes:
    payload = kind + data
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)


def write_png(path: Path, width: int, height: int, pixels: bytearray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stride = width * 3
    raw = b"".join(b"\x00" + pixels[row * stride:(row + 1) * stride] for row in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += png_chunk(b"IHDR", header)
    data += png_chunk(b"IDAT", zlib.compress(raw, 9))
    data += png_chunk(b"IEND", b"")
    path.write_bytes(data)


def draw_wallpaper(width: int, height: int) -> bytearray:
    """Generate a restrained dark grid with an amber focal line, without external assets."""
    pixels = bytearray(width * height * 3)
    for y in range(height):
        for x in range(width):
            # Subtle warm-black gradient.
            lift = int(7 * (1 - y / max(1, height - 1)))
            r, g, b = 15 + lift, 15 + lift, 15 + lift
            # Low-contrast technical grid, deliberately subdued at 640x480.
            if x % 32 == 0 or y % 32 == 0:
                r, g, b = 27 + lift, 26 + lift, 24 + lift
            # Fine amber line near the lower third; not a fake UI element.
            if y == int(height * 0.72) and 48 <= x <= width - 48:
                r, g, b = 184, 119, 42
            index = (y * width + x) * 3
            pixels[index:index + 3] = bytes((r, g, b))
    return pixels


def draw_preview() -> bytearray:
    """Generate a 288x216 preview with simple geometric menu styling."""
    width, height = 288, 216
    pixels = bytearray(width * height * 3)
    for y in range(height):
        for x in range(width):
            lift = int(4 * (1 - y / max(1, height - 1)))
            colour = (16 + lift, 16 + lift, 16 + lift)
            if x % 16 == 0 or y % 16 == 0:
                colour = (27 + lift, 26 + lift, 24 + lift)
            # Amber highlight stripe and three abstract menu rows.
            if 40 <= x < 43 and 66 <= y < 176:
                colour = (240, 170, 69)
            if 52 <= x < 240 and y in (72, 104, 136, 168):
                colour = (76, 69, 58) if y != 104 else (240, 170, 69)
            index = (y * width + x) * 3
            pixels[index:index + 3] = bytes(colour)
    return pixels


def validate() -> None:
    for filename in ("name.txt", "version.txt", "credits.txt"):
        path = ROOT / filename
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise SystemExit(f"Required theme metadata missing or empty: {filename}")

    version = (ROOT / "version.txt").read_text(encoding="utf-8").strip()
    if not all(part.isdigit() for part in version.split(".")) or len(version.split(".")) != 3:
        raise SystemExit("version.txt must use numeric MAJOR.MINOR.PATCH format")

    scheme = ROOT / "scheme" / "global.ini"
    if not scheme.is_file():
        raise SystemExit("Required scheme/global.ini is missing")
    parser = configparser.ConfigParser()
    try:
        parser.read_string(scheme.read_text(encoding="utf-8"))
    except configparser.Error as exc:
        raise SystemExit(f"Invalid INI syntax in {scheme.relative_to(ROOT)}: {exc}") from exc

    for section, key in (("font", "FONT_LIST_SIZE"), ("terminal", "FONT_SIZE"),
                         ("terminal", "FOREGROUND"), ("terminal", "BACKGROUND")):
        if not parser.has_option(section, key):
            raise SystemExit(f"Required documented setting missing: [{section}] {key}")

    for key in ("FOREGROUND", "BACKGROUND"):
        value = parser.get("terminal", key)
        if len(value) != 6 or any(char not in "0123456789abcdefABCDEF" for char in value):
            raise SystemExit(f"[terminal] {key} must be a six-digit hex colour")


def main() -> None:
    validate()
    write_png(WALLPAPER, WIDTH, HEIGHT, draw_wallpaper(WIDTH, HEIGHT))
    write_png(PREVIEW, 288, 216, draw_preview())

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Important: archive the theme contents, not the repository/root directory.
    excluded_parts = {".git", ".github", "scripts", "dist", "__pycache__"}
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if any(part in excluded_parts for part in relative.parts):
                continue
            if path.suffix == ".pyc" or relative.name == "README.md":
                continue
            archive.write(path, relative.as_posix())

    with ZipFile(OUTPUT, "r") as archive:
        names = set(archive.namelist())
        for required in ("name.txt", "version.txt", "credits.txt",
                         "scheme/global.ini", "640x480/preview.png",
                         "640x480/image/wall/default.png"):
            if required not in names:
                raise SystemExit(f"Packaged archive missing required path: {required}")
        if any(name.startswith("Omamu/") for name in names):
            raise SystemExit("Archive incorrectly contains an extra Omamu/ parent folder")

    print(f"Built {OUTPUT.name} ({OUTPUT.stat().st_size} bytes)")
    print("Archive layout and required theme assets validated.")


if __name__ == "__main__":
    main()
