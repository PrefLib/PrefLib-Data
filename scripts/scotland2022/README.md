# Scotland council elections, 5 May 2022

347 partial-ranking profiles, one per contested ward, with 1,857,181 recorded
ballots across all 32 councils. Eight uncontested wards have no ballot data and
are excluded; their names are retained in `manifest.json`.

## Attribution and sources

The profiles come from [Denis Mollison's Scottish Council election 2022
collection](https://www.macs.hw.ac.uk/~denis/stv_elections/SC2022/). His
[source notes](https://www.macs.hw.ac.uk/~denis/stv_elections/SC2022/details.html)
describe a compilation of preference files published by council Returning
Officers. Use the **ballot-format ZIP**, whose rows give a multiplicity followed
by the rank assigned to each candidate. The separate preference-format ZIP uses
a different encoding.

Felix Sargent hosts interactive ward reports and a source mirror on
[stv.vote](https://stv.vote/), and prepared this PrefLib conversion. Each row in
`00078-00000348.dat` links to its report. The mirror is also available at the
[pinned stv.vote source revision](https://github.com/ranked-vote/stv.vote/tree/811407c6e767ff1f4617d7726d639eb804d90d20/raw-data/uk/scotland/2022/SC2022_ballot_format).
All 355 local ward files were byte-identical to the source ZIP retrieved on
22 November 2026. The checksum of that ZIP is
`0bfbb374f1f9cd305bc783a53dfaa31703cc0fab3ef31aaccba4443000f4e63d`.

Candidate names, party abbreviations and candidate order are preserved from the
source. A zero rank means unranked; it does not become a bottom tie. Identical
rankings are aggregated with exact integer multiplicities. No missing
preferences, rejected ballot papers, turnout figures or election results are
inferred. The source row counts and ballot totals are checked in every ward.

The companion `.dat` file is UTF-8 CSV metadata: profile filename, council,
ward, seats, ballots, source row count, source path, source SHA-256 and report
URL. It is not another preference profile. Seat counts are recorded because the
SOI format does not itself specify the number of winners.

## Reproduction

From the repository root, with Python 3.10 or newer:

```sh
python3 -m venv /tmp/scotland-preflib-venv
/tmp/scotland-preflib-venv/bin/pip install -r scripts/scotland2022/requirements.txt
curl --fail --location --output /tmp/SC2022_ballot_format.zip \
  'https://www.macs.hw.ac.uk/~denis/stv_elections/SC2022/SC2022_ballot_format.zip'
/tmp/scotland-preflib-venv/bin/python scripts/scotland2022/build.py \
  --source /tmp/SC2022_ballot_format.zip
/tmp/scotland-preflib-venv/bin/python scripts/scotland2022/validate.py \
  --source /tmp/SC2022_ballot_format.zip
```

The builder requires a fresh output directory (remove the generated dataset
directory before rebuilding). `--series` changes the proposed series number;
`--publication-date` can be supplied by maintainers. The publication date is
otherwise blank. `--modification-date` defaults to the conversion date.

Validation independently converts every parsed PrefLib ranking back into its
source rank vector and checks the complete frequency distribution. It also
checks candidate labels, all included and excluded wards, output checksums, and
the repository sanity checks with warnings escalated. It writes `validation.json`.
Standard `metadata.csv` is generated using `scripts/compute_metadata.py`.
