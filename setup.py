"""Verify local chat weights and download the pinned, MIT-licensed embedding weights."""
import hashlib
import json
from pathlib import Path
import urllib.request

DEMO = Path(__file__).resolve().parent
ROOT = DEMO.parents[2]
SCRATCH = ROOT / '.studio/ai-channel/caching'
MODEL = SCRATCH / 'models'
MODEL.mkdir(parents=True, exist_ok=True)
(SCRATCH / 'provenance').mkdir(parents=True, exist_ok=True)
for directory in ('results', 'logs'):
    (DEMO / directory).mkdir(parents=True, exist_ok=True)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    chat_hash = 'e35200cb6bd8ed0e263c0dbbe2d70c68d48eef96d9a073ee37f76d6872223509'
    if sha(MODEL / 'qwen3.5-0.8b-q8_0.gguf') != chat_hash:
        raise ValueError('Local chat model hash mismatch')
    repo = 'CompendiumLabs/bge-small-en-v1.5-gguf'
    revision = 'd32f8c040ea3b516330eeb75b72bcc2d3a780ab7'
    upstream = 'BAAI/bge-small-en-v1.5'
    upstream_revision = '5c38ec7c405ec4b44b94cc5a9bb96e735b38267a'
    filename = 'bge-small-en-v1.5-q8_0.gguf'
    expected = 'ec38e8da142596baa913124ae50550de284b6916bf59577ef2f0cb9660c2f514'
    for repository, rev in [(repo, revision), (upstream, upstream_revision)]:
        with urllib.request.urlopen(f'https://huggingface.co/api/models/{repository}/revision/{rev}', timeout=120) as r:
            card = json.load(r)
        if card['sha'] != rev or card.get('cardData', {}).get('license') != 'mit':
            raise ValueError('Embedding revision or permissive licence could not be verified')
    target = MODEL / filename
    if not target.exists():
        temporary = target.with_suffix('.partial')
        with urllib.request.urlopen(f'https://huggingface.co/{repo}/resolve/{revision}/{filename}', timeout=180) as r, temporary.open('wb') as f:
            while chunk := r.read(1024 * 1024):
                f.write(chunk)
        if sha(temporary) != expected:
            temporary.unlink()
            raise ValueError('Downloaded embedding hash mismatch')
        temporary.rename(target)
    if sha(target) != expected:
        raise ValueError('Embedding hash mismatch')
    from public_data import load_pairs
    load_pairs()
    provenance = {'image': 'ghcr.io/ggml-org/llama.cpp:full-b12211@sha256:8960de326dd60972cc4d442531f4efa006416d5896da2a39f0def0b55cbcb0c2',
                  'chat': {'repository': 'Qwen/Qwen3.5-0.8B', 'revision': '2fc06364715b967f1860aea9cf38778875588b17',
                           'file': 'qwen3.5-0.8b-q8_0.gguf', 'sha256': chat_hash,
                           'conversion': 'Existing local Q8_0 conversion; BotPsy demo provenance'},
                  'embedding': {'repository': repo, 'revision': revision, 'file': filename,
                                'sha256': expected, 'licence': 'MIT', 'language': 'English',
                                'upstream': upstream, 'upstream_revision': upstream_revision,
                                'verification': 'Pinned upstream and GGUF repository API licence metadata both MIT; SHA256 verified'},
                  'cpu': next(line.split(':', 1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),
                  'threads': 8, 'http_threads': 1, 'gpu_layers': 0, 'nice': 10, 'seed': 12648430,
                  'temperature': 0, 'n_predict': 48, 'repeats': 3, 'question_count': 30,
                  'chat_context_per_slot': 8192, 'embedding_context': 512, 'embedding_pooling': 'cls (GGUF bert.pooling_type=2)',
                  'binding': 'loopback only', 'prompt_ram_cache': 'disabled; slot KV reuse measured'}
    (SCRATCH / 'provenance/models.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print('Pinned model hashes, embedding licences and public sample verified')


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        import sys
        detail = str(error) if isinstance(error, ValueError) else 'Inspect saved state and server logs; no measurement was fabricated'
        print(f'Run stopped: {type(error).__name__}: {detail}', file=sys.stderr)
        sys.exit(1)
