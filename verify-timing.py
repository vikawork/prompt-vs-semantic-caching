#!/usr/bin/env python3
"""Check follow-up evidence, original-prompt identity, and load-gate records."""
import datetime as dt
import json
import math
from pathlib import Path
import re
import statistics as st

DEMO = Path(__file__).resolve().parent
SCRATCH = DEMO.parents[2] / '.studio/ai-channel/caching'


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    summary = json.loads((DEMO / 'results/summary.json').read_text())
    timing = summary['timing_pass']
    assert timing['status'] == 'complete' and timing['run']['status'] == 'complete'
    chronological = []
    count = 0
    for name, part in timing['conditions'].items():
        chosen = []
        loads = []
        for repeat in (1, 2, 3):
            values = rows(DEMO / 'results' / f'timing-{name}-r{repeat}.jsonl')
            original = rows(DEMO / 'results' / f'prefix-{name}-r{repeat}.jsonl')
            gate = json.loads((DEMO / 'results' / f'timing-start-{name}-r{repeat}.json').read_text())
            assert len(values) == 30
            assert gate['high_load_start'] == (gate['start_loadavg_1m'] > gate['limit'])
            assert gate['start_loadavg_1m'] == gate['samples'][-1]['loadavg_1m']
            if gate['high_load_start']:
                assert gate['wait_seconds'] >= gate['maximum_wait_seconds'] == 600
            chronological.append((values[0]['started_utc'], repeat, name, values[-1]['finished_utc']))
            log_candidates = []
            for log in (DEMO / 'logs').glob(f'timing-{name}-r{repeat}*.log'):
                lines = log.read_text().splitlines()
                matches = [re.search(r'prompt eval time =\s+([\d.]+) ms /\s+(\d+) tokens', line) for line in lines]
                matches = [m for m in matches if m]
                if len(matches) == 30 and all(int(m.group(2)) == r['prompt_n'] and abs(float(m.group(1)) - r['prompt_ms']) < .011 for m, r in zip(matches, values)):
                    log_candidates.append(log)
            assert len(log_candidates) == 1, 'Each timing block needs its own complete server log'
            assert values[0]['server_timings']['cache_n'] == 0, 'Fresh server must start with no cached prompt'
            for index, (row, first) in enumerate(zip(values, original)):
                for key in ['question_index', 'question_id', 'manual', 'slot', 'seed', 'temperature', 'n_predict', 'cache_prompt', 'prompt_sha256', 'manual_tokens']:
                    assert row[key] == first[key], 'Follow-up changed an original inference input'
                assert row['question_index'] == index and row['condition'] == name and row['repeat'] == repeat
                assert row['experiment'] == 'timing'
                assert row['server_final']['id_slot'] == 0 and row['server_final']['stop']
                assert row['output'] == ''.join(e.get('content', '') for e in row['stream_events'])
                assert row['tokens_evaluated'] == row['prompt_n'] + row['server_timings']['cache_n']
                assert math.isfinite(row['loadavg_1m']) and row['loadavg_1m'] >= 0
                assert row['started_utc'] >= gate['samples'][-1]['utc']
                assert 0 <= row['ttft_ms'] <= row['total_ms']
                row['cache_n'] = row['server_timings']['cache_n']
                row['prompt_ms_per_token'] = row['prompt_ms'] / row['prompt_n']
                count += 1
            chosen.extend(values if name == 'cold' else values[1:])
            loads.extend(r['loadavg_1m'] for r in values)
        for key, metric in part['metrics'].items():
            values = [r[key] for r in chosen]
            assert metric == {'count': len(values), 'median': st.median(values), 'min': min(values), 'max': max(values)}
        assert part['load']['median'] == st.median(loads) and part['load']['max'] == max(loads)
    chronological.sort()
    expected = [(repeat, condition) for repeat, order in enumerate(timing['orders'], 1) for condition in order]
    assert [(repeat, condition) for _, repeat, condition, _ in chronological] == expected
    for first, second in zip(chronological, chronological[1:]):
        assert first[3] < second[0], 'Condition blocks overlap'
    d = timing['warm_decomposition']
    assert d['reevaluated_manual_tokens'] + d['evaluated_question_template_tokens'] == d['evaluated']
    assert d['cached_manual_tokens'] + d['prefix_template_tokens'] == d['cache_n']
    assert d['cached_manual_tokens'] + d['reevaluated_manual_tokens'] == d['manual_tokens']
    result = {'status': 'passed', 'requests': count, 'blocks': len(chronological),
              'preserved_first_pass_files': timing['preserved_first_pass_files'],
              'checks': ['original inference inputs and prompt hashes', 'rotated fresh-server blocks and non-overlap',
                         'saved stream output', 'server-log timing reconciliation', 'load gate and per-request loads',
                         'all pooled timing and load statistics', 'manual/template token accounting']}
    (SCRATCH / 'timing-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Follow-up saved-evidence verification passed')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        detail = str(error) if isinstance(error, (AssertionError, ValueError)) else 'Inspect saved timing evidence'
        print(f'Timing verification failed: {type(error).__name__}: {detail}')
        raise SystemExit(1)
