# gThumb 4.0 with drag to zoom: release 4.0-dragzoom.1

The first release of this fork of gThumb 4.0, with drag to zoom, as an AppImage that runs on
Linux Mint 22.x, CachyOS and other x86-64 Linux distributions.

## Drag to zoom

Turn it on in **Preferences > Images > Drag Action > Zoom to Selection**.

- When the whole image fits the window, the pointer becomes a crosshair. Drag over the part you
  want to see: on release, gThumb zooms so that the selected area fills the window, as large as
  possible while still entirely visible, centred on the selection.
- When the image is larger than the window, dragging moves it, as before.
- Ctrl+drag drags the file to another application.
- A click does nothing.
- The zoom goes up to gThumb's maximum of 1000%.

The zoom is exact: across the window, each screen pixel shows the image pixel it should, to within
one screen pixel.

With the default setting, **Drag the File**, gThumb behaves as before.

## Fixes to gThumb 4.0

- When zoomed in, images were drawn up to one image pixel out of place, which is several screen
  pixels at high zoom levels. They are now drawn exactly where they should be.
- After a file had been dragged out of the viewer (Ctrl+drag), dragging the image no longer
  worked.
- The browser stayed empty, with a spinner, when the Pictures, Videos or Downloads folder was not
  set (no xdg-user-dirs), as on some minimal installations.

## The AppImage

Download `gThumb-4.0-dragzoom.1-anylinux-x86_64.AppImage`, make it executable and run it:

```sh
chmod +x gThumb-4.0-dragzoom.1-anylinux-x86_64.AppImage
./gThumb-4.0-dragzoom.1-anylinux-x86_64.AppImage
```

- It includes everything it needs, including GTK 4.22 and libadwaita 1.9, which gThumb 4 requires
  and Linux Mint 22 doesn't have. Nothing is installed on the system.
- It uses the same settings as an installed gThumb 4.
- It uses native Wayland when available, else X11.
- It contains update information, so AppImageUpdate can update it from this repository's
  releases.
- Size: about 160 MB.

## Checking the download

`SHA256SUMS` lists the checksums of the files of this release:

```sh
sha256sum -c SHA256SUMS
```

The build is reproducible: building the tag `4.0-dragzoom.1` with `appimage/build.sh` gives a
bit-for-bit identical AppImage. See [appimage/README.md](appimage/README.md).

## Tested

Automated tests of the AppImage on Ubuntu 24.04 (the base of Linux Mint 22.3) and CachyOS: drag to
zoom (38 checks, including pixel accuracy), settings, video thumbnails and playback, translations,
and starting under Wayland.
