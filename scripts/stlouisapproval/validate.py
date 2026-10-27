#!/usr/bin/env python3
"""Parse with PrefLib-Tools and check exact profiles, official totals and precinct sums."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path

from preflibtools.instances import sanity
from preflibtools.instances.dataset import read_info_file
from preflibtools.instances.preflibinstance import get_parsed_instance
from build import CONTESTS, ROOT, ARTIFACTS, parse_archive, require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--series', default='00077')
    args = parser.parse_args()
    dataset = ROOT / 'datasets' / f'{args.series} - stlouisapproval'
    source_profiles, source_precincts, source_count = parse_archive(args.source)
    manifest = json.loads((ARTIFACTS / 'manifest.json').read_text())
    require(hashlib.sha256(args.source.read_bytes()).hexdigest() == manifest['source_sha256'],
            'Raw source checksum mismatch')
    require(hashlib.sha256((ARTIFACTS / 'build.py').read_bytes()).hexdigest() == manifest['converter_sha256'],
            'Converter changed since build; regenerate dataset')
    for filename, digest in manifest['files_sha256'].items():
        require(hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() == digest,
                f'Generated file checksum mismatch: {filename}')
    info = read_info_file(str(dataset / 'info.txt'))
    require(set(info['files']) == {p.name for p in dataset.iterdir() if p.name not in ('info.txt', 'metadata.csv')}, 'info.txt file listing mismatch')
    actual_precincts = defaultdict(Counter)
    with (dataset / f'{args.series}-00000005.dat').open(newline='') as stream:
        for row in csv.DictReader(stream):
            approved = tuple(int(x) for x in row['approved_alternative_ids'].split(';') if x)
            key = row['file_name'], row['precinct_label']
            require(approved not in actual_precincts[key], 'Duplicate precinct-pattern row')
            count = int(row['multiplicity'])
            require(count > 0, 'Nonpositive precinct count')
            actual_precincts[key][approved] = count
    expected_precincts = {}
    results = []
    for index, (name, contest) in enumerate(CONTESTS.items(), 1):
        path = dataset / f'{args.series}-{index:08d}.cat'
        instance = get_parsed_instance(str(path))
        errors = sanity.metadata(instance) + sanity.categories(instance)
        require(not errors, f'{path.name}: {errors}')
        require(instance.num_categories == 2, 'Wrong category count')
        require(instance.categories_name == {1: 'Approved', 2: 'Not approved'}, 'Category names changed')
        require(instance.alternatives_name == dict(enumerate(contest['candidates'], 1)),
                'Candidate ID/name mapping changed')
        profile = Counter()
        for preference, count in instance.multiplicity.items():
            approved, not_approved = preference
            require(count > 0, 'Nonpositive multiplicity')
            require(set(approved).isdisjoint(not_approved), 'Overlapping categories')
            require(set(approved) | set(not_approved) == set(instance.alternatives_name), 'Missing candidate')
            profile[tuple(sorted(approved))] += count
        require(profile == source_profiles[name], 'PrefLib round-trip changed the source approval sets')
        for (contest_name, precinct), counts in source_precincts.items():
            if contest_name == name:
                expected_precincts[(path.name, precinct)] = counts
        results.append({'file': path.name, 'records': instance.num_voters,
                        'unique_patterns': instance.num_unique_preferences,
                        'empty_approval_sets': profile[()], 'status': 'PASS'})
    require(actual_precincts == expected_precincts, 'Precinct patterns differ from source')
    # Run the actual PrefLib-Data repository checker, in addition to CAT-specific checks.
    checker = ROOT / 'scripts' / 'sanitychecks.py'
    require(checker.exists(), 'Upstream sanitychecks.py is missing')
    spec = importlib.util.spec_from_file_location('upstream_sanitychecks', checker)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DATASET_FOLDER = str(ROOT / 'datasets')
    module.check_dataset(dataset.name, True)
    result = {
        'status': 'PASS', 'preflibtools_version': importlib.metadata.version('preflibtools'),
        'unique_source_cvrs': source_count, 'files': results,
        'checks': ['Raw and generated-file SHA-256 checksums', 'No duplicate source CVRs',
                   'All 13 candidate totals equal official final cumulative results',
                   'Every CAT profile equals its raw XML approval profile including empty sets',
                   'All precinct-pattern counts equal the source records',
                   'PrefLib-Tools metadata and categorical sanity checks',
                   'PrefLib-Data sanitychecks.py with warnings escalated'],
        'upstream_checker_url': 'https://raw.githubusercontent.com/PrefLib/PrefLib-Data/main/scripts/sanitychecks.py',
        'upstream_checker_sha256': hashlib.sha256(checker.read_bytes()).hexdigest(),
        'pending': ['PrefLib series-number assignment', 'PrefLib publication date',
                    'Maintainer review of source/redistribution terms and citation wording'],
    }
    (ARTIFACTS / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
