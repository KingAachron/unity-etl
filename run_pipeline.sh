#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_APK="${1:-$PROJECT_ROOT/input/app.apk}"
WORK_DIR="$PROJECT_ROOT/work"
OUT_DIR="$PROJECT_ROOT/output"
LOG_DIR="$PROJECT_ROOT/logs"
VENV_DIR="$PROJECT_ROOT/.venv"
mkdir -p "$WORK_DIR" "$OUT_DIR" "$LOG_DIR"

echo "[$(date -Is)] === Universal Android/Unity Data Pipeline ==="
echo "Target APK: $INPUT_APK"

if [[ ! -f "$INPUT_APK" ]]; then
    echo "Error: APK not found at $INPUT_APK" >&2
    exit 1
fi

command -v unzip >/dev/null || exit 1
command -v sha256sum >/dev/null || exit 1
command -v apktool >/dev/null || exit 1

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating venv..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install -r "$PROJECT_ROOT/requirements.txt" >/dev/null

APK_SHA="$(sha256sum "$INPUT_APK" | awk '{print $1}')"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
RUN_WORK="$WORK_DIR/run_$RUN_ID"
mkdir -p "$RUN_WORK"

cp -f "$INPUT_APK" "$RUN_WORK/app.apk"
python3 "$PROJECT_ROOT/src/extractor.py" --apk "$RUN_WORK/app.apk" --work "$RUN_WORK" --out "$OUT_DIR" --run-id "$RUN_ID" --apk-sha "$APK_SHA"
python3 "$PROJECT_ROOT/src/compiler.py" --out "$OUT_DIR" --run-id "$RUN_ID"

echo "Done. Outputs in $OUT_DIR"

