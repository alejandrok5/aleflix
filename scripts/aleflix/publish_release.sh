#!/usr/bin/env bash
# Publishes dist/*.apk as the GitHub release for the current Aleflix version,
# tagged at the given commit. Does nothing if that release already exists.
#
#   scripts/aleflix/publish_release.sh <commit-sha>
#
# Needs gh with a token that can write releases (GH_TOKEN on CI).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SHA="${1:?usage: publish_release.sh <commit-sha>}"
VERSION="$(scripts/aleflix/version.sh)"
BASE="$(scripts/aleflix/version.sh --base)"

if gh release view "$VERSION" >/dev/null 2>&1; then
  echo "publish: release $VERSION already exists"
  exit 0
fi

shopt -s nullglob
apks=(dist/Aleflix_Android_v"$VERSION".apk dist/Aleflix_AndroidTV_v"$VERSION".apk)
for apk in "${apks[@]}"; do
  [ -f "$apk" ] || { echo "publish: missing $apk" >&2; exit 1; }
done

notes="$(mktemp)"
cat > "$notes" <<NOTES
Aleflix ${VERSION}, built on [Moonfin ${BASE}](https://github.com/Moonfin-Client/Moonfin-Core/releases/tag/${BASE}).

- **Phone / tablet:** \`Aleflix_Android_v${VERSION}.apk\`
- **Android TV / Google TV:** \`Aleflix_AndroidTV_v${VERSION}.apk\`

Installed copies find this release under Settings → About → Check for updates.
NOTES

gh release create "$VERSION" "${apks[@]}" \
  --target "$SHA" \
  --title "Aleflix ${VERSION}" \
  --notes-file "$notes"
echo "publish: released Aleflix $VERSION"
