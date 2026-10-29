#!/usr/bin/env python3
"""Generate original Omamu artwork and package a muOS theme for 640x480."""

from __future__ import annotations

import configparser
import struct
import zlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
RESOLUTION = ROOT / "640x480"
IMAGE_WALL = RESOLUTION / "image" / "wall"
PREVIEW = RESOLUTION / "preview.png"
OUTPUT = ROOT / "dist" / "Omamu.muxthm"
WIDTH, HEIGHT = 640, 480
MODULES = ("muxlaunch", "muxplore", "muxconfig", "muxcustom", "muxretro")
BG = (16, 16, 16)
GRID = (28, 27, 24)
AMBER = (232, 168, 74)
CREAM = (244, 240, 232)
MUTED = (116, 108, 96)


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


def set_pixel(pixels: bytearray, width: int, x: int, y: int, colour: tuple[int, int, int]) -> None:
    if 0 <= x < width and 0 <= y < len(pixels) // (width * 3):
        offset = (y * width + x) * 3
        pixels[offset:offset + 3] = bytes(colour)


def line(pixels: bytearray, width: int, x1: int, y1: int, x2: int, y2: int,
         colour: tuple[int, int, int], thickness: int = 1) -> None:
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    while True:
        radius = thickness // 2
        for oy in range(-radius, radius + 1):
            for ox in range(-radius, radius + 1):
                set_pixel(pixels, width, x1 + ox, y1 + oy, colour)
        if x1 == x2 and y1 == y2:
            break
        twice = 2 * err
        if twice > -dy:
            err -= dy
            x1 += sx
        if twice < dx:
            err += dx
            y1 += sy


def rectangle(pixels: bytearray, width: int, x: int, y: int, w: int, h: int,
              colour: tuple[int, int, int], filled: bool = False) -> None:
    if filled:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                set_pixel(pixels, width, xx, yy, colour)
    else:
        line(pixels, width, x, y, x + w - 1, y, colour)
        line(pixels, width, x, y + h - 1, x + w - 1, y + h - 1, colour)
        line(pixels, width, x, y, x, y + h - 1, colour)
        line(pixels, width, x + w - 1, y, x + w - 1, y + h - 1, colour)


def draw_wallpaper(module: str = "default") -> bytearray:
    """Warm black, hairline grid, amber marker and subtle technical framing."""
    pixels = bytearray(WIDTH * HEIGHT * 3)
    for y in range(HEIGHT):
        lift = int(4 * (1 - y / (HEIGHT - 1)))
        for x in range(WIDTH):
            shade = (BG[0] + lift, BG[1] + lift, BG[2] + lift)
            if x % 32 == 0 or y % 32 == 0:
                shade = (GRID[0] + lift, GRID[1] + lift, GRID[2] + lift)
            # Quiet corner falloff gives the flat handheld screen a little depth.
            edge = min(x, WIDTH - 1 - x, y, HEIGHT - 1 - y)
            if edge < 10:
                shade = tuple(max(0, channel - (10 - edge) // 2) for channel in shade)
            offset = (y * WIDTH + x) * 3
            pixels[offset:offset + 3] = bytes(shade)

    # Asymmetric accent marks echo Omarchy's restrained terminal/editor palette.
    accent_x = {"default": 48, "muxlaunch": 48, "muxplore": 586,
                "muxconfig": 64, "muxcustom": 576, "muxretro": 48}.get(module, 48)
    line(pixels, WIDTH, accent_x, 76, accent_x, 392, AMBER, 2)
    line(pixels, WIDTH, 48, 346, 592, 346, (64, 48, 29), 1)
    # Broken registration marks; intentionally low contrast, not fake UI text.
    for x in range(80, 560, 32):
        if (x // 32) % 3 == 0:
            line(pixels, WIDTH, x, 70, x + 7, 70, (74, 57, 35), 1)
    # Fine amber ticks make the accent feel like a technical instrument panel.
    for y in range(88, 392, 24):
        line(pixels, WIDTH, accent_x - 4, y, accent_x + 4, y, AMBER, 1)
    return pixels


def draw_preview() -> bytearray:
    """A legible miniature mock-up of the intended dark, amber muOS layout."""
    width, height = 288, 216
    pixels = bytearray(width * height * 3)
    for y in range(height):
        for x in range(width):
            colour = (16, 16, 16)
            if x % 16 == 0 or y % 16 == 0:
                colour = (27, 26, 24)
            offset = (y * width + x) * 3
            pixels[offset:offset + 3] = bytes(colour)

    rectangle(pixels, width, 0, 0, width, 23, (18, 18, 17), True)
    line(pixels, width, 0, 23, width - 1, 23, (72, 54, 33))
    line(pixels, width, 15, 40, 15, 184, AMBER, 2)
    # Minimal wordmark bars instead of tiny illegible rasterised text.
    rectangle(pixels, width, 27, 8, 45, 3, CREAM, True)
    rectangle(pixels, width, 27, 14, 27, 2, AMBER, True)
    rectangle(pixels, width, 235, 9, 35, 3, AMBER, True)
    for index, y in enumerate((47, 78, 109, 140, 171)):
        focused = index == 1
        fill = (48, 39, 25) if focused else (24, 23, 21)
        rectangle(pixels, width, 27, y, 225, 23, fill, True)
        if focused:
            rectangle(pixels, width, 27, y, 3, 23, AMBER, True)
            rectangle(pixels, width, 39, y + 10, 76, 3, CREAM, True)
        else:
            rectangle(pixels, width, 39, y + 10, 64 + (index % 2) * 18, 2, MUTED, True)
        rectangle(pixels, width, 252, y + 8, 3, 7, AMBER if focused else (69, 60, 45), True)
    line(pixels, width, 0, 197, width - 1, 197, (55, 46, 32))
    rectangle(pixels, width, 18, 206, 26, 2, AMBER, True)
    rectangle(pixels, width, 53, 206, 35, 2, MUTED, True)
    rectangle(pixels, width, 225, 206, 43, 2, MUTED, True)
    return pixels


def write_glyphs() -> None:
    """Create simple original line glyphs for the eight main-menu destinations."""
    glyph_root = RESOLUTION / "glyph" / "muxlaunch"
    glyph_root.mkdir(parents=True, exist_ok=True)
    paths = {
        "apps": '<rect x="4" y="4" width="7" height="7"/><rect x="13" y="4" width="7" height="7"/><rect x="4" y="13" width="7" height="7"/><rect x="13" y="13" width="7" height="7"/>',
        "collection": '<path d="M3 7h7l2 2h9v10H3z"/><path d="M3 7V5h7l2 2"/>',
        "config": '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2"/><circle cx="15" cy="12" r="2"/><circle cx="8" cy="18" r="2"/>',
        "explore": '<circle cx="10" cy="10" r="6"/><path d="m14.5 14.5 5 5M8 12l4-4"/>',
        "history": '<path d="M4 7V3M4 7h4"/><path d="M4.5 7a8 8 0 1 1-1 6"/><path d="M12 7v5l3 2"/>',
        "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
        "reboot": '<path d="M12 3v9"/><path d="M7 5.5a8 8 0 1 0 10 0"/>',
        "shutdown": '<path d="M12 3v9"/><path d="M7 5.5a8 8 0 1 0 10 0"/>',
    }
    for name, body in paths.items():
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
            '<g fill="none" stroke="#E8A84A" stroke-width="1.6" stroke-linecap="square" '
            'stroke-linejoin="miter">' + body + '</g></svg>'
        )
        (glyph_root / f"{name}.svg").write_text(svg + "\n", encoding="utf-8")


def validate() -> None:
    for filename in ("name.txt", "version.txt", "credits.txt"):
        path = ROOT / filename
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise SystemExit(f"Required theme metadata missing or empty: {filename}")

    version = (ROOT / "version.txt").read_text(encoding="utf-8").strip()
    if len(version.split(".")) != 3 or not all(part.isdigit() for part in version.split(".")):
        raise SystemExit("version.txt must use numeric MAJOR.MINOR.PATCH format")

    schemes = [ROOT / "scheme" / "global.ini", RESOLUTION / "scheme" / "default.ini"]
    schemes.extend(RESOLUTION / "scheme" / f"{module}.ini" for module in MODULES)
    for scheme in schemes:
        if not scheme.is_file():
            raise SystemExit(f"Required scheme missing: {scheme.relative_to(ROOT)}")
        parser = configparser.ConfigParser(interpolation=None, strict=True)
        try:
            parser.read_string(scheme.read_text(encoding="utf-8"))
        except configparser.Error as exc:
            raise SystemExit(f"Invalid INI syntax in {scheme.relative_to(ROOT)}: {exc}") from exc

    font = RESOLUTION / "font" / "default.ttf"
    font_license = RESOLUTION / "font" / "OFL.txt"
    if not font.is_file() or font.stat().st_size < 10000:
        raise SystemExit("JetBrains Mono font is missing or unexpectedly small")
    if not font_license.is_file() or not font_license.read_text(encoding="utf-8").strip():
        raise SystemExit("JetBrains Mono OFL license is missing")

    global_parser = configparser.ConfigParser(interpolation=None)
    global_parser.read(ROOT / "scheme" / "global.ini", encoding="utf-8")
    for section, key in (("font", "FONT_LIST_SIZE"), ("terminal", "FONT_SIZE"),
                         ("terminal", "FOREGROUND"), ("terminal", "BACKGROUND")):
        if not global_parser.has_option(section, key):
            raise SystemExit(f"Required documented setting missing: [{section}] {key}")
    for key in ("FOREGROUND", "BACKGROUND"):
        value = global_parser.get("terminal", key)
        if len(value) != 6 or any(char not in "0123456789abcdefABCDEF" for char in value):
            raise SystemExit(f"[terminal] {key} must be a six-digit hex colour")


def main() -> None:
    validate()
    write_png(IMAGE_WALL / "default.png", WIDTH, HEIGHT, draw_wallpaper())
    for module in MODULES:
        write_png(IMAGE_WALL / f"{module}.png", WIDTH, HEIGHT, draw_wallpaper(module))
    write_png(PREVIEW, 288, 216, draw_preview())
    write_glyphs()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
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
        required = [
            "name.txt", "version.txt", "credits.txt", "scheme/global.ini",
            "640x480/scheme/default.ini", "640x480/preview.png",
            "640x480/image/wall/default.png",
            "640x480/glyph/muxlaunch/explore.svg",
            "640x480/font/default.ttf", "640x480/font/OFL.txt",
        ]
        required.extend(f"640x480/scheme/{module}.ini" for module in MODULES)
        required.extend(f"640x480/image/wall/{module}.png" for module in MODULES)
        for item in required:
            if item not in names:
                raise SystemExit(f"Packaged archive missing required path: {item}")
        if any(name.startswith("Omamu/") for name in names):
            raise SystemExit("Archive incorrectly contains an extra Omamu/ parent folder")

    print(f"Built {OUTPUT.name} ({OUTPUT.stat().st_size} bytes)")
    print(f"Validated metadata, {len(MODULES) + 2} scheme files, wallpapers, glyphs and archive layout.")


if __name__ == "__main__":
    main()
