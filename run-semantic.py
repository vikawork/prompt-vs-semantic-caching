#!/usr/bin/env python3
"""Measure paired similarity and exact nearest-neighbour answer-cache lookup."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

# A single lookup must not launch a thread pool larger than the server budget.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import numpy as np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_pairs(path):
    return validate_pairs(json.loads(path.read_text()))


def validate_pairs(pairs):
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("Pair fixture must be a nonempty array")
    ids = set()
    for pair in pairs:
        if not isinstance(pair.get("id"), (str, int)) or str(pair["id"]) in ids:
            raise ValueError("Pair IDs must be unique strings or integers")
        ids.add(str(pair["id"]))
        for key in ("question1", "question2"):
            if not isinstance(pair.get(key), str) or not pair[key].strip():
                raise ValueError("Each pair needs two nonempty question strings")
        if type(pair.get("same_answer")) is not bool:
            raise ValueError("Each pair needs a boolean same_answer label")
    return pairs


def embedding_vector(value):
    # Some server versions wrap the pooled vector in one extra array.
    while isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
        value = value[0]
    vector = np.asarray(value, dtype=np.float64)
    if vector.ndim != 1 or not len(vector) or not np.all(np.isfinite(vector)):
        raise ValueError("Embedding endpoint returned an invalid pooled vector")
    norm = np.linalg.norm(vector)
    if not math.isfinite(float(norm)) or norm == 0:
        raise ValueError("Embedding endpoint returned a zero or invalid norm")
    return vector / norm


class Embedder:
    def __init__(self, port, model):
        self.endpoint = f"http://127.0.0.1:{port}/v1/embeddings"
        self.model = model
        # Local measurements must never be routed through a configured proxy.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def __call__(self, texts):
        payload = json.dumps({"input": texts, "model": self.model,
                              "encoding_format": "float"}).encode()
        request = urllib.request.Request(self.endpoint, data=payload,
                                         headers={"Content-Type": "application/json"})
        started = time.perf_counter_ns()
        try:
            with self.opener.open(request, timeout=180) as response:
                result = json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise RuntimeError("Local embedding request failed") from error
        data = result.get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise ValueError("Embedding response count does not match input count")
        if sorted(item.get("index") for item in data) != list(range(len(texts))):
            raise ValueError("Embedding response indices do not match input order")
        vectors = [embedding_vector(item["embedding"])
                   for item in sorted(data, key=lambda item: item["index"])]
        if len({len(vector) for vector in vectors}) != 1:
            raise ValueError("Embedding dimensions differ within a response")
        elapsed_ms = (time.perf_counter_ns() - started) / 1e6
        return vectors, elapsed_ms


def write_row(handle, row):
    handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    handle.flush()


def score_pairs(pairs, dataset, embed, batch_size, pair_log, vector_log):
    first = []
    first_ms = []
    for offset in range(0, len(pairs), batch_size):
        batch = pairs[offset:offset + batch_size]
        vectors, elapsed = embed([pair["question1"] for pair in batch])
        first.extend(vectors)
        first_ms.extend([elapsed / len(batch)] * len(batch))
        for pair, vector in zip(batch, vectors):
            write_row(vector_log, {"dataset": dataset, "id": pair["id"], "side": 1,
                                   "embedding": vector.tolist(), "batch_embed_ms": elapsed,
                                   "batch_size": len(batch)})
    matrix = np.stack(first)
    store_rows = []
    for index, pair in enumerate(pairs):
        # Every query is embedded even if its text occurred earlier. These times
        # represent a request to the model, not an application embedding cache hit.
        (vector,), embed_ms = embed([pair["question2"]])
        if len(vector) != matrix.shape[1]:
            raise ValueError("Embedding dimensions changed between requests")
        pair_score = float(np.clip(matrix[index] @ vector, -1, 1))
        write_row(vector_log, {"dataset": dataset, "id": pair["id"], "side": 2,
                               "embedding": vector.tolist(), "embed_ms": embed_ms})
        row = {"dataset": dataset, "index": index, "id": pair["id"],
               "same_answer": pair["same_answer"], "cosine_similarity": pair_score,
               "stored_embed_ms_per_item": first_ms[index], "query_embed_ms": embed_ms}
        if dataset == "ours":
            row.update(question1=pair["question1"], question2=pair["question2"])
        if "reason" in pair:
            row["reason"] = pair["reason"]
        write_row(pair_log, row)
        if dataset == "public":
            start = time.perf_counter_ns()
            similarities = matrix @ vector
            # np.argmax selects the lowest source index for an exact tie.
            nearest = int(np.argmax(similarities))
            nearest_score = float(np.clip(similarities[nearest], -1, 1))
            lookup_ms = (time.perf_counter_ns() - start) / 1e6
            store_rows.append({"dataset": dataset, "index": index, "id": pair["id"],
                               "same_answer": pair["same_answer"], "nearest_index": nearest,
                               "nearest_id": pairs[nearest]["id"],
                               "nearest_similarity": nearest_score,
                               "nearest_correct": bool(nearest == index and pair["same_answer"]),
                               "paired_similarity": pair_score, "embed_ms": embed_ms,
                               "lookup_ms": lookup_ms, "total_ms": embed_ms + lookup_ms})
        if (index + 1) % 100 == 0:
            print(f"{dataset}: {index + 1} queries measured", flush=True)
    return store_rows, int(matrix.shape[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18083)
    parser.add_argument("--model", default="embedding")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--public-pairs", type=Path)
    parser.add_argument("--our-pairs", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--scratch", type=Path)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or not 1 <= args.batch_size <= 128:
        parser.error("Port or batch size is outside the accepted range")
    demo = Path(__file__).resolve().parent
    public_path = args.public_pairs
    ours_path = args.our_pairs or demo / "fixtures/pairs.json"
    output = args.output or demo / "results"
    scratch = args.scratch or demo.parents[2] / ".studio/ai-channel/caching"
    output.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    if public_path:
        public = load_pairs(public_path)
    else:
        # The public source contains identities. The pinned loader keeps its
        # downloaded bytes and selected text in memory, persisting only IDs.
        from public_data import load_pairs as load_public_pairs
        public = validate_pairs(load_public_pairs())
    ours = load_pairs(ours_path)
    if len(public) != 2000:
        raise ValueError("Public fixture must contain the predeclared 2000 pairs")
    if len(ours) != 60 or sum(pair["same_answer"] for pair in ours) != 30:
        raise ValueError("Authored fixture must contain 30 positive and 30 negative pairs")
    for name in ("semantic-pairs.jsonl", "semantic-store.jsonl", "semantic-run.jsonl"):
        if (output / name).exists():
            raise ValueError("Semantic output already exists; choose a fresh output directory")
    started = time.time()
    embed = Embedder(args.port, args.model)
    with (output / "semantic-pairs.jsonl").open("x") as pair_log, \
         (scratch / "semantic-embeddings.jsonl").open("w") as vector_log:
        store_rows, dimensions = score_pairs(public, "public", embed, args.batch_size,
                                             pair_log, vector_log)
        _, our_dimensions = score_pairs(ours, "ours", embed, args.batch_size,
                                        pair_log, vector_log)
    if dimensions != our_dimensions:
        raise ValueError("Embedding dimensions changed across datasets")
    with (output / "semantic-store.jsonl").open("x") as handle:
        for row in store_rows:
            write_row(handle, row)
    with (output / "semantic-run.jsonl").open("x") as handle:
        write_row(handle, {"started_unix": started, "ended_unix": time.time(),
                           "public_count": len(public), "our_count": len(ours),
                           "dimensions": dimensions, "batch_size": args.batch_size,
                           "public_pairs_sha256": hashlib.sha256(json.dumps(public, sort_keys=True,
                               ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(),
                           "our_fixture_sha256": digest(ours_path),
                           "lookup": "exact cosine over every stored first question",
                           "ties": "lowest source index", "query_batch_size": 1,
                           "timing": "client request plus normalization; exact lookup separately"})
    print("Semantic measurements complete", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Avoid copying environment-specific exception paths into public logs.
        detail = str(error) if type(error) in (ValueError, RuntimeError) else "See the measurement inputs and server state"
        print(f"Semantic measurement failed: {type(error).__name__}: {detail}", file=sys.stderr)
        sys.exit(1)
