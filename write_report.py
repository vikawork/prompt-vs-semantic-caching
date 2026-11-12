"""Render the report exclusively from summarize.py's summary.json."""
import json
from pathlib import Path

DEMO = Path(__file__).resolve().parent


def number(x):
    return f'{x:,.3f}' if isinstance(x, float) else str(x)


def span(value):
    return 'unmeasured' if value is None else f"{number(value['median'])} [{number(value['min'])}, {number(value['max'])}]"


def link(ref):
    return f"`{ref['file']}:{ref['line']}`"


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def table(headers, rows):
    return ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |',
            *['| ' + ' | '.join(cell(c) for c in row) + ' |' for row in rows], '']


def pair_thresholds(part):
    return table(['Threshold', 'Correct / positive', 'Wrong / negative', 'Correct share', 'Wrong share'],
                 [[number(r['threshold']), f"{r['correct_hits']} / {r['positive_count']}",
                   f"{r['wrong_hits']} / {r['negative_count']}", number(r['correct_share']), number(r['wrong_share'])]
                  for r in part['thresholds']])


def render(s):
    out = ['# Prompt caching and semantic caching: local measurement', '',
           'Question: how much prompt work does a prefix cache save, and how often does a similarity cache serve a different answer?', '']
    if 'timing_pass' in s:
        from timing_report import render as render_timing
        out += render_timing(s['timing_pass'], number, span, table, link)
    if s['status'] != 'complete':
        out += ['Status: incomplete. No headline measurement is claimed.', '',
                s.get('blocker', {}).get('reason', 'Required raw measurements are missing.'), '',
                'The scripts and pinned fixtures are prepared. Missing measurements:', '',
                *['- `' + name + '`' for name in s['missing']], '']
    setup = s['setup']
    if setup:
        out += ['## Setup', '', f"CPU: {setup['cpu']}. GPU layers: {setup['gpu_layers']}; threads per server: {setup['threads']}; nice: {setup['nice']}.", '',
                f"Image: `{setup['image']}`.", '',
                f"Chat: `{setup['chat']['repository']}` at `{setup['chat']['revision']}`, {setup['chat']['conversion']}. File `{setup['chat']['file']}`; SHA-256 `{setup['chat']['sha256']}`.", '',
                f"Embedding: `{setup['embedding']['repository']}` at `{setup['embedding']['revision']}`, {setup['embedding']['licence']}, {setup['embedding']['language']}. Upstream `{setup['embedding']['upstream']}` at `{setup['embedding']['upstream_revision']}`. File `{setup['embedding']['file']}`; SHA-256 `{setup['embedding']['sha256']}`.", '',
                f"Sampling: temperature {setup['temperature']}, seed {setup['seed']}, generation cap {setup['n_predict']} tokens. Prefix conditions: {setup['repeats']} repeats, {setup['question_count']} questions each. Context per chat slot: {setup['chat_context_per_slot']}; embedding context: {setup['embedding_context']}; pooling: {setup['embedding_pooling']}. Prompt RAM cache disabled to isolate slot KV reuse.", '',
                'Servers use loopback binding, read-only model mounts, CPU execution, and serial requests. Each condition/repeat starts a fresh server. Containers are removed by the runner.', '']
    source = s['public_source']
    if source:
        out += [f"Public data: `{source['repository']}` at `{source['revision']}`, `{source['file']}`; SHA-256 `{source['sha256']}`. {source['source']}.", '',
                f"Licence: {source['licence']} QQP is explicitly nominated in the brief; this report does not claim it is permissively licensed.", '',
                f"Source positives: {source['source_positive']} / {source['source_count']}; sample positives: {source['sample_positive']} / {source['sample_count']}; seed {source['seed']}. {source['selection']}. {source['text_storage']}.", '']
    window = s['measurement_range']
    if window['start']:
        out += [f"First-pass measurement range (UTC): {window['start']} through {window['end']}.", '']
    if s.get('measurement_wall_seconds') is not None:
        wall = s.get('first_pass_recorded_wall', s)
        out += [f"First-pass measurement wall time: {number(wall['measurement_wall_seconds'])} seconds; elapsed since its resume checkpoint: {number(wall['resume_elapsed_wall_seconds'])} seconds.", '']
    if s.get('elapsed_wall_seconds') is not None:
        wall = s.get('first_pass_recorded_wall', s)
        out += [f"First-pass wall time since its recorded job start, including setup and blocked time: {number(wall['elapsed_wall_seconds'])} seconds.", '']
    if s['status'] != 'complete':
        return '\n'.join(out)
    prefix = s['prefix']
    exp = s['experiments']
    out += ['## First pass: prefix measurements', '',
            'Timing columns are milliseconds. TTFT starts immediately before the native completion request and ends at the first nonempty content event; separate template-formatting and token-count requests are excluded. Each cell is median [minimum, maximum]. Ranges cover requests; per-repeat values below expose run variation. Steady excludes each slot’s first write. The cold baseline includes every request.', '']
    groups = [(exp[0] + ' cold', ['cold']), (exp[1] + ' warm', ['warm']),
              (exp[2] + ' timestamp at start', ['early-change']), (exp[3] + ' timestamp at end', ['late-change']),
              (exp[4] + ' alternating prefixes', ['two-prefixes-one', 'two-prefixes-two'])]
    for title, names in groups:
        out += ['### ' + title, '']
        entries = []
        for name in names:
            part = prefix[name]
            for repeat in part['repeats']:
                m = repeat['all'] if name == 'cold' else repeat['steady']
                entries.append([name, repeat['repeat'], span(m['prompt_n']), span(m['cache_n']), span(m['prompt_ms']), span(m['ttft_ms']), span(m['total_ms'])])
            m = part['all'] if name == 'cold' else part['steady']
            entries.append([name, 'pooled', span(m['prompt_n']), span(m['cache_n']), span(m['prompt_ms']), span(m['ttft_ms']), span(m['total_ms'])])
        out += table(['Condition', 'Repeat', 'Prompt tokens evaluated', 'Server cache_n', 'Prompt ms', 'TTFT ms', 'Total ms'], entries)
        if names != ['cold']:
            out += ['First writes, kept separate:', '']
            out += table(['Condition', 'Repeat', 'Question index', 'Prompt tokens', 'Prompt ms', 'TTFT ms', 'Total ms', 'Evidence'],
                         [[name, row['repeat'], row['question_index'], row['prompt_n'], number(row['prompt_ms']),
                           number(row['ttft_ms']), number(row['total_ms']), link(row['reference'])]
                          for name in names for row in prefix[name]['first_writes']])
    warm = prefix['warm']['steady']
    out += [f"Warm steady medians: {number(warm['cache_n']['median'])} cached prompt tokens and {number(warm['prompt_n']['median'])} evaluated tokens. Cached tokens need not cover the entire shared manual.", '']
    tokens = sorted({n for p in prefix.values() for n in p['manual_tokens']})
    out += ['Manual token counts from the model tokenizer: ' + ', '.join(map(str, tokens)) + '.', '',
            'Server cache_n records the cached prompt tokens from the server timing object. Raw final events, streaming events, prompt token timings, cached-token fields and outputs are retained in each prefix JSONL. Cached-token fields are preserved as reported; they are not treated as an independently verified count of reused prompt tokens.', '',
            '### ' + exp[5] + ' exact output equality', '']
    same = s['same_answer']
    out += [f"Identical: {same['identical']} / {same['count']}; different: {same['different']} / {same['count']}. Equality compares exact concatenated output text for matching question and repeat.", '']
    different = [row for row in same['pairs'] if not row['identical']]
    if different:
        out += table(['Repeat', 'Question', 'Cold output', 'Warm output', 'Cold evidence', 'Warm evidence'],
                     [[r['repeat'], r['question_id'], r['cold'], r['warm'], link(r['cold_reference']), link(r['warm_reference'])] for r in different])
    else:
        out += ['No output difference was observed. This run does not demonstrate nondeterministic output.', '']
    for key, title in [('public_pairs', exp[6] + ' labelled public pairs'), ('our_pairs', exp[7] + ' authored support pairs')]:
        part = s[key]
        out += ['## First pass: ' + title, '', 'Correct share divides accepted positive pairs by all positive pairs. Wrong share divides accepted negative pairs by all negative pairs. A pair label is a proxy for answer equivalence, not a verified answer.', '']
        out += [s['definitions']['first_under'] + '.', '']
        out += pair_thresholds(part)
        first = part['first_under_one_percent']
        if first:
            out += [f"First scanned threshold below the requested wrong-hit bound: {number(first['threshold'])}; wrong share {number(first['wrong_share'])}, correct share {number(first['correct_share'])}.", '']
        else:
            out += ['No scanned threshold meets the requested wrong-hit bound.', '']
        if key == 'our_pairs':
            out += ['Every authored pair, descending cosine similarity:', '']
            out += table(['ID', 'Same answer', 'Stored question', 'Query', 'Cosine', 'Reason', 'Evidence'],
                         [[r['id'], r['same_answer'], r['question1'], r['question2'], number(r['cosine_similarity']), r['reason'], link(r['reference'])]
                          for r in part['sorted']])
    out += ['## First pass: ' + exp[8] + ' full-store lookup', '',
            'Shares below divide by every public query. A hit counts as correct only when the nearest entry is that query’s own labelled positive counterpart. Repeated equivalent questions at other indices can therefore count as wrong. Exact ties choose the lowest stored index.', '']
    out += table(['Threshold', 'Correct', 'Wrong', 'Not served', 'Correct share', 'Wrong share', 'Not served share'],
                 [[number(r['threshold']), r['correct'], r['wrong'], r['not_served'], number(r['correct_share']),
                   number(r['wrong_share']), number(r['not_served_share'])] for r in s['store']['thresholds']])
    hit = s['hit_savings']
    out += ['## First pass: ' + exp[9] + ' time a cache hit saves', '',
            'Single-query client timing includes the local embedding request, response decoding and normalization. Lookup scans the complete store with exact cosine similarity. Stored-question embeddings are prepared in batches and are excluded from hit latency.', '']
    out += table(['Operation on this machine', 'Milliseconds: median [min, max]'],
                 [['Embed query', span(hit['embedding_ms'])], ['Exact nearest lookup', span(hit['lookup_ms'])],
                  ['Embed plus lookup', span(hit['hit_ms'])], ['Cold chat request, including generated output', span(hit['cold_total_ms'])]])
    out += [f"Cold-chat median divided by hit median: {number(hit['median_ratio'])}. This compares different work: a semantic hit returns a stored answer and skips chat generation.", '',
            '## First-pass screen evidence', '']
    for names, title in [(['cold', 'warm'], 'Cold and warm server timing events'),
                         (['early-change', 'late-change'], 'Changing timestamp at the start and end')]:
        out += ['### ' + title, '']
        out += table(['Condition', 'Raw event reference', 'Server log reference', 'Prompt tokens', 'Server cache_n', 'Prompt ms', 'TTFT ms', 'Total ms'],
                     [[name, link(s['screen'][name]['reference']), link(s['screen'][name]['server_log_reference']) if 'server_log_reference' in s['screen'][name] else 'Raw event timing above',
                       number(s['screen'][name]['prompt_n']), number(s['screen'][name]['cache_n']), number(s['screen'][name]['prompt_ms']),
                       number(s['screen'][name]['ttft_ms']), number(s['screen'][name]['total_ms'])] for name in names])
    worst = s['our_pairs']['worst_wrong']
    selected = [worst] + [p for p in s['our_pairs']['sorted'] if p['id'] != worst['id']][:4]
    out += ['### Authored pairs including the highest-similarity wrong pair', '']
    out += table(['Same answer', 'Stored question', 'Query', 'Cosine', 'Evidence'],
                 [[p['same_answer'], p['question1'], p['question2'], number(p['cosine_similarity']), link(p['reference'])] for p in selected])
    if s.get('server_warnings'):
        out += ['Server startup warns about unused GGUF tensors. The supplied conversion is retained; answer quality is not assessed here. Example: ' + link(s['server_warnings'][0]['reference']) + '.', '']
    if prefix['early-change']['steady']['total_ms']['median'] < prefix['cold']['all']['total_ms']['median']:
        out += [f"Early-change total latency has a lower median ({number(prefix['early-change']['steady']['total_ms']['median'])} ms) than the earlier cold baseline ({number(prefix['cold']['all']['total_ms']['median'])} ms), despite evaluating a full prompt. Conditions were not interleaved and background load was uncontrolled; latency alone does not establish the amount of cache reuse.", '']
    out += ['## Limits and observations', '',
            'These are local CPU measurements with a small quantized chat model and a small embedding model. They are not hosted-provider cache prices, billing rules or latency. The cold chat output is capped, not checked for support-answer quality. The embedding model is used symmetrically without a retrieval instruction prefix. No thresholds were selected on a held-out test split. First-pass conditions ran consecutively in a fixed order. The follow-up rotates condition blocks and records load; background CPU load and thermal state remain uncontrolled.', '',
            'QQP measures one kind of question similarity. Public labels do not verify that a stored support answer would be correct. Authored policies make the intended answer difference explicit but do not represent a population estimate. Full-store correctness uses the deliberately strict index rule described above.', '',
            'The changing timestamp is a fixed synthetic sequence, repeated consistently across runs. A changing timestamp can retain a short initial prefix before its first different token. Alternating manuals can retain a short shared chat-template prefix. Prompt timing reports evaluated work rather than assuming either condition produces a complete miss.', '',
            f"Observed exact-output differences: {same['different']} / {same['count']}. Highest authored wrong-pair similarity: {number(worst['cosine_similarity'])}. These outcomes are reported without a rerun selected for a preferred result.", '',
            'From this directory, reproduce with `bash setup.sh`, then `bash run-all.sh`, using the supplied local chat GGUF. The runner requires the pinned image already present and never pulls implicitly. Only `summarize.py` writes the summary; this report reads that summary exclusively.', '']
    if 'timing_pass' in s:
        out += [f"The timing follow-up collector is `nice -n {setup['nice']} python run-timing.py`; it preserves completed blocks on resume. After collection, run `python summarize.py`, `python write_report.py`, and `python verify-timing.py`.", '']
    return '\n'.join(out)


if __name__ == '__main__':
    try:
        summary = json.loads((DEMO / 'results/summary.json').read_text())
        (DEMO / 'REPORT.md').write_text(render(summary))
    except Exception as error:
        import sys
        print(f'Report failed: {type(error).__name__}; inspect summary fields', file=sys.stderr)
        sys.exit(1)
