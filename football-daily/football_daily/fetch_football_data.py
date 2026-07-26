from __future__ import annotations

from datetime import date
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from .config import CACHE_DIR, USER_AGENT
from .leagues import BIG5, normalize_team, season_codes_for_date


def _cache_path(code: str, season: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"fd_{code}_{season}.csv"


def fetch_league_results(
    league_key: str,
    seasons: list[str] | None = None,
    day: date | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    meta = BIG5[league_key]
    day = day or date.today()
    seasons = seasons or season_codes_for_date(day)
    frames: list[pd.DataFrame] = []
    for season in seasons:
        df = _download_season(meta["code"], season, use_cache=use_cache)
        if df.empty:
            continue
        df = df.copy()
        df["league_key"] = league_key
        df["league"] = meta["name"]
        df["season"] = season
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["date", "home", "away", "hg", "ag", "league", "league_key"])
    out = pd.concat(frames, ignore_index=True)
    out = out.dropna(subset=["date", "home", "away", "hg", "ag"])
    out = out.sort_values("date").drop_duplicates(["date", "home", "away", "league_key"])
    return out.reset_index(drop=True)


def fetch_big5_results(day: date | None = None, use_cache: bool = True) -> pd.DataFrame:
    day = day or date.today()
    frames = [fetch_league_results(k, day=day, use_cache=use_cache) for k in BIG5]
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame(columns=["date", "home", "away", "hg", "ag", "league", "league_key"])
    return pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)


def big5_club_set(results: pd.DataFrame) -> set[str]:
    if results.empty:
        return set()
    return set(results["home"]).union(set(results["away"]))


def _download_season(code: str, season: str, use_cache: bool = True) -> pd.DataFrame:
    cache = _cache_path(code, season)
    if use_cache and cache.exists() and cache.stat().st_size > 100:
        raw = cache.read_text(encoding="utf-8", errors="ignore")
    else:
        url = f"https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        if resp.status_code != 200 or "Div" not in resp.text[:200]:
            return pd.DataFrame()
        raw = resp.content.decode("utf-8", errors="ignore")
        cache.write_text(raw, encoding="utf-8")

    df = pd.read_csv(StringIO(raw))
    if df.empty or "HomeTeam" not in df.columns:
        return pd.DataFrame()

    # 日期格式有 16/08/2024 与可能的其他格式
    dates = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    out = pd.DataFrame(
        {
            "date": dates,
            "home": df["HomeTeam"].map(normalize_team),
            "away": df["AwayTeam"].map(normalize_team),
            "hg": pd.to_numeric(df["FTHG"], errors="coerce"),
            "ag": pd.to_numeric(df["FTAG"], errors="coerce"),
        }
    )
    # 若有盘口列，顺带保留平均欧赔（可用于校验）
    for src, dst in [("AvgH", "hist_odds_home"), ("AvgD", "hist_odds_draw"), ("AvgA", "hist_odds_away")]:
        if src in df.columns:
            out[dst] = pd.to_numeric(df[src], errors="coerce")
    return out.dropna(subset=["date", "hg", "ag"])