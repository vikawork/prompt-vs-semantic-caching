#!/usr/bin/env python3
"""The sole writer of summary.json: derive every report value from saved evidence."""
import datetime as dt
import json
from pathlib import Path
import statistics as st
import re
import time

DEMO = Path(__file__).resolve().parent
RESULTS = DEMO / 'results'
SCRATCH = DEMO.parents[2] / '.studio/ai-channel/caching'
CONDITIONS = ['cold', 'warm', 'early-change', 'late-change', 'two-prefixes-one', 'two-prefixes-two']
METRICS = ['prompt_n', 'prompt_ms', 'ttft_ms', 'total_ms', 'cache_n']


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def stats(values):
    if not values:
        return None
    return {'count': len(values), 'median': st.median(values), 'min': min(values), 'max': max(values)}


def metrics(items):
    return {key: stats([row[key] for row in items]) for key in METRICS}


def pair_table(items):
    positive = [p for p in items if p['same_answer']]
    negative = [p for p in items if not p['same_answer']]
    table = []
    for percent in range(50, 100):
        threshold = percent / 100
        correct = sum(p['cosine_similarity'] >= threshold for p in positive)
        wrong = sum(p['cosine_similarity'] >= threshold for p in negative)
        table.append({'threshold': threshold, 'correct_hits': correct, 'wrong_hits': wrong,
                      'correct_share': correct / len(positive), 'wrong_share': wrong / len(negative),
                      'positive_count': len(positive), 'negative_count': len(negative)})
    return {'count': len(items), 'positive': len(positive), 'negative': len(negative),
            'thresholds': table, 'first_under_one_percent': next((r for r in table if r['wrong_share'] < .01), None)}


def ref(filename, line):
    return {'file': filename, 'line': line}


def main():
    setup = read(SCRATCH / 'provenance/models.json') if (SCRATCH / 'provenance/models.json').exists() else {}
    manifest_path = DEMO / 'fixtures/public-manifest.json'
    source = read(manifest_path) if manifest_path.exists() else {}
    source.pop('pairs', None)
    summary = {'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'setup': setup,
               'public_source': source, 'status': 'incomplete', 'missing': [], 'prefix': {},
               'definitions': {'prefix_range': 'Median, minimum and maximum over requests; per-repeat medians also reported',
                               'pair_correct': 'Positive pairs served / all positive pairs',
                               'pair_wrong': 'Negative pairs served / all negative pairs',
                               'store_correct': 'Nearest is the same-index positive counterpart; all other accepted queries are wrong',
                               'store_denominator': 'All queries', 'store_ties': 'Lowest stored index',
                               'first_under': 'First scanned threshold with negative-pair wrong share strictly below one percent'},
               'experiments': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'S1', 'S2', 'S3', 'S4']}
    prefix_rows = {}
    for condition in CONDITIONS:
        all_rows = []
        repeats = []
        for repeat in (1, 2, 3):
            path = RESULTS / f'prefix-{condition}-r{repeat}.jsonl'
            if not path.exists():
                summary['missing'].append(path.name)
                continue
            data = rows(path)
            if len(data) != 30:
                summary['missing'].append(path.name + ': incomplete')
                continue
            if [r['question_index'] for r in data] != list(range(30)) or any(r['condition'] != condition or r['repeat'] != repeat for r in data):
                raise ValueError('Prefix condition identity or order mismatch')
            for index, row in enumerate(data):
                row['reference'] = ref('results/' + path.name, index + 1)
                row['cache_n'] = row['server_timings']['cache_n']
                if not all(row[k] >= 0 for k in METRICS) or row['total_ms'] < row['ttft_ms']:
                    raise ValueError('Invalid prefix timing')
            writes = 2 if condition == 'two-prefixes-two' else 1
            steady = data[writes:]
            repeats.append({'repeat': repeat, 'all': metrics(data), 'first_writes': data[:writes],
                            'steady': metrics(steady), 'steady_count': len(steady)})
            all_rows.extend(data)
            prefix_rows[(condition, repeat)] = data
        if all_rows:
            writes = [row for r in repeats for row in r['first_writes']]
            write_keys = {(r['repeat'], r['question_index']) for r in writes}
            steady = [r for r in all_rows if (r['repeat'], r['question_index']) not in write_keys]
            summary['prefix'][condition] = {'all': metrics(all_rows), 'steady': metrics(steady),
                'first_writes': [{k: r[k] for k in ['repeat', 'question_index', 'prompt_n', 'prompt_ms', 'ttft_ms', 'total_ms', 'cache_n', 'reference']} for r in writes],
                'repeats': repeats, 'manual_tokens': sorted({r['manual_tokens'] for r in all_rows}),
                'tokens_cached_reported': any(r['tokens_cached'] is not None for r in all_rows),
                'tokens_cached': stats([r['tokens_cached'] for r in all_rows if r['tokens_cached'] is not None]),
                'timing_note': 'tokens_cached is saved as reported, not assumed to mean reused prompt tokens'}
    summary['server_warnings'] = []
    for log in sorted((DEMO / 'logs').glob('*.log')):
        for index, line in enumerate(log.read_text().splitlines()):
            if 'unused tensor' in line:
                summary['server_warnings'].append({'kind': 'unused GGUF tensor', 'reference': ref('logs/' + log.name, index + 1)})
                break
    summary['screen'] = {condition: {k: data[1][k] for k in ['prompt_n', 'prompt_ms', 'ttft_ms', 'total_ms', 'cache_n', 'reference']}
                         for (condition, repeat), data in prefix_rows.items() if repeat == 1}
    for condition, screen in summary['screen'].items():
        candidates = []
        for log in (DEMO / 'logs').glob(f'{condition}-r1*.log'):
            timing_lines = [(i + 1, re.search(r'prompt eval time =\s+([\d.]+) ms /\s+(\d+) tokens', line))
                            for i, line in enumerate(log.read_text().splitlines())]
            timing_lines = [(i, match) for i, match in timing_lines if match]
            if len(timing_lines) == 30:
                index, match = timing_lines[1]
                if int(match.group(2)) == screen['prompt_n'] and abs(float(match.group(1)) - screen['prompt_ms']) < .011:
                    candidates.append(ref('logs/' + log.name, index))
        if len(candidates) == 1:
            screen['server_log_reference'] = candidates[0]
    comparisons = []
    for repeat in (1, 2, 3):
        if ('cold', repeat) in prefix_rows and ('warm', repeat) in prefix_rows:
            for cold, warm in zip(prefix_rows[('cold', repeat)], prefix_rows[('warm', repeat)]):
                if cold['question_id'] != warm['question_id']:
                    raise ValueError('Cold/warm question identity mismatch')
                comparisons.append({'repeat': repeat, 'question_id': cold['question_id'],
                                    'identical': cold['output'] == warm['output'], 'cold': cold['output'],
                                    'warm': warm['output'], 'cold_reference': cold['reference'],
                                    'warm_reference': warm['reference']})
    summary['same_answer'] = {'count': len(comparisons), 'identical': sum(r['identical'] for r in comparisons),
                              'different': sum(not r['identical'] for r in comparisons),
                              'pairs': comparisons}
    pairs_path = RESULTS / 'semantic-pairs.jsonl'
    store_path = RESULTS / 'semantic-store.jsonl'
    run_path = RESULTS / 'semantic-run.jsonl'
    for path in (pairs_path, store_path, run_path):
        if not path.exists():
            summary['missing'].append(path.name)
    if all(path.exists() for path in (pairs_path, store_path, run_path)):
        paired = rows(pairs_path)
        public = [p for p in paired if p['dataset'] == 'public']
        ours = [p for p in paired if p['dataset'] == 'ours']
        store = rows(store_path)
        if len(public) != 2000 or len(ours) != 60 or len(store) != 2000:
            raise ValueError('Semantic counts are incomplete')
        if sum(p['same_answer'] for p in ours) != 30 or sum(p['same_answer'] for p in public) != source['sample_positive']:
            raise ValueError('Semantic label balance mismatch')
        for index, pair in enumerate(paired):
            pair['reference'] = ref('results/semantic-pairs.jsonl', index + 1)
        summary['public_pairs'] = pair_table(public)
        summary['our_pairs'] = pair_table(ours)
        summary['our_pairs']['sorted'] = sorted(ours, key=lambda p: (-p['cosine_similarity'], str(p['id'])))
        summary['our_pairs']['worst_wrong'] = max((p for p in ours if not p['same_answer']), key=lambda p: p['cosine_similarity'])
        tables = []
        for percent in range(50, 100):
            threshold = percent / 100
            served = [r for r in store if r['nearest_similarity'] >= threshold]
            correct = sum(r['nearest_correct'] for r in served)
            wrong = len(served) - correct
            missed = len(store) - len(served)
            tables.append({'threshold': threshold, 'correct': correct, 'wrong': wrong, 'not_served': missed,
                           'correct_share': correct / len(store), 'wrong_share': wrong / len(store),
                           'not_served_share': missed / len(store)})
        summary['store'] = {'count': len(store), 'thresholds': tables,
                            'exact_ties_rule': 'lowest source index; identical text at a different index still marked wrong'}
        summary['semantic_run'] = rows(run_path)[0]
        cold = [r for (c, repeat), data in prefix_rows.items() if c == 'cold' for r in data]
        summary['hit_savings'] = {'embedding_ms': stats([r['embed_ms'] for r in store]),
                                  'lookup_ms': stats([r['lookup_ms'] for r in store]),
                                  'hit_ms': stats([r['total_ms'] for r in store]),
                                  'cold_total_ms': stats([r['total_ms'] for r in cold])}
        if cold:
            summary['hit_savings']['median_ratio'] = summary['hit_savings']['cold_total_ms']['median'] / summary['hit_savings']['hit_ms']['median']
    times = [r['started_utc'] for data in prefix_rows.values() for r in data]
    ends = [r['finished_utc'] for data in prefix_rows.values() for r in data]
    if 'semantic_run' in summary:
        run = summary['semantic_run']
        times.append(dt.datetime.fromtimestamp(run['started_unix'], dt.timezone.utc).isoformat())
        ends.append(dt.datetime.fromtimestamp(run['ended_unix'], dt.timezone.utc).isoformat())
    summary['measurement_range'] = {'start': min(times) if times else None, 'end': max(ends) if ends else None}
    start_path = SCRATCH / 'job-start.json'
    if start_path.exists():
        start = read(start_path)
        summary['job_start_record'] = start
        epoch = next((v for k, v in start.items() if isinstance(v, (int, float)) and v > 1e9), None)
        if epoch:
            summary['elapsed_wall_seconds'] = time.time() - epoch
    if summary['measurement_range']['start']:
        window = summary['measurement_range']
        summary['measurement_wall_seconds'] = (dt.datetime.fromisoformat(window['end']) - dt.datetime.fromisoformat(window['start'])).total_seconds()
    resume = SCRATCH / 'resume-start.json'
    if resume.exists():
        summary['resume_start_record'] = read(resume)
        summary['resume_elapsed_wall_seconds'] = time.time() - summary['resume_start_record']['started_epoch']
    if not summary['missing']:
        summary['status'] = 'complete'
    snapshot = RESULTS / 'summary-first-pass.json'
    if snapshot.exists():
        first = read(snapshot)
        summary['first_pass_recorded_wall'] = {k: first[k] for k in ['measurement_wall_seconds', 'resume_elapsed_wall_seconds', 'elapsed_wall_seconds']}
    from timing_summary import derive
    timing = derive(DEMO, SCRATCH, stats)
    if timing is not None:
        summary['timing_pass'] = timing
    block = SCRATCH / 'blocker.json'
    if block.exists():
        summary['blocker'] = read(block)
    (RESULTS / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    status = summary['status'] if timing is None else f"first pass {summary['status']}; timing follow-up {timing['status']}"
    print('Summary derived from saved raw evidence: ' + status)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        import sys
        detail = str(error) if isinstance(error, (AssertionError, ValueError)) else 'Inspect saved evidence and script inputs'
        print(f'Check failed: {type(error).__name__}: {detail}', file=sys.stderr)
        sys.exit(1)
