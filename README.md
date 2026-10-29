# Omamu

**An Omarchy-inspired theme for muOS**  
Designed for the Anbernic RG35XX H at **640 × 480**.

Omamu brings a restrained, workstation-inspired look to the muOS frontend: near-black surfaces, warm cream text, amber focus states, compact typography, crisp square edges, and a futuristic pixel-art planet wallpaper. It is an original muOS theme—not a port of the Omarchy desktop environment.

## Highlights

- **Dark, minimal palette:** near-black backgrounds, cream text, and amber focus accents.
- **RG35XX H layout:** resolution-specific schemes for the main menu and supported muOS screens.
- **Main-menu grid:** two rows of four destinations with custom line glyphs and clear focus styling.
- **Pixel-art wallpaper:** generated from the project's original source artwork, with a subtle animated wallpaper asset included in the build.
- **Artwork keeps its colour:** box art and image previews are not recoloured by the theme.
- **Native dialog colours:** the Download Theme dialog is intended to retain its normal muOS colours instead of receiving a theme tint.
- **JetBrains Mono:** bundled during the build under the SIL Open Font License 1.1; the license is included in the package.
- **Windows-friendly preview:** a standalone HTML preview helps inspect the layout and experiment with selected styling values without connecting the handheld.

## Preview on Windows

Open [preview/index.html](preview/index.html) in GitHub, choose **Download raw file**, and save it as **omamu-preview.html**. Open the saved file in Edge, Chrome, or Firefox.

The preview can simulate the 640 × 480 screen and switch between available screen layouts, adjust selected spacing and text settings, and test status colours and long labels. Where supported, use **Muat INI** to load a scheme file and inspect selected values.

> **Note:** The HTML preview is a visual approximation. It does not run the native muOS frontend or its actual glyph renderer, so its icons and rendering may differ from the handheld. Use it to iterate quickly, then verify the built theme on the device when possible.

## Build the theme

The theme package is built by GitHub Actions; you do not need a local Linux environment.

1. Open [**Actions → Build muOS theme**](https://github.com/insomdroid/Omamu/actions/workflows/build-theme.yml).
2. Select **Run workflow** on the **main** branch, or push a commit to **main** to trigger a build.
3. Open the completed workflow run.
4. Download the **omamu-muxthm** artifact and extract it.
5. The installable theme file is **Omamu.muxthm**.

The workflow generates the resolution-specific wallpaper assets, prepares the font and its license, validates theme files, and packages the output. The generated .muxthm artifact is the installable package; the Actions artifact itself is a ZIP containing that file.

## Install on muOS

1. Copy **Omamu.muxthm** to the **ARCHIVE** folder on SD1 or SD2.
2. On the handheld, open **Applications → Archive Manager** and select the file.
3. Open **Configuration → Customisation → Theme Picker**.
4. Select **Omamu** and activate it.

Keep your previous theme available until you have confirmed that Omamu works as expected. The automated build checks files and package structure, but only the actual device can confirm how each frontend element renders on your installed muOS version.

## Repository layout

| Path | Purpose |
| --- | --- |
| **scheme/global.ini** | Shared colours and common UI styling |
| **640x480/scheme/** | Resolution defaults and per-screen overrides |
| **640x480/glyph/muxlaunch/** | Custom main-menu SVG glyphs |
| **640x480/image/wall/** | Generated screen-specific wallpapers |
| **Pixel Planet Over a Misty Horizon.png** | Source pixel-art wallpaper |
| **preview/index.html** | Standalone browser preview |
| **scripts/build_theme.py** | Asset generation, validation, and packaging |
| **.github/workflows/build-theme.yml** | Automated theme build and artifact upload |

Some assets (including generated wallpapers and the bundled font) are prepared during CI rather than stored as generated files in the source tree.

## Design and licensing

Omamu is an original, Omarchy-inspired theme and is **not affiliated with Omarchy or MustardOS**.

JetBrains Mono is © JetBrains and is distributed under the SIL Open Font License 1.1. Its license is included in the generated theme package. Wallpaper and glyph assets are produced for this project by its build script.

For muOS theme format and scheme behaviour, see the official documentation:

- [Theme Structure](https://muos.dev/themes/structure)
- [Scheme Files](https://muos.dev/themes/scheme)
- [Glyph Gallery](https://muos.dev/themes/glyphs)
- [Finishing a Theme](https://muos.dev/themes/finish)
