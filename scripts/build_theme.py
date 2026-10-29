#!/usr/bin/env python3
"""Generate original Omamu artwork and package a muOS theme for 640x480."""

from __future__ import annotations

import configparser
import struct
import subprocess
import zlib
from pathlib import Path
from PIL import Image, ImageOps
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
RESOLUTION = ROOT / "640x480"
IMAGE_WALL = RESOLUTION / "image" / "wall"
PREVIEW = RESOLUTION / "preview.png"
OUTPUT = ROOT / "dist" / "Omamu.muxthm"
WIDTH, HEIGHT = 640, 480
MODULES = ("muxlaunch", "muxplore", "muxconfig", "muxcustom", "muxretro", "muxapp")
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
    # Eight compact grid cells with chunky, pixel-inspired glyph marks.
    cell_w, cell_h, gap_x, gap_y = 59, 67, 7, 7
    start_x, start_y = 10, 34
    for index in range(8):
        col, row = index % 4, index // 4
        x, y = start_x + col * (cell_w + gap_x), start_y + row * (cell_h + gap_y)
        focused = index == 1
        fill = (48, 39, 25) if focused else (24, 23, 21)
        border = AMBER if focused else (81, 64, 42)
        rectangle(pixels, width, x, y, cell_w, cell_h, fill, True)
        rectangle(pixels, width, x, y, cell_w, 1, border, True)
        rectangle(pixels, width, x, y + cell_h - 1, cell_w, 1, border, True)
        rectangle(pixels, width, x, y, 1, cell_h, border, True)
        rectangle(pixels, width, x + cell_w - 1, y, 1, cell_h, border, True)
        gx, gy = x + 23, y + 13
        # Different block patterns keep the eight destinations visually distinct.
        if index == 0:
            for dx, dy in ((0,0),(8,0),(0,8),(8,8)): rectangle(pixels,width,gx+dx,gy+dy,6,6,AMBER if focused else CREAM,True)
        elif index == 1:
            rectangle(pixels,width,gx,gy+3,18,13,AMBER if focused else CREAM,True)
            rectangle(pixels,width,gx+4,gy,8,4,AMBER if focused else CREAM,True)
        elif index == 2:
            rectangle(pixels,width,gx+5,gy,7,7,AMBER if focused else CREAM,True)
            rectangle(pixels,width,gx+2,gy+7,13,3,AMBER if focused else CREAM,True)
            rectangle(pixels,width,gx+5,gy+10,7,5,AMBER if focused else CREAM,True)
        elif index == 3:
            for dx,dy in ((0,0),(8,0),(0,8),(8,8)): rectangle(pixels,width,gx+dx,gy+dy,6,6,AMBER if focused else CREAM,True)
        elif index == 4:
            rectangle(pixels,width,gx,gy+3,18,3,AMBER if focused else CREAM,True)
            rectangle(pixels,width,gx,gy+9,18,3,AMBER if focused else CREAM,True)
            rectangle(pixels,width,gx,gy+15,18,3,AMBER if focused else CREAM,True)
        elif index == 5:
            rectangle(pixels,width,gx+6,gy,6,6,AMBER if focused else CREAM,True)
            rectangle(pixels,width,gx+6,gy+8,6,10,AMBER if focused else CREAM,True)
        elif index == 6:
            rectangle(pixels,width,gx+7,gy,4,11,AMBER if focused else CREAM,True)
            rectangle(pixels,width,gx+2,gy+9,14,4,AMBER if focused else CREAM,True)
        else:
            rectangle(pixels,width,gx+7,gy,4,11,AMBER if focused else CREAM,True)
            rectangle(pixels,width,gx+2,gy+9,14,4,AMBER if focused else CREAM,True)
        rectangle(pixels, width, x + 9, y + 43, 27 + (index % 3) * 4, 2, CREAM if focused else MUTED, True)
        rectangle(pixels, width, x + 9, y + 49, 19 + (index % 2) * 7, 2, AMBER if focused else MUTED, True)
    line(pixels, width, 0, 197, width - 1, 197, (55, 46, 32))
    rectangle(pixels, width, 18, 206, 26, 2, AMBER, True)
    rectangle(pixels, width, 53, 206, 35, 2, MUTED, True)
    rectangle(pixels, width, 225, 206, 43, 2, MUTED, True)
    return pixels



def draw_submenu_wallpaper() -> Image.Image:
    """Create the original near-black grid background used for secondary screens."""
    pixels = bytearray(WIDTH * HEIGHT * 3)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            # Subtle 32 px grid, matching the project's original dark-grid concept.
            colour = GRID if x % 32 == 0 or y % 32 == 0 else BG
            offset = (y * WIDTH + x) * 3
            pixels[offset:offset + 3] = bytes(colour)

    image = Image.frombytes("RGB", (WIDTH, HEIGHT), bytes(pixels))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    # Restrained amber HUD corners keep the grid atmospheric without competing with menus.
    amber = AMBER
    for x0, y0, x1, y1 in ((24, 30, 62, 30), (24, 30, 24, 92),
                            (578, 30, 616, 30), (616, 30, 616, 92)):
        draw.line((x0, y0, x1, y1), fill=amber, width=2)
    for y in (104, 112, 120):
        draw.rectangle((24, y, 26, y + 2), fill=amber)
        draw.rectangle((613, y, 615, y + 2), fill=amber)
    return image


def prepare_wallpapers() -> None:
    """Use the planet on the main menu and the original dark grid on submenu screens."""
    source = ROOT / "Pixel Planet Over a Misty Horizon.png"
    if not source.is_file():
        raise SystemExit(f"Source wallpaper missing: {source.name}")
    IMAGE_WALL.mkdir(parents=True, exist_ok=True)
    grid = draw_submenu_wallpaper()
    grid.save(IMAGE_WALL / "default.png", format="PNG", optimize=True)
    with Image.open(source) as artwork:
        artwork = ImageOps.fit(artwork.convert("RGB"), (WIDTH, HEIGHT),
                               method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        artwork.save(IMAGE_WALL / "muxlaunch.png", format="PNG", optimize=True)
    # Remove the misplaced full-size PNGs; muxlaunch icons belong in glyph/muxlaunch
    # so muOS renders them inside each native grid tile.
    icon_dir = IMAGE_WALL / "muxlaunch"
    for item in ("explore", "collection", "history", "apps", "info", "config", "reboot", "shutdown"):
        (icon_dir / f"{item}.png").unlink(missing_ok=True)
    if icon_dir.exists() and not any(icon_dir.iterdir()):
        icon_dir.rmdir()
    for module in MODULES:
        if module == "muxlaunch":
            continue
        grid.save(IMAGE_WALL / f"{module}.png", format="PNG", optimize=True)


def write_wallpaper_videos() -> None:
    """Preserve the existing muOS wallpaper video paths using the existing artwork."""
    main_video = IMAGE_WALL / "muxlaunch.mp4"
    background_video = RESOLUTION / "image" / "background.mp4"
    background_video.parent.mkdir(parents=True, exist_ok=True)
    common = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-framerate", "12",
    ]
    options = [
        "-t", "6", "-vf",
        "drawbox=x='mod(t*10,640)':y=0:w=2:h=480:color=0xe8a84a@0.13:t=fill,format=yuv420p",
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "30",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    ]
    subprocess.run(common + ["-i", str(IMAGE_WALL / "muxlaunch.png")] + options + [str(main_video)], check=True)
    subprocess.run(common + ["-i", str(IMAGE_WALL / "default.png")] + options + [str(background_video)], check=True)


def write_glyphs() -> None:
    """Write filled, block-based pixel glyphs using the documented muOS filenames."""
    glyph_root = RESOLUTION / "glyph" / "muxlaunch"
    glyph_root.mkdir(parents=True, exist_ok=True)
    # Filled rectangular blocks avoid thin SVG strokes disappearing in the grid renderer.
    patterns = {
        "apps": [(4,4,6,6),(14,4,6,6),(4,14,6,6),(14,14,6,6)],
        "collection": [(3,6,18,3),(3,9,3,10),(6,16,12,3),(18,9,3,10),(7,3,8,3),(10,12,7,3)],
        "config": [(3,4,18,3),(3,11,18,3),(3,18,18,3),(7,2,3,7),(14,9,3,7),(6,16,3,7)],
        "explore": [(4,3,10,3),(2,6,3,9),(14,6,3,8),(5,15,9,3),(16,15,5,3),(17,17,3,4),(8,8,3,3),(11,11,3,3)],
        "history": [(5,3,3,4),(2,6,5,3),(4,9,3,7),(7,16,4,3),(11,18,6,3),(17,15,3,4),(18,8,3,6),(12,5,3,8)],
        "info": [(10,3,5,5),(10,10,5,8),(10,20,5,3)],
        "reboot": [(10,2,5,10),(5,5,4,3),(3,8,3,7),(5,15,4,4),(9,18,7,3),(16,15,4,4),(18,8,3,7),(15,5,4,3)],
        "shutdown": [(10,2,5,10),(5,5,4,3),(3,8,3,7),(5,15,4,4),(9,18,7,3),(16,15,4,4),(18,8,3,7),(15,5,4,3)],
    }
    for name, blocks in patterns.items():
        # Use simple filled rect elements, matching the conservative SVG subset used by muOS glyphs.
        rects = "".join(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#F4F0E8"/>'
            for x, y, w, h in blocks
        )
        svg = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" '
            'viewBox="0 0 24 24" shape-rendering="crispEdges">'
            f'{rects}</svg>'
        )
        (glyph_root / f"{name}.svg").write_text(svg + chr(10), encoding="utf-8")


def validate() -> None:
    for filename in ("name.txt", "version.txt", "credits.txt"):
        path = ROOT / filename
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise SystemExit(f"Required theme metadata missing or empty: {filename}")

    version = (ROOT / "version.txt").read_text(encoding="utf-8").strip()
    if len(version.split(".")) not in (2, 3) or not all(part.isdigit() for part in version.split(".")):
        raise SystemExit("version.txt must use the numeric muOS release format (for example 2606.0)")

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

    if not (ROOT / "Pixel Planet Over a Misty Horizon.png").is_file():
        raise SystemExit("Repository wallpaper source is missing")

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
    prepare_wallpapers()
    write_png(PREVIEW, 288, 216, draw_preview())
    write_glyphs()
    write_wallpaper_videos()

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
            # Artwork uploaded as design references belongs in the repository, not the theme.
            # Only image assets inside the runtime theme directory (640x480/) are packaged.
            image_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}
            if path.suffix.lower() in image_suffixes and relative.parts[0] != "640x480":
                continue
            archive.write(path, relative.as_posix())

    with ZipFile(OUTPUT, "r") as archive:
        names = set(archive.namelist())
        required = [
            "name.txt", "version.txt", "credits.txt", "scheme/global.ini",
            "640x480/scheme/default.ini", "640x480/preview.png",
            "640x480/image/wall/default.png",
            "640x480/image/wall/muxlaunch.mp4", "640x480/image/background.mp4",
            "640x480/glyph/muxlaunch/apps.svg", "640x480/glyph/muxlaunch/collection.svg",
            "640x480/glyph/muxlaunch/config.svg", "640x480/glyph/muxlaunch/explore.svg",
            "640x480/glyph/muxlaunch/history.svg", "640x480/glyph/muxlaunch/info.svg",
            "640x480/glyph/muxlaunch/reboot.svg", "640x480/glyph/muxlaunch/shutdown.svg",
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
    print(f"Validated metadata, {len(MODULES) + 2} scheme files, shared submenu wallpapers, glyphs and archive layout.")


if __name__ == "__main__":
    main()
