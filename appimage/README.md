# AppImage

Builds the gThumb drag-to-zoom fork as an AppImage that runs on older distributions such as
Linux Mint 22 (which lacks the GTK 4.18 that gThumb 4 needs) as well as on current ones such as
CachyOS. It bundles every library, glibc included, using
[quick-sharun](https://github.com/pkgforge-dev/Anylinux-AppImages) ("Anylinux" AppImage).

The build is **reproducible**: building the same commit again gives a bit-for-bit identical
AppImage, so a release can be checked against its source.

## Build

Requires podman, git and network access (Arch Linux Archive, GitHub).

```sh
appimage/build.sh [COMMIT] [OUTPUT_DIR]       # defaults: HEAD, ./dist
```

Output: `gThumb-<version>-anylinux-x86_64.AppImage`, its `.zsync` file (for AppImage update tools)
and `SHA256SUMS`. Only committed files are used: the build environment is made from that commit's
`appimage/Containerfile` and the build runs in a fresh clone of the commit, so uncommitted changes
are ignored.

To check a release, build its tag and compare `SHA256SUMS` with the one published with the release:

```sh
appimage/build.sh 4.0-dragzoom.1 /tmp/check && cat /tmp/check/SHA256SUMS
```

## What is pinned

| Input | Pinned by |
| --- | --- |
| gThumb source | the commit; all dates in the build are its date (`SOURCE_DATE_EPOCH`) |
| Base image | `archlinux` image digest |
| Compiler, libraries, GStreamer, Mesa, ... | [Arch Linux Archive](https://archive.archlinux.org/) snapshot (`ARCHIVE_DATE` in the Containerfile) |
| quick-sharun | commit and SHA-256 (it pins sharun, appimagetool and its runtime the same way) |

Also needed for identical output: fixed names for the `/tmp` links quick-sharun uses to relocate
hardcoded paths (random by default), and one time stamp for all files in the image (`--set-time`).

To update the libraries, change `ARCHIVE_DATE` (and the base image digest if needed), rebuild and
run the tests.

The AppImage uses the regular Arch packages rather than the smaller "debloated" ones of the
Anylinux project, which are published as a rolling release and so cannot be pinned. That makes it
larger, mostly because Mesa needs LLVM, but it includes llvmpipe, so GTK's usual software-rendering
fallback works on computers without a GPU.

## Test

```sh
appimage/test.sh [OUTPUT_DIR]                 # default: ./dist
```

Runs the tests against the AppImage in containers with Ubuntu 24.04 (glibc 2.39, the Linux Mint 22
base) and CachyOS, which have no GTK 4 or GStreamer of their own:

- `functional_test.py` (38 checks): drag to zoom on Xvfb, with a test image whose pixel colours
  encode their own coordinates, so screenshots are decoded to check that the selection fills the
  window to the pixel; also the overlay, crosshair cursor, panning, click, Ctrl+drag, the default
  setting and changing it while running.
- `real_world_test.py` (8 checks): settings in dconf, video thumbnails and playback, German
  translation.
- `wayland_test.sh`: native Wayland start on headless Weston.

Logs and screenshots: `OUTPUT_DIR/test-results/`.

## Run-time notes

- Settings are the same as an installed gThumb 4's (dconf, `org.gnome.gthumb`).
- Native Wayland when available, else X11.
- `bin/10-gthumb.hook` in the AppImage recreates `~/.cache/thumbnails` if it was deleted, since
  the AppImage's cache folder links to it.
