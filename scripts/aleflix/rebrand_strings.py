#!/usr/bin/env python3
"""Rebrand user-visible strings in the ARB translation files from Moonfin to Aleflix.

Idempotent: safe to re-run after every upstream merge. On a merge conflict in
lib/l10n/, take upstream's side (`git checkout --theirs lib/l10n`), re-run this
script, then `flutter gen-l10n`.

Only the values of top-level message keys change. Keys, @metadata and
descriptions stay as upstream wrote them, so diffs against upstream remain
small and line-for-line.

usage: python3 scripts/aleflix/rebrand_strings.py [--check]
  --check   report how many values would change and exit 1 if any would
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
L10N = ROOT / "lib" / "l10n"

# Whole-value overrides, applied in every language (brand names aren't translated).
OVERRIDES = {
    "sourceCodeUrl": "https://github.com/alejandrok5/aleflix",
    "themeMoonfin": "Aleflix Noir",
}

# Keys where "Moonfin" names the Moonbase server plugin rather than the app.
PLUGIN_KEYS = {"savedThemesDescription"}

LINE = re.compile(r'^(\s*)"([^"@][^"]*)"(\s*:\s*)"((?:[^"\\]|\\.)*)"(\s*,?\s*)$')


def rebrand_value(key, value):
    if key in OVERRIDES:
        return json.dumps(OVERRIDES[key], ensure_ascii=False)[1:-1]
    target = "Moonbase" if key in PLUGIN_KEYS else "Aleflix"
    return value.replace("Moonfin", target)


def process(path, check):
    text = path.read_text(encoding="utf-8")
    top_level = set(json.loads(text).keys())
    changed = 0
    out = []
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        eol = line[len(body):]
        m = LINE.match(body)
        if m and m.group(2) in top_level:
            indent, key, sep, value, tail = m.groups()
            new = rebrand_value(key, value)
            if new != value:
                changed += 1
                body = f'{indent}"{key}"{sep}"{new}"{tail}'
        out.append(body + eol)
    if changed and not check:
        new_text = "".join(out)
        json.loads(new_text)  # never write a file that no longer parses
        path.write_text(new_text, encoding="utf-8")
    return changed


def main():
    check = "--check" in sys.argv[1:]
    total = 0
    for path in sorted(L10N.glob("app_*.arb")):
        total += process(path, check)
    verb = "would change" if check else "changed"
    print(f"{verb} {total} values across {len(list(L10N.glob('app_*.arb')))} ARB files")
    if check and total:
        sys.exit(1)


if __name__ == "__main__":
    main()
