from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .config import CACHE_DIR, ODDSMATH_LEAGUE_KEYS, USER_AGENT
from .teams import normalize_team


def _cache_path(day: date) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"oddsmath_{day.isoformat()}.csv"


def fetch_oddsmath_day(day: date | None = None, use_cache: bool = True) -> pd.DataFrame:
    """抓取 OddsMath 某日足球欧赔（尽量解析全部联赛，再按需过滤）。"""
    day = day or date.today()
    cache = _cache_path(day)
    if use_cache and cache.exists():
        df = pd.read_csv(cache)
        if not df.empty:
            return df

    url = f"https://www.oddsmath.com/football/matches/{day.isoformat()}/"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    df = parse_oddsmath_html(resp.text, day)
    if not df.empty:
        df.to_csv(cache, index=False)
    return df


def parse_oddsmath_html(html: str, day: date) -> pd.DataFrame:
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict] = []

    # 优先用结构化选择器（homeTeam / awayTeam）
    rows.extend(_parse_oddsmath_structured(soup, day))

    # 回退：泛化 tr 解析
    if not rows:
        current_league = None
        for tr in soup.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if not cells:
                continue
            joined = " ".join(cells)
            if len(cells) <= 2 and ("‐" in joined or "-" in joined) and any(
                k in joined for k in ("League", "Liga", "Serie", "Division", "Allsvenskan", "Super")
            ):
                current_league = joined.replace("‐", "-").strip()
                continue
            odds = _extract_three_odds(cells)
            if not odds:
                continue
            teams = _extract_teams(cells)
            if not teams:
                continue
            home, away = teams
            kickoff = _extract_time(cells)
            status = "finished" if any("Finished" in c for c in cells) else "scheduled"
            score = None
            for c in cells:
                m = re.search(r"Finished\s+(\d+-\d+)", c)
                if m:
                    score = m.group(1)
            rows.append(
                {
                    "date": day.isoformat(),
                    "kickoff": kickoff,
                    "league": current_league or "",
                    "home": normalize_team(home),
                    "away": normalize_team(away),
                    "odds_home": odds[0],
                    "odds_draw": odds[1],
                    "odds_away": odds[2],
                    "status": status,
                    "score": score,
                    "source": "oddsmath",
                }
            )

    if not rows:
        text = soup.get_text("\n", strip=True)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        rows = _parse_text_fallback(lines, day)

    if not rows:
        return pd.DataFrame(
            columns=[
                "date",
                "kickoff",
                "league",
                "home",
                "away",
                "odds_home",
                "odds_draw",
                "odds_away",
                "status",
                "score",
                "source",
            ]
        )
    return pd.DataFrame(rows).drop_duplicates(["league", "home", "away", "kickoff"])


def _parse_oddsmath_structured(soup: BeautifulSoup, day: date) -> list[dict]:
    rows: list[dict] = []
    for home_a in soup.select("td.homeTeam a.event"):
        tr = home_a.find_parent("tr")
        if tr is None:
            continue
        away_td = tr.select_one("td.awayTeam")
        time_td = tr.select_one("td.time")
        if away_td is None:
            continue
        home = home_a.get_text(strip=True)
        away = away_td.get_text(strip=True)
        kickoff = time_td.get_text(strip=True) if time_td else ""
        href = home_a.get("href") or ""
        league = _league_from_href(href)
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        odds = _extract_three_odds(cells)
        if not odds:
            continue
        status = "finished" if any("Finished" in c for c in cells) else "scheduled"
        score = None
        for c in cells:
            m = re.search(r"Finished\s+(\d+-\d+)", c)
            if m:
                score = m.group(1)
        rows.append(
            {
                "date": day.isoformat(),
                "kickoff": kickoff,
                "league": league,
                "home": normalize_team(home),
                "away": normalize_team(away),
                "odds_home": odds[0],
                "odds_draw": odds[1],
                "odds_away": odds[2],
                "status": status,
                "score": score,
                "source": "oddsmath",
            }
        )
    return rows


def _league_from_href(href: str) -> str:
    # /football/south-korea/k-league-classic-1555/...
    m = re.search(r"/football/([^/]+)/([^/]+)-\d+/", href)
    if not m:
        return ""
    country = m.group(1).replace("-", " ").title()
    league = m.group(2).replace("-", " ").title()
    return f"{country} - {league}"


def filter_kleague(odds_df: pd.DataFrame) -> pd.DataFrame:
    if odds_df.empty:
        return odds_df
    mask = odds_df["league"].fillna("").apply(_is_kleague_label)
    # also match by known team set if league label missing
    if not mask.any():
        known = {
            "Seoul",
            "Ulsan",
            "Gwangju",
            "Jeju",
            "Anyang",
            "Gangwon",
            "Incheon",
            "Bucheon",
            "Jeonbuk",
            "Pohang",
            "Sangmu",
            "Daejeon",
        }
        mask = odds_df["home"].isin(known) & odds_df["away"].isin(known)
    return odds_df.loc[mask].reset_index(drop=True)


def _is_kleague_label(label: str) -> bool:
    s = label.replace("‐", "-").replace("–", "-").lower()
    if "korea" not in s:
        return False
    return "k-league classic" in s or "k league 1" in s or "k-league 1" in s


def _extract_three_odds(cells: list[str]) -> tuple[float, float, float] | None:
    nums: list[float] = []
    for c in cells:
        # skip integers that look like bookmaker counts
        if re.fullmatch(r"\d{1,2}", c):
            continue
        if re.fullmatch(r"-?\d+\.\d+%", c):
            continue
        if re.fullmatch(r"\d+\.\d{1,4}", c):
            val = float(c)
            if 1.01 <= val <= 50:
                nums.append(val)
    if len(nums) < 3:
        return None
    # last three decimal odds in row are usually 1 X 2
    a, b, c = nums[-3], nums[-2], nums[-1]
    # sanity: draw usually middle-ish
    return a, b, c


def _extract_teams(cells: list[str]) -> tuple[str, str] | None:
    # common pattern: TIME | Home | - | Away | ...
    cleaned = [c for c in cells if c not in {"‐", "-", "–"}]
    # remove time-only / odds / finished
    candidates: list[str] = []
    for c in cleaned:
        if re.fullmatch(r"\d{1,2}:\d{2}", c):
            continue
        if re.fullmatch(r"\d+\.\d+", c):
            continue
        if re.fullmatch(r"-?\d+\.\d+%", c):
            continue
        if c.startswith("Finished"):
            continue
        if re.fullmatch(r"\d{1,2}", c):
            continue
        if len(c) >= 2:
            candidates.append(c)
    if len(candidates) >= 2:
        return candidates[0], candidates[1]
    return None


def _extract_time(cells: list[str]) -> str:
    for c in cells:
        if re.fullmatch(r"\d{1,2}:\d{2}", c):
            return c
    return ""


def _parse_text_fallback(lines: list[str], day: date) -> list[dict]:
    rows: list[dict] = []
    league = ""
    i = 0
    while i < len(lines):
        ln = lines[i]
        if any(k.split("‐")[-1].strip() in ln or "K-League" in ln for k in ODDSMATH_LEAGUE_KEYS) or (
            "Korea" in ln and "League" in ln
        ):
            league = ln
            i += 1
            continue
        m = re.match(r"^(\d{1,2}:\d{2})$", ln)
        if m and i + 6 < len(lines):
            # expect home, -, away, ...
            home = lines[i + 1]
            away = lines[i + 3] if lines[i + 2] in {"‐", "-", "–"} else lines[i + 2]
            # scan forward for 3 odds
            odds_vals: list[float] = []
            for j in range(i, min(i + 12, len(lines))):
                if re.fullmatch(r"\d+\.\d{1,4}", lines[j]):
                    odds_vals.append(float(lines[j]))
            if len(odds_vals) >= 3 and home and away:
                rows.append(
                    {
                        "date": day.isoformat(),
                        "kickoff": m.group(1),
                        "league": league,
                        "home": normalize_team(home),
                        "away": normalize_team(away),
                        "odds_home": odds_vals[-3],
                        "odds_draw": odds_vals[-2],
                        "odds_away": odds_vals[-1],
                        "status": "scheduled",
                        "score": None,
                        "source": "oddsmath",
                    }
                )
        i += 1
    return rows


def demo_kleague_odds(day: date | None = None) -> pd.DataFrame:
    """网络失败时的演示数据，保证页面可打开。"""
    day = day or date.today()
    data = [
        ("10:30", "Gwangju", "Jeju", 4.317, 3.41, 2.016),
        ("10:30", "Anyang", "Gangwon", 4.294, 3.29, 2.06),
        ("10:30", "Incheon", "Bucheon", 1.758, 3.52, 5.912),
        ("10:30", "Seoul", "Ulsan", 1.862, 3.91, 4.38),
    ]
    return pd.DataFrame(
        [
            {
                "date": day.isoformat(),
                "kickoff": k,
                "league": "South Korea - K-League Classic",
                "home": h,
                "away": a,
                "odds_home": oh,
                "odds_draw": od,
                "odds_away": oa,
                "status": "scheduled",
                "score": None,
                "source": "demo",
            }
            for k, h, a, oh, od, oa in data
        ]
    )