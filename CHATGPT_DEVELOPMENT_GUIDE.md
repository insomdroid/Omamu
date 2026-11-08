# ChatGPT Development Guide — Omamu

Repository: https://github.com/insomdroid/Omamu

This guide defines the workflow for developing Omamu, an original muOS theme inspired by workstation-style design. The repository's scripts, theme structure, source artwork, and muOS compatibility are authoritative.

## Product direction

Omamu targets the Anbernic RG35XX H at **640 × 480**. Preserve its restrained near-black surfaces, warm cream text, amber focus accents, compact typography, and approved pixel-art/line-art direction. Omamu is a muOS theme, not an Android application.

## Non-negotiable working rules

- Work only in this repository. Do not mix code, assets, or assumptions from the Android launcher/icon-pack projects.
- Inspect current theme structure, scripts, asset paths, configuration formats, and build workflow before editing.
- Prefer small, focused changes on `main` for routine work; do not create a PR unless requested or required.
- Do not invent muOS file paths, configuration keys, supported screens, asset names, or build commands.
- Preserve existing working screens, source artwork, licensing, and package structure.
- Do not bundle reference screenshots as production theme assets unless explicitly requested.
- Do not make unrelated artwork, palette, font, or layout changes when the task is a narrow alignment fix.
- Build the distributable `.muxthm` through the repository's actual GitHub Actions workflow.

## Visual and layout rules

- Treat 640 × 480 as the target canvas and verify the exact output resolution.
- Check focus/selection states, not just the idle screen.
- Keep text legible against dark surfaces; amber should communicate focus/selection rather than become indiscriminate decoration.
- Keep icon geometry, line weight, and visual language consistent with the approved simple-outline direction unless the task explicitly changes it.
- Center icons within their actual tile/content bounds, not merely the overall screen.
- Verify padding, grid spacing, clipping, baseline alignment, and selected/unselected states.
- Keep artwork colors intact where the theme is expected to display box art or image previews without recoloring.
- Ensure generated submenu backgrounds are consistent with the source artwork and intended menu hierarchy.
- Do not alter the main-menu wallpaper or other screens during a request that only asks for tile icon centering.

## Asset and build discipline

- Keep source artwork separate from generated outputs where the repository structure allows.
- Preserve font license files and all third-party attribution.
- Inspect scripts before changing generated assets; prefer fixing the source/script rather than manually editing disposable build output.
- Confirm the final archive contains the expected theme files and no temporary previews, debug images, or unrelated files.
- Use the Windows/browser preview workflow when available to inspect layout without repeatedly swapping the device SD card.
- A successful archive build is not proof that muOS renders every screen correctly; test on the target device or a reliable preview.

## Recommended task workflow

1. State one exact screen or asset change.
2. Inspect the relevant theme file, source asset, generator script, and workflow.
3. Identify the actual 640 × 480 layout bounds and affected screens.
4. Make only the requested adjustment.
5. Generate the preview/build and inspect the rendered result.
6. Compare before/after screenshots at the same resolution.
7. Verify the `.muxthm` contents and install/test on muOS when possible.
8. Record commit, workflow URL, artifact, tested screens, and remaining issues.

## Copy-ready prompts

### Audit a visual issue
> Inspect the current Omamu source and build scripts for this exact visual issue. Do not edit yet. Identify the relevant file(s), coordinate system, tile/content bounds, generated assets, and screens that could be affected. Propose the smallest fix and a 640 × 480 verification plan.

### Implement a narrow visual fix
> Implement only the approved Omamu change. Preserve the current palette, wallpaper, icon style, typography, and all unrelated screens. Fix the requested geometry at the correct 640 × 480 content bounds. Review the diff and rebuild the .muxthm.

### Compare previews
> Compare these Omamu previews at 640 × 480. Check icon centering within tiles, margins, grid spacing, clipping, text readability, focus state, and unintended changes to other screens. Report measured/observable differences separately from guesses.

### Diagnose a failed theme build
> Inspect the actual GitHub Actions log and repository build script. Identify the first meaningful failure and the exact source/configuration responsible. Make the smallest fix, rerun the workflow, and inspect the resulting .muxthm archive contents. Do not change unrelated assets.

## Checkpoint template

- Target device/resolution:
- Last known-good commit:
- Last successful Actions run:
- .muxthm artifact:
- Screens verified:
- Assets/scripts changed:
- License/attribution changes:
- Known visual issues:
- Current task:
- Next single task:

## Definition of done

The requested screen renders correctly at 640 × 480, the intended focus states and neighboring screens remain correct, generated assets/archive contents are inspected, the GitHub Actions result is known, and device/preview verification status is stated honestly. If only the archive build passed, do not claim device rendering is verified.
