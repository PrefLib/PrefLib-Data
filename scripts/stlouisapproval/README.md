# St Louis approval primary, 4 March 2025

Four categorical profiles record the approvals cast for Mayor, Comptroller,
and Alderman in Wards 3 and 11. Each contest selected two finalists for the
subsequent general election. The proposed dataset number is **00077**;
maintainers can change it before publication.

| Contest | Contest records | Empty approval sets | Distinct approval sets | Approvals |
| --- | ---: | ---: | ---: | ---: |
| Mayor | 34,982 | 37 | 16 | 48,908 |
| Comptroller | 34,982 | 1,315 | 8 | 41,403 |
| Alderman, Ward 3 | 1,643 | 19 | 8 | 2,065 |
| Alderman, Ward 11 | 1,187 | 35 | 8 | 1,306 |

The archive contains 34,982 unique ballot records. The contest electorates
overlap: these are not four independent voter samples. Empty approval sets are
retained. The mayoral analysis linked below uses the 34,945 nonempty ballots
as its denominator.

## Source and encoding

The source is the Hart Verity XML cast vote record export supplied by the
St Louis Board of Election Commissioners and archived with Felix Sargent's
[published analysis](https://felixsargent.com/democracy/2025/08/29/st-louis-approval-voting).
The [pinned public archive](https://raw.githubusercontent.com/ranked-vote/approval.vote/086dc7642c2f6f151a053b4d6fdac15361e66a06/static/papers/st-louis-cvr-paper/data/raw/CVRExport-8-27-2025.zip)
is 24,239,400 bytes, with SHA-256
`a4fdd323884fd340372a20e0a2cd32aa5e4f6f9cd3619789a0a0cc932336224f`.
The archive filename reflects its export date, not the election date.

All 13 candidate approval totals match the city's
[final official results](https://www.stlouis-mo.gov/government/departments/board-election-commissioners/documents/election-results/upload/Mar25-Final-Official-Results.pdf),
dated 11 March 2025. Candidate names and their ordering follow that report.

Each CAT file has two categories: **Approved** and **Not approved**. They record
marks, not inferred rankings, preference intensity or reasons for voting.
Identical approval sets are aggregated with their exact multiplicities;
an empty first category preserves a contest record with no approvals.

`00077-00000005.dat` is a UTF-8 CSV file with columns:

- `file_name`: the corresponding CAT file.
- `precinct_label`: the source's precinct/split label, preserved verbatim.
- `approved_alternative_ids`: semicolon-separated candidate IDs from that CAT
  file; an empty field represents no approvals.
- `multiplicity`: the number of matching contest records in that precinct.

The precinct file preserves the joint approval patterns within each contest.
It contains no ballot identifiers or links between a person's votes in different
contests. Precinct labels are source labels, not a separately verified geographic
crosswalk. There are 179 distinct source labels for each citywide contest,
16 for Ward 3, and 10 for Ward 11.

## Reproduce and validate

From the repository root, using Python 3.10 or newer:

```sh
python3 -m venv /tmp/stlouis-preflib-venv
/tmp/stlouis-preflib-venv/bin/pip install -r scripts/stlouisapproval/requirements.txt
curl --fail --location --output /tmp/CVRExport-8-27-2025.zip \
  'https://raw.githubusercontent.com/ranked-vote/approval.vote/086dc7642c2f6f151a053b4d6fdac15361e66a06/static/papers/st-louis-cvr-paper/data/raw/CVRExport-8-27-2025.zip'
/tmp/stlouis-preflib-venv/bin/python scripts/stlouisapproval/build.py \
  --source /tmp/CVRExport-8-27-2025.zip
/tmp/stlouis-preflib-venv/bin/python scripts/stlouisapproval/validate.py \
  --source /tmp/CVRExport-8-27-2025.zip
```

The converter verifies the source hash, rejects duplicate ballot identifiers,
checks every candidate total against the official report, and writes the CAT
profiles, precinct data and `info.txt`. It also writes `summary.json` and a
SHA-256 `manifest.json` here. `--series` changes the dataset number;
`--publication-date` can be supplied once publication is arranged.

The validator parses each generated profile with PrefLib-Tools, checks its exact
agreement with the XML export, reconciles every precinct pattern, and runs the
repository's `sanitychecks.py` with warnings escalated. Its results are saved in
`validation.json`. The repository's separate `compute_metadata.py` workflow can
generate its standard `metadata.csv`; the converter leaves that file untouched.

The source archive remains at the public link above rather than being duplicated
in this repository.
