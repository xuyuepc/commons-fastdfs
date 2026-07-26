from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
REPORTS_DIR = ROOT / "reports"

# TheSportsDB: K League 1（可选）
KLEAGUE1 = {
    "id": "4689",
    "name": "K League 1",
    "slug": "k-league-1",
    "season_url": "https://www.thesportsdb.com/season/4689-south-korean-k-league-1/{season}",
}

# OddsMath 页面里韩职联赛标题
ODDSMATH_LEAGUE_KEYS = (
    "South Korea‐ K-League Classic",
    "South Korea- K-League Classic",
    "South Korea – K-League Classic",
    "South Korea K-League Classic",
)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)