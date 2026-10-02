#!/bin/sh
# Builds gThumb from the source tree this script is part of and packages it
# as an AppImage that bundles all its libraries, glibc included (Anylinux
# AppImage made with quick-sharun), so it runs on older distributions such
# as Linux Mint 22 as well as on current ones.
#
# Runs as root inside the container made from appimage/Containerfile; use
# appimage/build.sh, which also checks out the commit to build.
# Output: $OUT/gThumb-<version>-anylinux-x86_64.AppImage, its .zsync file
# and SHA256SUMS.
set -eu

SRC=$(cd "$(dirname "$0")/.." && pwd)
OUT=${OUT:-/out}
BUILD=/tmp/build

# All dates in the build are the date of the commit.
SOURCE_DATE_EPOCH=$(git -C "$SRC" log -1 --format=%ct)
COMMIT=$(git -C "$SRC" rev-parse HEAD)
export SOURCE_DATE_EPOCH

echo "== Build $COMMIT"
meson setup $BUILD "$SRC" --prefix=/usr --buildtype=release
ninja -C $BUILD

echo "== Install into the container's /usr"
ninja -C $BUILD install > /dev/null
glib-compile-schemas /usr/share/glib-2.0/schemas

# The version is the commit's release tag (<gThumb version>-dragzoom.<n>),
# or the gThumb version and the commit for other commits.
GTHUMB_VERSION="$(meson introspect --projectinfo $BUILD | python3 -c 'import json,sys; print(json.load(sys.stdin)["version"])')"
VERSION=$(git -C "$SRC" describe --tags --exact-match --match "$GTHUMB_VERSION-dragzoom.*" 2>/dev/null) ||
	VERSION="$GTHUMB_VERSION-dragzoom-g$(git -C "$SRC" rev-parse --short=9 HEAD)"
ARCH=x86_64
export ARCH VERSION
export APPDIR=/tmp/AppDir
export OUTPATH=/tmp/dist
export OUTNAME="gThumb-$VERSION-anylinux-$ARCH.AppImage"
export DESKTOP=/usr/share/applications/org.gnome.gthumb.desktop
export ICON=/usr/share/icons/hicolor/256x256/apps/org.gnome.gthumb.png
export UPINFO="gh-releases-zsync|DigitalArchon|gthumb-dragzoom|latest|gThumb-*-anylinux-$ARCH.AppImage.zsync"
# Video support: the GStreamer plugins, with libav for common codecs.
export DEPLOY_GSTREAMER=1
# Paths compiled into the libraries (/usr/share, ...) are replaced by links
# in /tmp with random names; fixed names keep the build reproducible.
export _tmp_bin=gTb _tmp_lib=gTl _tmp_share=gThmb

echo "== Deploy (quick-sharun)"
cd /tmp
quick-sharun /usr/bin/gthumb /usr/libexec/gthumb/video-thumbnailer

# GLib's translations (file error messages) are not found by quick-sharun.
for mo in /usr/share/locale/*/LC_MESSAGES/glib20.mo; do
	dir=$APPDIR/share/locale/$(basename "$(dirname "$(dirname "$mo")")")/LC_MESSAGES
	if [ -d "$dir" ]; then
		cp "$mo" "$dir"/
	fi
done

echo "== gThumb hook (sourced by AppRun before starting the program)"
cat > "$APPDIR"/bin/10-gthumb.hook <<'EOF'
# AppRun.lib links the AppImage's cache folder to the user's thumbnail
# folder only once: recreate the folder if it was deleted since (cache
# cleaners do this), or thumbnails can't be saved.
mkdir -p "$CACHEDIR"/thumbnails 2>/dev/null || :
EOF

echo "== AppImage"
# Same time stamp on every file, including those written while making the
# AppImage (appimagetool's default compression, plus --set-time).
export DWARFS_COMP="zstd:level=22 -S26 -B6 --set-time=$SOURCE_DATE_EPOCH"
quick-sharun --make-appimage

mkdir -p "$OUT"
cp "$OUTPATH/$OUTNAME" "$OUTPATH/$OUTNAME.zsync" "$OUT"/
cd "$OUT"
sha256sum "$OUTNAME" "$OUTNAME.zsync" > SHA256SUMS
echo "== Done: $OUT/$OUTNAME (source commit $COMMIT)"
cat SHA256SUMS
