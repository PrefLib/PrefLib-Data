"""Convert AEC 2025 Senate formal preferences to PrefLib SOI profiles.

The AEC publishes one zipped CSV per state and territory with a row per formal
ballot paper. After six identifying columns come one column per group (above
the line, "A:Liberal") and one per candidate (below the line, "A:SMITH Jane";
"UG:" for ungrouped candidates). A cell holds a preference number, or "*" / "/"
for a tick or cross, which counts as a 1.

Each paper is read as the Commonwealth Electoral Act counts it. A
below-the-line vote numbering at least six candidates (1 to 6, each once) is
used. Otherwise the above-the-line vote is used, each group standing for its
candidates in ballot order. Preferences stop at the first missing or repeated
number. Identical rankings are aggregated.

Profiles over 50 MB are stored gzip-compressed (see README "Large data files").
"""

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
ABB = "aec_senate_2025"
URL = "https://results.aec.gov.au/31496/Website/External/aec-senate-formalpreferences-31496-{}.zip"
STATES = {  # code: (name, seats, source SHA-256)
    "NSW": ("New South Wales", 6, "0ad82e3067c0eddfdfa7df9dfc82b370d217c393f48b8c323006f936324396b0"),
    "VIC": ("Victoria", 6, "71cfd2168dc8295dfd33a19e321c2fe2d96edfb229d16a002e30e9d23e67aeca"),
    "QLD": ("Queensland", 6, "0a25d5015b7dbfcb05e3140c8a890a96aa323e1fce6c34596a384d6d87471c90"),
    "WA": ("Western Australia", 6, "c8ce58e7bedcb2c0e26308adf871cc7d3d9c4cbe986b5105e4f59472f0947846"),
    "SA": ("South Australia", 6, "f33526464953681e00cb99d1378dce5408db3962511d2f033952033d35983168"),
    "TAS": ("Tasmania", 6, "704b67fa2b754866086c6151694623069ce74364e3473aa1c2fd5fa812545523"),
    "ACT": ("Australian Capital Territory", 2, "320b42fd26a45d8719efc9c54c5cc9f3d8b4370d95365b109fd2087beff1c28a"),
    "NT": ("Northern Territory", 2, "00526d34f8dd598c8453db2136de38117513b345ecadd982ce1ad1a60cc1d4fc"),
}
COMPRESS_ABOVE = 50_000_000


def preference(cell):
    cell = cell.strip()
    if cell in ("*", "/"):
        return 1
    return int(cell) if cell.isdigit() and int(cell) > 0 else None


def sequence(cells):
    """Positions numbered 1, 2, 3, ...; stop at a missing or repeated number."""
    at, repeated = {}, set()
    for i, cell in enumerate(cells):
        if cell:
            n = preference(cell)
            if n is None:
                continue
            if n in at:
                repeated.add(n)
            else:
                at[n] = i
    order, n = [], 1
    while n in at and n not in repeated:
        order.append(at[n])
        n += 1
    return order


def read_state(source_root, code):
    name, seats, digest = STATES[code]
    path = source_root / f"aec-senate-formalpreferences-31496-{code}.zip"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"{path}: SHA-256 mismatch"
    with zipfile.ZipFile(path) as archive:
        (member,) = archive.namelist()
        with archive.open(member) as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
            header = next(reader)[6:]
            letters = [h.split(":")[0] for h in header]
            # Group columns come first; the first repeated letter starts the candidates.
            ngroups = next(i for i, l in enumerate(letters) if l in letters[:i])
            group_name = {l: h.split(":", 1)[1].strip() for l, h in zip(letters, header[:ngroups])}
            labels = []
            for l, h in zip(letters[ngroups:], header[ngroups:]):
                party = "Ungrouped" if l == "UG" else (group_name.get(l) or f"Group {l}")
                labels.append(f"{h.split(':', 1)[1].strip()} ({party})")
            members = [[i for i, cl in enumerate(letters[ngroups:]) if cl == l] for l in letters[:ngroups]]
            width = len(header)
            profile, papers, below, empty = Counter(), 0, 0, 0
            for row in reader:
                cells = row[6:]
                cells += [""] * (width - len(cells))
                papers += 1
                order = sequence(cells[ngroups:])
                if len(order) >= 6:
                    below += 1
                else:
                    order = [c for g in sequence(cells[:ngroups]) for c in members[g]]
                if not order:
                    empty += 1
                    continue
                profile[tuple(c + 1 for c in order)] += 1
    return dict(code=code, state=name, seats=seats, candidates=labels, groups=ngroups,
                papers=papers, below_the_line=below, no_usable_preference=empty,
                ballots=sum(profile.values()), profile=profile, source_file=path.name,
                source_url=URL.format(code), source_sha256=digest,
                report_url=f"https://stv.vote/report/au/senate/2025/05/{re.sub(r'[^a-z0-9]+', '-', name.lower())}")


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
    parser.add_argument("--source-root", type=Path, required=True, help="folder holding the eight AEC zips")
    parser.add_argument("--series", default="00080")
    parser.add_argument("--publication-date", default="")
    parser.add_argument("--modification-date", default="2026-11-22")
    args = parser.parse_args()
    assert re.fullmatch(r"\d{5}", args.series)
    dest = ROOT / "datasets" / f"{args.series} - {ABB}"
    dest.mkdir(exist_ok=True)
    assert not list(dest.glob("*.soi*")), "Use a fresh output directory"
    companion = f"{args.series}-{len(STATES) + 1:08d}.dat"
    records, manifest = [], []
    for n, code in enumerate(STATES, 1):
        s = read_state(args.source_root, code)
        print(f"{code}: {s['papers']:,} papers, {s['ballots']:,} counted, {len(s['profile']):,} distinct rankings")
        filename = f"{args.series}-{n:08d}.soi"
        title = f"2025 Australian Senate - {s['state']}"
        header = {"FILE NAME": filename, "TITLE": title,
                  "DESCRIPTION": f"3 May 2025; STV, {s['seats']} seats. Rankings as counted (above-the-line votes expanded). Source: AEC; reports: stv.vote.",
                  "DATA TYPE": "soi", "MODIFICATION TYPE": "original", "RELATES TO": "",
                  "RELATED FILES": companion, "PUBLICATION DATE": args.publication_date,
                  "MODIFICATION DATE": args.modification_date,
                  "NUMBER ALTERNATIVES": len(s["candidates"]), "NUMBER VOTERS": s["ballots"],
                  "NUMBER UNIQUE ORDERS": len(s["profile"])}
        data = soi_text(header, s["candidates"], s["profile"]).encode("utf-8")
        stored = filename
        if len(data) > COMPRESS_ABOVE:
            stored += ".gz"
            (dest / stored).write_bytes(gzip.compress(data, compresslevel=9, mtime=0))
        else:
            (dest / stored).write_bytes(data)
        meta = {k: v for k, v in s.items() if k not in ("profile", "candidates")}
        meta.update(file_name=filename, stored_as=stored, title=title, unique_rankings=len(s["profile"]))
        records.append(meta)
        manifest.append(dict(meta, output_sha256=hashlib.sha256(data).hexdigest(), output_bytes=len(data)))
    columns = ["file_name", "stored_as", "code", "state", "seats", "ballots", "papers", "below_the_line",
               "no_usable_preference", "groups", "source_url", "source_sha256", "report_url"]
    with (dest / companion).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    total = sum(r["ballots"] for r in records)
    description = (
        "<p>Ranked ballot profiles from the Australian Senate election of 3 May 2025: one profile for each "
        f"of the six states (six seats each) and two territories (two seats each), containing {total:,} ballots. "
        "The Senate is elected by single transferable vote. The source is the formal preference data published "
        'by the <a href="https://results.aec.gov.au/31496/Website/SenateDownloadsMenu-31496-Csv.htm">Australian '
        "Electoral Commission</a>, which gives the preferences on every formal ballot paper. Felix Sargent converted "
        'the files to PrefLib; interactive reports are hosted on <a href="https://stv.vote/">stv.vote</a>.</p>'
        "<p>Each paper is read as the Commonwealth Electoral Act counts it: a below-the-line vote numbering at least "
        "six candidates is used; otherwise the above-the-line vote is used, each group standing for its candidates "
        "in ballot order. Preferences stop at the first missing or repeated number, and a tick or cross counts as "
        "a 1. Identical rankings are combined with their exact multiplicities, and unranked candidates remain "
        "unranked. Candidate labels are the AEC names with their group. The three largest profiles are stored "
        "gzip-compressed in the repository and are plain SOI files in the download. "
        f"{companion} is a CSV crosswalk giving seats, ballot and paper counts, below-the-line counts, source URLs, "
        "checksums and stv.vote report links. It is metadata, not a further election.</p>")
    text = (f"Name: 2025 Australian Senate Election\n\nAbbreviation: {ABB}\n\nTags: Election,Politics,STV\n\n"
            f"Series Number: {args.series}\n\nPublication Date: {args.publication_date}\n\nDescription: {description}\n\n"
            "Required Citations: Australian Electoral Commission. 2025 federal election, Senate formal preferences. "
            "https://results.aec.gov.au/31496/Website/SenateDownloadsMenu-31496-Csv.htm ; Felix Sargent. stv.vote: "
            "Australian Senate reports and PrefLib conversion. https://stv.vote/\n\nSelected Studies:\n\n")
    rows = [info_row(["file_name", "modification_type", "relates_to", "title", "description", "publication_date"])]
    rows += [info_row([r["file_name"], "original", "", r["title"], f"{r['seats']} seats; {r['ballots']} ballots",
                       args.publication_date]) for r in records]
    rows.append(info_row([companion, "original", "", "2025 Australian Senate crosswalk",
                          "CSV metadata and report links", args.publication_date]))
    (dest / "info.txt").write_text("\n".join(l.rstrip() for l in (text + "\n".join(rows)).splitlines()) + "\n",
                                   encoding="utf-8")
    summary = dict(contests=len(records), ballots=total, files=manifest)
    (HERE / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Wrote {len(records)} profiles: {total:,} ballots")


if __name__ == "__main__":
    main()
