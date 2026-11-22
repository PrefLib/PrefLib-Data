# ACT Legislative Assembly elections, 2008–2024

21 partial-ranking profiles, one per electorate contest, with 1,220,223 ballots
across five Hare-Clark STV elections:

- 2008 and 2012: Brindabella and Ginninderra (5 seats each) and Molonglo (7 seats);
- 2016, 2020 and 2024: Brindabella, Ginninderra, Kurrajong, Murrumbidgee and Yerrabi (5 seats each).

## Sources

Elections ACT publishes the preferences on every formal ballot paper, captured by
its electronic counting system, as "ballot paper preference data". For each
election the builder reads:

- `Electorates.txt`
- `Groups.txt` (party groups)
- `Candidates.txt`
- one `<Electorate>Total.txt` per electorate (a row per preference: batch, paper index, preference number, party code, candidate code)

The 2024 files come from the [2024 election page](https://www.elections.act.gov.au/elections/previous-assembly-elections/2024-election).
The current Elections ACT site no longer links the 2008–2020 files. They were
retrieved byte for byte from Internet Archive captures of the original Elections
ACT URLs. `sources.json` gives each election's original page and the SHA-256 of
every file used. The builder refuses files that do not match.

## Conversion

A paper's preferences are read 1, 2, 3, … and stop at the first missing number,
at a number given to two candidates, or at a candidate numbered twice. This is
how a Hare-Clark paper is counted. Every paper in the data has a usable first
preference. Identical rankings are aggregated with exact multiplicities, and
unranked candidates stay unranked. Candidate order follows `Candidates.txt`. Each
label is the source name followed by its party group, or `UNGROUPED`.

The companion `.dat` file is UTF-8 CSV metadata. For each profile it gives:

- year and date;
- electorate and seats;
- ballots, source papers and preference rows;
- source file and its SHA-256;
- the [stv.vote](https://stv.vote/) report URL.

It is not another preference profile. Seats are recorded because SOI does not
say how many candidates are elected.

## Reproduction

From the repository root, with Python 3.10 or newer, and the five source folders
saved as `act-2008` … `act-2024` under one directory:

```sh
python3 -m venv /tmp/act-preflib-venv
/tmp/act-preflib-venv/bin/pip install -r scripts/act/requirements.txt
/tmp/act-preflib-venv/bin/python scripts/act/build.py --source-root <dir>
/tmp/act-preflib-venv/bin/python scripts/act/validate.py --source-root <dir> \
  --stv-profiles <stv.vote checkout>/raw-data/au/act
```

`validate.py` compares every PrefLib file, parsed with preflibtools, against
stv.vote's own conversion of the same source files. That conversion is a separate
TypeScript implementation (`scripts/convert-act-preferences.ts` in
[stv.vote](https://github.com/ranked-vote/stv.vote)). The validator requires
identical ranking frequencies, candidate counts and ballot totals. It also
re-checks source and output checksums and runs the repository sanity checks with
warnings escalated, then writes `validation.json`.

stv.vote counts these profiles with its weighted inclusive Gregory tabulator, and
elects the official members in all 21 contests. Standard `metadata.csv` is
generated with `scripts/compute_metadata.py`.

Note: `metadata.csv` reports `hasCondorcet = True` for every contest. preflibtools
counts a head-to-head only when a ballot ranks both candidates. Counting a ranked
candidate as preferred to an unranked one gives no Condorcet winner in 2020
Yerrabi: Coe, Orr and Pettersson form a cycle.
