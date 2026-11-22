"""Check the Alaska PrefLib profiles against ranked.vote's independent count.

ranked.vote reads the same cast vote records with its own TypeScript loader
and Alaska's skipped-ranking rule, and stores per contest the first-round votes
of every candidate and the full pairwise table (how many ballots rank each
candidate above each other, a ranked candidate beating an unranked one). This
script parses every PrefLib file with preflibtools and requires:

- the first preferences of each alternative to equal ranked.vote's first-round votes;
- every pairwise count to equal ranked.vote's.

It also re-checks the source and output checksums and runs the repository sanity
checks with warnings escalated, and writes validation.json.

Usage: validate.py --source-root <dir> --reports <ranked.vote>/report_pipeline/reports.sqlite3
"""

import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3

from preflibtools.instances import OrdinalInstance

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent


def name_key(label):
    """Order- and punctuation-insensitive key: 'Peltola, Mary S. (Dem)' ~ 'Mary S. Peltola'."""
    label = re.sub(r" \([^()]*\)$", "", label)
    return tuple(sorted(re.findall(r"[a-z0-9]+", label.lower())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--series", default="00081")
    args = parser.parse_args()
    folder = ROOT / "datasets" / f"{args.series} - alaska"
    manifest = json.loads((HERE / "manifest.json").read_text())
    for meta in manifest["sources"].values():
        path = next(args.source_root.glob(f"*/{meta['file']}"))
        assert hashlib.sha256(path.read_bytes()).hexdigest() == meta["sha256"], path
    db = sqlite3.connect(args.reports)
    crosswalk = list(csv.DictReader(next(folder.glob("*.dat")).open(encoding="utf-8")))
    assert len(crosswalk) == len(manifest["files"]) == manifest["contests"]
    total = pairs = 0
    for row in crosswalk:
        instance = OrdinalInstance(str(folder / row["file_name"]))
        assert instance.data_type == "soi"
        report_id, pairwise = db.execute(
            "SELECT id, pairwisePreferences FROM reports WHERE path = ? AND office = ?",
            (f"us/ak/{row['election']}", row["office"])).fetchone()
        stored = {name_key(name): (index, votes) for index, name, votes in db.execute(
            "SELECT candidate_index, name, firstRoundVotes FROM candidates WHERE report_id = ?", (report_id,))}
        alt_index = {}
        for alt, label in instance.alternatives_name.items():
            alt_index[alt] = stored[name_key(label)][0]
        assert len(set(alt_index.values())) == len(alt_index) == len(stored), row["file_name"]
        first = Counter()
        beats = Counter()
        for order, count in instance.multiplicity.items():
            ranked = [tier[0] for tier in order]
            assert all(len(tier) == 1 for tier in order)
            first[ranked[0]] += count
            for i, a in enumerate(ranked):
                for b in alternatives_after(ranked, i, instance.alternatives_name):
                    beats[(a, b)] += count
        for alt, label in instance.alternatives_name.items():
            assert first[alt] == stored[name_key(label)][1], (row["file_name"], label)
        table = json.loads(pairwise)
        position = {c: i for i, c in enumerate(table["rows"])}
        for a in alt_index:
            for b in alt_index:
                if a != b:
                    entry = table["entries"][position[alt_index[a]]][position[alt_index[b]]]
                    assert beats[(a, b)] == (entry["numerator"] if entry else 0), (row["file_name"], a, b)
                    pairs += 1
        assert instance.num_voters == sum(first.values()) == int(row["ballots"])
        total += instance.num_voters
    assert total == manifest["ballots"]
    spec = importlib.util.spec_from_file_location("sanitychecks", ROOT / "scripts/sanitychecks.py")
    sanity = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sanity)
    sanity.check_dataset(folder.name, True)
    for record in manifest["files"]:
        assert hashlib.sha256((folder / record["file_name"]).read_bytes()).hexdigest() == record["output_sha256"]
    result = dict(profiles=len(crosswalk), ballots=total,
                  no_counted_preference=sum(int(r["no_counted_preference"]) for r in crosswalk),
                  invalid_contest_records=sum(int(r["invalid_contest_records"]) for r in crosswalk),
                  first_preferences_match_ranked_vote=True, pairwise_counts_checked=pairs,
                  pairwise_counts_match_ranked_vote=True,
                  repository_sanity_checks="passed_with_warnings_escalated")
    (HERE / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def alternatives_after(ranked, i, alternatives):
    """Alternatives the i-th ranked one beats: those ranked later, then all unranked ones."""
    later = ranked[i + 1:]
    unranked = [a for a in alternatives if a not in ranked]
    return later + unranked


if __name__ == "__main__":
    main()
