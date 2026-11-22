"""Convert Alaska cast vote records to PrefLib SOI profiles.

Alaska's Division of Elections publishes a Dominion cast vote record export
(NIST SP 1500-103 JSON) for each election counted by ranked-choice voting. Each
session record holds, per contest, the marks read from the ballot: a candidate
and a rank, flagged when ambiguous.

Each ballot is read as Alaska counts it (AS 15.15.350):

- ambiguous marks are ignored;
- a rank with no mark is a skipped ranking, and two consecutive skipped
  rankings end the ballot;
- a rank marked for more than one candidate (an overvote) ends the ballot;
- a candidate ranked again is ignored at the later rank.

Records the export flags with the InvalidContest outstack condition are left
out, as the official count leaves them out. All write-ins in a contest form one
"Write-in" alternative. Identical rankings are aggregated. Ballots with no
counted preference are left out and counted in the crosswalk.
"""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
SOURCES = json.loads((HERE / "sources.json").read_text())
ABB = "alaska"


def session_contests(session):
    """Contests of a session, chosen as ranked.vote does."""
    original = session["Original"]
    if original.get("Contests"):
        return original["Contests"]
    ballot = session.get("Modified") or original
    return [c for card in ballot.get("Cards", []) for c in card["Contests"]]


def ranking(marks, label_of):
    by_rank = defaultdict(list)
    for m in marks:
        if not m["IsAmbiguous"]:
            by_rank[m["Rank"]].append(m["CandidateId"])
    last = max((m["Rank"] for m in marks), default=0)
    order, skipped = [], False
    for rank in range(1, last + 1):
        marked = by_rank.get(rank, [])
        if not marked:
            if skipped:
                break
            skipped = True
            continue
        if len(marked) > 1:
            break
        skipped = False
        alt = label_of[marked[0]]
        if alt not in order:
            order.append(alt)
    return tuple(order)


def read_election(source_root, key):
    meta = SOURCES[key]
    path = next(source_root.glob(f"*/{meta['file']}"))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == meta["sha256"], f"{path}: SHA-256 mismatch"
    with zipfile.ZipFile(path) as archive:
        manifest = lambda name: json.loads(archive.read(name))["List"]
        parties = {p["Id"]: p["Description"] for p in manifest("PartyManifest.json")}
        contests = {c["Id"]: c for c in manifest("ContestManifest.json")}
        invalid = {o["Id"] for o in manifest("OutstackConditionManifest.json") if o["Description"] == "InvalidContest"}
        wanted = {c["contest_id"]: c for c in meta["contests"]}
        alternatives, label_of = {}, {}
        for cid in wanted:
            labels = []
            for entry in manifest("CandidateManifest.json"):
                if entry["ContestId"] != cid:
                    continue
                if entry["Type"] == "WriteIn":
                    label = "Write-in"
                else:
                    party = "; ".join(parties[a] for a in entry.get("Affiliations") or [] if a in parties)
                    label = f"{entry['Description']} ({party})" if party else entry["Description"]
                if label not in labels:
                    labels.append(label)
                label_of[entry["Id"]] = labels.index(label) + 1
            alternatives[cid] = labels
        profiles = {cid: Counter() for cid in wanted}
        records = Counter()
        excluded = Counter()
        files = sorted(n for n in archive.namelist() if re.fullmatch(r"CvrExport(_\d+)?\.json", n))
        for name in files:
            for session in json.loads(archive.read(name))["Sessions"]:
                for contest in session_contests(session):
                    cid = contest["Id"]
                    if cid not in wanted:
                        continue
                    if invalid & set(contest.get("OutstackConditionIds") or []):
                        excluded[cid] += 1
                        continue
                    records[cid] += 1
                    marks = contest["Marks"] if isinstance(contest["Marks"], list) else []
                    order = ranking(marks, label_of)
                    profiles[cid][order] += 1
    out = []
    for cid, c in wanted.items():
        profile = profiles[cid]
        empty = profile.pop((), 0)
        out.append(dict(
            election=key, election_name=meta["name"], date=meta["date"], contest_id=cid,
            contest=contests[cid]["Description"], office=c["office"], office_name=c["office_name"],
            candidates=alternatives[cid], records=records[cid], invalid_contest_records=excluded[cid],
            no_counted_preference=empty, ballots=sum(profile.values()), profile=profile,
            source_file=meta["file"], source_sha256=meta["sha256"],
            report_url=f"https://ranked.vote/report/us/ak/{key}/{c['office']}"))
    return out


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
                        help="folder whose subfolders hold the three CVR zips")
    parser.add_argument("--series", default="00081")
    parser.add_argument("--publication-date", default="")
    parser.add_argument("--modification-date", default="2026-11-22")
    args = parser.parse_args()
    assert re.fullmatch(r"\d{5}", args.series)
    contests = []
    for key in SOURCES:
        contests += read_election(args.source_root, key)
        print(f"{key}: read {len(SOURCES[key]['contests'])} contests")
    dest = ROOT / "datasets" / f"{args.series} - {ABB}"
    dest.mkdir(exist_ok=True)
    assert not list(dest.glob("*.soi")), "Use a fresh output directory"
    companion = f"{args.series}-{len(contests) + 1:08d}.dat"
    records, manifest = [], []
    for n, c in enumerate(contests, 1):
        filename = f"{args.series}-{n:08d}.soi"
        title = f"{c['date'][:4]} Alaska {c['election_name']} - {c['office_name']}"
        header = {"FILE NAME": filename, "TITLE": title,
                  "DESCRIPTION": f"{c['date']}; instant runoff, 1 seat. Rankings as counted under AS 15.15.350. Source: Alaska Division of Elections; reports: ranked.vote.",
                  "DATA TYPE": "soi", "MODIFICATION TYPE": "original", "RELATES TO": "",
                  "RELATED FILES": companion, "PUBLICATION DATE": args.publication_date,
                  "MODIFICATION DATE": args.modification_date,
                  "NUMBER ALTERNATIVES": len(c["candidates"]), "NUMBER VOTERS": c["ballots"],
                  "NUMBER UNIQUE ORDERS": len(c["profile"])}
        text = soi_text(header, c["candidates"], c["profile"])
        (dest / filename).write_text(text, encoding="utf-8")
        meta = {k: v for k, v in c.items() if k not in ("profile", "candidates")}
        meta.update(file_name=filename, title=title)
        records.append(meta)
        manifest.append(dict(meta, output_sha256=hashlib.sha256(text.encode()).hexdigest()))
    columns = ["file_name", "election", "election_name", "date", "contest_id", "contest", "office",
               "ballots", "records", "no_counted_preference", "invalid_contest_records",
               "source_file", "source_sha256", "report_url"]
    with (dest / companion).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    total = sum(r["ballots"] for r in records)
    description = (
        "<p>Ranked ballot profiles from Alaska's ranked-choice elections: the special general election of "
        "16 August 2022 for the U.S. House, and the general elections of 8 November 2022 and 5 November 2024. "
        f"{len(records)} single-winner instant-runoff contests containing {total:,} ballots. The general-election "
        "contests are those with at least three named candidates: President, U.S. Senate, U.S. House, Governor, "
        "and state legislative seats. The source is the cast vote record (Dominion NIST SP 1500-103 JSON) published "
        'by the <a href="https://www.elections.alaska.gov/">Alaska Division of Elections</a>. Felix Sargent converted '
        'the records to PrefLib; interactive reports are hosted on <a href="https://ranked.vote/">ranked.vote</a>.</p>'
        "<p>Each ballot is read as Alaska counts it (AS 15.15.350): ambiguous marks are ignored; two consecutive "
        "skipped rankings or an overvoted ranking end the ballot; a candidate ranked again is ignored at the later "
        "rank. Records the export marks as an invalid contest are left out, as in the official count. All write-ins "
        "form one Write-in alternative. Identical rankings are combined with their exact multiplicities, and "
        "unranked candidates remain unranked. Ballots with no counted preference are omitted and counted in the "
        f"crosswalk. {companion} is a CSV crosswalk giving contest IDs, ballot and record counts, source "
        "checksums and ranked.vote report links. It is metadata, not a further election.</p>")
    text = (f"Name: Alaska Ranked-Choice Elections 2022-2024\n\nAbbreviation: {ABB}\n\nTags: Election,Politics\n\n"
            f"Series Number: {args.series}\n\nPublication Date: {args.publication_date}\n\nDescription: {description}\n\n"
            "Required Citations: Alaska Division of Elections. Cast vote records, 2022 special general election and "
            "2022 and 2024 general elections. https://www.elections.alaska.gov/ ; Felix Sargent. ranked.vote: Alaska "
            "election reports and PrefLib conversion. https://ranked.vote/\n\nSelected Studies:\n\n")
    rows = [info_row(["file_name", "modification_type", "relates_to", "title", "description", "publication_date"])]
    rows += [info_row([r["file_name"], "original", "", r["title"], f"1 seat; {r['ballots']} ballots",
                       args.publication_date]) for r in records]
    rows.append(info_row([companion, "original", "", "Alaska contest crosswalk",
                          "CSV metadata and report links", args.publication_date]))
    (dest / "info.txt").write_text("\n".join(l.rstrip() for l in (text + "\n".join(rows)).splitlines()) + "\n",
                                   encoding="utf-8")
    summary = dict(sources=SOURCES, contests=len(records), ballots=total, files=manifest)
    (HERE / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Wrote {len(records)} profiles: {total:,} ballots")


if __name__ == "__main__":
    main()
