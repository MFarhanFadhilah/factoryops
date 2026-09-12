#!/usr/bin/env bash
# Switch which chat+embedding pair is loaded from factoryops-kit.
# Usage: ./switch-model.sh [status | 1.7b | 4b | 8b]
#   status (or no argument) reports which model is actually in use —
#   run this first if you're not sure what's active right now.
set -euo pipefail

MODEL="${1:-status}"

if [ "$MODEL" = "status" ]; then
  echo "== loaded in memory right now (actually in use) =="
  ps_out="$(ollama ps 2>/dev/null)" || { echo "No ollama server reachable at \$OLLAMA_HOST (default 127.0.0.1:11434)"; exit 0; }
  body="$(echo "$ps_out" | tail -n +2)"
  if [ -z "$body" ]; then
    echo "Nothing loaded — server is idle (models unload after inactivity). It'll load on the next request."
  else
    echo "$ps_out"
  fi
  echo
  echo "-- everything available on disk (not necessarily in use) --"
  ollama list 2>/dev/null
  exit 0
fi

KIT="$(pwd)/load/factoryops-kit/model-backup/ollama"

case "$MODEL" in
  1.7b|4b) CHAT="qwen3:$MODEL"; EMBED="nomic-embed-text";   EMBED_DIR="embed-nomic-embed-text" ;;
  8b)      CHAT="qwen3:8b";     EMBED="mxbai-embed-large";  EMBED_DIR="embed-mxbai-embed-large" ;;
  *) echo "Unknown model '$MODEL' — expected status, 1.7b, 4b, or 8b" >&2; exit 1 ;;
esac

TARGET="$KIT/$MODEL"
[ -d "$TARGET" ] || { echo "Missing $TARGET — is factoryops-kit pasted into load/?" >&2; exit 1; }

echo "== stopping any running ollama server =="
sudo systemctl stop ollama 2>/dev/null || true
pkill -f "ollama serve" 2>/dev/null || true
sleep 1

echo "== merging $EMBED into $MODEL (idempotent — skips files already there) =="
cp -n "$KIT/$EMBED_DIR/blobs/"* "$TARGET/blobs/"
mkdir -p "$TARGET/manifests/registry.ollama.ai/library"
cp -rn "$KIT/$EMBED_DIR/manifests/registry.ollama.ai/library/$EMBED" \
       "$TARGET/manifests/registry.ollama.ai/library/"

echo "== starting ollama serve against $TARGET =="
export OLLAMA_MODELS="$TARGET"
ollama serve > /tmp/ollama-switch.log 2>&1 &
sleep 2

echo "== verifying =="
ollama list
ollama run "$CHAT" "Reply exactly: FACTORYOPS LOCAL MODEL READY"
curl -s http://127.0.0.1:11434/api/embed -d "{\"model\":\"$EMBED\",\"input\":\"test\"}" | head -c 120
echo
echo "Active pair: $CHAT + $EMBED  (OLLAMA_MODELS=$TARGET)"
