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


def fill_polygon(pixels: bytearray, width: int, points: list[tuple[int, int]],
                 colour: tuple[int, int, int]) -> None:
    """Fill a polygon with hard pixel edges for a low-resolution pixel-art look."""
    min_y = max(0, min(y for _, y in points))
    max_y = min(len(pixels) // (width * 3) - 1, max(y for _, y in points))
    for y in range(min_y, max_y + 1):
        intersections = []
        for i, (x1, y1) in enumerate(points):
            x2, y2 = points[(i + 1) % len(points)]
            if y1 == y2 or y < min(y1, y2) or y >= max(y1, y2):
                continue
            intersections.append(round(x1 + (y - y1) * (x2 - x1) / (y2 - y1)))
        intersections.sort()
        for i in range(0, len(intersections) - 1, 2):
            for x in range(max(0, intersections[i]), min(width, intersections[i + 1] + 1)):
                set_pixel(pixels, width, x, y, colour)


def pixel_circle(pixels: bytearray, width: int, cx: int, cy: int, radius: int,
                 colour: tuple[int, int, int], block: int = 4) -> None:
    """Draw a chunky circle on the pixel grid."""
    for y in range(cy - radius, cy + radius + 1, block):
        for x in range(cx - radius, cx + radius + 1, block):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                for oy in range(block):
                    for ox in range(block):
                        set_pixel(pixels, width, x + ox, y + oy, colour)


def draw_wallpaper(module: str = "default") -> bytearray:
    """Pixel-art cyber valley, dark planetary horizon and restrained Omamu amber."""
    pixels = bytearray(WIDTH * HEIGHT * 3)
    # Nearly-black sky with a subtle square grid and a low horizon glow.
    for y in range(HEIGHT):
        for x in range(WIDTH):
            lift = max(0, 9 - abs(y - 335) // 16)
            shade = (BG[0] + lift, BG[1] + lift, BG[2] + lift)
            if x % 32 == 0 or y % 32 == 0:
                shade = (GRID[0] + lift, GRID[1] + lift, GRID[2] + lift)
            offset = (y * WIDTH + x) * 3
            pixels[offset:offset + 3] = bytes(shade)

    # Sparse pixel stars, intentionally kept out of the central menu-safe zone.
    stars = [(93, 104, CREAM), (132, 132, MUTED), (214, 88, AMBER),
             (284, 151, CREAM), (450, 92, CREAM), (521, 123, AMBER),
             (565, 82, CREAM), (377, 176, MUTED), (62, 180, AMBER)]
    for x, y, colour in stars:
        rectangle(pixels, WIDTH, x, y, 2, 2, colour, True)

    # Distant stepped mountains in charcoal, then foreground ridges in graphite.
    fill_polygon(pixels, WIDTH, [(0, 326), (40, 298), (72, 313), (110, 277),
        (148, 315), (190, 288), (230, 326), (274, 300), (318, 329),
        (362, 294), (408, 322), (455, 286), (496, 316), (545, 279),
        (590, 309), (639, 286), (639, 392), (0, 392)], (29, 29, 28))
    fill_polygon(pixels, WIDTH, [(0, 352), (36, 326), (68, 340), (104, 307),
        (140, 345), (179, 318), (218, 353), (259, 330), (299, 354),
        (339, 326), (381, 354), (425, 321), (468, 351), (510, 319),
        (554, 347), (600, 315), (639, 336), (639, 416), (0, 416)], (22, 23, 23))

    # Pixelated eclipsed planet and a small amber rim on its right edge.
    pixel_circle(pixels, WIDTH, 423, 258, 58, (36, 36, 34), 4)
    pixel_circle(pixels, WIDTH, 418, 254, 51, (16, 16, 16), 4)
    for y in range(208, 310, 4):
        for x in range(460, 482, 4):
            if (x - 423) ** 2 + (y - 258) ** 2 <= 58 ** 2 and (x - 418) ** 2 + (y - 254) ** 2 > 51 ** 2:
                rectangle(pixels, WIDTH, x, y, 4, 4, AMBER, True)

    # Far shoreline and angular amber reflections across still water.
    line(pixels, WIDTH, 275, 352, 530, 352, (74, 54, 32), 1)
    for i, (y, x1, x2) in enumerate([(365, 378, 470), (373, 394, 455),
        (382, 382, 468), (392, 401, 449), (403, 388, 461),
        (414, 402, 443), (425, 394, 456), (437, 408, 444)]):
        colour = AMBER if i in (0, 2, 4, 6) else (96, 65, 31)
        line(pixels, WIDTH, x1, y, x2, y, colour, 2 if i < 3 else 1)
    fill_polygon(pixels, WIDTH, [(0, 385), (88, 379), (143, 398), (205, 413),
        (267, 440), (322, 480), (0, 480)], (8, 9, 10))
    fill_polygon(pixels, WIDTH, [(0, 396), (72, 390), (128, 410), (185, 430),
        (233, 452), (270, 480), (0, 480)], (18, 19, 19))
    # Pixel steps catch the light along the left cliff edge.
    for x, y, w in [(34, 390, 16), (54, 397, 12), (69, 405, 18),
                    (91, 414, 12), (108, 423, 16), (128, 433, 12),
                    (145, 443, 16), (165, 454, 14), (185, 466, 13)]:
        rectangle(pixels, WIDTH, x, y, w, 2, AMBER, True)

    # Tiny windswept pixel tree on the cliff, a silhouette rather than a focal point.
    fill_polygon(pixels, WIDTH, [(48, 366), (57, 337), (66, 324), (75, 328),
        (86, 316), (97, 323), (108, 320), (98, 332), (85, 334),
        (73, 342), (65, 359), (62, 379)], (7, 8, 8))
    line(pixels, WIDTH, 61, 348, 80, 324, (9, 10, 10), 3)
    line(pixels, WIDTH, 70, 339, 95, 329, (9, 10, 10), 2)
    for x, y in [(82, 325), (92, 329), (72, 338), (58, 349)]:
        rectangle(pixels, WIDTH, x, y, 3, 2, AMBER, True)

    # Fine amber HUD marks only at the outer edges; the menu area stays uncluttered.
    line(pixels, WIDTH, 24, 30, 24, 108, AMBER)
    line(pixels, WIDTH, 24, 30, 62, 30, AMBER)
    line(pixels, WIDTH, 616, 30, 616, 108, AMBER)
    line(pixels, WIDTH, 578, 30, 616, 30, AMBER)
    for y in (116, 124, 132):
        rectangle(pixels, WIDTH, 24, y, 3, 3, AMBER, True)
        rectangle(pixels, WIDTH, 613, y, 3, 3, AMBER, True)
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
    for module in MODULES:
        if module == "muxlaunch":
            continue
        grid.save(IMAGE_WALL / f"{module}.png", format="PNG", optimize=True)


def write_animated_wallpaper() -> None:
    """Create a subtle, low-bitrate Omamu moving grid wallpaper."""
    output = IMAGE_WALL / "muxlaunch.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-framerate", "12", "-i", str(IMAGE_WALL / "muxlaunch.png"),
        "-t", "6",
        "-vf",
        "drawbox=x='mod(t*10,640)':y=0:w=2:h=480:color=0xe8a84a@0.13:t=fill,"
        "format=yuv420p",
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "30",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ]
    subprocess.run(command, check=True)
    background_video = RESOLUTION / "image" / "background.mp4"
    background_video.parent.mkdir(parents=True, exist_ok=True)
    background_video.write_bytes(output.read_bytes())


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
        rects = "".join(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#F4F0E8"/>'
            for x, y, w, h in blocks
        )
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
            'viewBox="0 0 24 24" shape-rendering="crispEdges">' + rects + '</svg>'
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
    write_animated_wallpaper()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    excluded_parts = {".git", ".github", "scripts", "dist", "__pycache__"}
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if any(part in excluded_parts for part in relative.parts):
                continue
            if path.suffix == ".pyc" or relative.name in ("README.md", "Pixel Planet Over a Misty Horizon.png"):
                continue
            archive.write(path, relative.as_posix())

    with ZipFile(OUTPUT, "r") as archive:
        names = set(archive.namelist())
        required = [
            "name.txt", "version.txt", "credits.txt", "scheme/global.ini",
            "640x480/scheme/default.ini", "640x480/preview.png",
            "640x480/image/wall/default.png",
            "640x480/image/wall/muxlaunch.mp4",
            "640x480/image/background.mp4",
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
    print(f"Validated metadata, {len(MODULES) + 2} scheme files, wallpapers, glyphs and archive layout.")


if __name__ == "__main__":
    main()
