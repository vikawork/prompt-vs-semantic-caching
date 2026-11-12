#!/usr/bin/env python3
"""Stateless token accounting for an existing first-pass warm request."""
import hashlib
import importlib.util
import json
from pathlib import Path

DEMO = Path(__file__).resolve().parent


def main():
    spec = importlib.util.spec_from_file_location('prefix_runner', DEMO / 'run-prefix.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    values = [json.loads(line) for line in (DEMO / 'results/prefix-warm-r1.jsonl').read_text().splitlines()]
    index, row = next((i, r) for i, r in enumerate(values) if r['prompt_n'] == 514 and r['server_timings']['cache_n'] == 3266)
    prompt = row['server_final']['prompt']
    manual_file = (DEMO / 'fixtures/manual.md').read_text()
    inserted = manual_file if manual_file in prompt else manual_file.strip()
    prefix, suffix = prompt.split(inserted, 1)
    parts = {}
    for name, text in [('full', prompt), ('prefix', prefix), ('manual', inserted), ('manual_file', manual_file), ('suffix', suffix)]:
        with module.post(18940, 'tokenize', {'content': text, 'add_special': False, 'parse_special': True, 'with_pieces': True}) as response:
            parts[name] = json.load(response)['tokens']
    result = {'question_id': row['question_id'], 'repeat': 1, 'source_index': index,
              'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
              'prefix_text': prefix, 'suffix_text': suffix, 'tokens': parts,
              'manual_whitespace_trimmed': inserted != manual_file,
              'tokenize_options': {'add_special': False, 'parse_special': True, 'with_pieces': True}}
    with (DEMO / 'results/warm-tokenization.json').open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print('Saved first-pass warm token accounting:', {k: len(v) for k, v in parts.items()})


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Warm diagnostic stopped:', type(error).__name__)
        raise SystemExit(1)
