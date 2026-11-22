"""Convert Elections ACT ballot paper preference data to PrefLib SOI profiles.

Elections ACT publishes, for each Legislative Assembly election, one CSV per
electorate (<Electorate>Total.txt) with a row per preference:
"batch","pindex","pref","pcode","ccode","rcand". A ballot paper is identified
by (batch, pindex); (pcode, ccode) identifies the candidate within the
electorate (Candidates.txt), and pcode the party group (Groups.txt).

A paper's preferences are read 1, 2, 3, ... and stop at the first missing
number, at a number given to two candidates, or at a candidate numbered twice.
This is how a Hare-Clark paper is counted. Papers with no usable first
preference are not in the data. Identical rankings are aggregated.
"""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
SOURCES = json.loads((HERE / "sources.json").read_text())
ABB = "act"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    return [r for r in rows[1:] if r]


def find(folder, name):
    matches = [p for p in folder.iterdir() if p.name.lower() == name.lower()]
    assert len(matches) == 1, (folder, name)
    return matches[0]


def check_sources(folder, year):
    for name, digest in SOURCES[year]["files"].items():
        actual = hashlib.sha256((folder / name).read_bytes()).hexdigest()
        assert actual == digest, f"{year}/{name}: SHA-256 mismatch"


def read_election(folder, year):
    check_sources(folder, year)
    electorates = read_csv(find(folder, "Electorates.txt"))
    groups = read_csv(find(folder, "Groups.txt"))
    candidates = read_csv(find(folder, "Candidates.txt"))
    contests = []
    for ecode, electorate in electorates:
        party = {g[1]: g[2] for g in groups if g[0] == ecode}
        cands = [c for c in candidates if c[0] == ecode]
        index = {(c[1], c[2]): i for i, c in enumerate(cands)}
        assert len(index) == len(cands)
        labels = [f"{c[3]} ({party.get(c[1], 'UNGROUPED')})" for c in cands]
        source = find(folder, f"{electorate.replace(' ', '')}Total.txt")
        papers = defaultdict(dict)
        rows = 0
        for batch, pindex, pref, pcode, ccode, _ in read_csv(source):
            rows += 1
            cand = index[(pcode, ccode)]
            prefs = papers[(batch, pindex)]
            n = int(pref)
            # Two candidates at the same number: the paper stops there.
            prefs[n] = None if n in prefs else cand
        profile = Counter()
        for prefs in papers.values():
            order, seen = [], set()
            n = 1
            while n in prefs and prefs[n] is not None and prefs[n] not in seen:
                seen.add(prefs[n])
                order.append(prefs[n] + 1)
                n += 1
            if order:
                profile[tuple(order)] += 1
        contests.append(dict(
            year=year, date=SOURCES[year]["date"], electorate=electorate,
            seats=SOURCES[year]["seats"].get(electorate, 5), candidates=labels,
            papers=len(papers), preference_rows=rows, ballots=sum(profile.values()),
            profile=profile, source_file=source.name,
            report_url=f"https://stv.vote/report/au/act/{year}/10/{slug(electorate)}"))
    return contests


def soi_text(header, labels, profile):
    text = "".join(f"# {k}: {v}".rstrip() + "\n" for k, v in header.items())
    text += "".join(f"# ALTERNATIVE NAME {i}: {name}\n" for i, name in enumerate(labels, 1))
    text += "".join(f"{count}: {', '.join(map(str, order))}\n"
                    for order, count in sorted(profile.items(), key=lambda x: (-x[1], x[0])))
    return text


def info_row(values):
    return ", ".join('"""' + str(v) + '"""' if "," in str(v) else str(v) for v in values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True,
                        help="folder holding act-2008 ... act-2024, one per election")
    parser.add_argument("--series", default="00079")
    parser.add_argument("--publication-date", default="")
    parser.add_argument("--modification-date", default="2026-11-22")
    args = parser.parse_args()
    assert re.fullmatch(r"\d{5}", args.series)
    contests = [c for year in SOURCES for c in read_election(args.source_root / f"act-{year}", year)]
    dest = ROOT / "datasets" / f"{args.series} - {ABB}"
    dest.mkdir(exist_ok=True)
    assert not list(dest.glob("*.soi")), "Use a fresh output directory"
    companion = f"{args.series}-{len(contests) + 1:08d}.dat"
    records, manifest = [], []
    for n, c in enumerate(contests, 1):
        filename = f"{args.series}-{n:08d}.soi"
        title = f"{c['year']} ACT Legislative Assembly - {c['electorate']}"
        header = {"FILE NAME": filename, "TITLE": title,
                  "DESCRIPTION": f"{c['date']}; Hare-Clark STV, {c['seats']} seats. Partial rankings as counted. Source: Elections ACT; reports: stv.vote.",
                  "DATA TYPE": "soi", "MODIFICATION TYPE": "original", "RELATES TO": "",
                  "RELATED FILES": companion, "PUBLICATION DATE": args.publication_date,
                  "MODIFICATION DATE": args.modification_date,
                  "NUMBER ALTERNATIVES": len(c["candidates"]), "NUMBER VOTERS": c["ballots"],
                  "NUMBER UNIQUE ORDERS": len(c["profile"])}
        text = soi_text(header, c["candidates"], c["profile"])
        (dest / filename).write_text(text, encoding="utf-8")
        meta = {k: v for k, v in c.items() if k not in ("profile", "candidates")}
        meta.update(file_name=filename, title=title,
                    source_sha256=SOURCES[c["year"]]["files"][c["source_file"]])
        records.append(meta)
        manifest.append(dict(meta, output_sha256=hashlib.sha256(text.encode()).hexdigest()))
    columns = ["file_name", "year", "date", "electorate", "seats", "ballots", "papers",
               "preference_rows", "source_file", "source_sha256", "report_url"]
    with (dest / companion).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    total = sum(r["ballots"] for r in records)
    description = (
        "<p>Ranked ballot profiles from the Australian Capital Territory Legislative Assembly elections of "
        f"2008, 2012, 2016, 2020 and 2024: {len(records)} electorate contests containing {total:,} ballots. "
        "The Assembly is elected by Hare-Clark single transferable vote, with five seats per electorate "
        "(seven in Molonglo in 2008 and 2012). The source is the ballot paper preference data published "
        'by <a href="https://www.elections.act.gov.au/">Elections ACT</a> from its electronic counting system, '
        "which records the preferences on every formal ballot paper. Felix Sargent converted the files to "
        'PrefLib; interactive reports are hosted on <a href="https://stv.vote/">stv.vote</a>.</p>'
        "<p>Each paper's preferences are read in order and stop at the first missing number, at a number "
        "given to two candidates, or at a candidate numbered twice, as in a Hare-Clark count. Identical "
        "rankings are combined with their exact multiplicities, and unranked candidates remain unranked. "
        "Candidate labels are the source names with their party group. "
        f"{companion} is a CSV crosswalk giving seats, ballot and paper counts, source files, checksums and "
        "stv.vote report links. It is metadata, not a further election.</p>")
    text = (f"Name: ACT Legislative Assembly Elections\n\nAbbreviation: {ABB}\n\nTags: Election,Politics,STV\n\n"
            f"Series Number: {args.series}\n\nPublication Date: {args.publication_date}\n\nDescription: {description}\n\n"
            "Required Citations: Elections ACT. Ballot paper preference data, ACT Legislative Assembly elections 2008-2024. "
            "https://www.elections.act.gov.au/ ; Felix Sargent. stv.vote: ACT election reports and PrefLib conversion. https://stv.vote/\n\n"
            "Selected Studies:\n\n")
    rows = [info_row(["file_name", "modification_type", "relates_to", "title", "description", "publication_date"])]
    rows += [info_row([r["file_name"], "original", "", r["title"], f"{r['seats']} seats; {r['ballots']} ballots",
                       args.publication_date]) for r in records]
    rows.append(info_row([companion, "original", "", "ACT Legislative Assembly contest crosswalk",
                          "CSV metadata and report links", args.publication_date]))
    (dest / "info.txt").write_text("\n".join(l.rstrip() for l in (text + "\n".join(rows)).splitlines()) + "\n",
                                   encoding="utf-8")
    summary = dict(sources=SOURCES, contests=len(records), ballots=total, files=manifest)
    (HERE / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Wrote {len(records)} profiles: {total:,} ballots")


if __name__ == "__main__":
    main()
