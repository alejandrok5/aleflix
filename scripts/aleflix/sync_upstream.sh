#!/usr/bin/env bash
# Merges a Moonfin release into the current branch and re-applies the Aleflix
# rebrand, then sets the Aleflix version for it.
#
#   scripts/aleflix/sync_upstream.sh [tag]     tag defaults to Moonfin's latest release
#   scripts/aleflix/sync_upstream.sh main      Moonfin's latest commits, released or not
#
# Exit codes:
#    0  merged; two commits were made (the merge, then the rebrand + version)
#   10  nothing to do, that release is already merged
#   20  conflicts outside the localization files; the merge was aborted
#
# Localization files (lib/l10n) are taken from Moonfin on conflict, because the
# rebrand script re-derives every Aleflix change to them. Moonfin's GitHub
# workflow files are kept out of the fork: Aleflix runs its own (aleflix-*.yml),
# and Moonfin's are disabled here. README.md is Aleflix's own, so Moonfin's
# edits to it are dropped.
#
# Needs: git, gh (for the latest release), python3, flutter (for gen-l10n).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

UPSTREAM_REPO="Moonfin-Client/Moonfin-Core"
FLUTTER="${FLUTTER_BIN:-flutter}"

if ! git remote get-url upstream >/dev/null 2>&1; then
  git remote add upstream "https://github.com/${UPSTREAM_REPO}.git"
fi
git fetch --quiet --tags upstream

TAG="${1:-}"
if [ -z "$TAG" ]; then
  TAG="$(gh release view --repo "$UPSTREAM_REPO" --json tagName --jq .tagName)"
fi
# A release tag, or a Moonfin branch (main) at its current commit. A branch is
# named by its commit, so the CI branch and the test checkout stay put while
# Moonfin moves on.
if git rev-parse -q --verify "refs/tags/${TAG}^{commit}" >/dev/null; then
  COMMIT="$(git rev-parse "refs/tags/${TAG}^{commit}")"
  UPSTREAM_URL="https://github.com/${UPSTREAM_REPO}/releases/tag/${TAG}"
elif git rev-parse -q --verify "refs/remotes/upstream/${TAG}^{commit}" >/dev/null; then
  COMMIT="$(git rev-parse "refs/remotes/upstream/${TAG}^{commit}")"
  UPSTREAM_URL="https://github.com/${UPSTREAM_REPO}/commit/${COMMIT}"
  TAG="${TAG}-${COMMIT:0:10}"
else
  echo "sync: Moonfin tag or branch '$TAG' not found" >&2
  exit 1
fi
echo "sync: Moonfin release $TAG"
echo "sync: Moonfin commit $COMMIT"

if git merge-base --is-ancestor "$COMMIT" HEAD; then
  echo "sync: Moonfin $TAG is already merged"
  exit 10
fi

prev_base="$(scripts/aleflix/version.sh --base)"
prev_revision="$(grep -E '^revision=' aleflix.properties | cut -d= -f2 | tr -d '[:space:]')"

if ! git merge --no-ff --no-commit "$COMMIT"; then
  while IFS= read -r file; do
    case "$file" in
      lib/l10n/*)
        git checkout --theirs -- "$file"
        git add -- "$file"
        ;;
      .github/workflows/*|README.md)
        # Aleflix's side always wins here (see the restore below).
        if git cat-file -e "HEAD:$file" 2>/dev/null; then
          git checkout --ours -- "$file"
          git add -- "$file"
        else
          git rm -q --cached -- "$file" 2>/dev/null || true
          rm -f -- "$file"
        fi
        ;;
    esac
  done < <(git diff --name-only --diff-filter=U)

  remaining="$(git diff --name-only --diff-filter=U)"
  if [ -n "$remaining" ]; then
    echo "sync: Moonfin $TAG conflicts with Aleflix changes in:" >&2
    printf '  %s\n' $remaining >&2
    git merge --abort
    exit 20
  fi
fi

# Keep the fork's own workflow set and README. Leaving the workflows alone also
# keeps the push possible with the Actions token, which may not change them.
git restore --source=HEAD --staged --worktree -- .github/workflows README.md 2>/dev/null || true

git commit --quiet --no-edit -m "Merge Moonfin ${TAG}" -m "Upstream: ${UPSTREAM_URL}"

# Re-apply the rebrand to whatever strings came in.
python3 scripts/aleflix/rebrand_strings.py
"$FLUTTER" pub get >/dev/null
"$FLUTTER" gen-l10n

# Follow Moonfin's Flutter pin for builds and tests.
moonfin_flutter="$(git show "${COMMIT}:.github/workflows/build.yml" 2>/dev/null \
  | sed -nE "s/^[[:space:]]*FLUTTER_VERSION:[[:space:]]*'?([0-9.]+)'?.*/\1/p" | head -1)"
if [ -n "$moonfin_flutter" ]; then
  printf '%s\n' "$moonfin_flutter" > scripts/aleflix/flutter-version
fi

new_base="$(scripts/aleflix/version.sh --base)"
if [ "$new_base" != "$prev_base" ]; then
  revision=1
else
  revision=$((prev_revision + 1))
fi
sed -i -E "s/^revision=.*/revision=${revision}/" aleflix.properties

git add -A lib/l10n aleflix.properties scripts/aleflix/flutter-version
if git diff --cached --quiet; then
  echo "sync: nothing to rebrand"
else
  git commit --quiet -m "Rebrand Moonfin ${TAG} as Aleflix $(scripts/aleflix/version.sh)"
fi

echo "sync: merged Moonfin $TAG as Aleflix $(scripts/aleflix/version.sh)"
