#!/usr/bin/env bash
set -euo pipefail

INPUT="renders/prematch_prediction.mp4"
OUTPUT="renders/prematch_prediction_compressed.mp4"

if [ ! -f "$INPUT" ]; then
  echo "Missing render: $INPUT" >&2
  exit 1
fi

ffmpeg -y -i "$INPUT" -vcodec libx264 -crf 28 -preset fast -movflags +faststart "$OUTPUT"
mv "$OUTPUT" "$INPUT"

echo "Compressed: $INPUT"
