"""Serial CPU experiments, fresh containers, cleanup even after measurement failure."""
import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

DEMO = Path(__file__).resolve().parent
SCRATCH = DEMO.parents[2] / '.studio/ai-channel/caching'
IMAGE = 'ghcr.io/ggml-org/llama.cpp:full-b12211@sha256:8960de326dd60972cc4d442531f4efa006416d5896da2a39f0def0b55cbcb0c2'
PORT = 18940
CONDITIONS = ['cold', 'warm', 'early-change', 'late-change', 'two-prefixes-one', 'two-prefixes-two']


def command(argv, **kwargs):
    return subprocess.run(argv, cwd=DEMO, check=True, **kwargs)


def stop_signal(signum, frame):
    raise KeyboardInterrupt


def measure(mode, label, slots, argv):
    name = f'vk-caching-{label}'
    log_path = DEMO / 'logs' / f'{label}.log'
    if log_path.exists():
        log_path = DEMO / 'logs' / f'{label}-attempt-{time.time_ns()}.log'
    # Only this invocation's name is removed; existing names are an error.
    exists = subprocess.run(['docker', 'container', 'inspect', name], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL).returncode == 0
    if exists:
        raise ValueError('A caching container already exists; inspect it before resuming')
    try:
        command(['bash', str(DEMO / 'serve.sh'), mode, name, str(PORT), str(slots)])
        command([sys.executable, *argv])
    finally:
        with log_path.open('x') as log:
            subprocess.run(['docker', 'logs', name], stdout=log, stderr=log, check=False)
        subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, check=False)


def archive_incomplete(paths):
    present = [p for p in paths if p.exists()]
    if present:
        archive = DEMO / 'results' / 'aborted' / str(time.time_ns())
        archive.mkdir(parents=True)
        for path in present:
            path.rename(archive / path.name)


def main():
    signal.signal(signal.SIGTERM, stop_signal)
    signal.signal(signal.SIGINT, stop_signal)
    command(['docker', 'image', 'inspect', IMAGE], stdout=subprocess.DEVNULL)
    if os.getpriority(os.PRIO_PROCESS, 0) < 10:
        raise ValueError('Run with nice -n 10')
    # setup.sh is deliberately separate: it downloads pinned HF assets only.
    provenance = SCRATCH / 'provenance/models.json'
    if not provenance.exists():
        raise ValueError('Run setup.sh first')
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    status_path = SCRATCH / 'run-status.json'
    try:
        for condition in CONDITIONS:
            for repeat in (1, 2, 3):
                path = DEMO / 'results' / f'prefix-{condition}-r{repeat}.jsonl'
                if path.exists() and len(path.read_text().splitlines()) == 30:
                    print(f'Preserving completed {condition} repeat {repeat}', flush=True)
                    continue
                archive_incomplete([path])
                measure('chat', f'{condition}-r{repeat}', 2 if condition == 'two-prefixes-two' else 1,
                        [str(DEMO / 'run-prefix.py'), '--port', str(PORT), '--condition', condition,
                         '--repeat', str(repeat)])
        paths = [DEMO / 'results' / f'semantic-{part}.jsonl' for part in ('pairs', 'store', 'run')]
        complete = (all(p.exists() for p in paths) and len(paths[0].read_text().splitlines()) == 2060
                    and len(paths[1].read_text().splitlines()) == 2000)
        if not complete:
            archive_incomplete(paths)
            measure('embedding', 'semantic', 1, [str(DEMO / 'run-semantic.py'), '--port', str(PORT),
                    '--scratch', str(SCRATCH)])
        state = 'complete'
    except BaseException:
        state = 'interrupted or failed; inspect preserved raw files and logs'
        raise
    finally:
        status_path.write_text(json.dumps({'invocation_started_utc': started,
            'invocation_finished_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'status': state}, indent=2) + '\n')
    command([sys.executable, str(DEMO / 'summarize.py')])
    command([sys.executable, str(DEMO / 'write_report.py')])


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        import sys
        detail = str(error) if isinstance(error, ValueError) else 'Inspect saved state and server logs; no measurement was fabricated'
        print(f'Run stopped: {type(error).__name__}: {detail}', file=sys.stderr)
        sys.exit(1)
