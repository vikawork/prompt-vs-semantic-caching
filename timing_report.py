"""Render only values already derived into summary.json."""


def render(t, number, span, table, link):
    out = ['## Timing follow-up: rotated condition blocks', '',
           'The first pass is preserved below and in `REPORT-first-pass.md`; its timing conditions were run consecutively while machine load changed. The follow-up rotates condition blocks, with a fresh server for each block and unchanged inference settings. It does not alternate individual requests between conditions.', '']
    out += table(['Repeat', 'Condition order'], [[i, ', '.join(order)] for i, order in enumerate(t['orders'], 1)])
    if t['status'] != 'complete':
        out += ['Status: incomplete; no follow-up headline timing is claimed.', '',
                *['- `' + name + '`' for name in t['missing']], '']
    else:
        out += [t['scope'], '', 'Cells below are median [minimum, maximum]. Timing units are milliseconds; per-token time divides each request’s prompt milliseconds by its evaluated prompt tokens before aggregation.', '']
        entries = []
        for name, condition in t['conditions'].items():
            for repeat in condition['repeats']:
                m = repeat['metrics']
                entries.append([name, repeat['repeat'], *[span(m[k]) for k in ['prompt_n', 'cache_n', 'prompt_ms', 'ttft_ms', 'total_ms', 'prompt_ms_per_token']]])
            m = condition['metrics']
            entries.append([name, 'pooled', *[span(m[k]) for k in ['prompt_n', 'cache_n', 'prompt_ms', 'ttft_ms', 'total_ms', 'prompt_ms_per_token']]])
        out += table(['Condition', 'Repeat', 'Evaluated tokens', 'Server cache_n', 'Prompt ms', 'TTFT ms', 'Total ms', 'Prompt ms / evaluated token'], entries)
        out += ['Fresh-server first requests for cached conditions, excluded from the steady table:', '']
        out += table(['Condition', 'Repeat', 'Evaluated', 'Server cache_n', 'Prompt ms', 'TTFT ms', 'Total ms', 'Evidence'],
            [[name, row['repeat'], row['prompt_n'], row['cache_n'], number(row['prompt_ms']), number(row['ttft_ms']), number(row['total_ms']), link(row['reference'])]
             for name, c in t['conditions'].items() if name != 'cold' for row in c['first_writes']])
        out += ['### Recorded machine load', '',
                'The one-minute load average is read immediately before every completion request. The start gate checks load before launching each server. Load is recorded, not held constant; this system-wide average is not a measurement of this server’s CPU contention.', '']
        out += table(['Condition', 'Repeat', 'Request load median', 'Request load maximum', 'Start load', 'Wait seconds', 'High-load start flag', 'Gate evidence'],
            [[name, r['repeat'], number(r['load']['median']), number(r['load']['max']), number(r['gate']['start_loadavg_1m']), number(r['gate']['wait_seconds']), r['gate']['high_load_start'], link(r['gate']['reference'])]
             for name, c in t['conditions'].items() for r in c['repeats']])
        out += table(['Condition', 'Pooled load median', 'Pooled load maximum', 'Flagged repeats'],
            [[name, number(c['load']['median']), number(c['load']['max']), ', '.join(map(str, c['high_load_repeats'])) or 'none'] for name, c in t['conditions'].items()])
        gate = t['gates'][0]
        out += [f"A condition waits when start load exceeds {number(gate['limit'])}, up to {number(gate['maximum_wait_seconds'])} seconds, then runs and is flagged if load remains above the limit.", '']
        a = t['agreement']
        out += ['### Do cold and early-change now agree?', '',
                f"For this descriptive comparison, agreement means a pooled median prompt time per evaluated token within {number(t['agreement_tolerance'] * 100)} percent of cold. This is a stated comparison bound, not a significance test.", '',
                f"Cold and early-change {'agree' if a['within_bound'] else 'do not agree'} under that bound: early-change differs from cold by {number(a['relative_difference'] * 100)} percent. Every repeat is within the same bound: {a['every_repeat_within_bound']}.", '']
        out += [f"Pooled prompt medians are {number(t['conditions']['cold']['metrics']['prompt_ms']['median'])} ms for cold and {number(t['conditions']['early-change']['metrics']['prompt_ms']['median'])} ms for early-change. Their pooled recorded load medians are {number(t['conditions']['cold']['load']['median'])} and {number(t['conditions']['early-change']['load']['median'])}, respectively. Rotation and the start gate did not produce matched load throughout the blocks. This pass does not establish the cause of the remaining per-token timing difference.", '']
        out += table(['Repeat', 'Cold ms/token median', 'Early-change ms/token median', 'Early minus cold, percent'],
            [[r['repeat'], number(r['cold_ms_per_token']), number(r['early_ms_per_token']), number(r['relative_difference'] * 100)] for r in a['repeats']])
        out += [f"Follow-up request window (UTC): {t['measurement_range']['start']} through {t['measurement_range']['end']}; measurement window {number(t['measurement_wall_seconds'])} seconds; follow-up wall time from its checkpoint {number(t['followup_wall_seconds'])} seconds, including preparation, load waits, the interrupted diagnostic attempt and server startup/cleanup. Final runner invocation: {number(t['run_wall_seconds'])} seconds.", '',
                f"Verified unchanged first-pass evidence files: {t['preserved_first_pass_files']}.", '']
    if t.get('excluded_attempts'):
        out += ['An initial warm block stopped when its tokenization diagnostic failed to split a manual whose trailing newline the chat template had stripped. The diagnostic was corrected and that incomplete block restarted on a fresh server. Completed blocks were retained. These partial attempts are preserved and excluded from all follow-up statistics:', '']
        out += table(['Partial attempt', 'Saved requests'], [[link(a['reference']), a['saved_requests']] for a in t['excluded_attempts']])
    if 'warm_decomposition' in t:
        d = t['warm_decomposition']
        out += ['### Why does a warm request evaluate so much of the prompt?', '',
                f"The first-pass request at {link(d['reference'])} evaluated {d['evaluated']} tokens: {d['reevaluated_manual_tokens']} unchanged manual tokens plus {d['evaluated_question_template_tokens']} question and chat-template tokens. The manual file is {d['manual_file_tokens']} tokens; the chat template strips its trailing newline, leaving {d['manual_tokens']} manual tokens in the prompt. The {d['cache_n']} cached tokens comprise {d['cached_manual_tokens']} manual tokens plus {d['prefix_template_tokens']} leading template tokens. Tokenization concatenates exactly to the {d['total_prompt']}-token prompt; evidence: {link(d['tokenization_reference'])}.", '',
                f"The server confirms the evaluated count at {link(d['server_log_reference'])}:", '',
                '> ' + d['server_log_quote'], '',
                'The cause is ' + d['cause'] + '. The saved log does not identify a cache-reuse boundary, batch boundary or checkpoint that explains the manual re-evaluation.', '']
    return out
