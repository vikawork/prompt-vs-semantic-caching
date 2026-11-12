#!/usr/bin/env python3
"""Native llama-server completion streams; one fixed, serial condition per invocation."""
import argparse
import datetime as dt
import hashlib
import json
import time
import urllib.request
from pathlib import Path


def post(port, endpoint, value):
    request = urllib.request.Request(f"http://127.0.0.1:{port}/{endpoint}",
                                     json.dumps(value).encode(), {"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(request, timeout=600)


def run(args):
    base = Path(__file__).resolve().parent
    questions = json.loads((base / "fixtures/questions.json").read_text())
    manuals = [(base / f"fixtures/{name}").read_text() for name in ["manual.md", "manual-b.md"]]
    output = base / "results" / f"{'timing' if args.timing else 'prefix'}-{args.condition}-r{args.repeat}.jsonl"
    if output.exists():
        raise ValueError("Refusing to overwrite an existing condition")
    token_counts = []
    for manual in manuals:
        with post(args.port, "tokenize", {"content": manual, "add_special": False}) as response:
            token_counts.append(len(json.load(response)["tokens"]))
    with output.open("x") as file:
        for index, question in enumerate(questions):
            alternating = args.condition.startswith("two-prefixes")
            manual_index = index % 2 if alternating else 0
            system = manuals[manual_index]
            timestamp = (dt.datetime(2026, 11, 12, tzinfo=dt.timezone.utc)
                         + dt.timedelta(seconds=index)).isoformat()
            changing_line = f"Current time: {timestamp}\n"
            if args.condition == "early-change":
                system = changing_line + system
            elif args.condition == "late-change":
                system += "\n" + changing_line
            # Use the model's own embedded template; disable thinking consistently.
            messages = [{"role": "system", "content": system},
                        {"role": "user", "content": question["question"]}]
            with post(args.port, "apply-template", {"messages": messages,
                      "add_generation_prompt": True, "chat_template_kwargs": {"enable_thinking": False}}) as response:
                prompt = json.load(response)["prompt"]
            request = {"prompt": prompt, "stream": True, "temperature": 0, "seed": 12648430,
                       "n_predict": 48, "cache_prompt": args.condition != "cold",
                       "id_slot": manual_index if args.condition == "two-prefixes-two" else 0}
            if args.timing and args.condition == 'warm' and index == 2:
                inserted_manual = system if system in prompt else system.strip()
                prefix, suffix = prompt.split(inserted_manual, 1)
                parts = {}
                for key, content in [('full', prompt), ('prefix', prefix), ('manual', inserted_manual), ('manual_file', system), ('suffix', suffix)]:
                    with post(args.port, 'tokenize', {'content': content, 'add_special': False,
                              'parse_special': True, 'with_pieces': True}) as response:
                        parts[key] = json.load(response)['tokens']
                diagnostic = {'question_id': question['id'], 'repeat': args.repeat,
                              'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                              'prefix_text': prefix, 'suffix_text': suffix, 'tokens': parts,
                              'manual_whitespace_trimmed': inserted_manual != system,
                              'tokenize_options': {'add_special': False, 'parse_special': True, 'with_pieces': True}}
                path = base / 'results' / f'timing-tokenization-r{args.repeat}.json'
                with path.open('x') as handle:
                    json.dump(diagnostic, handle, indent=2)
                    handle.write('\n')
            load = float(Path('/proc/loadavg').read_text().split()[0]) if args.timing else None
            start_utc = dt.datetime.now(dt.timezone.utc).isoformat()
            start = time.perf_counter_ns()
            first = None
            text = []
            final = None
            events = []
            with post(args.port, "completion", request) as response:
                for raw in response:
                    if not raw.startswith(b"data: "):
                        continue
                    body = raw[6:].strip()
                    if body == b"[DONE]":
                        continue
                    event = json.loads(body)
                    events.append(event)
                    if event.get("content"):
                        if first is None:
                            first = time.perf_counter_ns()
                        text.append(event["content"])
                    if event.get("stop"):
                        final = event
            end = time.perf_counter_ns()
            if final is None or first is None or "timings" not in final:
                raise ValueError("Stream omitted content, final event, or server timings")
            timings = final["timings"]
            row = {"experiment": "prefix", "condition": args.condition, "repeat": args.repeat,
                   "question_index": index, "question_id": question["id"], "manual": manual_index,
                   "manual_tokens": token_counts[manual_index], "slot": request["id_slot"],
                   "cache_prompt": request["cache_prompt"], "seed": request["seed"],
                   "n_predict": request["n_predict"], "temperature": request["temperature"],
                   "started_utc": start_utc, "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                   "prompt_n": timings["prompt_n"], "prompt_ms": timings["prompt_ms"],
                   "tokens_evaluated": final.get("tokens_evaluated"),
                   "tokens_cached": final.get("tokens_cached"),
                   "ttft_ms": (first - start) / 1e6, "total_ms": (end - start) / 1e6,
                   "output": "".join(text), "server_timings": timings,
                   "server_final": final, "stream_events": events}
            if args.timing:
                row.update(experiment='timing', loadavg_1m=load)
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
            file.flush()
            print(f"{args.condition} repeat {args.repeat}: request {index + 1} saved", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18940)
    parser.add_argument("--condition", required=True, choices=["cold", "warm", "early-change", "late-change",
                                                             "two-prefixes-one", "two-prefixes-two"])
    parser.add_argument("--repeat", type=int, required=True, choices=[1, 2, 3])
    parser.add_argument('--timing', action='store_true')
    try:
        run(parser.parse_args())
    except Exception as error:
        import sys
        detail = str(error) if isinstance(error, ValueError) else 'Inspect the local server log; no request was fabricated'
        print(f'Prefix measurement failed: {type(error).__name__}: {detail}', file=sys.stderr)
        sys.exit(1)
