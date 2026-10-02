# Drag to zoom: fork notes

This branch (`zoom-to-selection`, based on gThumb 4.0) adds one feature, ACDSee-style drag to zoom,
and fixes three upstream problems found while porting it. The same feature for gThumb 3.12 was a
patch to the old C code; gThumb 4 is a Vala/GTK 4 rewrite, so this is a port, not a cherry-pick.

## Behaviour

Enable it in Preferences > Images > Drag Action > "Zoom to Selection"
(setting `org.gnome.gthumb.viewers.images drag-to-zoom`, default `false`).

- When the image fits the window, the pointer is a crosshair and a left-drag draws a selection,
  dimming the area outside it. On release, the image is zoomed so the whole selection is visible
  and either its width or its height exactly fills the window, centred on the selection.
- When the image is larger than the window, a left-drag scrolls, as before.
- Ctrl+drag drags the file.
- A click (movement under the drag threshold) does nothing.
- Selections are limited to the image. Near an image edge the view can't scroll further, so the
  selection isn't centred, but it still fills the window along its limiting side.
- The zoom is limited to gThumb's maximum of 1000%.
- The setting applies immediately, without restarting.

## Commits

1. **Image view: draw the image pixels at their exact position** (upstream bug). When the image was
   scrolled, the visible area was rounded down to whole image pixels, both origin and size, and
   stretched over the widget: the image was shifted and stretched by up to one image pixel, about
   9 screen pixels at 900%. The editor tools and zoom-at-pointer assume the exact mapping
   `(x - texture_box.origin + scroll) / zoom`. Now the whole pixels covering the visible area are
   drawn at their exact position and clipped; `texture_box` keeps its meaning.
2. **Image view: reset the drag gesture after the viewer drags the file** (upstream bug). After a
   file drag (Ctrl+drag), the button release never reached the image view's drag gesture, which
   then ignored the following presses.
3. **Viewer: add drag to zoom**: `src/Ext/Image/ImageView.vala` (selection, overlay, cursor,
   `zoom_to_area ()`), the setting, and its row in the Images preferences.
4. **File manager: don't wait forever when a user folder is not set** (upstream bug). Without
   configured XDG user folders (Pictures, Videos, Downloads), the browser stayed empty with a
   spinner: a non-nullable parameter made an async method return without completing.
5. **Video: find the thumbnailer when the program has been moved**: looks for `video-thumbnailer`
   in the PATH when it isn't in the compiled-in folder, as in the AppImage.

### Pixel accuracy

The chain is: selection in widget pixels → image pixels → zoom factor → scroll offset, all in
floating point; nothing is rounded to whole image pixels or whole zoom percentages, because such an
error is multiplied by the zoom. The renderer fix (commit 1) is what makes the result visible as
computed: without it, the zoomed selection was off by up to one image pixel.

Measured result: every screen pixel along the limiting axis shows the predicted image pixel, within
1 screen pixel at pixel boundaries, at zoom levels from 296% to 976% (automated test, see below).
Accuracy is in GTK logical pixels.

## AppImage

Built on Arch Linux and packaged with [sharun/quick-sharun](https://github.com/pkgforge-dev/Anylinux-AppImages)
("Anylinux" AppImage): it bundles every library including glibc, Mesa's hardware drivers and
GStreamer (with libav), so it doesn't depend on the host's GTK 4 (4.18.5 or later is required, while
Linux Mint 22 has 4.14) or glibc. About 92 MB.

- Settings are stored in the user's normal dconf database; translations are included.
- Uses native Wayland when available, else X11.
- Without a GPU (`/dev/dri/renderD*`), it uses GTK's cairo renderer, as a native GTK does on such
  systems; set `GSK_RENDERER` to override.
- The build scripts and tests live outside this repository, in `../build-env` (see its README).

## Tests

Run against the AppImage on Ubuntu 24.04 (glibc 2.39, the Linux Mint 22.3 base) and CachyOS
(glibc 2.44) test containers:

- 38 automated drag-to-zoom checks under Xvfb, using a test image whose colours encode pixel
  coordinates, so screenshots can be decoded exactly: five zoom scenarios (width- and
  height-limited, deep zoom, image corner, image edge), the selection overlay and crosshair cursor,
  panning when zoomed, click, Ctrl+drag, drag after a file drag, the default setting, and turning
  the setting on while running.
- Settings read from and saved to dconf, video thumbnails and playback (MP4 and WebM), German
  translation, and a native Wayland start on headless Weston.

## Upstream

Commits 1, 2 and 4 fix upstream bugs and could be proposed upstream independently of the feature.
