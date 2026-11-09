#!/usr/bin/env bash
# Builds the Aleflix release APKs into dist/:
#   dist/Aleflix_Android_v<version>.apk     phone/tablet (update channel: apk)
#   dist/Aleflix_AndroidTV_v<version>.apk   Android TV / Google TV
#
#   scripts/aleflix/build_release.sh [all|mobile|tv]
#
# Signs with android/app/release.keystore + android/keystore.properties. Set
# REQUIRE_RELEASE_KEY=1 (CI does) to fail instead of falling back to the debug
# key, and ALEFLIX_CERT_SHA256 to the expected signing certificate digest.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

TARGET="${1:-all}"
case "$TARGET" in all|mobile|tv) ;; *) echo "usage: $0 [all|mobile|tv]" >&2; exit 2 ;; esac

FLUTTER="${FLUTTER_BIN:-flutter}"
VERSION="$(scripts/aleflix/version.sh)"
mkdir -p dist

if [ "${REQUIRE_RELEASE_KEY:-}" = 1 ] && [ ! -f android/app/release.keystore ]; then
  echo "build_release.sh: REQUIRE_RELEASE_KEY=1 but android/app/release.keystore is missing" >&2
  exit 1
fi

# aapt2 and apksigner from the newest installed build-tools.
BUILD_TOOLS="$(ls -d "${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"/build-tools/* 2>/dev/null | sort -V | tail -1)"

check_apk() {
  local apk="$1"
  local name
  name="$("$BUILD_TOOLS/aapt2" dump badging "$apk" | sed -nE "s/.*versionName='([^']*)'.*/\1/p" | head -1)"
  if [ "$name" != "$VERSION" ]; then
    echo "build_release.sh: $apk has versionName '$name', expected '$VERSION'" >&2
    exit 1
  fi
  if [ -n "${ALEFLIX_CERT_SHA256:-}" ]; then
    local digest
    digest="$("$BUILD_TOOLS/apksigner" verify --print-certs "$apk" | sed -nE 's/.*certificate SHA-256 digest: //p' | head -1)"
    if [ "$digest" != "${ALEFLIX_CERT_SHA256,,}" ]; then
      echo "build_release.sh: $apk is signed with $digest, expected $ALEFLIX_CERT_SHA256" >&2
      exit 1
    fi
  fi
  echo "ok: $apk ($name)"
}

"$FLUTTER" pub get

if [ "$TARGET" != tv ]; then
  "$FLUTTER" build apk --release --flavor mobile \
    --dart-define=DISTRIBUTION_CHANNEL=apk
  cp build/app/outputs/flutter-apk/app-mobile-release.apk "dist/Aleflix_Android_v${VERSION}.apk"
  check_apk "dist/Aleflix_Android_v${VERSION}.apk"
fi

if [ "$TARGET" != mobile ]; then
  "$FLUTTER" build apk --release --flavor androidTv \
    --dart-define=MOONFIN_FORCE_TV=true \
    --dart-define=DISTRIBUTION_CHANNEL=android_tv_apk
  cp build/app/outputs/flutter-apk/app-androidtv-release.apk "dist/Aleflix_AndroidTV_v${VERSION}.apk"
  check_apk "dist/Aleflix_AndroidTV_v${VERSION}.apk"
fi
