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
    """Generate crisp, block-based pixel glyphs for the main menu and secondary menus."""
    # muOS resolves glyphs by module/item name. Keep all artwork in glyph/, never
    # image/static/: static images are screen overlays and can appear in the centre.
    modules = {
        "muxlaunch": ("apps", "collection", "config", "explore", "history", "info", "reboot", "shutdown"),
        "muxconfig": ("access", "backup", "colour", "connect", "core", "custom", "general", "interface", "power", "storage", "theme"),
        "muxcustom": ("align", "alternate", "animation", "backgroundscale", "battery", "blackfade", "bluetooth", "boxart", "boxarthide", "boxartpadding", "boxartplaceholder", "boxartscale", "boxarttransition", "catalogue", "chime", "clock", "config", "content", "contentcollect", "contenthistory", "count", "dash", "displayemptyfolder", "elementtransition", "folderitemcount", "font", "fontname", "footerheight", "footersize", "forwardhistory", "friendlyfolder", "glyphfooter", "glyphgrid", "glyphheader", "glyphlist", "gridmodecontent", "groupcontent", "headerheight", "headersize", "headertitle", "hidden", "labelscrollspeed", "labelwidth", "launch_swap", "listglyph", "listsize", "logo", "menucounterfile", "menucounterfolder", "mixedcontent", "music", "musicvolume", "name", "namescroll", "network", "notifytime", "overlayimage", "overlaytransparency", "pageskip", "panelsize", "picklesstartupmessages", "randomtheme", "rendershadows", "resolution", "savescreenshot", "scaling", "selectionanimation", "selectionstyle", "shuffle", "sort", "sortorder", "sound", "soundvolume", "splash", "tagorder", "textscale", "theme", "themeopt", "thetitleformat", "titleincluderootdrive", "type"),
        "muxplore": ("collection", "folder", "history", "rom"),
        "muxapp": ("app", "archive", "dingux", "flip", "logo_2048", "moonlight", "music", "portmaster", "ppsspp", "retroarch", "rgbcontroller", "scummvm", "task", "terminal", "video", "vtree"),
        "muxinfo": ("activity", "chrony", "credit", "detail", "news", "reload", "screenshot", "space", "tester", "third"),
        "muxpower": ("battery", "gov_default", "gov_idle", "idle_display", "idle_mute", "idle_sleep", "saver_speed", "saver_type", "shutdown"),
        "muxconnect": ("bluetooth", "link", "net_proxy", "netadv", "network", "service", "webcode"),
        "muxstorage": ("apps", "bios", "catalogue", "collection", "history", "init", "launch", "manifest", "migrate_all", "music", "name", "network", "override", "package", "pickles", "profile", "purge_all", "save", "screenshot", "sync_all", "syncthing", "theme", "track", "wasabi"),
        "muxhistory": ("collection", "history"),
        "muxcollect": ("collection", "folder"),
        "muxassign": ("core", "default", "download", "system"),
        "muxnetwork": ("ethernet", "profile"),
        "muxoption": ("colfilter", "control", "core", "folder", "governor", "launch", "name", "overlay", "remconfig", "retroarch", "search", "shader", "storage", "tag", "time"),
        "muxpicker": ("catalogue", "config", "download", "folder", "theme"),
        "muxtheme": ("download", "folder", "theme"),
        "muxcontrol": ("default", "modern", "retro", "system"),
        "muxarchive": ("archive", "installed"),
        "muxrtc": ("custom", "day", "hour", "minute", "month", "notation", "timezone", "year"),
        "muxlanguage": ("language",),
        "muxaccess": ("boldfocus", "highcontrast", "legiblefont", "reducemotion", "textsize"),
        "muxterm": ("background", "fonthinting", "fontsize", "foreground", "quit", "reset", "terminal"),
    }
    # 5x5 bitmap alphabet of simple, recognizable symbols; each cell becomes a
    # hard-edged rectangle, avoiding anti-aliased strokes at 640x480.
    bitmaps = {
        "apps": ("10101","10101","00000","10101","10101"),
        "folder": ("11111","10000","11110","10010","11111"),
        "config": ("00100","10101","01110","10101","00100"),
        "explore": ("00100","10101","01110","00100","00100"),
        "history": ("01110","10001","10111","10001","01110"),
        "info": ("00100","00100","00100","00000","00100"),
        "power": ("00100","10101","10001","11011","01110"),
        "shutdown": ("00100","00100","10101","10001","01110"),
        "collection": ("01010","11111","11111","01110","00100"),
        "star": ("00100","10101","01110","11111","01010"),
        "clock": ("01110","10001","10111","10001","01110"),
        "battery": ("11111","10001","10101","10001","11111"),
        "bluetooth": ("10010","11100","10110","11100","10010"),
        "network": ("00100","01010","10101","01010","00100"),
        "theme": ("01110","11011","10101","11011","01110"),
        "storage": ("01110","10001","11111","10001","01110"),
        "lock": ("01110","10001","11111","11011","11111"),
        "document": ("11110","10010","10110","10010","11110"),
        "search": ("01110","10001","10111","01100","00110"),
        "download": ("00100","00100","10101","01110","00100"),
        "link": ("01001","10010","00100","01001","10010"),
        "music": ("00110","00101","00101","11101","11110"),
        "font": ("00100","01010","11111","10001","10001"),
        "screen": ("11111","10001","10101","10001","11111"),
        "wifi": ("00100","01010","10001","00100","00100"),
        "refresh": ("01110","10001","00110","01001","01110"),
        "archive": ("11111","10001","10101","10001","11111"),
        "game": ("10101","11111","11011","11111","10101"),
    }
    def symbol_for(name: str) -> str:
        key = name.lower()
        if any(word in key for word in ("shutdown", "power", "reboot", "quit", "blackfade")): return "power"
        if any(word in key for word in ("app", "bios", "package", "portmaster", "retroarch", "ppsspp", "scumm", "vtree", "dingux", "moonlight")): return "apps"
        if any(word in key for word in ("folder", "directory", "catalogue", "collection", "pickles")): return "folder" if "folder" in key or "directory" in key else "collection"
        if any(word in key for word in ("history", "last", "recent", "time", "clock", "hour", "minute", "day", "month", "year")): return "history" if "history" in key else "clock"
        if any(word in key for word in ("config", "setting", "general", "interface", "governor", "control", "access", "custom", "align", "scale", "size", "sort", "order", "option", "animation")): return "config"
        if any(word in key for word in ("explore", "search", "find", "filter", "rom", "launch", "core")): return "search"
        if any(word in key for word in ("info", "detail", "credit", "news", "about", "third", "tester")): return "info"
        if any(word in key for word in ("bluetooth", "link", "connect", "network", "wifi", "ethernet", "proxy", "service", "webcode")): return "bluetooth" if "bluetooth" in key else "network"
        if any(word in key for word in ("battery", "power", "saver")): return "battery"
        if any(word in key for word in ("theme", "colour", "color", "background", "overlay", "logo", "boxart", "splash")): return "theme"
        if any(word in key for word in ("storage", "space", "save", "backup", "restore", "install", "download", "sync", "manifest", "archive")): return "storage" if "storage" in key or "space" in key else "download"
        if any(word in key for word in ("font", "text", "label", "title", "name", "language")): return "font"
        if any(word in key for word in ("music", "sound", "chime", "audio", "volume")): return "music"
        if any(word in key for word in ("screen", "screenshot", "display", "resolution", "header", "footer", "panel", "glyph")): return "screen"
        if any(word in key for word in ("retro", "game", "content", "shuffle", "play")): return "game"
        if any(word in key for word in ("lock", "profile", "accessibility", "highcontrast", "hidden")): return "lock"
        if any(word in key for word in ("refresh", "reload", "reset", "restore")): return "refresh"
        return "document"

    for module, names in modules.items():
        glyph_root = RESOLUTION / "glyph" / module
        glyph_root.mkdir(parents=True, exist_ok=True)
        for name in names:
            symbol = bitmaps[symbol_for(name)]
            cells = []
            for row, bits in enumerate(symbol):
                for col, bit in enumerate(bits):
                    if bit == "1":
                        cells.append(f'<rect x="{3 + col * 4}" y="{3 + row * 4}" width="3" height="3" fill="#F4F0E8"/>')
            # Tiny amber corner pixels give the set a consistent Omamu accent.
            cells.append('<rect x="19" y="19" width="3" height="3" fill="#E8A84A"/>')
            svg = ('<?xml version="1.0" encoding="UTF-8"?>'
                   '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" '
                   'viewBox="0 0 24 24" shape-rendering="crispEdges">'
                   + ''.join(cells) + '</svg>')
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
            "640x480/image/wall/muxlaunch.png",
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
