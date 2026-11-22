# Alaska ranked-choice elections, 2022–2024

41 partial-ranking profiles from single-winner instant-runoff contests:

- 16 August 2022 special general election: U.S. House (1 contest);
- 8 November 2022 general election: U.S. Senate, U.S. House, Governor, 8 State Senate and 14 State House contests (25);
- 5 November 2024 general election: President, U.S. House, 5 State Senate and 8 State House contests (15).

The general-election contests are those with at least three named candidates,
the same selection [ranked.vote](https://ranked.vote/) reports. Most other
Alaska contests had one or two candidates.

## Sources

The Alaska Division of Elections publishes a Dominion cast vote record export
(NIST SP 1500-103 JSON) for each ranked-choice election. `elections.alaska.gov`
puts an interactive bot check in front of these files. The zips were retrieved
byte for byte from Internet Archive captures of the official URLs. For 2022
and 2024, two independent captures of each file have the same SHA-256. For the
special election, the capture has the SHA-1 that ranked.vote recorded from the
original download. `sources.json` gives each file's official URL, an archived
copy, its SHA-256 and the contest IDs used. The builder refuses files that do
not match.

## Conversion

Each ballot is read as Alaska counts it ([AS 15.15.350](https://law.justia.com/codes/alaska/title-15/chapter-15/section-15-15-350/)):

- ambiguous marks are ignored;
- a rank with no mark is a skipped ranking, and two consecutive skipped rankings end the ballot;
- a rank marked for more than one candidate (an overvote) ends the ballot;
- a candidate ranked again is ignored at the later rank.

The export flags some records with the `InvalidContest` outstack condition, and
the official count leaves these out. The builder drops them too: 10,037
contest records in 2024, and none in 2022.

Unqualified write-ins in a contest form one `Write-in` alternative. Ballots with
no counted preference are left out of the profile and counted in the
crosswalk. Identical rankings are aggregated with exact multiplicities, and
unranked candidates stay unranked. Labels are the manifest names with party
affiliation where the manifest gives one.

The official reports apply the skipped-ranking rule only from round 2, so a
ballot whose first ranking is blank does not count in their round 1. These
profiles apply the rule throughout, which makes their first preferences match
the official round 2. The pairwise comparisons are unaffected.

The companion `.dat` file is UTF-8 CSV metadata. For each profile it gives:

- election and contest ID;
- ballots and records;
- ballots with no counted preference;
- source file and its SHA-256;
- the ranked.vote report URL.

It is not another preference profile.

## Reproduction

From the repository root, with Python 3.10 or newer and each zip in its own
subfolder of one directory:

```sh
python3 -m venv /tmp/alaska-preflib-venv
/tmp/alaska-preflib-venv/bin/pip install -r scripts/alaska/requirements.txt
/tmp/alaska-preflib-venv/bin/python scripts/alaska/build.py --source-root <dir>
/tmp/alaska-preflib-venv/bin/python scripts/alaska/validate.py --source-root <dir> \
  --reports <ranked.vote checkout>/report_pipeline/reports.sqlite3
```

`validate.py` checks every PrefLib file against ranked.vote's count, which
comes from a separate TypeScript reader of the same records. For each contest
it requires every alternative's first preferences to equal ranked.vote's
first-round votes, and every pairwise count to equal ranked.vote's pairwise
table. It also checks source and output checksums and runs the repository
sanity checks with warnings escalated.

The final rounds of the 2022 and 2024 U.S. House counts match the certified
results to within 10 votes.

The 2022 special election is a known Condorcet failure: Nick Begich beats both
Mary Peltola and Sarah Palin head to head, but Peltola won the instant runoff.
