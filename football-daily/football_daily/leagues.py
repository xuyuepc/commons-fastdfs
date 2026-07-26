from __future__ import annotations

# football-data.co.uk 代码
BIG5 = {
    "EPL": {
        "code": "E0",
        "name": "英超",
        "fd_name": "ENG Premier League",
        "oddsmath_keys": ("England - Premier League", "England Premier League"),
    },
    "LALIGA": {
        "code": "SP1",
        "name": "西甲",
        "fd_name": "ESP La Liga",
        "oddsmath_keys": (
            "Spain - Primera Division",
            "Spain - La Liga",
            "Spain Primera Division",
        ),
    },
    "SERIEA": {
        "code": "I1",
        "name": "意甲",
        "fd_name": "ITA Serie A",
        "oddsmath_keys": ("Italy - Serie A", "Italy Serie A"),
    },
    "BUNDESLIGA": {
        "code": "D1",
        "name": "德甲",
        "fd_name": "DEU Bundesliga 1",
        "oddsmath_keys": ("Germany - Bundesliga", "Germany Bundesliga"),
    },
    "LIGUE1": {
        "code": "F1",
        "name": "法甲",
        "fd_name": "FRA Ligue 1",
        "oddsmath_keys": ("France - Ligue 1", "France Ligue 1"),
    },
}

# OddsMath / football-data 常见队名对齐
TEAM_ALIASES = {
    "Man United": "Man United",
    "Manchester United": "Man United",
    "Man City": "Man City",
    "Manchester City": "Man City",
    "Tottenham Hotspur": "Tottenham",
    "Tottenham": "Tottenham",
    "Spurs": "Tottenham",
    "West Ham United": "West Ham",
    "West Ham": "West Ham",
    "Newcastle United": "Newcastle",
    "Newcastle": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Nott'm Forest": "Nott'm Forest",
    "Wolverhampton Wanderers": "Wolves",
    "Wolves": "Wolves",
    "Brighton & Hove Albion": "Brighton",
    "Brighton": "Brighton",
    "Leicester City": "Leicester",
    "Leeds United": "Leeds",
    "Ipswich Town": "Ipswich",
    "Athletic Bilbao": "Ath Bilbao",
    "Athletic Club": "Ath Bilbao",
    "Atletico Madrid": "Ath Madrid",
    "Atlético Madrid": "Ath Madrid",
    "Ath Madrid": "Ath Madrid",
    "Real Madrid": "Real Madrid",
    "Barcelona": "Barcelona",
    "FC Barcelona": "Barcelona",
    "Sevilla": "Sevilla",
    "Sevilla FC": "Sevilla",
    "Real Sociedad": "Sociedad",
    "Inter": "Inter",
    "Inter Milan": "Inter",
    "Internazionale": "Inter",
    "AC Milan": "Milan",
    "Milan": "Milan",
    "Napoli": "Napoli",
    "SSC Napoli": "Napoli",
    "Juventus": "Juventus",
    "AS Roma": "Roma",
    "Roma": "Roma",
    "Lazio": "Lazio",
    "Atalanta": "Atalanta",
    "Bayern Munich": "Bayern Munich",
    "Bayern München": "Bayern Munich",
    "Borussia Dortmund": "Dortmund",
    "Dortmund": "Dortmund",
    "RB Leipzig": "RB Leipzig",
    "Bayer Leverkusen": "Leverkusen",
    "Leverkusen": "Leverkusen",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "Paris Saint Germain": "Paris SG",
    "Paris Saint-Germain": "Paris SG",
    "PSG": "Paris SG",
    "Paris SG": "Paris SG",
    "Marseille": "Marseille",
    "Olympique Marseille": "Marseille",
    "Lyon": "Lyon",
    "Olympique Lyonnais": "Lyon",
    "Monaco": "Monaco",
    "AS Monaco": "Monaco",
    "Lille": "Lille",
    "FC Seoul": "Seoul",
    "Ulsan HD": "Ulsan",
    "Ulsan Hyundai": "Ulsan",
    "Gwangju FC": "Gwangju",
    "Jeju United": "Jeju",
    "Jeju SK": "Jeju",
    "FC Anyang": "Anyang",
    "Gangwon FC": "Gangwon",
    "Incheon United": "Incheon",
    "Bucheon FC 1995": "Bucheon",
    "Jeonbuk Hyundai Motors": "Jeonbuk",
    "Jeonbuk FC": "Jeonbuk",
    "Pohang Steelers": "Pohang",
    "Gimcheon Sangmu": "Sangmu",
    "Daejeon Hana Citizen": "Daejeon",
    "Daejeon Citizen": "Daejeon",
}


def normalize_team(name: str) -> str:
    name = (name or "").strip()
    return TEAM_ALIASES.get(name, name)


def match_big5_league(label: str) -> str | None:
    s = (label or "").replace("‐", "-").replace("–", "-").strip()
    sl = s.lower()
    # 排除女足 / 青年 / 乙级等
    if any(
        x in sl
        for x in (
            "women",
            "woman",
            "u17",
            "u18",
            "u19",
            "u20",
            "u21",
            "u23",
            "youth",
            " reserve",
            "2.",
            "2nd",
            "segunda",
            "serie b",
            "bundesliga 2",
            "2 bundesliga",
            "championship",
            "ligue 2",
            "la liga 2",
            "primera division women",
        )
    ):
        return None

    for key, meta in BIG5.items():
        for k in meta["oddsmath_keys"]:
            if sl == k.lower() or sl.endswith(k.lower()) or k.lower() == sl:
                return key
        if key == "EPL" and sl in {"england - premier league", "england premier league"}:
            return key
        if key == "LALIGA" and sl in {
            "spain - primera division",
            "spain - la liga",
            "spain primera division",
            "spain la liga",
        }:
            return key
        if key == "SERIEA" and sl in {"italy - serie a", "italy serie a"}:
            return key
        if key == "BUNDESLIGA" and sl in {
            "germany - bundesliga",
            "germany bundesliga",
            "germany - bundesliga 1",
        }:
            return key
        if key == "LIGUE1" and sl in {"france - ligue 1", "france ligue 1"}:
            return key
    return None


def season_codes_for_date(day) -> list[str]:
    """返回用于建模的 football-data 赛季代码，近两个赛季。"""
    y = day.year
    m = day.month
    # 欧洲赛季大致 8 月开始
    if m >= 8:
        current = f"{str(y)[-2:]}{str(y+1)[-2:]}"
        prev = f"{str(y-1)[-2:]}{str(y)[-2:]}"
    else:
        current = f"{str(y-1)[-2:]}{str(y)[-2:]}"
        prev = f"{str(y-2)[-2:]}{str(y-1)[-2:]}"
    return [prev, current]