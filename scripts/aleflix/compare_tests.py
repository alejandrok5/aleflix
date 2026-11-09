"""Fails when Aleflix breaks a test that passes on the Moonfin release it is
built on.

Moonfin's own suite has failing tests, so "everything passes" is not the bar.
The bar is: no test may fail on Aleflix that passes on Moonfin, apart from the
expected differences listed in expected-test-differences.txt (tests that check
Moonfin's name or the themes Aleflix removed).

    python3 compare_tests.py <aleflix.jsonl> <moonfin.jsonl> <expected.txt>

The .jsonl files are `flutter test --reporter json` output. Prints the new
failures and the test files they are in (one per line after "FILES:"), and
exits 1 when there are any.
"""
import json
import sys


def results(path):
    """Returns ({test name: suite path}, set of failed names) for one run."""
    names, suites, failed = {}, {}, set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = event.get("type")
            if kind == "suite":
                suites[event["suite"]["id"]] = event["suite"].get("path", "")
            elif kind == "testStart":
                test = event["test"]
                names[test["id"]] = (test.get("name", ""), test.get("suiteID"))
            elif kind == "testDone" and not event.get("hidden"):
                if event.get("result") != "success" and not event.get("skipped"):
                    failed.add(event["testID"])
    by_name = {name: suites.get(suite, "") for name, suite in names.values()}
    failed_names = {names[t][0] for t in failed if t in names}
    return by_name, failed_names


def main():
    aleflix_path, moonfin_path, expected_path = sys.argv[1:4]
    aleflix_tests, aleflix_failed = results(aleflix_path)
    moonfin_tests, moonfin_failed = results(moonfin_path)
    with open(expected_path, encoding="utf-8") as fh:
        expected = {l.strip() for l in fh if l.strip() and not l.startswith("#")}

    # A test that does not exist in Moonfin's run is Aleflix's own and must pass.
    new = sorted(
        name for name in aleflix_failed
        if name not in moonfin_failed and name not in expected
    )
    print(f"Aleflix: {len(aleflix_tests)} tests, {len(aleflix_failed)} failing; "
          f"Moonfin: {len(moonfin_tests)} tests, {len(moonfin_failed)} failing; "
          f"new failures: {len(new)}")
    for name in new:
        print(f"  NEW FAILURE: {name}  ({aleflix_tests.get(name, '?')})")
    if new:
        print("FILES:")
        for path in sorted({aleflix_tests.get(n, "") for n in new} - {""}):
            print(path)
        sys.exit(1)


if __name__ == "__main__":
    main()
