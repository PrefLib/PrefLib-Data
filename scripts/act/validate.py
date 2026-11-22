"""Check the ACT PrefLib profiles against a second, independent conversion.

stv.vote converts the same Elections ACT files with its own TypeScript code
(scripts/convert-act-preferences.ts) into gzipped JSON profiles:
{electorate, candidates: [{name, party}], ballots: [[count, [index, ...]], ...]}.
This script parses every PrefLib file with preflibtools and requires the exact
same ranking frequencies, candidate count and ballot total as that profile. It
also re-checks the source checksums, the output checksums and the repository
sanity checks with warnings escalated, and writes validation.json.

Usage: validate.py --source-root <folder with act-2008 ...> --stv-profiles <stv.vote raw-data/au/act>
"""

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re

from preflibtools.instances import OrdinalInstance

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--stv-profiles", type=Path, required=True)
    parser.add_argument("--series", default="00079")
    args = parser.parse_args()
    folder = ROOT / "datasets" / f"{args.series} - act"
    manifest = json.loads((HERE / "manifest.json").read_text())
    for year, source in manifest["sources"].items():
        for name, digest in source["files"].items():
            path = args.source_root / f"act-{year}" / name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
    crosswalk = list(csv.DictReader(next(folder.glob("*.dat")).open(encoding="utf-8")))
    assert len(crosswalk) == len(manifest["files"]) == manifest["contests"]
    total = unique = 0
    for row in crosswalk:
        instance = OrdinalInstance(str(folder / row["file_name"]))
        assert instance.data_type == "soi"
        profile = json.loads(gzip.decompress(
            (args.stv_profiles / row["year"] / f"{slug(row['electorate'])}.json.gz").read_bytes()))
        assert profile["electorate"] == row["electorate"]
        assert len(profile["candidates"]) == instance.num_alternatives
        expected = Counter({tuple(i + 1 for i in order): count for count, order in profile["ballots"]})
        actual = Counter()
        for order, count in instance.multiplicity.items():
            assert all(len(tier) == 1 for tier in order)
            actual[tuple(tier[0] for tier in order)] += count
        assert actual == expected, row["file_name"]
        assert instance.num_voters == sum(expected.values()) == int(row["ballots"])
        assert instance.num_unique_orders == len(expected)
        # Every source paper with a usable first preference is counted.
        assert int(row["ballots"]) <= int(row["papers"])
        total += instance.num_voters
        unique += len(expected)
    assert total == manifest["ballots"]
    spec = importlib.util.spec_from_file_location("sanitychecks", ROOT / "scripts/sanitychecks.py")
    sanity = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sanity)
    sanity.check_dataset(folder.name, True)
    for record in manifest["files"]:
        assert hashlib.sha256((folder / record["file_name"]).read_bytes()).hexdigest() == record["output_sha256"]
    result = dict(profiles=len(crosswalk), ballots=total, unique_rankings=unique,
                  papers_without_usable_first_preference=sum(int(r["papers"]) - int(r["ballots"]) for r in crosswalk),
                  matches_independent_stv_vote_conversion=True,
                  repository_sanity_checks="passed_with_warnings_escalated")
    (HERE / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
