"""Independently reconcile PrefLib profiles against the original rank vectors."""

import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

from preflibtools.instances import OrdinalInstance

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--series", default="00078")
    args = parser.parse_args()
    folder = ROOT / "datasets" / f"{args.series} - scotland2022"
    manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
    assert hashlib.sha256(args.source.read_bytes()).hexdigest() == manifest["source_sha256"]
    crosswalk = list(csv.DictReader((folder / f"{args.series}-00000348.dat").open()))
    assert len(crosswalk) == len(manifest["files"]) == 347
    total, unique = 0, 0
    first_preferences = Counter()
    with zipfile.ZipFile(args.source) as source:
        for row in crosswalk:
            content = source.read(row["source_path"])
            assert hashlib.sha256(content).hexdigest() == row["source_sha256"]
            lines = content.decode().splitlines()
            seats, nc, nr, ballots = map(int, lines[1].split())
            instance = OrdinalInstance(str(folder / row["file_name"]))
            assert instance.data_type == "soi"
            # PrefLib's metadata parser strips surrounding whitespace from labels.
            assert instance.alternatives_name == dict(enumerate((s.strip() for s in lines[2:2 + nc]), 1))
            assert seats == int(row["seats"]) and ballots == int(row["ballots"])
            expected = Counter()
            for line in lines[2 + nc:]:
                if line.strip():
                    count, *ranks = map(int, line.split())
                    expected[tuple(ranks)] += count
            actual = Counter()
            for order, count in instance.multiplicity.items():
                ranks = [0] * nc
                for rank, tier in enumerate(order, 1):
                    assert len(tier) == 1
                    ranks[tier[0] - 1] = rank
                actual[tuple(ranks)] += count
                first_preferences[(row["file_name"], order[0][0])] += count
            assert actual == expected, row["source_path"]
            assert instance.num_voters == sum(actual.values()) == ballots
            assert instance.num_unique_orders == len(expected)
            total += ballots
            unique += len(expected)
        covered = {r["source_path"] for r in crosswalk}
        excluded = {r["source_path"] for r in manifest["excluded_wards"]}
        assert covered.isdisjoint(excluded)
        assert covered | excluded == {n for n in source.namelist() if n.endswith(".dat")}
        for name in excluded:
            lines = source.read(name).decode().splitlines()
            _, nc, nr, ballots = map(int, lines[1].split())
            assert nr == ballots == 0 and not any(s.strip() for s in lines[2 + nc:])
    spec = importlib.util.spec_from_file_location("sanitychecks", ROOT / "scripts/sanitychecks.py")
    sanity = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sanity)
    sanity.check_dataset(folder.name, True)
    for record in manifest["files"]:
        assert hashlib.sha256((folder / record["file_name"]).read_bytes()).hexdigest() == record["output_sha256"]
    result = dict(profiles=len(crosswalk), excluded_uncontested_wards=len(excluded), ballots=total,
                  unique_rankings=unique, exact_source_reconciliation=True,
                  repository_sanity_checks="passed_with_warnings_escalated")
    (Path(__file__).parent / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
