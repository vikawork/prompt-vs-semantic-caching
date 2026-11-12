"""Pinned QQP text stays in memory; artifacts contain IDs, labels and hashes."""
import hashlib
import json
from pathlib import Path
import random
import urllib.request

REVISION = 'df33eff016c496a5b944d026d5c0b511dc1f64f1'
SHA256 = 'e7fbbe5677938f14662bccb47598768f5574da144972a73e066763fca2215290'
URL = f'https://huggingface.co/datasets/SetFit/qqp/resolve/{REVISION}/validation.jsonl'
SEED = 12648430


def load_pairs():
    raw = urllib.request.urlopen(URL, timeout=180).read()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError('Public dataset hash mismatch')
    rows = [json.loads(line) for line in raw.splitlines()]
    groups = [[row for row in rows if row['label'] == label] for label in (0, 1)]
    positive_count = round(2000 * len(groups[1]) / len(rows))
    rng = random.Random(SEED)
    chosen = rng.sample(groups[0], 2000 - positive_count) + rng.sample(groups[1], positive_count)
    rng.shuffle(chosen)
    pairs = [{'id': row['idx'], 'question1': row['text1'], 'question2': row['text2'],
              'same_answer': bool(row['label'])} for row in chosen]
    manifest = {'repository': 'SetFit/qqp', 'revision': REVISION, 'file': 'validation.jsonl',
                'sha256': SHA256, 'source': 'GLUE QQP validation; JSONL conversion',
                'licence': 'Not specified by the mirror; GLUE metadata says other and refers to upstream terms. No permissive grant verified.',
                'selection': 'Stratified random sample; positive count rounded to nearest integer; shuffled once',
                'seed': SEED, 'source_count': len(rows), 'source_positive': len(groups[1]),
                'sample_count': len(pairs), 'sample_positive': positive_count,
                'text_storage': 'Downloaded and embedded in memory; public text omitted from artifacts',
                'pairs': [{'id': p['id'], 'same_answer': p['same_answer'],
                           'question1_sha256': hashlib.sha256(p['question1'].encode()).hexdigest(),
                           'question2_sha256': hashlib.sha256(p['question2'].encode()).hexdigest()} for p in pairs]}
    path = Path(__file__).resolve().parent / 'fixtures/public-manifest.json'
    encoded = json.dumps(manifest, indent=2) + '\n'
    if path.exists() and path.read_text() != encoded:
        raise ValueError('Public sample changed from its recorded manifest')
    if not path.exists():
        path.write_text(encoded)
    return pairs
