#!/usr/bin/env bash
# Prints the Aleflix release version: Moonfin's version from pubspec.yaml plus
# the revision from aleflix.properties (3.0.0 + 1 -> 3.0.0.1).
#
#   scripts/aleflix/version.sh          full version, e.g. 3.0.0.1
#   scripts/aleflix/version.sh --base   Moonfin's version, e.g. 3.0.0
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

base=$(grep -E '^version:' "$ROOT/pubspec.yaml" | sed -E 's/^version:[[:space:]]*//; s/\+.*//' | tr -d '[:space:]')
tv_base=$(grep -E '^[[:space:]]*android_tv_version:' "$ROOT/pubspec.yaml" | sed -E 's/.*android_tv_version:[[:space:]]*//' | tr -d '[:space:]')
revision=$(grep -E '^revision=' "$ROOT/aleflix.properties" | cut -d= -f2 | tr -d '[:space:]')

if [ -z "$base" ] || [ -z "$revision" ]; then
  echo "version.sh: could not read the version from pubspec.yaml or aleflix.properties" >&2
  exit 1
fi
# One release carries both APKs under one tag, so the phone and TV versions
# have to agree. Moonfin keeps them equal; stop loudly if that ever changes.
if [ -n "$tv_base" ] && [ "$tv_base" != "$base" ]; then
  echo "version.sh: pubspec version ($base) and android_tv_version ($tv_base) differ" >&2
  exit 1
fi

if [ "${1:-}" = "--base" ]; then
  printf '%s\n' "$base"
else
  printf '%s.%s\n' "$base" "$revision"
fi
