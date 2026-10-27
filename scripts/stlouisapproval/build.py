#!/usr/bin/env python3
"""Convert the archived St Louis export to PrefLib CAT without inferring rankings."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import hashlib
import html
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ARTIFACTS = Path(__file__).resolve().parent
ROOT = ARTIFACTS.parents[1]
NS = {'c': 'http://tempuri.org/CVRDesign.xsd'}
SOURCE_COMMIT = '086dc7642c2f6f151a053b4d6fdac15361e66a06'
RAW_URL = f'https://raw.githubusercontent.com/ranked-vote/approval.vote/{SOURCE_COMMIT}/static/papers/st-louis-cvr-paper/data/raw/CVRExport-8-27-2025.zip'
OFFICIAL_URL = 'https://www.stlouis-mo.gov/government/departments/board-election-commissioners/documents/election-results/upload/Mar25-Final-Official-Results.pdf'
BLOG_URL = 'https://felixsargent.com/democracy/2025/08/29/st-louis-approval-voting'
# Names and ordering follow the city's final official cumulative report of 11 March 2025.
CONTESTS = {
    'MAYOR': {'title': 'Mayor', 'records': 34982, 'empty': 37, 'candidates': {
        'MICHAEL "MIKE" BUTLER': 8701, 'TISHAURA O. JONES': 11612,
        'CARA SPENCER': 23826, 'ANDREW JONES': 4769}},
    'COMPTROLLER': {'title': 'Comptroller', 'records': 34982, 'empty': 1315, 'candidates': {
        'DONNA M.C. BARINGER': 16689, 'DARLENE GREEN': 16157, 'CELESTE METCALF': 8557}},
    'ALDERMAN - WARD 3': {'title': 'Alderman Ward 3', 'records': 1643, 'empty': 19, 'candidates': {
        'DALLAS ADAMS': 694, 'SHANE COHN': 921, 'INEZ BORDEAUX': 450}},
    'ALDERMAN - WARD 11': {'title': 'Alderman Ward 11', 'records': 1187, 'empty': 35, 'candidates': {
        'MELINDA LONG': 140, 'REBECCA MCCLOUD': 422, 'LAURA M. KEYS': 744}},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(element, path):
    value = element.findtext(path, namespaces=NS)
    require(value is not None and bool(value.strip()), f'Missing {path}')
    return value.strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_archive(path):
    patterns = defaultdict(Counter)
    precinct_patterns = defaultdict(Counter)
    guids = set()
    contest_ids = defaultdict(set)
    candidate_ids = defaultdict(set)
    precinct_ids = defaultdict(set)
    with ZipFile(path) as archive:
        members = [m for m in archive.infolist() if not m.is_dir()]
        require(len({m.filename for m in members}) == len(members), 'Duplicate archive filename')
        require(all(m.filename.endswith('.xml') for m in members), 'Unexpected archive member')
        for member in members:
            root = ET.fromstring(archive.read(member))
            require(root.tag == '{http://tempuri.org/CVRDesign.xsd}Cvr', 'Unknown XML schema')
            guid = text(root, 'c:CvrGuid')
            require(guid not in guids, 'Duplicate CVR GUID; no silent deduplication')
            guids.add(guid)
            precinct = text(root, 'c:PrecinctSplit/c:Name')
            precinct_ids[precinct].add(text(root, 'c:PrecinctSplit/c:Id'))
            seen_contests = set()
            for contest in root.findall('c:Contests/c:Contest', NS):
                name = text(contest, 'c:Name')
                require(name in CONTESTS, f'Unknown contest: {name}')
                require(name not in seen_contests, 'Duplicate contest in a CVR')
                seen_contests.add(name)
                contest_ids[name].add(text(contest, 'c:Id'))
                candidates = list(CONTESTS[name]['candidates'])
                approved = []
                seen_candidates = set()
                for option in contest.findall('c:Options/c:Option', NS):
                    candidate = text(option, 'c:Name')
                    require(candidate in candidates, f'Unknown candidate: {candidate}')
                    require(candidate not in seen_candidates, 'Duplicate candidate in a contest')
                    seen_candidates.add(candidate)
                    candidate_ids[(name, candidate)].add(text(option, 'c:Id'))
                    value = int(text(option, 'c:Value'))
                    require(value in (0, 1), f'Non-binary selection value: {value}')
                    if value:
                        approved.append(candidates.index(candidate) + 1)
                # The source omits Undervotes precisely when all candidates are marked.
                undervotes = contest.findtext('c:Undervotes', default='0', namespaces=NS)
                require(int(undervotes) == len(candidates) - len(approved),
                        'Unexpected undervote semantics')
                pattern = tuple(sorted(approved))
                patterns[name][pattern] += 1
                precinct_patterns[(name, precinct)][pattern] += 1
            require({'MAYOR', 'COMPTROLLER'} <= seen_contests, 'Missing citywide contest')
            require(not {'ALDERMAN - WARD 3', 'ALDERMAN - WARD 11'} <= seen_contests,
                    'Both ward contests on one ballot')
    require(len(guids) == 34982, 'Unexpected number of CVRs')
    require(all(len(ids) == 1 for ids in contest_ids.values()), 'Contest ID mismatch')
    require(all(len(ids) == 1 for ids in candidate_ids.values()), 'Candidate ID mismatch')
    require(all(len(ids) == 1 for ids in precinct_ids.values()), 'Precinct ID mismatch')
    for name, spec in CONTESTS.items():
        profile = patterns[name]
        require(sum(profile.values()) == spec['records'], f'Record count mismatch: {name}')
        require(profile[()] == spec['empty'], f'Empty approval-set count mismatch: {name}')
        for i, (candidate, official_total) in enumerate(spec['candidates'].items(), 1):
            total = sum(count for approved, count in profile.items() if i in approved)
            require(total == official_total, f'Official total mismatch: {candidate}')
    return patterns, precinct_patterns, len(guids)


def category(alternatives):
    return '{' + ','.join(map(str, alternatives)) + '}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--series', default='00077', help='Proposed PrefLib series number')
    parser.add_argument('--publication-date', default='', help='Leave blank until PrefLib publication')
    parser.add_argument('--prepared-date', default='2026-10-27')
    args = parser.parse_args()
    require(re.fullmatch(r'\d{5}', args.series) is not None, 'Series must contain five digits')
    date.fromisoformat(args.prepared_date)
    if args.publication_date:
        date.fromisoformat(args.publication_date)
    require(sha256(args.source) == 'a4fdd323884fd340372a20e0a2cd32aa5e4f6f9cd3619789a0a0cc932336224f',
            'Source archive differs from the pinned public export')
    profiles, precincts, ballot_count = parse_archive(args.source)
    dataset = ROOT / 'datasets' / f'{args.series} - stlouisapproval'
    dataset.mkdir(parents=True, exist_ok=True)
    summary = {'election_date': '2025-03-04', 'prepared_date': args.prepared_date,
               'unique_source_cvrs': ballot_count, 'contests': []}
    precinct_file = f'{args.series}-00000005.dat'
    rows = [[precinct_file, 'original', '', 'Approval patterns by precinct',
             'CSV counts grouped by contest and source precinct label', args.publication_date]]
    precinct_rows = []
    for index, (name, spec) in enumerate(CONTESTS.items(), 1):
        filename = f'{args.series}-{index:08d}.cat'
        title = f'2025 St Louis primary - {spec["title"]}'
        profile = profiles[name]
        candidates = list(spec['candidates'])
        description = ('Observed approvals in a top-two primary; empty approval sets retained. '
                       'Not approved means no recorded approval, not inferred sincere dislike.')
        headers = {
            'FILE NAME': filename, 'TITLE': title, 'DESCRIPTION': description,
            'DATA TYPE': 'cat', 'MODIFICATION TYPE': 'original', 'RELATES TO': '',
            'RELATED FILES': precinct_file, 'PUBLICATION DATE': args.publication_date,
            'MODIFICATION DATE': args.prepared_date, 'NUMBER ALTERNATIVES': len(candidates),
            'NUMBER VOTERS': sum(profile.values()), 'NUMBER UNIQUE PREFERENCES': len(profile),
            'NUMBER CATEGORIES': 2, 'CATEGORY NAME 1': 'Approved', 'CATEGORY NAME 2': 'Not approved',
        }
        headers.update({f'ALTERNATIVE NAME {i}': candidate for i, candidate in enumerate(candidates, 1)})
        lines = [f'# {key}: {value}'.rstrip() for key, value in headers.items()]
        for approved, count in sorted(profile.items(), key=lambda item: (-item[1], item[0])):
            not_approved = tuple(i for i in range(1, len(candidates) + 1) if i not in approved)
            lines.append(f'{count}: {category(approved)},{category(not_approved)}')
        (dataset / filename).write_text('\n'.join(lines) + '\n')
        rows.append([filename, 'original', '', title, '', args.publication_date])
        for (contest, precinct), counts in sorted(precincts.items()):
            if contest == name:
                for approved, count in sorted(counts.items()):
                    precinct_rows.append([filename, precinct, ';'.join(map(str, approved)), count])
        summary['contests'].append({
            'file': filename, 'contest': name, 'candidates': spec['candidates'],
            'contest_records': sum(profile.values()), 'empty_approval_sets': profile[()],
            'nonempty_approval_sets': sum(profile.values()) - profile[()],
            'unique_approval_sets': len(profile),
            'total_approvals': sum(len(p) * n for p, n in profile.items()),
            'approval_count_distribution': dict(sorted(Counter({
                k: sum(n for p, n in profile.items() if len(p) == k)
                for k in range(len(candidates) + 1)}).items())),
            'precinct_labels': sum(contest == name for contest, _ in precincts),
            'official_candidate_totals_match': True,
        })
    with (dataset / precinct_file).open('w', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['file_name', 'precinct_label', 'approved_alternative_ids', 'multiplicity'])
        writer.writerows(precinct_rows)
    description = (
        '<p>Observed approval ballots from the 4 March 2025 St. Louis, Missouri, nonpartisan '
        'primary: Mayor, Comptroller, and Alderman in Wards 3 and 11. Each contest selected '
        'two finalists for a later single-office general election. Converted by Felix Sargent '
        'from the archived Hart Verity '
        'cast vote record export supplied by the city election board, as described in his '
        'published analysis.</p><p>Four CAT files retain every contest record, including empty '
        'approval sets. Identical approval sets are aggregated with exact multiplicities. '
        'The categories record approved and not approved candidates; they do not recover '
        f'sincere rankings, intensity, or motives. {precinct_file} provides per-contest '
        'approval-pattern counts by source precinct label. No individual ballot identifiers '
        'or cross-contest ballot links are included. The electorates overlap across contests '
        'and must not be treated as independent voter samples.</p><p>All candidate totals '
        f'match the <a href="{html.escape(OFFICIAL_URL)}">final official results</a>. '
        'The Mayor file has 34,982 records, including 37 empty approval sets; the companion '
        'blog uses 34,945 nonempty mayoral ballots as its denominator. The source ZIP and '
        f'analysis are available through <a href="{html.escape(RAW_URL)}">approval.vote</a> '
        f'and <a href="{html.escape(BLOG_URL)}">the contributor\'s blog</a>.</p>')
    info = {
        'Name': 'St Louis 2025 Approval Primary Elections', 'Abbreviation': 'stlouisapproval',
        'Tags': 'Election, Politics', 'Series Number': args.series,
        'Publication Date': args.publication_date, 'Description': description,
        'Required Citations': ('Felix Sargent. St. Louis Approval Voting: What the Cast Vote Records Reveal. '
                               f'29 August 2025. {BLOG_URL}'),
        'Selected Studies': '',
    }
    with (dataset / 'info.txt').open('w', newline='') as stream:
        stream.write('\n\n'.join(f'{key}: {value}'.rstrip() for key, value in info.items()) + '\n\n')
        # PrefLib's info.txt parser expects a literal comma-space header and its
        # own triple-quote convention, rather than general RFC 4180 CSV.
        stream.write('file_name, modification_type, relates_to, title, description, publication_date\n')
        for row in rows:
            stream.write(', '.join(f'"""{value}"""' if ',' in value else value for value in row).rstrip() + '\n')
    (ARTIFACTS / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    manifest = {
        'status': 'Contribution prepared for PrefLib maintainer review',
        'prepared_date': args.prepared_date, 'proposed_series_number': args.series,
        'source_file': args.source.name, 'source_bytes': args.source.stat().st_size,
        'source_sha256': sha256(args.source), 'source_mirror_url': RAW_URL,
        'source_repository_commit': SOURCE_COMMIT, 'converter_sha256': sha256(Path(__file__)),
        'official_results_url': OFFICIAL_URL,
        'files_sha256': {str(p.relative_to(ROOT)): sha256(p)
                         for p in sorted(dataset.iterdir()) if p.is_file() and p.name != 'metadata.csv'},
    }
    (ARTIFACTS / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
