from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .config import CACHE_DIR, KLEAGUE1, USER_AGENT
from .teams import normalize_team


def _cache_path(season: int) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"kleague1_results_{season}.csv"


def fetch_kleague1_results(season: int = 2026, use_cache: bool = True) -> pd.DataFrame:
    """从 TheSportsDB 赛季页解析 K League 1 已赛比分。"""
    cache = _cache_path(season)
    if use_cache and cache.exists():
        df = pd.read_csv(cache, parse_dates=["date"])
        if not df.empty:
            return df

    url = KLEAGUE1["season_url"].format(season=season)
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    df = parse_thesportsdb_season_html(resp.text)
    if not df.empty:
        df.to_csv(cache, index=False)
    return df


def parse_thesportsdb_season_html(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict] = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        date_text = re.sub(r"\s+", " ", tds[0].get_text(" ", strip=True))
        dm = re.fullmatch(r"(\d{1,2}\s+\w{3}\s+\d{2})", date_text)
        if not dm:
            continue
        score_text = None
        for td in tds:
            t = td.get_text(" ", strip=True)
            if re.fullmatch(r"\d\s*-\s*\d", t):
                score_text = t
                break
        if not score_text:
            continue
        home_links = tr.select("a.d-none.d-lg-block")
        if len(home_links) < 2:
            # fallback: event title texts
            texts = [a.get_text(strip=True) for a in tr.select("a") if a.get_text(strip=True)]
            # unlikely; skip
            if len(texts) < 2:
                continue
            home, away = texts[0], texts[1]
        else:
            home = home_links[0].get_text(strip=True)
            away = home_links[1].get_text(strip=True)
        hg, ag = [int(x) for x in re.findall(r"\d", score_text)[:2]]
        rows.append(
            {
                "date": datetime.strptime(dm.group(1), "%d %b %y"),
                "home": normalize_team(home),
                "away": normalize_team(away),
                "hg": hg,
                "ag": ag,
                "league": "K League 1",
            }
        )
    if not rows:
        return pd.DataFrame(columns=["date", "home", "away", "hg", "ag", "league"])
    df = pd.DataFrame(rows).drop_duplicates(["date", "home", "away"]).sort_values("date")
    return df.reset_index(drop=True)