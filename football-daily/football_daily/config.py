from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"

# TheSportsDB: K League 1
KLEAGUE1 = {
    "id": "4689",
    "name": "K League 1",
    "slug": "k-league-1",
    "season_url": "https://www.thesportsdb.com/season/4689-south-korean-k-league-1/{season}",
}

TEAM_ALIASES = {
    "Ulsan HD": "Ulsan",
    "Ulsan Hyundai": "Ulsan",
    "Jeju SK": "Jeju",
    "Jeju United": "Jeju",
    "Jeonbuk Hyundai Motors": "Jeonbuk",
    "Jeonbuk FC": "Jeonbuk",
    "Gimcheon Sangmu": "Sangmu",
    "Gimcheon Sangmu FC": "Sangmu",
    "Daejeon Hana Citizen": "Daejeon",
    "Daejeon Citizen": "Daejeon",
    "Bucheon FC 1995": "Bucheon",
    "FC Anyang": "Anyang",
    "FC Seoul": "Seoul",
    "Gwangju FC": "Gwangju",
    "Gangwon FC": "Gangwon",
    "Incheon United": "Incheon",
    "Pohang Steelers": "Pohang",
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