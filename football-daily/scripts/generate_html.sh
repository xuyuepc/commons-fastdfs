#!/usr/bin/env bash
# 每日生成五大联赛 HTML 日报
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="${HOME}/.local/bin:${PATH}"
DATE="${1:-}"
if [[ -n "$DATE" ]]; then
  python3 -m football_daily --date "$DATE" --open
else
  python3 -m football_daily --open
fi
echo "HTML 目录: $(pwd)/reports"