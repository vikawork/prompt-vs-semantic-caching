# Prompt caching and semantic caching, measured on one machine

A measurement by [Vikawork](https://vikawork.com/). Prompt (prefix) caching reuses the model's work on an identical
start of a prompt and still generates a fresh answer. Semantic caching returns a stored answer when a new question
is similar enough to an old one, and skips the answering model. We measured how each one goes wrong.

Everything ran locally on a CPU on 12 November 2026: a small open chat model (our Q8_0 conversion of
Qwen3.5-0.8B) on a pinned llama.cpp server, and a small embedding model (bge-small-en-v1.5, Q8_0). None of this is
a hosted provider's cache.

## Prefix cache

A support manual of about 3,750 tokens, then one of 30 questions. Medians over three runs; warm figures leave out
each server's first request.

| Condition | Prompt tokens evaluated | Reported as cached |
| --- | ---: | ---: |
| Cache off | 3,780 | 0 |
| Cache on | 514 | 3,266 |
| A changing timestamp line at the start of the prompt | 3,810 | 0 |
| The same line after the manual | 514 | 3,296 |
| Two manuals alternating on one slot | 3,898 | 0 |
| Two manuals on two slots | 514 | 3,325 |

- In one warm request we took apart, 22 of the 514 evaluated tokens were the question and chat template; 492 were
  unchanged manual text. The server log does not say why.
- 24 of 90 answers differed in exact text between cache off and cache on at temperature 0 (eight of the 30
  questions, three runs each), with output capped at 48 tokens.
- Timings are in the report with the machine's load average beside them. The machine was busy; they are rough.

## Semantic cache

Embed the stored question and the query, take the cosine similarity, serve from cache above a cutoff.

- 2,000 labelled public question pairs: 0.97 was the first cutoff that accepted fewer than 1% of the pairs labelled
  not duplicate. It accepted 17% of the labelled duplicates. The cutoff was chosen and scored on the same sample.
- 60 support-desk pairs we wrote (`fixtures/pairs.json`), 30 that need the same answer and 30 traps that need a
  different one. Same-answer pairs scored 0.762 to 0.940; traps 0.723 to 0.982; five traps scored above every
  same-answer pair. "Can I get a refund within 30 days?" against "Can I get a refund after 30 days?" scored 0.982.
- Embedding a query and searching the store took about 2.5 ms.

We tested the matching of questions, not the answers a cache would return. The public pairs are a sample of Quora
Question Pairs; this repository holds their ids, labels and scores, not their text.

[REPORT.md](REPORT.md) has every table, the setup (image digest, model revisions and hashes), the examples and the
limits. Every number in it comes from `results/summary.json`, which `summarize.py` writes from `results/*.jsonl`.

## Run it

Needs Docker, Python 3 and the chat model file. `setup.sh` pulls nothing by itself except the embedding model;
pull the llama.cpp image by the digest in the report first. The scripts were written inside a larger repository
and expect to sit at `episodes/prompt-caching-and-semantic-caching-fail-in-different-ways/demo/` under a root that
also holds `.studio/ai-channel/caching/` for models and scratch. Recreate that layout or change the `SCRATCH` and
`ROOT` lines at the top of the scripts.
