"""Check the 2025 Senate PrefLib profiles against a second, independent conversion.

stv.vote converts the same AEC files with its own TypeScript code
(scripts/convert-aec-senate.ts) into gzipped JSON profiles:
{electorate, candidates: [{name, party}], ballots: [[count, [index, ...]], ...]}.
This script parses every PrefLib file (compressed or not) with preflibtools and
requires the exact same ranking frequencies, candidate count and ballot total
as that profile. It also re-checks the source checksums, the checksums of the
plain output, and runs the repository sanity checks with warnings escalated,
then writes validation.json.

Usage: validate.py --source-root <folder with the AEC zips> --stv-profiles <stv.vote>/raw-data/au/senate/2025
"""

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT / "scripts"))
from datafiles import open_data_file, parse_instance  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--stv-profiles", type=Path, required=True)
    parser.add_argument("--series", default="00080")
    args = parser.parse_args()
    folder = ROOT / "datasets" / f"{args.series} - aec_senate_2025"
    manifest = json.loads((HERE / "manifest.json").read_text())
    crosswalk = list(csv.DictReader(next(folder.glob("*.dat")).open(encoding="utf-8")))
    assert len(crosswalk) == len(manifest["files"]) == manifest["contests"]
    total = unique = 0
    for row, record in zip(crosswalk, manifest["files"]):
        assert row["file_name"] == record["file_name"]
        source = args.source_root / record["source_file"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == row["source_sha256"]
        assert (folder / row["stored_as"]).exists()
        digest = hashlib.sha256()
        with open_data_file(str(folder / row["file_name"])) as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                digest.update(chunk)
        assert digest.hexdigest() == record["output_sha256"], row["file_name"]
        instance = parse_instance(str(folder / row["file_name"]))
        assert instance.data_type == "soi"
        profile = json.loads(gzip.decompress((args.stv_profiles / f"{row['code'].lower()}.json.gz").read_bytes()))
        assert profile["electorate"] == row["state"]
        assert len(profile["candidates"]) == instance.num_alternatives
        expected = Counter({tuple(i + 1 for i in order): count for count, order in profile["ballots"]})
        actual = Counter()
        for order, count in instance.multiplicity.items():
            assert all(len(tier) == 1 for tier in order)
            actual[tuple(tier[0] for tier in order)] += count
        assert actual == expected, row["file_name"]
        assert instance.num_voters == sum(expected.values()) == int(row["ballots"])
        assert int(row["ballots"]) + int(row["no_usable_preference"]) == int(row["papers"])
        print(f"{row['code']}: {instance.num_voters:,} ballots match")
        total += instance.num_voters
        unique += len(expected)
    assert total == manifest["ballots"]
    spec = importlib.util.spec_from_file_location("sanitychecks", ROOT / "scripts/sanitychecks.py")
    sanity = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sanity)
    sanity.check_dataset(folder.name, True)
    result = dict(profiles=len(crosswalk), ballots=total, unique_rankings=unique,
                  papers_without_usable_preference=sum(int(r["no_usable_preference"]) for r in crosswalk),
                  compressed_files=[r["stored_as"] for r in crosswalk if r["stored_as"].endswith(".gz")],
                  matches_independent_stv_vote_conversion=True,
                  repository_sanity_checks="passed_with_warnings_escalated")
    (HERE / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
