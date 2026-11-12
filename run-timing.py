#!/usr/bin/env python3
"""Rotated condition blocks, unchanged inference settings, recorded load gate."""
import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from run_all import DEMO, SCRATCH, IMAGE, PORT, measure, archive_incomplete, stop_signal

ORDERS = [['cold', 'warm', 'early-change', 'late-change'],
          ['warm', 'early-change', 'late-change', 'cold'],
          ['early-change', 'late-change', 'cold', 'warm']]


def load_gate():
    started = time.monotonic()
    samples = []
    while True:
        load = float(Path('/proc/loadavg').read_text().split()[0])
        samples.append({'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'loadavg_1m': load})
        elapsed = time.monotonic() - started
        if load <= 6 or elapsed >= 600:
            return {'samples': samples, 'wait_seconds': elapsed, 'start_loadavg_1m': load,
                    'high_load_start': load > 6, 'limit': 6, 'maximum_wait_seconds': 600}
        print(f'Waiting at load {load:.2f}; elapsed {elapsed:.0f} seconds', flush=True)
        time.sleep(min(10, 600 - elapsed))


def main():
    signal.signal(signal.SIGTERM, stop_signal)
    signal.signal(signal.SIGINT, stop_signal)
    if os.getpriority(os.PRIO_PROCESS, 0) < 10:
        raise ValueError('Run with nice -n 10')
    subprocess.run(['docker', 'image', 'inspect', IMAGE], check=True, stdout=subprocess.DEVNULL)
    active = subprocess.check_output(['docker', 'ps', '--filter', 'name=vk-caching-', '--format', '{{.Names}}'], text=True)
    if active.strip():
        raise ValueError('An existing caching server is active; inspect before starting another')
    started = time.time()
    state = 'interrupted or failed'
    try:
        for repeat, order in enumerate(ORDERS, 1):
            for position, condition in enumerate(order):
                path = DEMO / 'results' / f'timing-{condition}-r{repeat}.jsonl'
                meta = DEMO / 'results' / f'timing-start-{condition}-r{repeat}.json'
                diagnostic = DEMO / 'results' / f'timing-tokenization-r{repeat}.json'
                if path.exists() and len(path.read_text().splitlines()) == 30:
                    if not meta.exists():
                        raise ValueError('Completed timing condition has no load-gate record')
                    print(f'Preserving timing {condition} repeat {repeat}', flush=True)
                    continue
                archive_incomplete([path, meta, *([diagnostic] if condition == 'warm' else [])])
                gate = load_gate()
                gate.update(condition=condition, repeat=repeat, order_position=position, order=order)
                with meta.open('x') as handle:
                    json.dump(gate, handle, indent=2)
                    handle.write('\n')
                print(f'Timing {condition} repeat {repeat}, start load {gate["start_loadavg_1m"]:.2f}, high-load flag {gate["high_load_start"]}', flush=True)
                measure('chat', f'timing-{condition}-r{repeat}', 1,
                        [str(DEMO / 'run-prefix.py'), '--timing', '--condition', condition,
                         '--repeat', str(repeat), '--port', str(PORT)])
        state = 'complete'
    finally:
        (SCRATCH / 'timing-status.json').write_text(json.dumps({'status': state,
            'started_unix': started, 'ended_unix': time.time()}, indent=2) + '\n')
    print('Interleaved timing measurements complete', flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        detail = str(error) if isinstance(error, ValueError) else 'Inspect preserved timing evidence and server logs'
        print(f'Timing run stopped: {type(error).__name__}: {detail}', file=sys.stderr)
        sys.exit(1)
