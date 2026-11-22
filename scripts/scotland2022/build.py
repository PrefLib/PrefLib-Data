"""Convert Mollison's Scotland 2022 rank-vector archive to PrefLib SOI profiles."""

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

SOURCE_URL = "https://www.macs.hw.ac.uk/~denis/stv_elections/SC2022/SC2022_ballot_format.zip"
SOURCE_SHA256 = "0bfbb374f1f9cd305bc783a53dfaa31703cc0fab3ef31aaccba4443000f4e63d"
ROOT = Path(__file__).resolve().parents[2]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def read_wards(source):
    """Validate every source row before returning any converted data."""
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256, "Source hash mismatch"
    wards = []
    with zipfile.ZipFile(source) as archive:
        names = sorted(n for n in archive.namelist() if n.endswith(".dat"))
        assert len(names) == 355
        for name in names:
            raw = archive.read(name)
            lines = raw.decode("utf-8").splitlines()
            seats, nc, nr, ballots = map(int, lines[1].split())
            candidates = lines[2:2 + nc]
            assert len(set(candidates)) == nc
            rows = [list(map(int, line.split())) for line in lines[2 + nc:] if line.strip()]
            assert len(rows) == nr, name
            profile = Counter()
            for row in rows:
                assert len(row) == nc + 1 and row[0] > 0, (name, row)
                ranks = row[1:]
                positive = sorted(r for r in ranks if r)
                assert positive == list(range(1, len(positive) + 1)), (name, row)
                assert positive, (name, "Empty source ballot")
                order = tuple(i + 1 for _, i in sorted((r, i) for i, r in enumerate(ranks) if r))
                profile[order] += row[0]
            assert sum(profile.values()) == ballots, name
            council = Path(name).parent.name
            ward_slug = slug(re.sub(r"^\d+_", "", Path(name).stem))
            report_url = f"https://stv.vote/report/gb/scotland/{slug(council)}/2022/05/{ward_slug}"
            wards.append(dict(source_path=name, source_sha256=hashlib.sha256(raw).hexdigest(),
                              council=council, ward=lines[0], seats=seats, candidates=candidates,
                              source_rows=nr, ballots=ballots, profile=profile, report_url=report_url))
    return wards


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--series", default="00078")
    parser.add_argument("--publication-date", default="")
    parser.add_argument("--modification-date", default="2026-11-22")
    args = parser.parse_args()
    assert re.fullmatch(r"\d{5}", args.series)
    wards = read_wards(args.source)
    dest = ROOT / "datasets" / f"{args.series} - scotland2022"
    dest.mkdir(exist_ok=True)
    assert not list(dest.glob("*.soi")), "Use a fresh output directory"
    records, excluded = [], []
    manifest = []
    for ward in wards:
        meta = {k: v for k, v in ward.items() if k not in ("profile", "candidates")}
        if not ward["ballots"]:
            excluded.append(meta)
            continue
        filename = f"{args.series}-{len(records) + 1:08d}.soi"
        title = f"2022 Scotland - {ward['council'].replace('_', ' ')} - {ward['ward']}"
        profile = ward["profile"]
        header = {"FILE NAME": filename, "TITLE": title,
                  "DESCRIPTION": f"5 May 2022; {ward['seats']} seats. Partial rankings retained. Source: Denis Mollison; reports: stv.vote.",
                  "DATA TYPE": "soi", "MODIFICATION TYPE": "original", "RELATES TO": "",
                  "RELATED FILES": f"{args.series}-00000348.dat", "PUBLICATION DATE": args.publication_date,
                  "MODIFICATION DATE": args.modification_date,
                  "NUMBER ALTERNATIVES": len(ward["candidates"]), "NUMBER VOTERS": ward["ballots"],
                  "NUMBER UNIQUE ORDERS": len(profile)}
        text = "".join(f"# {k}: {v}".rstrip() + "\n" for k, v in header.items())
        text += "".join(f"# ALTERNATIVE NAME {i}: {name}".rstrip() + "\n" for i, name in enumerate(ward["candidates"], 1))
        text += "".join(f"{count}: {', '.join(map(str, order))}\n" for order, count in sorted(profile.items(), key=lambda x: (-x[1], x[0])))
        (dest / filename).write_text(text, encoding="utf-8")
        meta.update(file_name=filename, title=title)
        records.append(meta)
        manifest.append(dict(meta, output_sha256=hashlib.sha256(text.encode()).hexdigest()))
    assert len(records) == 347 and len(excluded) == 8
    companion = f"{args.series}-00000348.dat"
    columns = ["file_name", "council", "ward", "seats", "ballots", "source_rows", "source_path", "source_sha256", "report_url"]
    with (dest / companion).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    description = ('<p>Ranked ballot profiles from the Scottish council elections of 5 May 2022: '
                   '347 contested wards across all 32 councils, containing 1,857,181 recorded ballots. '
                   'Eight uncontested wards have no ballot records and are excluded. The source is '
                   '<a href="https://www.macs.hw.ac.uk/~denis/stv_elections/SC2022/">Denis Mollison\'s compilation</a> '
                   'of preference data published by council Returning Officers. Felix Sargent converted the '
                   'rank-vector files to PrefLib; interactive reports and the source mirror are hosted on '
                   '<a href="https://stv.vote/">stv.vote</a>.</p>'
                   '<p>Each SOI file preserves observed partial rankings, candidate order and candidate/party labels. '
                   'Identical rankings are combined with their exact multiplicities. Unranked candidates remain '
                   'unranked; no bottom ties or additional preferences are inferred. These profiles contain '
                   'the recorded preferences supplied by the source, not rejected ballot papers or turnout totals. '
                   f'{companion} is a CSV crosswalk giving seats, ballot counts, source paths, checksums and '
                   'stv.vote report links. It is metadata, not a further election.</p>')
    text = (f"Name: Scotland 2022 Council Elections\n\nAbbreviation: scotland2022\n\nTags: Election,Politics,STV\n\n"
            f"Series Number: {args.series}\n\nPublication Date: {args.publication_date}\n\nDescription: {description}\n\n"
            'Required Citations: Denis Mollison. Scottish Council election 2022. https://www.macs.hw.ac.uk/~denis/stv_elections/SC2022/ ; Felix Sargent. stv.vote: Scottish council election reports and PrefLib conversion. https://stv.vote/\n\nSelected Studies:\n\n')
    # PrefLib info.txt uses a specific spaced header and triple-quoted fields.
    buf = io.StringIO()
    def write_info_row(values):
        buf.write(", ".join('"""' + str(v) + '"""' if ',' in str(v) else str(v) for v in values) + "\n")
    write_info_row(["file_name", "modification_type", "relates_to", "title", "description", "publication_date"])
    for r in records:
        write_info_row([r["file_name"], "original", "", r["title"], f"{r['seats']} seats; {r['ballots']} recorded ballots", args.publication_date])
    write_info_row([companion, "original", "", "Scotland 2022 ward crosswalk", "CSV metadata and report links", args.publication_date])
    (dest / "info.txt").write_text("\n".join(line.rstrip() for line in (text + buf.getvalue()).splitlines()) + "\n", encoding="utf-8")
    summary = dict(source_url=SOURCE_URL, source_sha256=SOURCE_SHA256,
                   wards=len(records), councils=len(set(r["council"] for r in records)),
                   ballots=sum(r["ballots"] for r in records), excluded_wards=excluded, files=manifest)
    (Path(__file__).parent / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Wrote {len(records)} profiles: {summary['ballots']:,} ballots, {summary['councils']} councils")


if __name__ == "__main__":
    main()
