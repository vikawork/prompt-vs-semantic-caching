# Prompt caching and semantic caching: local measurement

Question: how much prompt work does a prefix cache save, and how often does a similarity cache serve a different answer?

## Headline figures

Written by hand from `results/summary.json` and `results/semantic-pairs.jsonl`; every figure also appears in a table below.

- Prefix cache, first pass, pooled medians over three runs of 30 questions: with the cache off a request evaluated 3,780 prompt tokens and the server reported 0 cached; warm requests evaluated 514 and the server reported 3,266 cached. Warm figures exclude each server's first request.
- With a changing synthetic timestamp line at the start of the prompt, the median was 3,810 tokens evaluated and the server reported 0 cached tokens on every request. With the same line after the manual, warm requests evaluated a median of 514 and the server reported 3,296 cached.
- Two manuals alternating on one server slot: median 3,898 tokens evaluated, 0 reported cached. On two slots: median 514 evaluated, 3,325 reported cached.
- Follow-up timing pass, pooled median time to first output: cache off 4,514.339 ms; warm 728.903 ms; timestamp at the start 5,664.979 ms; timestamp after the manual 785.973 ms. Load was recorded, not controlled; the timings do not isolate the speedup from caching.
- Exact-output comparison, cache off against warm, temperature 0, output capped at 48 tokens: 24 of 90 pairs differed, across 8 of the 30 questions.
- Public labelled pairs (2,000 sampled from Quora Question Pairs): 0.970 was the first scanned cutoff accepting fewer than 1% of pairs labelled not duplicate; it accepted 17.1% of pairs labelled duplicate. The cutoff was selected and scored on the same sample.
- Authored support pairs (60): the 30 same-answer pairs scored 0.762 to 0.940; the 30 different-answer pairs scored 0.723 to 0.982; 5 different-answer pairs scored above every same-answer pair. At a cutoff of 0.900 the pairwise test accepts 7 of 30 same-answer pairs and 13 of 30 different-answer pairs. This tests question matching, not the answers a cache would return.
- Embedding one query and searching the store took a median of 2.547 ms on this machine.


## Timing follow-up: rotated condition blocks

The first pass is preserved below and in `REPORT-first-pass.md`; its timing conditions were run consecutively while machine load changed. The follow-up rotates condition blocks, with a fresh server for each block and unchanged inference settings. It does not alternate individual requests between conditions.

| Repeat | Condition order |
| --- | --- |
| 1 | cold, warm, early-change, late-change |
| 2 | warm, early-change, late-change, cold |
| 3 | early-change, late-change, cold, warm |

Cold uses all requests; cached conditions exclude each fresh server first write. Load statistics include all requests.

Cells below are median [minimum, maximum]. Timing units are milliseconds; per-token time divides each request’s prompt milliseconds by its evaluated prompt tokens before aggregation.

| Condition | Repeat | Evaluated tokens | Server cache_n | Prompt ms | TTFT ms | Total ms | Prompt ms / evaluated token |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cold | 1 | 3,780.000 [3777, 3784] | 0.000 [0, 0] | 4,295.923 [4,222.899, 4,386.917] | 4,306.104 [4,232.711, 4,397.034] | 5,115.228 [4,479.044, 5,223.306] | 1.136 [1.118, 1.160] |
| cold | 2 | 3,780.000 [3777, 3784] | 0.000 [0, 0] | 4,595.041 [4,268.069, 5,667.894] | 4,604.982 [4,277.911, 5,676.976] | 5,448.487 [4,521.358, 6,497.490] | 1.214 [1.129, 1.499] |
| cold | 3 | 3,780.000 [3777, 3784] | 0.000 [0, 0] | 4,682.627 [4,294.058, 6,510.308] | 4,693.069 [4,303.723, 6,520.173] | 5,549.306 [4,686.679, 7,345.815] | 1.239 [1.136, 1.724] |
| cold | pooled | 3,780.000 [3777, 3784] | 0.000 [0, 0] | 4,503.907 [4,222.899, 6,510.308] | 4,514.339 [4,232.711, 6,520.173] | 5,286.750 [4,479.044, 7,345.815] | 1.191 [1.118, 1.724] |
| warm | 1 | 514 [511, 517] | 3266 [3264, 3268] | 656.560 [626.682, 688.492] | 666.505 [636.361, 698.533] | 1,480.864 [853.615, 1,525.472] | 1.272 [1.215, 1.339] |
| warm | 2 | 514 [511, 517] | 3266 [3264, 3268] | 739.277 [675.081, 791.912] | 749.876 [685.399, 802.329] | 1,643.498 [975.875, 1,751.365] | 1.435 [1.319, 1.547] |
| warm | 3 | 514 [511, 517] | 3266 [3264, 3268] | 1,008.143 [670.911, 1,756.541] | 1,058.078 [681.139, 1,766.785] | 2,334.787 [895.985, 2,679.707] | 1.958 [1.300, 3.398] |
| warm | pooled | 514 [511, 517] | 3266 [3264, 3268] | 716.745 [626.682, 1,756.541] | 728.903 [636.361, 1,766.785] | 1,615.363 [853.615, 2,679.707] | 1.389 [1.215, 3.398] |
| early-change | 1 | 3810 [3807, 3814] | 0 [0, 0] | 7,143.331 [4,260.710, 10,701.204] | 7,153.722 [4,270.762, 10,729.707] | 8,694.523 [5,085.737, 12,404.320] | 1.875 [1.119, 2.809] |
| early-change | 2 | 3810 [3807, 3814] | 0 [0, 0] | 4,753.480 [4,464.655, 5,941.371] | 4,763.164 [4,475.040, 5,952.287] | 5,567.591 [4,833.553, 6,158.108] | 1.248 [1.172, 1.559] |
| early-change | 3 | 3810 [3807, 3814] | 0 [0, 0] | 5,831.293 [5,403.835, 7,100.835] | 5,849.945 [5,413.543, 7,133.229] | 7,161.745 [6,033.296, 7,588.132] | 1.531 [1.418, 1.863] |
| early-change | pooled | 3810 [3807, 3814] | 0 [0, 0] | 5,655.031 [4,260.710, 10,701.204] | 5,664.979 [4,270.762, 10,729.707] | 6,666.039 [4,833.553, 12,404.320] | 1.483 [1.119, 2.809] |
| late-change | 1 | 514 [511, 517] | 3296 [3294, 3298] | 754.672 [702.886, 1,067.152] | 765.106 [713.433, 1,078.071] | 1,683.901 [1,000.040, 1,799.655] | 1.463 [1.373, 2.084] |
| late-change | 2 | 514 [511, 517] | 3296 [3294, 3298] | 1,583.565 [676.556, 1,777.750] | 1,602.691 [686.831, 1,809.640] | 3,265.867 [1,064.618, 3,561.672] | 3.080 [1.321, 3.459] |
| late-change | 3 | 514 [511, 517] | 3296 [3294, 3298] | 726.815 [647.961, 1,689.038] | 736.722 [658.034, 1,698.777] | 1,952.565 [943.209, 2,590.718] | 1.411 [1.266, 3.286] |
| late-change | pooled | 514 [511, 517] | 3296 [3294, 3298] | 772.659 [647.961, 1,777.750] | 785.973 [658.034, 1,809.640] | 1,799.655 [943.209, 3,561.672] | 1.506 [1.266, 3.459] |

Fresh-server first requests for cached conditions, excluded from the steady table:

| Condition | Repeat | Evaluated | Server cache_n | Prompt ms | TTFT ms | Total ms | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| warm | 1 | 3780 | 0 | 4,250.889 | 4,259.683 | 5,096.045 | `results/timing-warm-r1.jsonl:1` |
| warm | 2 | 3780 | 0 | 4,877.178 | 4,888.001 | 5,843.852 | `results/timing-warm-r2.jsonl:1` |
| warm | 3 | 3780 | 0 | 6,821.660 | 6,832.105 | 8,511.723 | `results/timing-warm-r3.jsonl:1` |
| early-change | 1 | 3810 | 0 | 4,372.441 | 4,381.305 | 5,205.324 | `results/timing-early-change-r1.jsonl:1` |
| early-change | 2 | 3810 | 0 | 4,777.291 | 4,786.250 | 5,655.532 | `results/timing-early-change-r2.jsonl:1` |
| early-change | 3 | 3810 | 0 | 6,577.390 | 6,586.000 | 7,467.321 | `results/timing-early-change-r3.jsonl:1` |
| late-change | 1 | 3810 | 0 | 4,916.953 | 4,929.099 | 5,939.402 | `results/timing-late-change-r1.jsonl:1` |
| late-change | 2 | 3810 | 0 | 9,032.271 | 9,050.011 | 9,916.990 | `results/timing-late-change-r2.jsonl:1` |
| late-change | 3 | 3810 | 0 | 6,486.892 | 6,496.137 | 7,307.867 | `results/timing-late-change-r3.jsonl:1` |

### Recorded machine load

The one-minute load average is read immediately before every completion request. The start gate checks load before launching each server. Load is recorded, not held constant; this system-wide average is not a measurement of this server’s CPU contention.

| Condition | Repeat | Request load median | Request load maximum | Start load | Wait seconds | High-load start flag | Gate evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cold | 1 | 7.480 | 8.830 | 2.670 | 0.000 | False | `results/timing-start-cold-r1.json:1` |
| cold | 2 | 11.605 | 12.400 | 12.400 | 600.000 | True | `results/timing-start-cold-r2.json:1` |
| cold | 3 | 9.570 | 13.450 | 5.970 | 420.031 | False | `results/timing-start-cold-r3.json:1` |
| warm | 1 | 5.220 | 6.240 | 3.040 | 0.000 | False | `results/timing-start-warm-r1.json:1` |
| warm | 2 | 10.930 | 11.610 | 5.890 | 170.004 | False | `results/timing-start-warm-r2.json:1` |
| warm | 3 | 24.365 | 28.200 | 18.560 | 600.010 | True | `results/timing-start-warm-r3.json:1` |
| early-change | 1 | 20.460 | 25.300 | 5.590 | 10.000 | False | `results/timing-start-early-change-r1.json:1` |
| early-change | 2 | 9.310 | 10.020 | 5.660 | 90.002 | False | `results/timing-start-early-change-r2.json:1` |
| early-change | 3 | 22.560 | 26.260 | 5.570 | 90.002 | False | `results/timing-start-early-change-r3.json:1` |
| late-change | 1 | 10.315 | 12.130 | 8.840 | 600.000 | True | `results/timing-start-late-change-r1.json:1` |
| late-change | 2 | 32.560 | 41.590 | 24.830 | 600.001 | True | `results/timing-start-late-change-r2.json:1` |
| late-change | 3 | 18.515 | 21.710 | 13.870 | 600.000 | True | `results/timing-start-late-change-r3.json:1` |

| Condition | Pooled load median | Pooled load maximum | Flagged repeats |
| --- | --- | --- | --- |
| cold | 9.570 | 13.450 | 2 |
| warm | 10.930 | 28.200 | 3 |
| early-change | 16.055 | 26.260 | none |
| late-change | 18.515 | 41.590 | 1, 2, 3 |

A condition waits when start load exceeds 6, up to 600 seconds, then runs and is flagged if load remains above the limit.

### Do cold and early-change now agree?

For this descriptive comparison, agreement means a pooled median prompt time per evaluated token within 10.000 percent of cold. This is a stated comparison bound, not a significance test.

Cold and early-change do not agree under that bound: early-change differs from cold by 24.521 percent. Every repeat is within the same bound: False.

Pooled prompt medians are 4,503.907 ms for cold and 5,655.031 ms for early-change. Their pooled recorded load medians are 9.570 and 16.055, respectively. Rotation and the start gate did not produce matched load throughout the blocks. This pass does not establish the cause of the remaining per-token timing difference.

| Repeat | Cold ms/token median | Early-change ms/token median | Early minus cold, percent |
| --- | --- | --- | --- |
| 1 | 1.136 | 1.875 | 65.060 |
| 2 | 1.214 | 1.248 | 2.729 |
| 3 | 1.239 | 1.531 | 23.566 |

Follow-up request window (UTC): 2026-11-12T11:53:24.664818+00:00 through 2026-11-12T13:23:08.705302+00:00; measurement window 5,384.040 seconds; follow-up wall time from its checkpoint 5,433.807 seconds, including preparation, load waits, the interrupted diagnostic attempt and server startup/cleanup. Final runner invocation: 5,141.611 seconds.

Verified unchanged first-pass evidence files: 48.

An initial warm block stopped when its tokenization diagnostic failed to split a manual whose trailing newline the chat template had stripped. The diagnostic was corrected and that incomplete block restarted on a fresh server. Completed blocks were retained. These partial attempts are preserved and excluded from all follow-up statistics:

| Partial attempt | Saved requests |
| --- | --- |
| `results/aborted/1794484647727195608/timing-warm-r1.jsonl:1` | 2 |

### Why does a warm request evaluate so much of the prompt?

The first-pass request at `results/prefix-warm-r1.jsonl:8` evaluated 514 tokens: 492 unchanged manual tokens plus 22 question and chat-template tokens. The manual file is 3756 tokens; the chat template strips its trailing newline, leaving 3755 manual tokens in the prompt. The 3266 cached tokens comprise 3263 manual tokens plus 3 leading template tokens. Tokenization concatenates exactly to the 3780-token prompt; evidence: `results/warm-tokenization.json:1`.

The server confirms the evaluated count at `logs/warm-r1.log:89`:

> 0.29.499.606 I slot print_timing: id  0 | task 334 | prompt eval time =     693.17 ms /   514 tokens (    1.35 ms per token,   741.53 tokens per second)

The cause is not established by saved server logs. The saved log does not identify a cache-reuse boundary, batch boundary or checkpoint that explains the manual re-evaluation.

## Setup

CPU: AMD Ryzen 9 9950X 16-Core Processor. GPU layers: 0; threads per server: 8; nice: 10.

Image: `ghcr.io/ggml-org/llama.cpp:full-b12211@sha256:8960de326dd60972cc4d442531f4efa006416d5896da2a39f0def0b55cbcb0c2`.

Chat: `Qwen/Qwen3.5-0.8B` at `2fc06364715b967f1860aea9cf38778875588b17`, Existing local Q8_0 conversion; BotPsy demo provenance. File `qwen3.5-0.8b-q8_0.gguf`; SHA-256 `e35200cb6bd8ed0e263c0dbbe2d70c68d48eef96d9a073ee37f76d6872223509`.

Embedding: `CompendiumLabs/bge-small-en-v1.5-gguf` at `d32f8c040ea3b516330eeb75b72bcc2d3a780ab7`, MIT, English. Upstream `BAAI/bge-small-en-v1.5` at `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`. File `bge-small-en-v1.5-q8_0.gguf`; SHA-256 `ec38e8da142596baa913124ae50550de284b6916bf59577ef2f0cb9660c2f514`.

Sampling: temperature 0, seed 12648430, generation cap 48 tokens. Prefix conditions: 3 repeats, 30 questions each. Context per chat slot: 8192; embedding context: 512; pooling: cls (GGUF bert.pooling_type=2). Prompt RAM cache disabled to isolate slot KV reuse.

Servers use loopback binding, read-only model mounts, CPU execution, and serial requests. Each condition/repeat starts a fresh server. Containers are removed by the runner.

Public data: `SetFit/qqp` at `df33eff016c496a5b944d026d5c0b511dc1f64f1`, `validation.jsonl`; SHA-256 `e7fbbe5677938f14662bccb47598768f5574da144972a73e066763fca2215290`. GLUE QQP validation; JSONL conversion.

Licence: Not specified by the mirror; GLUE metadata says other and refers to upstream terms. No permissive grant verified. QQP is explicitly nominated in the brief; this report does not claim it is permissively licensed.

Source positives: 14885 / 40430; sample positives: 736 / 2000; seed 12648430. Stratified random sample; positive count rounded to nearest integer; shuffled once. Downloaded and embedded in memory; public text omitted from artifacts.

First-pass measurement range (UTC): 2026-11-12T11:07:18.425806+00:00 through 2026-11-12T11:49:30.083287+00:00.

First-pass measurement wall time: 2,531.657 seconds; elapsed since its resume checkpoint: 2,759.364 seconds.

First-pass wall time since its recorded job start, including setup and blocked time: 9,420.847 seconds.

## First pass: prefix measurements

Timing columns are milliseconds. TTFT starts immediately before the native completion request and ends at the first nonempty content event; separate template-formatting and token-count requests are excluded. Each cell is median [minimum, maximum]. Ranges cover requests; per-repeat values below expose run variation. Steady excludes each slot’s first write. The cold baseline includes every request.

### P1 cold

| Condition | Repeat | Prompt tokens evaluated | Server cache_n | Prompt ms | TTFT ms | Total ms |
| --- | --- | --- | --- | --- | --- | --- |
| cold | 1 | 3,780.000 [3777, 3784] | 0.000 [0, 0] | 8,964.166 [5,045.198, 9,898.139] | 8,979.674 [5,055.636, 9,909.944] | 9,890.584 [6,559.432, 11,687.825] |
| cold | 2 | 3,780.000 [3777, 3784] | 0.000 [0, 0] | 8,635.647 [4,277.635, 9,850.339] | 8,651.746 [4,287.836, 9,869.802] | 9,642.222 [5,103.953, 11,569.548] |
| cold | 3 | 3,780.000 [3777, 3784] | 0.000 [0, 0] | 8,872.487 [4,237.461, 9,789.552] | 8,889.639 [4,247.559, 9,812.320] | 9,991.014 [4,496.719, 11,638.250] |
| cold | pooled | 3,780.000 [3777, 3784] | 0.000 [0, 0] | 8,821.570 [4,237.461, 9,898.139] | 8,836.376 [4,247.559, 9,909.944] | 9,891.380 [4,496.719, 11,687.825] |

### P2 warm

| Condition | Repeat | Prompt tokens evaluated | Server cache_n | Prompt ms | TTFT ms | Total ms |
| --- | --- | --- | --- | --- | --- | --- |
| warm | 1 | 514 [511, 517] | 3266 [3264, 3268] | 1,413.475 [659.912, 1,599.992] | 1,433.606 [669.515, 1,621.183] | 2,999.134 [873.684, 3,340.779] |
| warm | 2 | 514 [511, 517] | 3266 [3264, 3268] | 1,387.786 [637.554, 1,673.698] | 1,405.780 [647.743, 1,690.712] | 2,890.058 [1,345.883, 3,306.632] |
| warm | 3 | 514 [511, 517] | 3266 [3264, 3268] | 695.427 [625.246, 1,683.032] | 705.909 [634.799, 1,706.841] | 1,540.178 [844.365, 3,394.744] |
| warm | pooled | 514 [511, 517] | 3266 [3264, 3268] | 1,381.559 [625.246, 1,683.032] | 1,398.076 [634.799, 1,706.841] | 2,847.744 [844.365, 3,394.744] |

First writes, kept separate:

| Condition | Repeat | Question index | Prompt tokens | Prompt ms | TTFT ms | Total ms | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| warm | 1 | 0 | 3780 | 9,009.819 | 9,021.167 | 10,659.632 | `results/prefix-warm-r1.jsonl:1` |
| warm | 2 | 0 | 3780 | 8,719.396 | 8,733.862 | 9,566.067 | `results/prefix-warm-r2.jsonl:1` |
| warm | 3 | 0 | 3780 | 6,180.291 | 6,189.749 | 7,889.258 | `results/prefix-warm-r3.jsonl:1` |

### P3 timestamp at start

| Condition | Repeat | Prompt tokens evaluated | Server cache_n | Prompt ms | TTFT ms | Total ms |
| --- | --- | --- | --- | --- | --- | --- |
| early-change | 1 | 3810 [3807, 3814] | 0 [0, 0] | 8,703.515 [5,079.504, 9,986.725] | 8,716.835 [5,097.358, 10,002.545] | 10,182.218 [6,377.533, 11,760.046] |
| early-change | 2 | 3810 [3807, 3814] | 0 [0, 0] | 4,815.556 [4,274.301, 9,715.018] | 4,825.625 [4,284.028, 9,730.153] | 5,685.617 [4,509.536, 11,421.789] |
| early-change | 3 | 3810 [3807, 3814] | 0 [0, 0] | 4,407.969 [4,223.743, 4,976.713] | 4,418.260 [4,234.352, 4,987.267] | 5,213.345 [4,481.295, 5,916.540] |
| early-change | pooled | 3810 [3807, 3814] | 0 [0, 0] | 4,822.658 [4,223.743, 9,986.725] | 4,832.249 [4,234.352, 10,002.545] | 5,716.468 [4,481.295, 11,760.046] |

First writes, kept separate:

| Condition | Repeat | Question index | Prompt tokens | Prompt ms | TTFT ms | Total ms | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| early-change | 1 | 0 | 3810 | 6,747.002 | 6,761.727 | 7,847.195 | `results/prefix-early-change-r1.jsonl:1` |
| early-change | 2 | 0 | 3810 | 9,731.148 | 9,746.967 | 11,419.615 | `results/prefix-early-change-r2.jsonl:1` |
| early-change | 3 | 0 | 3810 | 4,698.993 | 4,709.796 | 5,620.150 | `results/prefix-early-change-r3.jsonl:1` |

### P4 timestamp at end

| Condition | Repeat | Prompt tokens evaluated | Server cache_n | Prompt ms | TTFT ms | Total ms |
| --- | --- | --- | --- | --- | --- | --- |
| late-change | 1 | 514 [511, 517] | 3296 [3294, 3298] | 661.635 [628.688, 783.876] | 671.727 [638.830, 796.545] | 1,484.330 [864.800, 1,721.821] |
| late-change | 2 | 514 [511, 517] | 3296 [3294, 3298] | 660.344 [632.038, 795.882] | 670.079 [641.899, 805.673] | 1,499.526 [851.449, 1,667.652] |
| late-change | 3 | 514 [511, 517] | 3296 [3294, 3298] | 681.710 [638.018, 750.636] | 692.314 [647.748, 760.528] | 1,536.153 [875.881, 1,643.336] |
| late-change | pooled | 514 [511, 517] | 3296 [3294, 3298] | 661.736 [628.688, 795.882] | 672.443 [638.830, 805.673] | 1,498.088 [851.449, 1,721.821] |

First writes, kept separate:

| Condition | Repeat | Question index | Prompt tokens | Prompt ms | TTFT ms | Total ms | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| late-change | 1 | 0 | 3810 | 4,346.292 | 4,355.303 | 5,183.089 | `results/prefix-late-change-r1.jsonl:1` |
| late-change | 2 | 0 | 3810 | 4,323.848 | 4,332.642 | 5,184.206 | `results/prefix-late-change-r2.jsonl:1` |
| late-change | 3 | 0 | 3810 | 4,473.334 | 4,482.236 | 5,440.604 | `results/prefix-late-change-r3.jsonl:1` |

### P5 alternating prefixes

| Condition | Repeat | Prompt tokens evaluated | Server cache_n | Prompt ms | TTFT ms | Total ms |
| --- | --- | --- | --- | --- | --- | --- |
| two-prefixes-one | 1 | 3898 [3777, 3903] | 0 [0, 0] | 4,380.679 [4,190.554, 4,499.930] | 4,391.079 [4,201.654, 4,510.734] | 5,211.325 [4,424.444, 5,348.819] |
| two-prefixes-one | 2 | 3898 [3777, 3903] | 0 [0, 0] | 4,584.877 [4,186.223, 5,017.493] | 4,595.193 [4,196.735, 5,028.711] | 5,658.718 [4,786.826, 6,045.920] |
| two-prefixes-one | 3 | 3898 [3777, 3903] | 0 [0, 0] | 4,399.039 [4,206.762, 5,112.988] | 4,409.034 [4,216.434, 5,123.411] | 5,224.254 [4,663.591, 5,958.504] |
| two-prefixes-one | pooled | 3898 [3777, 3903] | 0 [0, 0] | 4,438.290 [4,186.223, 5,112.988] | 4,448.466 [4,196.735, 5,123.411] | 5,248.457 [4,424.444, 6,045.920] |
| two-prefixes-two | 1 | 514.000 [511, 518] | 3,325.000 [3264, 3387] | 658.705 [628.291, 687.135] | 669.112 [638.905, 697.476] | 1,485.103 [867.437, 1,537.057] |
| two-prefixes-two | 2 | 514.000 [511, 518] | 3,325.000 [3264, 3387] | 656.892 [623.499, 724.819] | 669.549 [633.456, 734.998] | 1,486.497 [886.862, 1,561.525] |
| two-prefixes-two | 3 | 514.000 [511, 518] | 3,325.000 [3264, 3387] | 654.954 [627.114, 720.684] | 665.803 [636.819, 731.671] | 1,478.513 [890.261, 1,615.418] |
| two-prefixes-two | pooled | 514.000 [511, 518] | 3,325.000 [3264, 3387] | 656.765 [623.499, 724.819] | 668.077 [633.456, 734.998] | 1,483.660 [867.437, 1,615.418] |

First writes, kept separate:

| Condition | Repeat | Question index | Prompt tokens | Prompt ms | TTFT ms | Total ms | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| two-prefixes-one | 1 | 0 | 3780 | 4,312.906 | 4,322.084 | 5,145.503 | `results/prefix-two-prefixes-one-r1.jsonl:1` |
| two-prefixes-one | 2 | 0 | 3780 | 4,278.113 | 4,286.841 | 5,102.399 | `results/prefix-two-prefixes-one-r2.jsonl:1` |
| two-prefixes-one | 3 | 0 | 3780 | 4,703.424 | 4,713.579 | 5,734.898 | `results/prefix-two-prefixes-one-r3.jsonl:1` |
| two-prefixes-two | 1 | 0 | 3780 | 4,305.995 | 4,315.282 | 5,159.659 | `results/prefix-two-prefixes-two-r1.jsonl:1` |
| two-prefixes-two | 1 | 1 | 3899 | 4,402.823 | 4,413.796 | 5,244.071 | `results/prefix-two-prefixes-two-r1.jsonl:2` |
| two-prefixes-two | 2 | 0 | 3780 | 4,268.115 | 4,278.260 | 5,094.083 | `results/prefix-two-prefixes-two-r2.jsonl:1` |
| two-prefixes-two | 2 | 1 | 3899 | 4,627.959 | 4,638.091 | 5,454.816 | `results/prefix-two-prefixes-two-r2.jsonl:2` |
| two-prefixes-two | 3 | 0 | 3780 | 4,213.974 | 4,225.930 | 5,038.243 | `results/prefix-two-prefixes-two-r3.jsonl:1` |
| two-prefixes-two | 3 | 1 | 3899 | 4,433.124 | 4,443.284 | 5,265.993 | `results/prefix-two-prefixes-two-r3.jsonl:2` |

Warm steady medians: 3266 cached prompt tokens and 514 evaluated tokens. Cached tokens need not cover the entire shared manual.

Manual token counts from the model tokenizer: 3756, 3875.

Server cache_n records the cached prompt tokens from the server timing object. Raw final events, streaming events, prompt token timings, cached-token fields and outputs are retained in each prefix JSONL. Cached-token fields are preserved as reported; they are not treated as an independently verified count of reused prompt tokens.

### P6 exact output equality

Identical: 66 / 90; different: 24 / 90. Equality compares exact concatenated output text for matching question and repeat.

| Repeat | Question | Cold output | Warm output | Cold evidence | Warm evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Q05 | No, a factory reset **does not cancel your subscription**.  According to the manual, a factory reset is a different action found under **Account, then Orders**. It is a hardware-level operation that erases all local profiles, saved readings | No, a factory reset does **not** cancel your subscription.  According to the manual, a factory reset is a different action found under **Account, then Orders**. It is a hardware-level operation that erases all local profiles, saved | `results/prefix-cold-r1.jsonl:5` | `results/prefix-warm-r1.jsonl:5` |
| 1 | Q06 | Version three supports exporting readings and reminder history as a **comma-separated-values (CSV) file**.  Additionally, the manual notes that **PDF export is not supported**. | Version three supports exporting readings and reminder history as a **comma-separated-values (CSV) file**.  It does not support PDF export. | `results/prefix-cold-r1.jsonl:6` | `results/prefix-warm-r1.jsonl:6` |
| 1 | Q08 | Based on the manual provided, you can create **up to five** additional household profiles in addition to your owner profile.  This means you can have a total of **six** profiles (Owner + 5 others).  *   ** | Based on the manual, you can create **up to five** additional household profiles in addition to your owner profile.  This means you can have a total of **six** profiles (Owner + 5 others).  *   **Note | `results/prefix-cold-r1.jsonl:8` | `results/prefix-warm-r1.jsonl:8` |
| 1 | Q15 | Yes, annual billing is available.  According to the manual, **Annual billing is available and renews on the anniversary date.**  The manual also notes that renewal notices are sent seven days before annual charges and one day before monthly charges. | Yes, annual billing is available.  According to the manual, **Annual billing is available and renews on the anniversary date.**  The manual also notes that: *   Renewal notices are sent **seven days before annual charges**. | `results/prefix-cold-r1.jsonl:15` | `results/prefix-warm-r1.jsonl:15` |
| 1 | Q17 | No, you cannot return opened hardware because you changed your mind.  According to the rules, **opened hardware is not eligible for a change-of-mind return.**  While you can return an unopened hardware unit within thirty days after delivery | No, you cannot return opened hardware because you changed your mind.  According to the rules, **opened hardware is not eligible for a change-of-mind return**. The only exceptions to this rule are: *   **Fault or delivery | `results/prefix-cold-r1.jsonl:17` | `results/prefix-warm-r1.jsonl:17` |
| 1 | Q21 | No, the warranty does not cover a lost adapter.  According to rule **21**, lost adapters and stands are sold as replacement parts; loss is not considered a warranty fault. The warranty only covers manufacturing faults in the display and supplied | No, the warranty does not cover a lost adapter.  According to the manual, **lost adapters and stands are sold as replacement parts; loss is not a warranty fault.** The warranty covers manufacturing faults in the display and supplied adapter under normal | `results/prefix-cold-r1.jsonl:21` | `results/prefix-warm-r1.jsonl:21` |
| 1 | Q22 | Based on the FennelBox support manual provided:  **Support Availability** *   **Text Support:** Available every day from **8:00 AM to 8:00 PM** using the account's selected local time | Based on the FennelBox support manual provided:  **Support Availability:** *   **Text Support:** Available every day from **8:00 AM to 8:00 PM** using the account's selected local time | `results/prefix-cold-r1.jsonl:22` | `results/prefix-warm-r1.jsonl:22` |
| 1 | Q29 | Based on the FennelBox support manual provided, here is how you should clean the display safely:  **1. Disconnect Power** Before touching the display, **disconnect the power supply**. The manual explicitly states: "Reconnect | Based on the FennelBox support manual provided, here is how you should clean the display safely:  **1. Disconnect Power** Before touching the display, **disconnect the power** to prevent accidental damage.  **2. | `results/prefix-cold-r1.jsonl:29` | `results/prefix-warm-r1.jsonl:29` |
| 2 | Q05 | No, a factory reset **does not cancel your subscription**.  According to the manual, a factory reset is a different action found under **Account, then Orders**. It is a hardware-level operation that erases all local profiles, saved readings | No, a factory reset does **not** cancel your subscription.  According to the manual, a factory reset is a different action found under **Account, then Orders**. It is a hardware-level operation that erases all local profiles, saved | `results/prefix-cold-r2.jsonl:5` | `results/prefix-warm-r2.jsonl:5` |
| 2 | Q06 | Version three supports exporting readings and reminder history as a **comma-separated-values (CSV) file**.  Additionally, the manual notes that **PDF export is not supported**. | Version three supports exporting readings and reminder history as a **comma-separated-values (CSV) file**.  It does not support PDF export. | `results/prefix-cold-r2.jsonl:6` | `results/prefix-warm-r2.jsonl:6` |
| 2 | Q08 | Based on the manual provided, you can create **up to five** additional household profiles in addition to your owner profile.  This means you can have a total of **six** profiles (Owner + 5 others).  *   ** | Based on the manual, you can create **up to five** additional household profiles in addition to your owner profile.  This means you can have a total of **six** profiles (Owner + 5 others).  *   **Note | `results/prefix-cold-r2.jsonl:8` | `results/prefix-warm-r2.jsonl:8` |
| 2 | Q15 | Yes, annual billing is available.  According to the manual, **Annual billing is available and renews on the anniversary date.**  The manual also notes that renewal notices are sent seven days before annual charges and one day before monthly charges. | Yes, annual billing is available.  According to the manual, **Annual billing is available and renews on the anniversary date.**  The manual also notes that: *   Renewal notices are sent **seven days before annual charges**. | `results/prefix-cold-r2.jsonl:15` | `results/prefix-warm-r2.jsonl:15` |
| 2 | Q17 | No, you cannot return opened hardware because you changed your mind.  According to the rules, **opened hardware is not eligible for a change-of-mind return.**  While you can return an unopened hardware unit within thirty days after delivery | No, you cannot return opened hardware because you changed your mind.  According to the rules, **opened hardware is not eligible for a change-of-mind return**. The only exceptions to this rule are: *   **Fault or delivery | `results/prefix-cold-r2.jsonl:17` | `results/prefix-warm-r2.jsonl:17` |
| 2 | Q21 | No, the warranty does not cover a lost adapter.  According to rule **21**, lost adapters and stands are sold as replacement parts; loss is not considered a warranty fault. The warranty only covers manufacturing faults in the display and supplied | No, the warranty does not cover a lost adapter.  According to the manual, **lost adapters and stands are sold as replacement parts; loss is not a warranty fault.** The warranty covers manufacturing faults in the display and supplied adapter under normal | `results/prefix-cold-r2.jsonl:21` | `results/prefix-warm-r2.jsonl:21` |
| 2 | Q22 | Based on the FennelBox support manual provided:  **Support Availability** *   **Text Support:** Available every day from **8:00 AM to 8:00 PM** using the account's selected local time | Based on the FennelBox support manual provided:  **Support Availability:** *   **Text Support:** Available every day from **8:00 AM to 8:00 PM** using the account's selected local time | `results/prefix-cold-r2.jsonl:22` | `results/prefix-warm-r2.jsonl:22` |
| 2 | Q29 | Based on the FennelBox support manual provided, here is how you should clean the display safely:  **1. Disconnect Power** Before touching the display, **disconnect the power supply**. The manual explicitly states: "Reconnect | Based on the FennelBox support manual provided, here is how you should clean the display safely:  **1. Disconnect Power** Before touching the display, **disconnect the power** to prevent accidental damage.  **2. | `results/prefix-cold-r2.jsonl:29` | `results/prefix-warm-r2.jsonl:29` |
| 3 | Q05 | No, a factory reset **does not cancel your subscription**.  According to the manual, a factory reset is a different action found under **Account, then Orders**. It is a hardware-level operation that erases all local profiles, saved readings | No, a factory reset does **not** cancel your subscription.  According to the manual, a factory reset is a different action found under **Account, then Orders**. It is a hardware-level operation that erases all local profiles, saved | `results/prefix-cold-r3.jsonl:5` | `results/prefix-warm-r3.jsonl:5` |
| 3 | Q06 | Version three supports exporting readings and reminder history as a **comma-separated-values (CSV) file**.  Additionally, the manual notes that **PDF export is not supported**. | Version three supports exporting readings and reminder history as a **comma-separated-values (CSV) file**.  It does not support PDF export. | `results/prefix-cold-r3.jsonl:6` | `results/prefix-warm-r3.jsonl:6` |
| 3 | Q08 | Based on the manual provided, you can create **up to five** additional household profiles in addition to your owner profile.  This means you can have a total of **six** profiles (Owner + 5 others).  *   ** | Based on the manual, you can create **up to five** additional household profiles in addition to your owner profile.  This means you can have a total of **six** profiles (Owner + 5 others).  *   **Note | `results/prefix-cold-r3.jsonl:8` | `results/prefix-warm-r3.jsonl:8` |
| 3 | Q15 | Yes, annual billing is available.  According to the manual, **Annual billing is available and renews on the anniversary date.**  The manual also notes that renewal notices are sent seven days before annual charges and one day before monthly charges. | Yes, annual billing is available.  According to the manual, **Annual billing is available and renews on the anniversary date.**  The manual also notes that: *   Renewal notices are sent **seven days before annual charges**. | `results/prefix-cold-r3.jsonl:15` | `results/prefix-warm-r3.jsonl:15` |
| 3 | Q17 | No, you cannot return opened hardware because you changed your mind.  According to the rules, **opened hardware is not eligible for a change-of-mind return.**  While you can return an unopened hardware unit within thirty days after delivery | No, you cannot return opened hardware because you changed your mind.  According to the rules, **opened hardware is not eligible for a change-of-mind return**. The only exceptions to this rule are: *   **Fault or delivery | `results/prefix-cold-r3.jsonl:17` | `results/prefix-warm-r3.jsonl:17` |
| 3 | Q21 | No, the warranty does not cover a lost adapter.  According to rule **21**, lost adapters and stands are sold as replacement parts; loss is not considered a warranty fault. The warranty only covers manufacturing faults in the display and supplied | No, the warranty does not cover a lost adapter.  According to the manual, **lost adapters and stands are sold as replacement parts; loss is not a warranty fault.** The warranty covers manufacturing faults in the display and supplied adapter under normal | `results/prefix-cold-r3.jsonl:21` | `results/prefix-warm-r3.jsonl:21` |
| 3 | Q22 | Based on the FennelBox support manual provided:  **Support Availability** *   **Text Support:** Available every day from **8:00 AM to 8:00 PM** using the account's selected local time | Based on the FennelBox support manual provided:  **Support Availability:** *   **Text Support:** Available every day from **8:00 AM to 8:00 PM** using the account's selected local time | `results/prefix-cold-r3.jsonl:22` | `results/prefix-warm-r3.jsonl:22` |
| 3 | Q29 | Based on the FennelBox support manual provided, here is how you should clean the display safely:  **1. Disconnect Power** Before touching the display, **disconnect the power supply**. The manual explicitly states: "Reconnect | Based on the FennelBox support manual provided, here is how you should clean the display safely:  **1. Disconnect Power** Before touching the display, **disconnect the power** to prevent accidental damage.  **2. | `results/prefix-cold-r3.jsonl:29` | `results/prefix-warm-r3.jsonl:29` |

## First pass: S1 labelled public pairs

Correct share divides accepted positive pairs by all positive pairs. Wrong share divides accepted negative pairs by all negative pairs. A pair label is a proxy for answer equivalence, not a verified answer.

First scanned threshold with negative-pair wrong share strictly below one percent.

| Threshold | Correct / positive | Wrong / negative | Correct share | Wrong share |
| --- | --- | --- | --- | --- |
| 0.500 | 736 / 736 | 1081 / 1264 | 1.000 | 0.855 |
| 0.510 | 736 / 736 | 1077 / 1264 | 1.000 | 0.852 |
| 0.520 | 736 / 736 | 1072 / 1264 | 1.000 | 0.848 |
| 0.530 | 736 / 736 | 1066 / 1264 | 1.000 | 0.843 |
| 0.540 | 736 / 736 | 1056 / 1264 | 1.000 | 0.835 |
| 0.550 | 736 / 736 | 1045 / 1264 | 1.000 | 0.827 |
| 0.560 | 736 / 736 | 1036 / 1264 | 1.000 | 0.820 |
| 0.570 | 736 / 736 | 1022 / 1264 | 1.000 | 0.809 |
| 0.580 | 736 / 736 | 1013 / 1264 | 1.000 | 0.801 |
| 0.590 | 736 / 736 | 1002 / 1264 | 1.000 | 0.793 |
| 0.600 | 736 / 736 | 993 / 1264 | 1.000 | 0.786 |
| 0.610 | 736 / 736 | 985 / 1264 | 1.000 | 0.779 |
| 0.620 | 736 / 736 | 964 / 1264 | 1.000 | 0.763 |
| 0.630 | 736 / 736 | 941 / 1264 | 1.000 | 0.744 |
| 0.640 | 735 / 736 | 915 / 1264 | 0.999 | 0.724 |
| 0.650 | 735 / 736 | 897 / 1264 | 0.999 | 0.710 |
| 0.660 | 735 / 736 | 878 / 1264 | 0.999 | 0.695 |
| 0.670 | 735 / 736 | 851 / 1264 | 0.999 | 0.673 |
| 0.680 | 735 / 736 | 824 / 1264 | 0.999 | 0.652 |
| 0.690 | 735 / 736 | 793 / 1264 | 0.999 | 0.627 |
| 0.700 | 735 / 736 | 769 / 1264 | 0.999 | 0.608 |
| 0.710 | 734 / 736 | 736 / 1264 | 0.997 | 0.582 |
| 0.720 | 734 / 736 | 696 / 1264 | 0.997 | 0.551 |
| 0.730 | 733 / 736 | 666 / 1264 | 0.996 | 0.527 |
| 0.740 | 731 / 736 | 641 / 1264 | 0.993 | 0.507 |
| 0.750 | 728 / 736 | 614 / 1264 | 0.989 | 0.486 |
| 0.760 | 720 / 736 | 579 / 1264 | 0.978 | 0.458 |
| 0.770 | 713 / 736 | 553 / 1264 | 0.969 | 0.438 |
| 0.780 | 708 / 736 | 517 / 1264 | 0.962 | 0.409 |
| 0.790 | 696 / 736 | 486 / 1264 | 0.946 | 0.384 |
| 0.800 | 685 / 736 | 455 / 1264 | 0.931 | 0.360 |
| 0.810 | 675 / 736 | 428 / 1264 | 0.917 | 0.339 |
| 0.820 | 657 / 736 | 391 / 1264 | 0.893 | 0.309 |
| 0.830 | 631 / 736 | 358 / 1264 | 0.857 | 0.283 |
| 0.840 | 603 / 736 | 317 / 1264 | 0.819 | 0.251 |
| 0.850 | 578 / 736 | 275 / 1264 | 0.785 | 0.218 |
| 0.860 | 543 / 736 | 247 / 1264 | 0.738 | 0.195 |
| 0.870 | 517 / 736 | 213 / 1264 | 0.702 | 0.169 |
| 0.880 | 493 / 736 | 188 / 1264 | 0.670 | 0.149 |
| 0.890 | 457 / 736 | 162 / 1264 | 0.621 | 0.128 |
| 0.900 | 422 / 736 | 137 / 1264 | 0.573 | 0.108 |
| 0.910 | 368 / 736 | 112 / 1264 | 0.500 | 0.089 |
| 0.920 | 328 / 736 | 77 / 1264 | 0.446 | 0.061 |
| 0.930 | 286 / 736 | 58 / 1264 | 0.389 | 0.046 |
| 0.940 | 248 / 736 | 43 / 1264 | 0.337 | 0.034 |
| 0.950 | 216 / 736 | 31 / 1264 | 0.293 | 0.025 |
| 0.960 | 171 / 736 | 19 / 1264 | 0.232 | 0.015 |
| 0.970 | 126 / 736 | 8 / 1264 | 0.171 | 0.006 |
| 0.980 | 81 / 736 | 2 / 1264 | 0.110 | 0.002 |
| 0.990 | 36 / 736 | 0 / 1264 | 0.049 | 0.000 |

First scanned threshold below the requested wrong-hit bound: 0.970; wrong share 0.006, correct share 0.171.

## First pass: S2 authored support pairs

Correct share divides accepted positive pairs by all positive pairs. Wrong share divides accepted negative pairs by all negative pairs. A pair label is a proxy for answer equivalence, not a verified answer.

First scanned threshold with negative-pair wrong share strictly below one percent.

| Threshold | Correct / positive | Wrong / negative | Correct share | Wrong share |
| --- | --- | --- | --- | --- |
| 0.500 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.510 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.520 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.530 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.540 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.550 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.560 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.570 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.580 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.590 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.600 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.610 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.620 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.630 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.640 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.650 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.660 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.670 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.680 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.690 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.700 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.710 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.720 | 30 / 30 | 30 / 30 | 1.000 | 1.000 |
| 0.730 | 30 / 30 | 28 / 30 | 1.000 | 0.933 |
| 0.740 | 30 / 30 | 28 / 30 | 1.000 | 0.933 |
| 0.750 | 30 / 30 | 27 / 30 | 1.000 | 0.900 |
| 0.760 | 30 / 30 | 27 / 30 | 1.000 | 0.900 |
| 0.770 | 28 / 30 | 27 / 30 | 0.933 | 0.900 |
| 0.780 | 27 / 30 | 27 / 30 | 0.900 | 0.900 |
| 0.790 | 25 / 30 | 26 / 30 | 0.833 | 0.867 |
| 0.800 | 24 / 30 | 25 / 30 | 0.800 | 0.833 |
| 0.810 | 23 / 30 | 25 / 30 | 0.767 | 0.833 |
| 0.820 | 22 / 30 | 24 / 30 | 0.733 | 0.800 |
| 0.830 | 21 / 30 | 24 / 30 | 0.700 | 0.800 |
| 0.840 | 20 / 30 | 22 / 30 | 0.667 | 0.733 |
| 0.850 | 19 / 30 | 20 / 30 | 0.633 | 0.667 |
| 0.860 | 18 / 30 | 19 / 30 | 0.600 | 0.633 |
| 0.870 | 15 / 30 | 17 / 30 | 0.500 | 0.567 |
| 0.880 | 13 / 30 | 16 / 30 | 0.433 | 0.533 |
| 0.890 | 11 / 30 | 16 / 30 | 0.367 | 0.533 |
| 0.900 | 7 / 30 | 13 / 30 | 0.233 | 0.433 |
| 0.910 | 5 / 30 | 10 / 30 | 0.167 | 0.333 |
| 0.920 | 4 / 30 | 7 / 30 | 0.133 | 0.233 |
| 0.930 | 3 / 30 | 5 / 30 | 0.100 | 0.167 |
| 0.940 | 1 / 30 | 5 / 30 | 0.033 | 0.167 |
| 0.950 | 0 / 30 | 5 / 30 | 0.000 | 0.167 |
| 0.960 | 0 / 30 | 4 / 30 | 0.000 | 0.133 |
| 0.970 | 0 / 30 | 2 / 30 | 0.000 | 0.067 |
| 0.980 | 0 / 30 | 1 / 30 | 0.000 | 0.033 |
| 0.990 | 0 / 30 | 0 / 30 | 0.000 | 0.000 |

First scanned threshold below the requested wrong-hit bound: 0.990; wrong share 0.000, correct share 0.000.

Every authored pair, descending cosine similarity:

| ID | Same answer | Stored question | Query | Cosine | Reason | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| S2-032 | False | Can I get a refund within 30 days? | Can I get a refund after 30 days? | 0.982 | The fixture permits refunds within 30 days and excludes later refunds. | `results/semantic-pairs.jsonl:2032` |
| S2-035 | False | Can delivery be moved to 15 June? | Can delivery be moved to 16 June? | 0.975 | The requested delivery dates are different. | `results/semantic-pairs.jsonl:2035` |
| S2-053 | False | Can I change the order before dispatch? | Can I change the order after dispatch? | 0.965 | Before dispatch the order can be edited; after dispatch it must be recalled. | `results/semantic-pairs.jsonl:2053` |
| S2-059 | False | Can I cancel without a fee? | Can I cancel for a fee? | 0.963 | The fixture charges a cancellation fee, so a free cancellation is unavailable. | `results/semantic-pairs.jsonl:2059` |
| S2-033 | False | Does version 2 support data export? | Does version 3 support data export? | 0.953 | The fixture gives version 3 data export and version 2 no data export. | `results/semantic-pairs.jsonl:2033` |
| S2-027 | True | Can I collect my order in Northport? | Is pickup in Northport available for my order? | 0.940 | Both ask about pickup in the same invented service area. | `results/semantic-pairs.jsonl:2027` |
| S2-011 | True | Does the plan include phone support? | Is telephone support part of this plan? | 0.937 | Both ask whether phone support is included. | `results/semantic-pairs.jsonl:2011` |
| S2-012 | True | When will my order arrive? | What is the expected delivery date for my order? | 0.935 | Both ask for the order delivery estimate. | `results/semantic-pairs.jsonl:2012` |
| S2-026 | True | Can I get a refund within 30 days? | Am I eligible for a refund during the first 30 days? | 0.929 | Both ask about the same refund window. | `results/semantic-pairs.jsonl:2026` |
| S2-046 | False | Please pause my plan for one month. | Please pause my plan for one year. | 0.923 | The requested pause durations differ. | `results/semantic-pairs.jsonl:2046` |
| S2-058 | False | Please keep my saved files. | Please do not keep my saved files. | 0.921 | Negation reverses the requested data-retention action. | `results/semantic-pairs.jsonl:2058` |
| S2-056 | False | Can I add five team seats? | Can I remove five team seats? | 0.918 | Adding seats and removing seats change capacity in opposite directions. | `results/semantic-pairs.jsonl:2056` |
| S2-036 | False | Why was I charged 20 credits? | Why was I charged 200 credits? | 0.917 | The amounts identify different billing issues. | `results/semantic-pairs.jsonl:2036` |
| S2-045 | False | How do I upgrade from basic to plus? | How do I downgrade from plus to basic? | 0.912 | The plan changes run in opposite directions. | `results/semantic-pairs.jsonl:2045` |
| S2-021 | True | How do I report a damaged item? | My item arrived broken. How do I report it? | 0.911 | Both ask to report delivery damage. | `results/semantic-pairs.jsonl:2021` |
| S2-040 | False | Can I return an unopened item? | Can I return an opened item? | 0.909 | The fixture accepts unopened returns and excludes opened returns. | `results/semantic-pairs.jsonl:2040` |
| S2-044 | False | Please remove the team owner. | Please remove a team member. | 0.905 | Removing an owner requires a different role-sensitive procedure. | `results/semantic-pairs.jsonl:2044` |
| S2-006 | True | How do I reset my password? | I forgot my password. How can I set a new one? | 0.905 | Both ask for the password reset procedure. | `results/semantic-pairs.jsonl:2006` |
| S2-049 | False | Please send a replacement battery. | Please send a replacement charger. | 0.905 | The requests need different replacement parts. | `results/semantic-pairs.jsonl:2049` |
| S2-028 | True | Can delivery be moved to 15 June? | May I reschedule delivery for 15 June? | 0.904 | Both ask to move delivery to the same date. | `results/semantic-pairs.jsonl:2028` |
| S2-029 | True | Why was I charged 20 credits? | What caused the 20-credit charge on my bill? | 0.896 | Both ask about the same charge amount. | `results/semantic-pairs.jsonl:2029` |
| S2-043 | False | Please refund order 410. | Please refund order 401. | 0.895 | The requests target different orders. | `results/semantic-pairs.jsonl:2043` |
| S2-038 | False | Please enable email alerts. | Please disable email alerts. | 0.895 | The requested alert settings are opposites. | `results/semantic-pairs.jsonl:2038` |
| S2-001 | True | How do I cancel my order? | How can I stop an order I placed? | 0.894 | Both ask to cancel an order. | `results/semantic-pairs.jsonl:2001` |
| S2-030 | True | How do I stop email notifications? | Where can I switch off notification emails? | 0.894 | Both ask to disable email notifications. | `results/semantic-pairs.jsonl:2030` |
| S2-052 | False | Please turn on two-step login. | Please turn off two-step login. | 0.892 | The requested security settings are opposites. | `results/semantic-pairs.jsonl:2052` |
| S2-025 | True | Does version 3 work offline? | Can I use version 3 without an internet connection? | 0.892 | Both ask about offline use of the same version. | `results/semantic-pairs.jsonl:2025` |
| S2-017 | True | Can I change the billing email? | May I update the email address that receives bills? | 0.882 | Both ask to update the billing contact email. | `results/semantic-pairs.jsonl:2017` |
| S2-023 | True | How do I remove a team member? | How can I revoke a member's access to my team? | 0.881 | Both ask to remove a team member's access. | `results/semantic-pairs.jsonl:2023` |
| S2-009 | True | Why was my payment declined? | Why did the payment fail to go through? | 0.878 | Both ask why a payment was rejected. | `results/semantic-pairs.jsonl:2009` |
| S2-020 | True | Can I exchange this for another size? | May I swap my item for a different size? | 0.877 | Both ask for a size exchange. | `results/semantic-pairs.jsonl:2020` |
| S2-042 | False | Can I transfer a personal licence? | Can I transfer a team licence? | 0.871 | The fixture allows personal licence transfers and forbids team licence transfers. | `results/semantic-pairs.jsonl:2042` |
| S2-037 | False | Please renew my subscription. | Please do not renew my subscription. | 0.870 | Negation reverses the requested renewal action. | `results/semantic-pairs.jsonl:2037` |
| S2-005 | True | How do I change my delivery address? | Where can I update the address for my shipment? | 0.869 | Both ask to update a shipment address. | `results/semantic-pairs.jsonl:2005` |
| S2-003 | True | Where is my refund? | How can I check the status of my refund? | 0.869 | Both ask for the refund status. | `results/semantic-pairs.jsonl:2003` |
| S2-055 | False | Can I export my data as CSV? | Can I export my data as PDF? | 0.866 | The fixture supports CSV export and does not support PDF export. | `results/semantic-pairs.jsonl:2055` |
| S2-010 | True | How do I turn off renewal? | How can I stop my plan from renewing automatically? | 0.865 | Both ask to disable automatic renewal. | `results/semantic-pairs.jsonl:2010` |
| S2-004 | True | Can I return an unopened item? | May I send back a product I have not opened? | 0.854 | Both ask about returning an unopened item. | `results/semantic-pairs.jsonl:2004` |
| S2-050 | False | Can I use the device indoors? | Can I use the device outdoors? | 0.850 | The fixture permits indoor use and excludes outdoor use. | `results/semantic-pairs.jsonl:2050` |
| S2-041 | False | How do I change my billing address? | How do I change my delivery address? | 0.848 | Billing and delivery addresses affect different records. | `results/semantic-pairs.jsonl:2041` |
| S2-060 | False | Please deliver to unit 12. | Please deliver to unit 21. | 0.843 | The requested destination units are different. | `results/semantic-pairs.jsonl:2060` |
| S2-015 | True | How do I delete my account? | What steps permanently close my account? | 0.842 | Both ask to permanently close the account. | `results/semantic-pairs.jsonl:2015` |
| S2-016 | True | How do I enable two-step login? | How can I add a second verification step when signing in? | 0.838 | Both ask to enable a second login factor. | `results/semantic-pairs.jsonl:2016` |
| S2-034 | False | Can I collect my order in Northport? | Can I collect my order in Southport? | 0.836 | The fixture offers pickup in Northport and delivery only in Southport. | `results/semantic-pairs.jsonl:2034` |
| S2-031 | False | How do I cancel my order? | How do I cancel my subscription? | 0.833 | An order cancellation and a subscription cancellation use different procedures. | `results/semantic-pairs.jsonl:2031` |
| S2-018 | True | How do I track my parcel? | Where can I see the tracking status of my shipment? | 0.822 | Both ask for shipment tracking. | `results/semantic-pairs.jsonl:2018` |
| S2-057 | False | My payment went through twice. | My payment did not go through. | 0.817 | A duplicate payment and a failed payment require different remedies. | `results/semantic-pairs.jsonl:2057` |
| S2-008 | True | How do I update my payment card? | Where can I replace the card used for payments? | 0.816 | Both ask to replace the saved payment card. | `results/semantic-pairs.jsonl:2008` |
| S2-014 | True | How do I export my data? | How can I download a copy of my account data? | 0.808 | Both ask for an account data export. | `results/semantic-pairs.jsonl:2014` |
| S2-024 | True | Can I pay once a year? | Is annual billing available? | 0.800 | Both ask whether yearly billing is available. | `results/semantic-pairs.jsonl:2024` |
| S2-054 | False | Is my trial still active? | Is my paid plan still active? | 0.793 | Trial and paid-plan status concern different entitlements. | `results/semantic-pairs.jsonl:2054` |
| S2-022 | True | Where can I find my licence key? | How do I locate the key that activates my software? | 0.789 | Both ask to locate the activation key. | `results/semantic-pairs.jsonl:2022` |
| S2-019 | True | Is the warranty transferable? | Can a new owner use the remaining warranty? | 0.781 | Both ask whether the warranty transfers to a new owner. | `results/semantic-pairs.jsonl:2019` |
| S2-051 | False | Can I pay in monthly instalments? | Can I pay the full amount now? | 0.780 | Instalments and a full payment are different billing arrangements. | `results/semantic-pairs.jsonl:2051` |
| S2-007 | True | Where can I download my invoice? | How do I get a copy of my bill? | 0.771 | Both ask to obtain an invoice copy. | `results/semantic-pairs.jsonl:2007` |
| S2-013 | True | Can I pause my subscription? | Can I temporarily put my recurring plan on hold? | 0.770 | Both ask about temporarily pausing a subscription. | `results/semantic-pairs.jsonl:2013` |
| S2-002 | True | How do I cancel my subscription? | How can I end my recurring plan? | 0.762 | Both ask to end a recurring subscription. | `results/semantic-pairs.jsonl:2002` |
| S2-047 | False | The item arrived damaged. | The item never arrived. | 0.745 | Damage and non-delivery require different investigations. | `results/semantic-pairs.jsonl:2047` |
| S2-039 | False | How do I delete my account? | How do I delete my saved payment card? | 0.729 | Account deletion and payment-card deletion remove different objects. | `results/semantic-pairs.jsonl:2039` |
| S2-048 | False | Can I reset a forgotten password? | Can I recover a deleted account? | 0.723 | A password reset cannot answer an account-recovery request. | `results/semantic-pairs.jsonl:2048` |

## First pass: S3 full-store lookup

Shares below divide by every public query. A hit counts as correct only when the nearest entry is that query’s own labelled positive counterpart. Repeated equivalent questions at other indices can therefore count as wrong. Exact ties choose the lowest stored index.

| Threshold | Correct | Wrong | Not served | Correct share | Wrong share | Not served share |
| --- | --- | --- | --- | --- | --- | --- |
| 0.500 | 615 | 1384 | 1 | 0.307 | 0.692 | 0.001 |
| 0.510 | 615 | 1384 | 1 | 0.307 | 0.692 | 0.001 |
| 0.520 | 615 | 1384 | 1 | 0.307 | 0.692 | 0.001 |
| 0.530 | 615 | 1384 | 1 | 0.307 | 0.692 | 0.001 |
| 0.540 | 615 | 1383 | 2 | 0.307 | 0.692 | 0.001 |
| 0.550 | 615 | 1381 | 4 | 0.307 | 0.691 | 0.002 |
| 0.560 | 615 | 1381 | 4 | 0.307 | 0.691 | 0.002 |
| 0.570 | 615 | 1379 | 6 | 0.307 | 0.690 | 0.003 |
| 0.580 | 615 | 1372 | 13 | 0.307 | 0.686 | 0.006 |
| 0.590 | 615 | 1365 | 20 | 0.307 | 0.682 | 0.010 |
| 0.600 | 615 | 1354 | 31 | 0.307 | 0.677 | 0.015 |
| 0.610 | 615 | 1343 | 42 | 0.307 | 0.671 | 0.021 |
| 0.620 | 615 | 1326 | 59 | 0.307 | 0.663 | 0.029 |
| 0.630 | 615 | 1301 | 84 | 0.307 | 0.650 | 0.042 |
| 0.640 | 615 | 1268 | 117 | 0.307 | 0.634 | 0.059 |
| 0.650 | 615 | 1230 | 155 | 0.307 | 0.615 | 0.077 |
| 0.660 | 615 | 1193 | 192 | 0.307 | 0.597 | 0.096 |
| 0.670 | 615 | 1145 | 240 | 0.307 | 0.573 | 0.120 |
| 0.680 | 615 | 1096 | 289 | 0.307 | 0.548 | 0.144 |
| 0.690 | 615 | 1048 | 337 | 0.307 | 0.524 | 0.169 |
| 0.700 | 615 | 1009 | 376 | 0.307 | 0.504 | 0.188 |
| 0.710 | 615 | 958 | 427 | 0.307 | 0.479 | 0.213 |
| 0.720 | 615 | 902 | 483 | 0.307 | 0.451 | 0.241 |
| 0.730 | 615 | 860 | 525 | 0.307 | 0.430 | 0.263 |
| 0.740 | 615 | 830 | 555 | 0.307 | 0.415 | 0.278 |
| 0.750 | 614 | 796 | 590 | 0.307 | 0.398 | 0.295 |
| 0.760 | 609 | 760 | 631 | 0.304 | 0.380 | 0.316 |
| 0.770 | 607 | 729 | 664 | 0.303 | 0.364 | 0.332 |
| 0.780 | 604 | 683 | 713 | 0.302 | 0.342 | 0.356 |
| 0.790 | 597 | 642 | 761 | 0.298 | 0.321 | 0.381 |
| 0.800 | 593 | 598 | 809 | 0.296 | 0.299 | 0.405 |
| 0.810 | 584 | 566 | 850 | 0.292 | 0.283 | 0.425 |
| 0.820 | 572 | 522 | 906 | 0.286 | 0.261 | 0.453 |
| 0.830 | 554 | 485 | 961 | 0.277 | 0.242 | 0.480 |
| 0.840 | 535 | 431 | 1034 | 0.268 | 0.215 | 0.517 |
| 0.850 | 517 | 382 | 1101 | 0.259 | 0.191 | 0.550 |
| 0.860 | 498 | 340 | 1162 | 0.249 | 0.170 | 0.581 |
| 0.870 | 481 | 300 | 1219 | 0.240 | 0.150 | 0.610 |
| 0.880 | 464 | 266 | 1270 | 0.232 | 0.133 | 0.635 |
| 0.890 | 435 | 230 | 1335 | 0.217 | 0.115 | 0.667 |
| 0.900 | 405 | 190 | 1405 | 0.203 | 0.095 | 0.703 |
| 0.910 | 354 | 161 | 1485 | 0.177 | 0.081 | 0.743 |
| 0.920 | 317 | 116 | 1567 | 0.159 | 0.058 | 0.783 |
| 0.930 | 277 | 95 | 1628 | 0.139 | 0.048 | 0.814 |
| 0.940 | 241 | 73 | 1686 | 0.120 | 0.036 | 0.843 |
| 0.950 | 209 | 57 | 1734 | 0.104 | 0.029 | 0.867 |
| 0.960 | 166 | 42 | 1792 | 0.083 | 0.021 | 0.896 |
| 0.970 | 123 | 27 | 1850 | 0.061 | 0.013 | 0.925 |
| 0.980 | 81 | 12 | 1907 | 0.041 | 0.006 | 0.954 |
| 0.990 | 36 | 10 | 1954 | 0.018 | 0.005 | 0.977 |

## First pass: S4 time a cache hit saves

Single-query client timing includes the local embedding request, response decoding and normalization. Lookup scans the complete store with exact cosine similarity. Stored-question embeddings are prepared in batches and are excluded from hit latency.

| Operation on this machine | Milliseconds: median [min, max] |
| --- | --- |
| Embed query | 2.197 [1.474, 8.604] |
| Exact nearest lookup | 0.350 [0.314, 0.953] |
| Embed plus lookup | 2.547 [1.794, 8.943] |
| Cold chat request, including generated output | 9,891.380 [4,496.719, 11,687.825] |

Cold-chat median divided by hit median: 3,884.104. This compares different work: a semantic hit returns a stored answer and skips chat generation.

## First-pass screen evidence

### Cold and warm server timing events

| Condition | Raw event reference | Server log reference | Prompt tokens | Server cache_n | Prompt ms | TTFT ms | Total ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cold | `results/prefix-cold-r1.jsonl:2` | `logs/cold-r1-attempt-1794481635931723261.log:44` | 3780 | 0 | 9,399.538 | 9,414.735 | 11,170.958 |
| warm | `results/prefix-warm-r1.jsonl:2` | `logs/warm-r1.log:41` | 516 | 3264 | 1,554.192 | 1,574.728 | 3,340.779 |

### Changing timestamp at the start and end

| Condition | Raw event reference | Server log reference | Prompt tokens | Server cache_n | Prompt ms | TTFT ms | Total ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| early-change | `results/prefix-early-change-r1.jsonl:2` | `logs/early-change-r1.log:44` | 3810 | 0 | 8,703.515 | 8,716.835 | 10,359.446 |
| late-change | `results/prefix-late-change-r1.jsonl:2` | `logs/late-change-r1.log:40` | 516 | 3294 | 671.349 | 681.072 | 1,498.088 |

### Authored pairs including the highest-similarity wrong pair

| Same answer | Stored question | Query | Cosine | Evidence |
| --- | --- | --- | --- | --- |
| False | Can I get a refund within 30 days? | Can I get a refund after 30 days? | 0.982 | `results/semantic-pairs.jsonl:2032` |
| False | Can delivery be moved to 15 June? | Can delivery be moved to 16 June? | 0.975 | `results/semantic-pairs.jsonl:2035` |
| False | Can I change the order before dispatch? | Can I change the order after dispatch? | 0.965 | `results/semantic-pairs.jsonl:2053` |
| False | Can I cancel without a fee? | Can I cancel for a fee? | 0.963 | `results/semantic-pairs.jsonl:2059` |
| False | Does version 2 support data export? | Does version 3 support data export? | 0.953 | `results/semantic-pairs.jsonl:2033` |

Server startup warns about unused GGUF tensors. The supplied conversion is retained; answer quality is not assessed here. Example: `logs/cold-r1-attempt-1794481635931723261.log:8`.

Early-change total latency has a lower median (5,716.468 ms) than the earlier cold baseline (9,891.380 ms), despite evaluating a full prompt. Conditions were not interleaved and background load was uncontrolled; latency alone does not establish the amount of cache reuse.

## Limits and observations

These are local CPU measurements with a small quantized chat model and a small embedding model. They are not hosted-provider cache prices, billing rules or latency. The cold chat output is capped, not checked for support-answer quality. The embedding model is used symmetrically without a retrieval instruction prefix. No thresholds were selected on a held-out test split. First-pass conditions ran consecutively in a fixed order. The follow-up rotates condition blocks and records load; background CPU load and thermal state remain uncontrolled.

QQP measures one kind of question similarity. Public labels do not verify that a stored support answer would be correct. Authored policies make the intended answer difference explicit but do not represent a population estimate. Full-store correctness uses the deliberately strict index rule described above.

The changing timestamp is a fixed synthetic sequence, repeated consistently across runs. A changing timestamp can retain a short initial prefix before its first different token. Alternating manuals can retain a short shared chat-template prefix. Prompt timing reports evaluated work rather than assuming either condition produces a complete miss.

Observed exact-output differences: 24 / 90. Highest authored wrong-pair similarity: 0.982. These outcomes are reported without a rerun selected for a preferred result.

From this directory, reproduce with `bash setup.sh`, then `bash run-all.sh`, using the supplied local chat GGUF. The runner requires the pinned image already present and never pulls implicitly. Only `summarize.py` writes the summary; this report reads that summary exclusively.

The timing follow-up collector is `nice -n 10 python run-timing.py`; it preserves completed blocks on resume. After collection, run `python summarize.py`, `python write_report.py`, and `python verify-timing.py`.
