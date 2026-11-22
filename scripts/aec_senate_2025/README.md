# 2025 Australian Senate election

Eight partial-ranking profiles, one per state and territory, with 15,871,189
ballots. The election was the half-Senate election of 3 May 2025. Each state
elected six senators by single transferable vote, and each territory elected two.

## Source

The Australian Electoral Commission publishes
[Senate formal preferences](https://results.aec.gov.au/31496/Website/SenateDownloadsMenu-31496-Csv.htm)
for the 2025 federal election (event 31496): one zipped CSV per state or
territory, with a row per formal ballot paper. `build.py` lists the SHA-256 of
each zip (downloaded 22 November 2026) and refuses files that do not match.

## Conversion

Each paper is read as the Commonwealth Electoral Act counts it:

- A below-the-line vote that numbers at least six candidates, 1 to 6 each once, is used.
- Otherwise the above-the-line vote is used, each group standing for its candidates in ballot order.
- Preferences stop at the first missing or repeated number.
- A tick or cross counts as a 1.

Identical rankings are aggregated with exact multiplicities, and unranked
candidates stay unranked. Candidate order follows the AEC's below-the-line
columns. Each label is the AEC name followed by its group name, or `Ungrouped`.

The NSW, Victoria and Queensland profiles are 116, 106 and 96 MB as plain SOI,
so they are stored as `.soi.gz` (see "Large data files" in the repository
README). The release zip holds them as plain `.soi` files.

The companion `.dat` file is UTF-8 CSV metadata. For each profile it gives:

- seats;
- ballots, papers and below-the-line papers;
- the stored file name;
- the source URL and its SHA-256;
- the [stv.vote](https://stv.vote/) report URL.

It is not another preference profile.

## Reproduction

From the repository root, with Python 3.10 or newer and the eight zips in one folder:

```sh
python3 -m venv /tmp/senate-preflib-venv
/tmp/senate-preflib-venv/bin/pip install -r scripts/aec_senate_2025/requirements.txt
/tmp/senate-preflib-venv/bin/python scripts/aec_senate_2025/build.py --source-root <dir>
/tmp/senate-preflib-venv/bin/python scripts/aec_senate_2025/validate.py --source-root <dir> \
  --stv-profiles <stv.vote checkout>/raw-data/au/senate/2025
```

The build takes about 10 minutes.

`validate.py` compares every PrefLib file, parsed with preflibtools, against
stv.vote's own conversion of the same zips. That conversion is a separate
TypeScript implementation (`scripts/convert-aec-senate.ts` in
[stv.vote](https://github.com/ranked-vote/stv.vote)). The validator requires
identical ranking frequencies, candidate counts and ballot totals. It also
checks source and output checksums and runs the repository sanity checks with
warnings escalated.

stv.vote counts these profiles with a weighted inclusive Gregory tabulator. It
elects all 40 senators the AEC declared and reproduces the AEC's quotas.
