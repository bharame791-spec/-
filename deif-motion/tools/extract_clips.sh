#!/usr/bin/env bash
# Extracts archival B-roll from the Al Jazeera documentary as frame sequences.
# Crop keeps the middle band: removes channel logo (top) and burned-in subtitles (bottom).
set -e
SRC="$1"; OUT="$2"
clip(){ # name start duration
  mkdir -p "$OUT/$1"
  ffmpeg -v error -y -ss "$2" -t "$3" -i "$SRC" -vf "crop=300:250:60:150,fps=25,scale=720:600:flags=lanczos,format=gray" -q:v 3 "$OUT/$1/%04d.jpg"
  echo "$1: $(ls "$OUT/$1" | wc -l) frames"
}
clip silhouette 241 6
clip alley      36 4
clip camp       40 7
clip university 64 9
clip arrest89   94 5
clip street     84 3
clip checkpoint 116.6 4.4
clip armor      165 5
clip ruins      275.1 2.3
