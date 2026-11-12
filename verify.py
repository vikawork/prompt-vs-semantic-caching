"""Audit completed saved evidence; never fabricate or rewrite measurement rows."""
import getpass
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import socket

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
import numpy as np

DEMO = Path(__file__).resolve().parent
SCRATCH = DEMO.parents[2] / '.studio/ai-channel/caching'
CONDITIONS = ['cold', 'warm', 'early-change', 'late-change', 'two-prefixes-one', 'two-prefixes-two']


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    summary = json.loads((DEMO / 'results/summary.json').read_text())
    assert summary['status'] == 'complete', 'Summary must be complete'
    questions = json.loads((DEMO / 'fixtures/questions.json').read_text())
    warnings = []
    data = {}
    for condition in CONDITIONS:
        for repeat in (1, 2, 3):
            path = DEMO / 'results' / f'prefix-{condition}-r{repeat}.jsonl'
            values = rows(path)
            assert len(values) == len(questions) == 30
            data[(condition, repeat)] = values
            for index, (row, question) in enumerate(zip(values, questions)):
                assert row['condition'] == condition and row['repeat'] == repeat
                assert row['question_index'] == index and row['question_id'] == question['id']
                assert row['seed'] == 12648430 and row['temperature'] == 0 and row['n_predict'] == 48
                assert row['cache_prompt'] == (condition != 'cold')
                assert row['slot'] == (index % 2 if condition == 'two-prefixes-two' else 0)
                assert row['manual'] == (index % 2 if condition.startswith('two-prefixes') else 0)
                assert row['server_final']['stop'] and row['server_final']['id_slot'] == row['slot']
                assert row['output'] == ''.join(event.get('content', '') for event in row['stream_events'])
                assert row['prompt_n'] == row['server_timings']['prompt_n']
                assert row['prompt_ms'] == row['server_timings']['prompt_ms']
                assert 0 <= row['ttft_ms'] <= row['total_ms']
                assert 0 <= row['server_timings']['predicted_n'] <= row['n_predict']
                if row['tokens_evaluated'] != row['prompt_n'] + row['server_timings']['cache_n']:
                    warnings.append({'kind': 'tokens_evaluated differs from prompt_n plus cache_n', 'file': path.name, 'line': index + 1})
    for repeat in (1, 2, 3):
        for cold, warm in zip(data[('cold', repeat)], data[('warm', repeat)]):
            assert cold['prompt_sha256'] == warm['prompt_sha256'], 'Output equality requires identical prompts'
    paired = rows(DEMO / 'results/semantic-pairs.jsonl')
    store = rows(DEMO / 'results/semantic-store.jsonl')
    assert len(paired) == 2060 and len(store) == 2000
    vectors = {(r['dataset'], str(r['id']), r['side']): np.array(r['embedding'])
               for r in rows(SCRATCH / 'semantic-embeddings.jsonl')}
    assert len(vectors) == 4120
    for vector in vectors.values():
        assert np.isfinite(vector).all() and abs(np.linalg.norm(vector) - 1) < 1e-10
    public = [r for r in paired if r['dataset'] == 'public']
    matrix = np.stack([vectors[('public', str(r['id']), 1)] for r in public])
    for row in paired:
        first = vectors[(row['dataset'], str(row['id']), 1)]
        second = vectors[(row['dataset'], str(row['id']), 2)]
        assert abs(float(np.clip(first @ second, -1, 1)) - row['cosine_similarity']) < 1e-10
        if row['dataset'] == 'public':
            assert 'question1' not in row and 'question2' not in row
    for index, row in enumerate(store):
        vector = vectors[('public', str(row['id']), 2)]
        similarities = matrix @ vector
        nearest = int(np.argmax(similarities))
        assert nearest == row['nearest_index']
        assert abs(float(np.clip(similarities[nearest], -1, 1)) - row['nearest_similarity']) < 1e-10
        assert row['nearest_id'] == public[nearest]['id']
        assert row['nearest_correct'] == bool(nearest == index and row['same_answer'])
        assert row['embed_ms'] >= 0 and row['lookup_ms'] >= 0
        assert abs(row['total_ms'] - row['embed_ms'] - row['lookup_ms']) < 1e-9
    for threshold in summary['store']['thresholds']:
        accepted = [r for r in store if r['nearest_similarity'] >= threshold['threshold']]
        assert threshold['correct'] == sum(r['nearest_correct'] for r in accepted)
        assert threshold['wrong'] == len(accepted) - threshold['correct']
        assert threshold['correct'] + threshold['wrong'] + threshold['not_served'] == 2000
    for dataset, key in [('public', 'public_pairs'), ('ours', 'our_pairs')]:
        values = [r for r in paired if r['dataset'] == dataset]
        positive = [r for r in values if r['same_answer']]
        negative = [r for r in values if not r['same_answer']]
        part = summary[key]
        assert part['positive'] == len(positive) and part['negative'] == len(negative)
        assert len(part['thresholds']) == 50
        for threshold in part['thresholds']:
            correct = sum(r['cosine_similarity'] >= threshold['threshold'] for r in positive)
            wrong = sum(r['cosine_similarity'] >= threshold['threshold'] for r in negative)
            assert threshold['correct_hits'] == correct and threshold['wrong_hits'] == wrong
            assert threshold['correct_share'] == correct / len(positive)
            assert threshold['wrong_share'] == wrong / len(negative)
        first = next((r for r in part['thresholds'] if r['wrong_share'] < .01), None)
        assert part['first_under_one_percent'] == first
    for condition in ('cold', 'warm', 'early-change', 'late-change'):
        screen = summary['screen'][condition]
        assert 'server_log_reference' in screen
        reference = screen['server_log_reference']
        line = (DEMO / reference['file']).read_text().splitlines()[reference['line'] - 1]
        assert 'prompt eval time' in line
    identifiers = [x for x in (getpass.getuser(), socket.gethostname()) if len(x) > 3]
    private = [ipaddress.ip_network(net) for net in [(0x0A000000, 8), (0xAC100000, 12), (0xC0A80000, 16)]]
    for path in DEMO.rglob('*'):
        if not path.is_file() or path.suffix not in ('.md', '.json', '.jsonl', '.log'):
            continue
        text = path.read_text()
        assert ('/' + 'home' + '/') not in text, 'Home directory found in an artifact'
        assert not any(re.search(r'(?<![A-Za-z0-9_])' + re.escape(identifier) + r'(?![A-Za-z0-9_])', text, re.I) for identifier in identifiers), 'Machine identifier found in an artifact'
        for match in re.finditer(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])', text):
            try:
                address = ipaddress.ip_address(match.group())
            except ValueError:
                continue
            assert not any(address in network for network in private), 'LAN address found in an artifact'
    report = {'status': 'passed', 'prefix_requests': sum(len(v) for v in data.values()),
              'paired_scores': len(paired), 'store_queries': len(store), 'normalized_vectors': len(vectors),
              'warnings': warnings, 'checks': ['condition settings and order', 'cold/warm prompt identity',
                  'stream output reconstruction', 'all saved cosine scores', 'all nearest indices and strict labels',
                  'all paired and store threshold counts and first-bound selection',
                  'screen server-log references', 'artifact privacy scan']}
    (SCRATCH / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Saved-evidence verification passed')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        import sys
        detail = str(error) if isinstance(error, (AssertionError, ValueError)) else 'Inspect saved evidence and script inputs'
        print(f'Check failed: {type(error).__name__}: {detail}', file=sys.stderr)
        sys.exit(1)
