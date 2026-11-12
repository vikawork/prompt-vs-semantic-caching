#!/usr/bin/env bash
# CPU-only server. The caller owns the container and must remove it.
set -euo pipefail
mode=${1:?chat or embedding} name=${2:?container name} port=${3:?port} slots=${4:-1}
case "$name" in vk-caching-*) ;; *) echo 'Invalid caching container name' >&2; exit 2;; esac
case "$slots" in 1|2) ;; *) exit 2;; esac
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
MODEL_DIR="$ROOT/.studio/ai-channel/caching/models"
IMAGE=ghcr.io/ggml-org/llama.cpp:full-b12211@sha256:8960de326dd60972cc4d442531f4efa006416d5896da2a39f0def0b55cbcb0c2
# The amendment permits this pinned image; require it locally rather than pulling implicitly.
docker image inspect "$IMAGE" >/dev/null
args=(-m /models/qwen3.5-0.8b-q8_0.gguf --jinja -c "$((8192 * slots))" --parallel "$slots" --cache-ram 0)
if [[ "$mode" == embedding ]]; then
  args=(-m /models/bge-small-en-v1.5-q8_0.gguf --embedding --pooling cls --alias embedding -c 512 --parallel 1 -b 512 -ub 512)
elif [[ "$mode" != chat ]]; then
  exit 2
fi
docker run -d --pull never --name "$name" --cap-drop ALL --security-opt no-new-privileges \
  --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m --pids-limit 128 \
  -p "127.0.0.1:$port:8080" -v "$MODEL_DIR:/models:ro" --entrypoint /usr/bin/nice "$IMAGE" \
  -n 10 /app/llama-server "${args[@]}" -ngl 0 -t 8 -tb 8 --threads-http 1 --host 0.0.0.0 --port 8080 >/dev/null
for ((i=0;i<120;i++)); do
  if curl --noproxy '*' -fsS "http://127.0.0.1:$port/health" >/dev/null 2>&1; then
    echo 'CPU server ready'; exit 0
  fi
  sleep 1
done
echo 'CPU server failed readiness' >&2
exit 1
