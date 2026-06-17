#!/bin/bash
# EVEZ Voice Dataset Preparer
# Takes a voice sample MP3/WAV and prepares it for both XTTS and RVC cloning

set -e

SAMPLE="${1:?Usage: prep-voice-dataset.sh <voice_sample.mp3>}"
OUTDIR="${2:-./voice-dataset}"

mkdir -p "$OUTDIR/xtts" "$OUTDIR/rvc" "$OUTDIR/rvc/chunks"

echo "🎙️ Preparing voice dataset from: $SAMPLE"

# Full sample for XTTS (22kHz mono WAV — what Coqui expects)
ffmpeg -y -i "$SAMPLE" -ar 22050 -ac 1 "$OUTDIR/xtts/voice_sample.wav" 2>/dev/null
echo "✅ XTTS: $OUTDIR/xtts/voice_sample.wav"

# Full sample for RVC (44kHz mono WAV)
ffmpeg -y -i "$SAMPLE" -ar 44100 -ac 1 "$OUTDIR/rvc/voice_sample.wav" 2>/dev/null
echo "✅ RVC: $OUTDIR/rvc/voice_sample.wav"

# Slice into 10-second chunks for RVC training
ffmpeg -y -i "$SAMPLE" -f segment -segment_time 10 -c copy "$OUTDIR/rvc/chunks/chunk_%03d.mp3" 2>/dev/null
N=$(ls "$OUTDIR/rvc/chunks/"chunk_*.mp3 2>/dev/null | wc -l)
echo "✅ RVC chunks: $N files"

# Create metadata
cat > "$OUTDIR/metadata.json" << META
{
  "source": "$SAMPLE",
  "prepared": "$(date -Iseconds)",
  "xtts_sample": "xtts/voice_sample.wav",
  "rvc_sample": "rvc/voice_sample.wav",
  "rvc_chunks": $N,
  "ready_for_colab": true
}
META

echo ""
echo "📦 Dataset ready: $OUTDIR"
echo "   Upload to Colab and run the EVEZ Voice Cloning notebook"
