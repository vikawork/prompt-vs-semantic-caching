"""Derive the follow-up section for summarize.py; never write a summary file."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import statistics as st

CONDITIONS = ['cold', 'warm', 'early-change', 'late-change']
ORDERS = [CONDITIONS, CONDITIONS[1:] + CONDITIONS[:1], CONDITIONS[2:] + CONDITIONS[:2]]
AGREEMENT_TOLERANCE = .10


def load(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def derive(demo, scratch, stats):
    if not (scratch / 'timing-start.json').exists():
        return None
    result = {'status': 'incomplete', 'orders': ORDERS, 'missing': [], 'conditions': {},
              'agreement_tolerance': AGREEMENT_TOLERANCE,
              'scope': 'Cold uses all requests; cached conditions exclude each fresh server first write. Load statistics include all requests.'}
    metrics = ['prompt_n', 'cache_n', 'prompt_ms', 'ttft_ms', 'total_ms', 'prompt_ms_per_token']
    all_data = []
    gates = []
    for condition in CONDITIONS:
        collected = []
        repeats = []
        writes = []
        for repeat in (1, 2, 3):
            path = demo / 'results' / f'timing-{condition}-r{repeat}.jsonl'
            meta = demo / 'results' / f'timing-start-{condition}-r{repeat}.json'
            if not path.exists() or len(path.read_text().splitlines()) != 30 or not meta.exists():
                result['missing'].append(path.name)
                continue
            data = rows(path)
            gate = load(meta)
            assert gate['order'] == ORDERS[repeat - 1]
            assert gate['condition'] == condition and gate['repeat'] == repeat
            assert gate['order_position'] == ORDERS[repeat - 1].index(condition)
            gate['reference'] = {'file': 'results/' + meta.name, 'line': 1}
            gates.append(gate)
            for index, row in enumerate(data):
                assert row['experiment'] == 'timing' and row['condition'] == condition and row['repeat'] == repeat
                assert row['question_index'] == index and row['prompt_n'] > 0
                assert row['loadavg_1m'] >= 0 and row['total_ms'] >= row['ttft_ms'] >= 0
                row['cache_n'] = row['server_timings']['cache_n']
                row['prompt_ms_per_token'] = row['prompt_ms'] / row['prompt_n']
                row['reference'] = {'file': 'results/' + path.name, 'line': index + 1}
            chosen = data if condition == 'cold' else data[1:]
            repeats.append({'repeat': repeat, 'metrics': {k: stats([r[k] for r in chosen]) for k in metrics},
                            'load': stats([r['loadavg_1m'] for r in data]), 'gate': gate})
            writes.append({k: data[0][k] for k in metrics + ['reference', 'repeat']})
            collected.extend(chosen)
            all_data.extend(data)
        if collected:
            condition_data = [r for r in all_data if r['condition'] == condition]
            result['conditions'][condition] = {'metrics': {k: stats([r[k] for r in collected]) for k in metrics},
                'load': stats([r['loadavg_1m'] for r in condition_data]), 'repeats': repeats, 'first_writes': writes,
                'high_load_repeats': [r['repeat'] for r in repeats if r['gate']['high_load_start']]}
    result['gates'] = gates
    result['excluded_attempts'] = [{'reference': {'file': str(path.relative_to(demo)), 'line': 1},
                                    'saved_requests': len(rows(path))}
                                   for path in sorted((demo / 'results/aborted').glob('*/timing-*.jsonl'))]
    if all_data:
        start = min(r['started_utc'] for r in all_data)
        end = max(r['finished_utc'] for r in all_data)
        result['measurement_range'] = {'start': start, 'end': end}
        result['measurement_wall_seconds'] = (dt.datetime.fromisoformat(end) - dt.datetime.fromisoformat(start)).total_seconds()
    if not result['missing']:
        result['status'] = 'complete'
        comparison = []
        for repeat in (1, 2, 3):
            cold = result['conditions']['cold']['repeats'][repeat - 1]['metrics']['prompt_ms_per_token']['median']
            early = result['conditions']['early-change']['repeats'][repeat - 1]['metrics']['prompt_ms_per_token']['median']
            comparison.append({'repeat': repeat, 'cold_ms_per_token': cold, 'early_ms_per_token': early,
                               'relative_difference': (early - cold) / cold})
        cold = result['conditions']['cold']['metrics']['prompt_ms_per_token']['median']
        early = result['conditions']['early-change']['metrics']['prompt_ms_per_token']['median']
        difference = (early - cold) / cold
        result['agreement'] = {'relative_difference': difference, 'within_bound': abs(difference) <= AGREEMENT_TOLERANCE,
            'repeats': comparison, 'every_repeat_within_bound': all(abs(r['relative_difference']) <= AGREEMENT_TOLERANCE for r in comparison)}
    diagnostic = demo / 'results/warm-tokenization.json'
    if diagnostic.exists():
        d = load(diagnostic)
        token_ids = {k: [t['id'] if isinstance(t, dict) else t for t in v] for k, v in d['tokens'].items()}
        assert token_ids['prefix'] + token_ids['manual'] + token_ids['suffix'] == token_ids['full'], 'Token boundary concatenation differs'
        source_index = d['source_index']
        original = rows(demo / 'results/prefix-warm-r1.jsonl')[source_index]
        assert original['question_id'] == d['question_id'] and original['prompt_sha256'] == d['prompt_sha256']
        prefix = len(token_ids['prefix'])
        manual = len(token_ids['manual'])
        cached = original['server_timings']['cache_n']
        total = len(token_ids['full'])
        assert total == original['tokens_evaluated'] == cached + original['prompt_n']
        assert prefix <= cached < prefix + manual
        detail = {'reference': {'file': 'results/prefix-warm-r1.jsonl', 'line': source_index + 1},
                  'tokenization_reference': {'file': 'results/' + diagnostic.name, 'line': 1},
                  'evaluated': original['prompt_n'], 'cache_n': cached, 'total_prompt': total,
                  'manual_tokens': manual, 'prefix_template_tokens': prefix,
                  'manual_file_tokens': len(token_ids['manual_file']),
                  'manual_whitespace_trimmed': d['manual_whitespace_trimmed'],
                  'cached_manual_tokens': cached - prefix, 'reevaluated_manual_tokens': prefix + manual - cached,
                  'evaluated_question_template_tokens': len(token_ids['suffix']), 'cause': 'not established by saved server logs'}
        log = demo / 'logs/warm-r1.log'
        timing = [(i + 1, line) for i, line in enumerate(log.read_text().splitlines()) if 'prompt eval time =' in line]
        assert len(timing) == 30
        detail['server_log_reference'] = {'file': 'logs/' + log.name, 'line': timing[source_index][0]}
        detail['server_log_quote'] = timing[source_index][1]
        # Keep any explicit causal evidence available to the reader. A progress
        # count or similarly sized batch alone does not establish a cause.
        detail['boundary_log_matches'] = [{'file': 'logs/' + log.name, 'line': i + 1, 'text': line}
            for i, line in enumerate(log.read_text().splitlines())
            if re.search(r'checkpoint|cache.reuse.boundary|batch.boundary', line, re.I)]
        result['warm_decomposition'] = detail
    manifest = load(scratch / 'first-pass-files.json')
    preserved = {name: hashlib.sha256((demo / ('results/summary-first-pass.json' if name == 'results/summary.json' else name)).read_bytes()).hexdigest() == digest
                 for name, digest in manifest.items()}
    assert all(preserved.values()), 'First-pass evidence changed'
    result['preserved_first_pass_files'] = len(preserved)
    status = scratch / 'timing-status.json'
    if status.exists():
        result['run'] = load(status)
        result['run_wall_seconds'] = result['run']['ended_unix'] - result['run']['started_unix']
        result['followup_wall_seconds'] = result['run']['ended_unix'] - load(scratch / 'timing-start.json')['started_epoch']
    return result
